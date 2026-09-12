"""
edgar_client.py
===============
Thread-safe, rate-limited HTTP client for the SEC EDGAR API.

Design constraints
------------------
* User-Agent header is mandatory for EDGAR (missing = 403).
* EDGAR enforces ≤ 10 req/s; we default to a 0.125 s floor (≈ 8 req/s).
* Exponential back-off (1 → 2 → 4 → 8 → 16 s) on 403 / 429 / 5xx.
* Raises :class:`EdgarClientError` after ``max_retries`` failed attempts.
* All I/O is logged via the standard ``logging`` module; nothing goes to
  stdout via ``print``.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import requests

__all__ = ["EdgarClient", "EdgarClientError"]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class EdgarClientError(RuntimeError):
    """Raised when an EDGAR request fails after all retry attempts.

    Attributes
    ----------
    url : str
        The URL that could not be fetched.
    status_code : int | None
        The final HTTP status code, or ``None`` if the request never completed.
    """

    def __init__(self, message: str, url: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.status_code = status_code

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EdgarClientError(url={self.url!r}, "
            f"status_code={self.status_code!r}, "
            f"message={str(self)!r})"
        )


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


class EdgarClient:
    """Rate-limited, retry-aware HTTP client for SEC EDGAR.

    Parameters
    ----------
    user_agent:
        Value for the ``User-Agent`` header.  SEC requires a non-empty,
        identifiable value or it will return 403.
    min_interval:
        Minimum number of seconds between consecutive requests.  Defaults
        to 0.125 s (≈ 8 req/s), just below EDGAR's 10 req/s cap.
    max_retries:
        How many times to retry after a retryable failure before giving up.
    session:
        Optional pre-configured :class:`requests.Session`.  If ``None`` a
        new session is created internally.

    Thread safety
    -------------
    Rate-limiting is protected by a :class:`threading.Lock`, so multiple
    threads can share one ``EdgarClient`` safely.

    Examples
    --------
    >>> client = EdgarClient()
    >>> data = client.get_json("https://data.sec.gov/submissions/CIK0000320193.json")
    """

    #: HTTP status codes that warrant a retry with back-off.
    RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({403, 429, 500, 502, 503, 504})

    def __init__(
        self,
        user_agent: str = "DriftLens research-project suryatejam2312@gmail.com",
        min_interval: float = 0.125,
        max_retries: int = 5,
        session: requests.Session | None = None,
    ) -> None:
        if not user_agent:
            raise ValueError("user_agent must be a non-empty string.")
        if min_interval < 0:
            raise ValueError("min_interval must be non-negative.")
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1.")

        self.user_agent = user_agent
        self.min_interval = min_interval
        self.max_retries = max_retries

        # Rate-limit state — protected by _lock
        self._lock = threading.Lock()
        self._last_call_time: float = 0.0  # monotonic seconds

        # Requests session
        self._session: requests.Session = session or requests.Session()
        self._session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )

        logger.debug(
            "EdgarClient initialised (user_agent=%r, min_interval=%.3fs, "
            "max_retries=%d)",
            self.user_agent,
            self.min_interval,
            self.max_retries,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _wait_for_rate_limit(self) -> None:
        """Block the calling thread until the minimum inter-request interval
        has elapsed since the last call.  Updates ``_last_call_time`` under
        the lock.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call_time
            if elapsed < self.min_interval:
                sleep_for = self.min_interval - elapsed
                logger.debug("Rate limiter sleeping %.4f s", sleep_for)
                time.sleep(sleep_for)
            self._last_call_time = time.monotonic()

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Return the back-off delay in seconds for *attempt* (0-indexed).

        Sequence: 1, 2, 4, 8, 16 seconds.
        """
        return float(2**attempt)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Fetch *url* and return the :class:`requests.Response`.

        Enforces the minimum inter-request interval and applies exponential
        back-off on retryable HTTP status codes.

        Parameters
        ----------
        url:
            Absolute URL to fetch.
        **kwargs:
            Additional keyword arguments forwarded to
            :meth:`requests.Session.get`.

        Returns
        -------
        requests.Response
            The successful response object.

        Raises
        ------
        EdgarClientError
            If the request fails after ``max_retries`` attempts, or if a
            non-retryable error status code is received.
        """
        last_exc: Exception | None = None
        last_status: int | None = None

        for attempt in range(self.max_retries):
            self._wait_for_rate_limit()

            try:
                logger.debug(
                    "GET %s (attempt %d/%d)", url, attempt + 1, self.max_retries
                )
                response = self._session.get(url, timeout=30, **kwargs)
            except requests.RequestException as exc:
                last_exc = exc
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "Network error on attempt %d/%d for %s: %s. "
                    "Retrying in %.1f s ...",
                    attempt + 1,
                    self.max_retries,
                    url,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue

            last_status = response.status_code

            if response.ok:
                logger.debug(
                    "GET %s -> %d (attempt %d/%d)",
                    url,
                    response.status_code,
                    attempt + 1,
                    self.max_retries,
                )
                return response

            if response.status_code in self.RETRYABLE_STATUS_CODES:
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "HTTP %d on attempt %d/%d for %s. Retrying in %.1f s ...",
                    response.status_code,
                    attempt + 1,
                    self.max_retries,
                    url,
                    delay,
                )
                time.sleep(delay)
                continue

            # Non-retryable client error (4xx other than 403/429)
            raise EdgarClientError(
                f"Non-retryable HTTP {response.status_code} for {url}",
                url=url,
                status_code=response.status_code,
            )

        # Exhausted all retries
        msg = (
            f"Failed to fetch {url} after {self.max_retries} attempts "
            f"(last status={last_status}, last_exc={last_exc!r})"
        )
        logger.error(msg)
        raise EdgarClientError(msg, url=url, status_code=last_status)

    def get_json(self, url: str, **kwargs: Any) -> dict:
        """Fetch *url* and parse the response body as JSON.

        Parameters
        ----------
        url:
            URL that returns a JSON document.
        **kwargs:
            Forwarded to :meth:`get`.

        Returns
        -------
        dict
            Parsed JSON payload.

        Raises
        ------
        EdgarClientError
            On HTTP failure (propagated from :meth:`get`).
        requests.JSONDecodeError
            If the response body is not valid JSON.
        """
        response = self.get(url, **kwargs)
        logger.debug("Parsing JSON from %s (%d bytes)", url, len(response.content))
        return response.json()  # type: ignore[return-value]

    def get_bytes(self, url: str, **kwargs: Any) -> bytes:
        """Fetch *url* and return the raw response body as :class:`bytes`.

        Parameters
        ----------
        url:
            URL to fetch.
        **kwargs:
            Forwarded to :meth:`get`.

        Returns
        -------
        bytes
            Raw response content.

        Raises
        ------
        EdgarClientError
            On HTTP failure (propagated from :meth:`get`).
        """
        response = self.get(url, **kwargs)
        logger.debug("Received %d bytes from %s", len(response.content), url)
        return response.content

    def get_text(self, url: str, **kwargs: Any) -> str:
        """Fetch *url* and return the response body decoded as text.

        Uses the encoding reported by the server, falling back to UTF-8.

        Parameters
        ----------
        url:
            URL to fetch.
        **kwargs:
            Forwarded to :meth:`get`.

        Returns
        -------
        str
            Decoded response body.

        Raises
        ------
        EdgarClientError
            On HTTP failure (propagated from :meth:`get`).
        """
        response = self.get(url, **kwargs)
        # Honour server-reported encoding; fall back to UTF-8
        encoding = response.encoding or "utf-8"
        logger.debug(
            "Decoding %d bytes from %s as %s", len(response.content), url, encoding
        )
        return response.content.decode(encoding, errors="replace")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying :class:`requests.Session`."""
        self._session.close()
        logger.debug("EdgarClient session closed.")

    def __enter__(self) -> "EdgarClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EdgarClient(user_agent={self.user_agent!r}, "
            f"min_interval={self.min_interval!r}, "
            f"max_retries={self.max_retries!r})"
        )
