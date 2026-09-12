"""
Ollama HTTP client for DriftLens.

Provides a thin, requests-based wrapper around the Ollama REST API
(https://github.com/ollama/ollama/blob/main/docs/api.md).  All external
LLM libraries are intentionally avoided; only the standard library plus
`requests` is used.

Graceful degradation:
    * ``is_available()`` returns ``False`` (never raises) when Ollama is
      unreachable or the configured model is not present.
    * ``generate()`` raises ``OllamaNotAvailableError`` in those same
      situations so callers can gate LLM calls behind an availability
      check.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class OllamaError(RuntimeError):
    """Base class for all Ollama-related errors."""


class OllamaNotAvailableError(OllamaError):
    """Raised when the Ollama server is unreachable or the model is missing."""


class OllamaParseError(OllamaError):
    """Raised when the LLM response cannot be parsed as valid JSON."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

_INSTALL_HINT = (
    "Ollama is not running. "
    "Install from https://ollama.ai, "
    "then run: ollama pull qwen2.5:7b-instruct"
)


class OllamaClient:
    """Thin HTTP client for the Ollama REST API.

    Parameters
    ----------
    base_url:
        Root URL of the Ollama server.  Defaults to the standard local port.
    model:
        Model tag to use for generation.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b-instruct",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})
        logger.debug("OllamaClient initialised: base_url=%s model=%s", self.base_url, self.model)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return *True* if the server is up **and** the configured model exists.

        Never raises; any connection / HTTP error is swallowed and logged at
        DEBUG level so callers can use this as a simple boolean gate.
        """
        try:
            available_models = self.list_models()
            # Match by prefix so that "qwen2.5:7b-instruct" matches
            # "qwen2.5:7b-instruct" as well as any version-tagged variant.
            for m in available_models:
                if m == self.model or m.startswith(self.model.split(":")[0]):
                    logger.debug("Ollama available; model %r found among %s", self.model, available_models)
                    return True
            logger.debug(
                "Ollama is running but model %r not found. Available: %s",
                self.model,
                available_models,
            )
            return False
        except Exception as exc:  # noqa: BLE001
            logger.debug("Ollama availability check failed: %s", exc)
            return False

    def list_models(self) -> list[str]:
        """Return a list of model name strings currently available in Ollama.

        Raises
        ------
        OllamaError
            If the HTTP request fails or the response is malformed.
        """
        url = f"{self.base_url}/api/tags"
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(f"GET {url} failed: {exc}") from exc

        try:
            data: dict[str, Any] = resp.json()
        except json.JSONDecodeError as exc:
            raise OllamaError(f"Could not parse /api/tags response as JSON: {exc}") from exc

        models_raw: list[dict[str, Any]] = data.get("models", [])
        return [m["name"] for m in models_raw if "name" in m]

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        format_json: bool = False,
        temperature: float = 0.1,
    ) -> str:
        """Send a generation request and return the model's text response.

        Parameters
        ----------
        prompt:
            The user-facing prompt text.
        system_prompt:
            Optional system-level instruction prepended to the conversation.
        format_json:
            When *True*, instructs Ollama to constrain output to valid JSON
            (``"format": "json"``).
        temperature:
            Sampling temperature passed through Ollama's ``options`` block.

        Returns
        -------
        str
            The raw text response from the model (stripped of leading/trailing
            whitespace).

        Raises
        ------
        OllamaNotAvailableError
            If the server is unreachable before or during the request.
        OllamaError
            For any other HTTP-level or response-parsing failure.
        """
        # Gate on availability so callers that bypass is_available() still get
        # a helpful error message.
        if not self.is_available():
            raise OllamaNotAvailableError(_INSTALL_HINT)

        url = f"{self.base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        logger.debug(
            "Sending generate request: model=%s format_json=%s len(prompt)=%d",
            self.model,
            format_json,
            len(prompt),
        )

        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.ConnectionError as exc:
            raise OllamaNotAvailableError(_INSTALL_HINT) from exc
        except requests.Timeout as exc:
            raise OllamaError(f"Request to Ollama timed out after {self.timeout}s") from exc
        except requests.RequestException as exc:
            raise OllamaError(f"POST {url} failed: {exc}") from exc

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise OllamaError(f"Could not parse /api/generate response as JSON: {exc}") from exc

        response_text: str = data.get("response", "")
        if not response_text:
            logger.warning("Ollama returned an empty 'response' field: %s", data)

        return response_text.strip()

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> dict[str, Any]:
        """Generate a response and parse it as JSON.

        Attempts the request once; if the returned text is not valid JSON,
        makes a single corrective follow-up before raising
        ``OllamaParseError``.

        Parameters
        ----------
        prompt:
            The user-facing prompt.
        system_prompt:
            Optional system instruction.

        Returns
        -------
        dict
            Parsed JSON object from the model.

        Raises
        ------
        OllamaParseError
            If both the initial and the retry responses cannot be parsed.
        OllamaNotAvailableError
            If Ollama is not running.
        OllamaError
            For any other generation failure.
        """
        raw = self.generate(prompt, system_prompt=system_prompt, format_json=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                "Initial JSON generation failed; attempting single retry. "
                "Raw response (first 300 chars): %.300s",
                raw,
            )

        # --- Corrective retry -----------------------------------------------
        retry_prompt = (
            "Your previous response was not valid JSON. "
            "Respond with only valid JSON, nothing else. "
            f"Here was your response: {raw}. "
            "Regenerate it as valid JSON."
        )
        retry_raw = self.generate(retry_prompt, system_prompt=system_prompt, format_json=True)
        try:
            return json.loads(retry_raw)
        except json.JSONDecodeError as exc:
            raise OllamaParseError(
                f"Model failed to produce valid JSON after one retry. "
                f"Last raw response: {retry_raw!r}"
            ) from exc
