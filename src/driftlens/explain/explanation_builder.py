"""
ExplanationBuilder — evidence-grounded drift explanations.

For each material theme change, ``ExplanationBuilder`` retrieves supporting
text chunks from the silver layer, constructs a structured prompt, and calls
Ollama to produce a 2-3 sentence explanation.  When Ollama is unavailable,
a template-based fallback is generated so the pipeline never hard-fails.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .ollama_client import OllamaClient, OllamaNotAvailableError

logger = logging.getLogger(__name__)


class ExplanationBuilder:
    """Build evidence-grounded explanations for theme drift changes.

    Parameters
    ----------
    ollama_client:
        A configured ``OllamaClient`` instance.
    chunks_df:
        Silver-layer chunks DataFrame.  Must contain at minimum the columns
        ``chunk_id``, ``cik``, ``cluster_id``, ``fiscal_year``, and whatever
        column name is passed as *text_col*.
    text_col:
        Name of the column in *chunks_df* that holds the chunk text.
    """

    _SYSTEM_PROMPT = (
        "You are a financial analyst assistant specializing in SEC 10-K filings. "
        "You provide concise, evidence-grounded explanations of changes in corporate "
        "disclosures.  You never speculate beyond what the provided excerpts support."
    )

    def __init__(
        self,
        ollama_client: OllamaClient,
        chunks_df: pd.DataFrame,
        text_col: str = "text",
    ) -> None:
        self.client = ollama_client
        self.chunks_df = chunks_df.copy()
        self.text_col = text_col

        # Validate required columns
        required = {"chunk_id", "cik", "cluster_id", "fiscal_year", text_col}
        missing = required - set(self.chunks_df.columns)
        if missing:
            raise ValueError(
                f"chunks_df is missing required columns: {missing}"
            )

        # Ensure correct types for fast filtering
        self.chunks_df["cik"] = self.chunks_df["cik"].astype(str)
        self.chunks_df["cluster_id"] = self.chunks_df["cluster_id"].astype(int)
        self.chunks_df["fiscal_year"] = self.chunks_df["fiscal_year"].astype(int)

        logger.debug(
            "ExplanationBuilder ready: %d chunks, text_col=%r",
            len(self.chunks_df),
            text_col,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_evidence_chunks(
        self,
        cik: str,
        cluster_id: int,
        fiscal_year: int,
        n: int = 2,
    ) -> list[dict[str, Any]]:
        """Return the top *n* chunks for a given (cik, cluster_id, fiscal_year).

        Chunks are returned in their natural DataFrame order (assumed to be
        relevance-ranked by the silver pipeline; first *n* rows are taken).

        Returns
        -------
        list[dict]
            Each element has keys ``chunk_id`` and ``text``.  Returns an
            empty list if no matching chunks exist.
        """
        mask = (
            (self.chunks_df["cik"] == str(cik))
            & (self.chunks_df["cluster_id"] == int(cluster_id))
            & (self.chunks_df["fiscal_year"] == int(fiscal_year))
        )
        subset = self.chunks_df.loc[mask].head(n)

        result: list[dict[str, Any]] = []
        for _, row in subset.iterrows():
            result.append(
                {
                    "chunk_id": str(row["chunk_id"]),
                    "text": str(row[self.text_col]),
                }
            )
        return result

    def _build_prompt(
        self,
        change_row: pd.Series,
        evidence_current: list[dict[str, Any]],
        evidence_prev: list[dict[str, Any]],
        theme_label: str,
    ) -> str:
        """Construct the generation prompt for a single change event.

        Parameters
        ----------
        change_row:
            A row from the top-changes DataFrame.  Expected fields:
            ``fiscal_year``, ``intensity_delta``, ``centroid_drift``,
            ``materiality_score``, plus the current/previous intensities
            (``intensity_curr`` and ``intensity_prev``); if those two are
            absent, ``intensity_delta`` is used as a fallback delta.
        evidence_current:
            Up to 2 chunk dicts for the *current* fiscal year.
        evidence_prev:
            Up to 2 chunk dicts for the *previous* fiscal year.
        theme_label:
            Human-readable cluster label.

        Returns
        -------
        str
            The fully-rendered prompt string.
        """
        year: int = int(change_row.get("fiscal_year", 0))
        delta: float = float(change_row.get("intensity_delta", 0.0))
        drift: float = float(change_row.get("centroid_drift", 0.0))
        materiality: float = float(change_row.get("materiality_score", 0.0))

        # Intensity values: prefer explicit curr/prev, fall back to delta only
        if "intensity_curr" in change_row and "intensity_prev" in change_row:
            curr_intensity: float = float(change_row["intensity_curr"])
            prev_intensity: float = float(change_row["intensity_prev"])
        else:
            # Reconstruct approximate values from delta (best effort)
            curr_intensity = max(0.0, min(1.0, 0.5 + delta / 2))
            prev_intensity = max(0.0, min(1.0, 0.5 - delta / 2))

        def _excerpt(chunks: list[dict[str, Any]], offset: int) -> list[str]:
            lines = []
            for i, chunk in enumerate(chunks):
                idx = offset + i + 1
                text = chunk["text"].replace("\n", " ").strip()
                # Truncate very long excerpts to keep prompt manageable
                if len(text) > 600:
                    text = text[:597] + "..."
                lines.append(f'[{idx}] "{text}"')
            return lines

        curr_excerpts = _excerpt(evidence_current, offset=0)
        prev_excerpts = _excerpt(evidence_prev, offset=len(evidence_current))

        curr_block = "\n".join(curr_excerpts) if curr_excerpts else "[No excerpts available]"
        prev_block = "\n".join(prev_excerpts) if prev_excerpts else "[No excerpts available]"

        prompt = (
            f"Theme: {theme_label}\n"
            f"Intensity change: {prev_intensity:.3f} -> {curr_intensity:.3f} (delta={delta:+.3f})\n"
            f"Materiality score: {materiality:.4f}\n"
            f"Centroid drift: {drift:.4f} (0=same meaning, 1=completely different phrasing)\n"
            f"\nExcerpts from FY{year} 10-K:\n{curr_block}\n"
            f"\nExcerpts from FY{year - 1} 10-K:\n{prev_block}\n"
            "\nUsing ONLY the excerpts and numbers provided, write a 2-3 sentence explanation "
            "of what changed and why it might matter. Do not speculate beyond the evidence. "
            "Cite which year's excerpt supports each claim."
        )
        return prompt

    def _generate_fallback_explanation(
        self,
        change_row: pd.Series,
        theme_label: str,
    ) -> str:
        """Template-based explanation used when Ollama is unavailable.

        Uses only numeric fields — no LLM call is made.
        """
        year: int = int(change_row.get("fiscal_year", 0))
        delta: float = float(change_row.get("intensity_delta", 0.0))
        drift: float = float(change_row.get("centroid_drift", 0.0))

        if "intensity_curr" in change_row and "intensity_prev" in change_row:
            curr_intensity = float(change_row["intensity_curr"])
            prev_intensity = float(change_row["intensity_prev"])
        else:
            curr_intensity = max(0.0, min(1.0, 0.5 + delta / 2))
            prev_intensity = max(0.0, min(1.0, 0.5 - delta / 2))

        direction = "significant increase" if delta > 0.05 else (
            "significant decrease" if delta < -0.05 else "moderate shift"
        )

        # Interpret centroid drift magnitude
        if drift < 0.15:
            phrasing_desc = "language used remained largely consistent"
        elif drift < 0.35:
            phrasing_desc = "language evolved noticeably across years"
        else:
            phrasing_desc = "language changed substantially, suggesting a reframing of the topic"

        return (
            f'The theme "{theme_label}" showed a {direction} in FY{year} '
            f"(intensity: {prev_intensity:.1%} \u2192 {curr_intensity:.1%}, "
            f"change: {delta:+.1%}). "
            f"The centroid drift of {drift:.3f} suggests the {phrasing_desc}."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_explanation(
        self,
        change_row: pd.Series,
        theme_label: str,
    ) -> dict[str, Any]:
        """Build a single explanation record for one theme-change event.

        Parameters
        ----------
        change_row:
            A row from the top-changes DataFrame.  Required fields: ``cik``,
            ``cluster_id``, ``fiscal_year``.
        theme_label:
            Human-readable label for the cluster.

        Returns
        -------
        dict
            Keys: ``change_id``, ``cik``, ``cluster_id``, ``fiscal_year``,
            ``explanation_text``, ``evidence_chunk_ids``, ``model_used``,
            ``generated_at``.
        """
        cik = str(change_row["cik"])
        cluster_id = int(change_row["cluster_id"])
        fiscal_year = int(change_row["fiscal_year"])
        change_id = f"{cik}_{cluster_id}_{fiscal_year}"

        # Fetch evidence chunks
        evidence_curr = self._get_evidence_chunks(cik, cluster_id, fiscal_year, n=2)
        evidence_prev = self._get_evidence_chunks(cik, cluster_id, fiscal_year - 1, n=2)
        all_chunk_ids = [c["chunk_id"] for c in evidence_curr + evidence_prev]

        # Determine model and generate explanation
        ollama_available = self.client.is_available()

        if ollama_available:
            prompt = self._build_prompt(change_row, evidence_curr, evidence_prev, theme_label)
            try:
                explanation_text = self.client.generate(
                    prompt,
                    system_prompt=self._SYSTEM_PROMPT,
                    temperature=0.1,
                )
                model_used = self.client.model
            except OllamaNotAvailableError:
                logger.warning(
                    "Ollama became unavailable mid-run for change %s; using fallback.",
                    change_id,
                )
                explanation_text = self._generate_fallback_explanation(change_row, theme_label)
                model_used = "fallback_template"
        else:
            explanation_text = self._generate_fallback_explanation(change_row, theme_label)
            model_used = "fallback_template"

        generated_at = datetime.now(tz=timezone.utc).isoformat()

        return {
            "change_id": change_id,
            "cik": cik,
            "cluster_id": cluster_id,
            "fiscal_year": fiscal_year,
            "explanation_text": explanation_text,
            "evidence_chunk_ids": all_chunk_ids,
            "model_used": model_used,
            "generated_at": generated_at,
        }

    def build_batch_explanations(
        self,
        top_changes_df: pd.DataFrame,
        themes_dict: dict[int, str],
        max_explanations: int = 500,
    ) -> pd.DataFrame:
        """Process the top-N change events and return an explanations DataFrame.

        Parameters
        ----------
        top_changes_df:
            DataFrame of ranked theme changes (already sorted by
            ``materiality_score`` descending or equivalent).
        themes_dict:
            Mapping of ``cluster_id`` → human-readable label.
        max_explanations:
            Hard cap on the number of explanations generated.  Rows beyond
            this limit are silently skipped.

        Returns
        -------
        pd.DataFrame
            Explanations table; empty DataFrame if *top_changes_df* is empty
            or Ollama is unavailable and no fallbacks are generated.
        """
        if top_changes_df.empty:
            logger.warning("top_changes_df is empty; no explanations to build.")
            return pd.DataFrame()

        # Check availability once up-front so we can log a single warning
        ollama_up = self.client.is_available()
        if not ollama_up:
            logger.warning(
                "Ollama is not available (%s). "
                "Falling back to template-based explanations for all %d changes.",
                self.client.base_url,
                min(len(top_changes_df), max_explanations),
            )

        records: list[dict[str, Any]] = []
        processed = 0

        for _, row in top_changes_df.iterrows():
            if processed >= max_explanations:
                logger.debug("Reached max_explanations=%d; stopping.", max_explanations)
                break

            cluster_id = int(row["cluster_id"])
            theme_label = themes_dict.get(cluster_id, f"cluster_{cluster_id}")

            try:
                record = self.build_explanation(row, theme_label)
                records.append(record)
            except Exception as exc:  # noqa: BLE001
                change_id = f"{row.get('cik', '?')}_{cluster_id}_{row.get('fiscal_year', '?')}"
                logger.error(
                    "Failed to build explanation for %s: %s",
                    change_id,
                    exc,
                    exc_info=True,
                )
            finally:
                processed += 1

        if not records:
            logger.warning("No explanation records were generated.")
            return pd.DataFrame()

        result_df = pd.DataFrame(records)
        logger.info(
            "Built %d explanations (%d fallback_template).",
            len(result_df),
            (result_df["model_used"] == "fallback_template").sum(),
        )
        return result_df
