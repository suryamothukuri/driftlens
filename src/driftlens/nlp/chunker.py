"""
chunker.py — Paragraph-level text chunking for DriftLens NLP pipeline.

Splits raw section text (e.g. 10-K Item 1A) into overlapping, token-bounded
chunks suitable for embedding.  Chunking is purely CPU-bound and stateless
so it can be parallelised trivially if needed.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Bullet / numbered-list markers that signal a new logical paragraph.
_BULLET_RE = re.compile(
    r"(?m)^(?:[•\-\*]|\d+[.):])\s"
)

# Sentence boundary: period / ! / ? followed by whitespace + capital letter
# (good-enough approximation without NLTK dependency).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

# Rough token count: split on whitespace.  We deliberately avoid a heavy
# tokenizer here so that chunking stays fast and dependency-free.
def _token_count(text: str) -> int:
    return len(text.split())


def generate_chunk_id(cik: str, fiscal_year: int, section: str, index: int) -> str:
    """Return a deterministic, human-readable chunk identifier.

    Format: ``{cik}_{fiscal_year}_{section}_{index:04d}``

    Examples
    --------
    >>> generate_chunk_id("0000789019", 2023, "item_1a", 7)
    '0000789019_2023_item_1a_0007'
    """
    return f"{cik}_{fiscal_year}_{section}_{index:04d}"


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

class Chunker:
    """Split SEC filing sections into token-bounded paragraph chunks.

    Parameters
    ----------
    min_tokens:
        Chunks with fewer tokens than this threshold are discarded.
    max_tokens:
        Chunks exceeding this threshold are recursively split at sentence
        boundaries.
    """

    def __init__(self, min_tokens: int = 40, max_tokens: int = 300) -> None:
        if min_tokens < 1:
            raise ValueError("min_tokens must be >= 1")
        if max_tokens <= min_tokens:
            raise ValueError("max_tokens must be > min_tokens")
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        cik: str,
        fiscal_year: int,
        accession_number: str,
        section: str = "item_1a",
    ) -> list[dict]:
        """Split *text* into paragraph-level chunks.

        Parameters
        ----------
        text:
            Raw section text.
        cik:
            SEC Central Index Key (string, zero-padded to 10 digits
            if you like, but any consistent format is fine).
        fiscal_year:
            Four-digit fiscal year integer (e.g. 2023).
        accession_number:
            SEC accession number string.
        section:
            Section label, e.g. ``"item_1a"``.

        Returns
        -------
        list[dict]
            Each element is a chunk record with keys:
            ``chunk_id``, ``cik``, ``fiscal_year``, ``accession_number``,
            ``section``, ``chunk_index``, ``text``, ``token_count``.
        """
        if not text or not text.strip():
            return []

        raw_chunks = self._split_into_paragraphs(text)
        final_chunks: list[str] = []

        for para in raw_chunks:
            tc = _token_count(para)
            if tc < self.min_tokens:
                # Too short — discard silently.
                continue
            if tc > self.max_tokens:
                # Too long — split at sentence boundaries.
                final_chunks.extend(self._split_by_sentences(para))
            else:
                final_chunks.append(para)

        records: list[dict] = []
        for idx, chunk_text in enumerate(final_chunks):
            tc = _token_count(chunk_text)
            if tc < self.min_tokens:
                # Could happen after sentence splitting; skip.
                continue
            records.append(
                {
                    "chunk_id": generate_chunk_id(cik, fiscal_year, section, idx),
                    "cik": cik,
                    "fiscal_year": fiscal_year,
                    "accession_number": accession_number,
                    "section": section,
                    "chunk_index": idx,
                    "text": chunk_text.strip(),
                    "token_count": tc,
                }
            )

        logger.debug(
            "chunker: cik=%s fy=%d section=%s → %d chunks",
            cik,
            fiscal_year,
            section,
            len(records),
        )
        return records

    def chunk_dataframe(self, sections_df: pd.DataFrame) -> pd.DataFrame:
        """Batch-process a DataFrame of section rows into a chunks DataFrame.

        Expected columns in *sections_df*:
        ``cik``, ``fiscal_year``, ``accession_number``, ``section``, ``text``.

        Returns
        -------
        pd.DataFrame
            All chunk records concatenated, with a reset integer index.
        """
        required_cols = {"cik", "fiscal_year", "accession_number", "section", "text"}
        missing = required_cols - set(sections_df.columns)
        if missing:
            raise ValueError(f"sections_df is missing columns: {missing}")

        all_records: list[dict] = []
        for _, row in sections_df.iterrows():
            chunks = self.chunk_text(
                text=str(row["text"]),
                cik=str(row["cik"]),
                fiscal_year=int(row["fiscal_year"]),
                accession_number=str(row["accession_number"]),
                section=str(row["section"]),
            )
            all_records.extend(chunks)

        if not all_records:
            logger.warning("chunk_dataframe: no chunks produced from %d rows", len(sections_df))
            return pd.DataFrame(
                columns=[
                    "chunk_id",
                    "cik",
                    "fiscal_year",
                    "accession_number",
                    "section",
                    "chunk_index",
                    "text",
                    "token_count",
                ]
            )

        result = pd.DataFrame(all_records)
        logger.info(
            "chunk_dataframe: %d sections → %d chunks",
            len(sections_df),
            len(result),
        )
        return result.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Primary split: double-newlines then bullet markers."""
        # Step 1 — split on blank lines.
        paragraphs: list[str] = [p.strip() for p in re.split(r"\n\s*\n", text)]

        # Step 2 — within each paragraph, further split on bullet/list markers.
        refined: list[str] = []
        for para in paragraphs:
            if not para:
                continue
            # Find all bullet positions.
            positions = [m.start() for m in _BULLET_RE.finditer(para)]
            if not positions:
                refined.append(para)
                continue
            # Slice the paragraph at each bullet start.
            boundaries = [0] + positions
            for i, start in enumerate(boundaries):
                end = boundaries[i + 1] if i + 1 < len(boundaries) else len(para)
                segment = para[start:end].strip()
                if segment:
                    refined.append(segment)

        return refined

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split *text* at sentence boundaries, grouping into token-bounded windows."""
        sentences = _SENTENCE_SPLIT_RE.split(text)
        groups: list[str] = []
        current_parts: list[str] = []
        current_count = 0

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            tc = _token_count(sent)
            if current_count + tc > self.max_tokens and current_parts:
                # Flush current group.
                groups.append(" ".join(current_parts))
                current_parts = []
                current_count = 0
            current_parts.append(sent)
            current_count += tc

        if current_parts:
            groups.append(" ".join(current_parts))

        return groups
