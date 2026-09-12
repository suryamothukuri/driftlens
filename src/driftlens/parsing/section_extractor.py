"""
section_extractor.py
====================
Extracts SEC 10-K Item 1A (Risk Factors) sections from raw HTML filings.

The extractor uses a layered regex strategy to handle the notoriously
inconsistent formatting of EDGAR filings across different filers, years,
and PDF-to-HTML conversion tools.

Design principles
-----------------
* Try cheap operations first; escalate to slower heuristics only on failure.
* Never raise on bad input — always return a structured result dict.
* All side-effects (file I/O, logging) are isolated in dedicated methods.

Typical usage::

    from pathlib import Path
    from driftlens.parsing.section_extractor import SectionExtractor

    extractor = SectionExtractor(silver_dir=Path("data/silver"))
    result = extractor.extract_and_save(
        cik="0000320193",
        fiscal_year=2022,
        accession_number="0000320193-22-000108",
        html_path=Path("data/bronze/0000320193/0000320193-22-000108/10k.htm"),
    )
    print(result["success"], result["char_count"])
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from bs4 import BeautifulSoup, Tag
    _BS4_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BS4_AVAILABLE = False
    BeautifulSoup = None  # type: ignore[assignment,misc]
    Tag = None  # type: ignore[assignment,misc]

from .text_cleaning import clean_text, token_count

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & compiled patterns
# ---------------------------------------------------------------------------

# Maximum characters of "text before the next heading" that still qualifies
# as a TOC entry (table-of-contents lines are very short).
_TOC_MAX_CHARS = 400

# Minimum length (chars) for a valid Item 1A extraction.
# Sections shorter than this are treated as failures (likely a TOC match only).
_MIN_SECTION_CHARS = 500

# ---------------------------------------------------------------------------
# Item 1A heading patterns (ordered from strict to permissive)
# ---------------------------------------------------------------------------

# Strategy 1 — strict: "Item 1A." or "Item 1A:" followed by "Risk Factors"
_RE_ITEM_1A_STRICT = re.compile(
    r"item\s+1a\.?\s*[:\-\u2013\u2014]?\s*risk\s+factors",
    re.IGNORECASE | re.MULTILINE,
)

# Strategy 2 — moderate: "Item 1A" optionally followed by anything on the
# same line, then "Risk Factors" within the next ~200 chars.
_RE_ITEM_1A_MODERATE = re.compile(
    r"item\s+1a[.\s]{0,5}(?:[^\n]{0,100}\n){0,3}[^\n]*risk\s+factors",
    re.IGNORECASE | re.DOTALL,
)

# Strategy 3 — permissive fallback: just "Item 1A" with wider tolerance
_RE_ITEM_1A_FALLBACK = re.compile(
    r"item\s+1a",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# End-of-section boundary patterns
# ---------------------------------------------------------------------------
# We look for the *first* match of any of these after the Item 1A start.
_RE_NEXT_SECTION = re.compile(
    r"item\s+1b[\s\W]"     # Item 1B (Unresolved Staff Comments)
    r"|item\s+2[\s\W]"     # Item 2
    r"|item\s+3[\s\W]"     # Item 3
    r"|part\s+ii\b"        # Part II (in case Part I ends early)
    r"|item\s+1\b(?!a)",   # Item 1 (but NOT Item 1A) — rare edge case
    re.IGNORECASE | re.MULTILINE,
)

# Boilerplate / page-header/footer patterns to strip from extracted text
_BOILERPLATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"table\s+of\s+contents?", re.IGNORECASE),
    re.compile(r"^\s*(?:forward[- ]looking\s+statement|cautionary\s+note)\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE),          # bare page numbers
    re.compile(r"^\s*-\s*\d{1,4}\s*-\s*$", re.MULTILINE),  # "- 42 -"
]

# ---------------------------------------------------------------------------
# Standalone utility functions
# ---------------------------------------------------------------------------


def load_html_soup(html_path: Path, *, encoding: str = "utf-8") -> "BeautifulSoup":
    """Load an HTML file and parse it into a :class:`BeautifulSoup` object.

    Tries ``lxml`` first (fastest), falls back to Python's built-in
    ``html.parser``.  Attempts common encodings if UTF-8 fails.

    Parameters
    ----------
    html_path:
        Absolute path to the HTML file.
    encoding:
        Primary encoding to try (default ``"utf-8"``).

    Returns
    -------
    BeautifulSoup
        Parsed soup object.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    RuntimeError
        If BeautifulSoup / bs4 is not installed.
    """
    if not _BS4_AVAILABLE:
        raise RuntimeError(
            "beautifulsoup4 is required for HTML parsing. "
            "Install it with: pip install beautifulsoup4 lxml"
        )
    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    # Try the specified encoding, then a few fallbacks
    for enc in [encoding, "latin-1", "cp1252", "utf-8-sig"]:
        try:
            raw = html_path.read_text(encoding=enc, errors="replace")
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        raw = html_path.read_bytes().decode("latin-1", errors="replace")

    for parser in ["lxml", "html.parser"]:
        try:
            soup = BeautifulSoup(raw, parser)
            logger.debug("Parsed %s with %s", html_path.name, parser)
            return soup
        except Exception as exc:  # noqa: BLE001
            logger.debug("Parser '%s' failed for %s: %s", parser, html_path.name, exc)

    # Last resort — return minimal soup
    return BeautifulSoup(raw, "html.parser")


def soup_to_text(soup: "BeautifulSoup", element: Optional["Tag"] = None) -> str:
    """Convert a BeautifulSoup object (or element) to plain text.

    Inserts newlines at block-level element boundaries so that heading
    structure is preserved.  Inline elements are concatenated without extra
    whitespace.

    Parameters
    ----------
    soup:
        The root BeautifulSoup object (used for tag lookups).
    element:
        Optional sub-element to convert.  If ``None``, uses ``soup`` itself.

    Returns
    -------
    str
        Extracted plain text (not yet cleaned — call :func:`clean_text`
        on the result if needed).
    """
    if not _BS4_AVAILABLE:
        raise RuntimeError("beautifulsoup4 is required.")

    root = element if element is not None else soup

    _BLOCK_TAGS = frozenset({
        "p", "div", "section", "article", "aside", "main",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "dl", "dt", "dd",
        "table", "thead", "tbody", "tr", "td", "th",
        "blockquote", "pre", "br", "hr",
        "header", "footer", "nav", "figure", "figcaption",
    })

    parts: list[str] = []

    def _walk(node: object) -> None:
        from bs4 import NavigableString, Tag as BS4Tag  # local import avoids circular ref issues
        if isinstance(node, NavigableString):
            parts.append(str(node))
        elif isinstance(node, BS4Tag):
            tag_name = node.name.lower() if node.name else ""
            if tag_name in ("script", "style", "meta", "link", "head"):
                return
            if tag_name in _BLOCK_TAGS:
                parts.append("\n")
            for child in node.children:
                _walk(child)
            if tag_name in _BLOCK_TAGS:
                parts.append("\n")

    _walk(root)
    return "".join(parts)


# ---------------------------------------------------------------------------
# SectionExtractor
# ---------------------------------------------------------------------------


class SectionExtractor:
    """Extract Item 1A Risk Factors from 10-K HTML filings.

    Parameters
    ----------
    silver_dir:
        Root directory for silver-layer output.  Extraction results are
        saved under ``<silver_dir>/<cik>/<fiscal_year>/``.
    """

    def __init__(self, silver_dir: Path) -> None:
        self.silver_dir = Path(silver_dir)
        self.silver_dir.mkdir(parents=True, exist_ok=True)
        logger.info("SectionExtractor initialised (silver_dir=%s)", self.silver_dir)

    # ------------------------------------------------------------------
    # Core extraction
    # ------------------------------------------------------------------

    def extract_item_1a(self, html_content: str, source_info: dict) -> dict:
        """Extract the Item 1A Risk Factors section from raw HTML content.

        The method tries four strategies in order and returns the first
        successful result.  It never raises — errors are captured in the
        return dict.

        Parameters
        ----------
        html_content:
            Raw HTML string (full 10-K filing).
        source_info:
            Metadata dict passed through to the result (e.g. cik, year).

        Returns
        -------
        dict
            Keys:

            * ``text`` — cleaned section text (empty string on failure)
            * ``success`` — bool
            * ``char_count`` — int
            * ``token_count`` — int (approximate LLM tokens)
            * ``extraction_method`` — which strategy succeeded
            * ``failure_reason`` — str or None
            * ``source_info`` — the passed-in metadata dict
        """
        failure_reason: Optional[str] = None

        # Step 1: convert HTML → plain text
        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception:
            try:
                soup = BeautifulSoup(html_content, "html.parser")
            except Exception as exc:
                return self._failure_result(source_info, f"HTML parse error: {exc}")

        raw_text = soup_to_text(soup)
        if not raw_text.strip():
            return self._failure_result(source_info, "soup_to_text returned empty string")

        # Step 2: try extraction strategies
        strategies = [
            ("strict_regex",   self._extract_strict,   raw_text),
            ("moderate_regex", self._extract_moderate,  raw_text),
            ("fallback_regex", self._extract_fallback,  raw_text),
        ]

        for method_name, method, text_input in strategies:
            result = method(text_input)
            if result is not None:
                section_text, extraction_method = result, method_name
                # Strip boilerplate lines
                section_text = self._strip_boilerplate(section_text)
                # Final clean
                section_text = clean_text(section_text)

                if len(section_text) < _MIN_SECTION_CHARS:
                    failure_reason = (
                        f"{method_name} matched but text too short "
                        f"({len(section_text)} chars < {_MIN_SECTION_CHARS} minimum)"
                    )
                    logger.debug("CIK %s: %s", source_info.get("cik"), failure_reason)
                    continue  # try next strategy

                logger.info(
                    "CIK %s FY%s: extracted via '%s' (%d chars)",
                    source_info.get("cik"),
                    source_info.get("fiscal_year"),
                    extraction_method,
                    len(section_text),
                )
                return {
                    "text": section_text,
                    "success": True,
                    "char_count": len(section_text),
                    "token_count": token_count(section_text),
                    "extraction_method": extraction_method,
                    "failure_reason": None,
                    "source_info": source_info,
                }

        return self._failure_result(
            source_info,
            failure_reason or "All extraction strategies failed",
        )

    # ------------------------------------------------------------------
    # Extraction strategies
    # ------------------------------------------------------------------

    def _extract_strict(self, text: str) -> Optional[str]:
        """Strategy 1: strict 'Item 1A ... Risk Factors' regex."""
        matches = list(_RE_ITEM_1A_STRICT.finditer(text))
        if not matches:
            return None

        # TOC-awareness: if the first match has very little text before the
        # next heading it is almost certainly a table-of-contents reference.
        start_match = matches[0]
        candidate_start = start_match.end()

        if self._is_toc_match(text, candidate_start) and len(matches) > 1:
            logger.debug("Strict: first match looks like TOC — using second match")
            start_match = matches[1]
            candidate_start = start_match.end()

        return self._slice_to_next_section(text, candidate_start)

    def _extract_moderate(self, text: str) -> Optional[str]:
        """Strategy 2: moderate regex allowing flexible whitespace."""
        match = _RE_ITEM_1A_MODERATE.search(text)
        if not match:
            return None
        candidate_start = match.end()
        if self._is_toc_match(text, candidate_start):
            # Try to find a second occurrence
            second = _RE_ITEM_1A_MODERATE.search(text, pos=match.end() + 1)
            if second:
                candidate_start = second.end()
            else:
                return None
        return self._slice_to_next_section(text, candidate_start)

    def _extract_fallback(self, text: str) -> Optional[str]:
        """Strategy 3: permissive 'Item 1A' fallback."""
        matches = list(_RE_ITEM_1A_FALLBACK.finditer(text))
        if not matches:
            return None

        # Skip TOC matches greedily
        for match in matches:
            candidate_start = match.end()
            if not self._is_toc_match(text, candidate_start):
                return self._slice_to_next_section(text, candidate_start)

        # If all matches look like TOC, use the last one as last resort
        candidate_start = matches[-1].end()
        return self._slice_to_next_section(text, candidate_start)

    # ------------------------------------------------------------------
    # Helper: TOC detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_toc_match(text: str, start: int) -> bool:
        """Return True if *start* position looks like a TOC entry.

        Heuristic: the amount of non-blank text before the next Item heading
        is very small, implying the "section" is just a one-liner index entry.
        """
        snippet = text[start: start + _TOC_MAX_CHARS * 2]
        next_item = _RE_NEXT_SECTION.search(snippet)
        if next_item is None:
            # No next section heading found in the snippet — probably real content
            return False
        chars_before_next = len(snippet[: next_item.start()].strip())
        return chars_before_next < _TOC_MAX_CHARS

    # ------------------------------------------------------------------
    # Helper: end-boundary slicing
    # ------------------------------------------------------------------

    @staticmethod
    def _slice_to_next_section(text: str, start: int) -> str:
        """Return text from *start* up to (but not including) the next Item heading."""
        remaining = text[start:]
        boundary = _RE_NEXT_SECTION.search(remaining)
        if boundary:
            return remaining[: boundary.start()]
        # No boundary found — return everything after the match
        # (common for the very last section in a short filing)
        return remaining

    # ------------------------------------------------------------------
    # Helper: boilerplate stripping
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_boilerplate(text: str) -> str:
        """Remove known boilerplate lines from extracted section text."""
        for pattern in _BOILERPLATE_PATTERNS:
            text = pattern.sub("", text)
        return text

    # ------------------------------------------------------------------
    # Helper: failure result
    # ------------------------------------------------------------------

    @staticmethod
    def _failure_result(source_info: dict, reason: str) -> dict:
        logger.warning(
            "Extraction failed for CIK %s FY%s: %s",
            source_info.get("cik"),
            source_info.get("fiscal_year"),
            reason,
        )
        return {
            "text": "",
            "success": False,
            "char_count": 0,
            "token_count": 0,
            "extraction_method": "none",
            "failure_reason": reason,
            "source_info": source_info,
        }

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def extract_and_save(
        self,
        cik: str,
        fiscal_year: int,
        accession_number: str,
        html_path: Path,
    ) -> dict:
        """Load an HTML filing, extract Item 1A, and persist to silver layer.

        Output files
        ------------
        * ``<silver_dir>/<cik>/<fiscal_year>/item_1a.txt``  — clean text
        * ``<silver_dir>/<cik>/<fiscal_year>/metadata.json`` — extraction metadata

        Parameters
        ----------
        cik:
            Company CIK (string, with or without leading zeros).
        fiscal_year:
            Fiscal year integer (e.g. ``2022``).
        accession_number:
            SEC accession number (used in metadata only).
        html_path:
            Path to the raw HTML filing.

        Returns
        -------
        dict
            The result dict from :meth:`extract_item_1a`, augmented with
            ``saved_text_path`` and ``saved_metadata_path`` keys.
        """
        html_path = Path(html_path)
        source_info = {
            "cik": cik,
            "fiscal_year": fiscal_year,
            "accession_number": accession_number,
            "html_path": str(html_path),
        }

        # Load HTML
        try:
            html_content = html_path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            result = self._failure_result(source_info, f"HTML file not found: {html_path}")
            return result
        except Exception as exc:  # noqa: BLE001
            result = self._failure_result(source_info, f"File read error: {exc}")
            return result

        # Extract
        result = self.extract_item_1a(html_content, source_info)

        # Save
        out_dir = self.silver_dir / str(cik) / str(fiscal_year)
        out_dir.mkdir(parents=True, exist_ok=True)

        text_path = out_dir / "item_1a.txt"
        metadata_path = out_dir / "metadata.json"

        text_path.write_text(result["text"], encoding="utf-8")

        metadata = {
            "cik": cik,
            "fiscal_year": fiscal_year,
            "accession_number": accession_number,
            "success": result["success"],
            "char_count": result["char_count"],
            "token_count": result["token_count"],
            "extraction_method": result["extraction_method"],
            "failure_reason": result["failure_reason"],
            "html_source": str(html_path),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        result["saved_text_path"] = str(text_path)
        result["saved_metadata_path"] = str(metadata_path)

        logger.info(
            "Saved extraction for CIK %s FY%d → %s (success=%s)",
            cik,
            fiscal_year,
            out_dir,
            result["success"],
        )
        return result

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------

    def batch_extract(
        self,
        filing_list: list[dict],
        bronze_dir: Path,
    ) -> pd.DataFrame:
        """Process multiple filings and return a summary DataFrame.

        Parameters
        ----------
        filing_list:
            List of dicts, each with keys:
            ``cik``, ``fiscal_year``, ``accession_number``, ``html_filename``.
            ``html_filename`` is relative to ``<bronze_dir>/<cik>/<accession_number>/``.
        bronze_dir:
            Root of the bronze data directory.

        Returns
        -------
        pd.DataFrame
            One row per filing.  Columns: ``cik``, ``fiscal_year``,
            ``accession_number``, ``success``, ``char_count``, ``token_count``,
            ``extraction_method``, ``failure_reason``.
        """
        bronze_dir = Path(bronze_dir)
        rows: list[dict] = []

        try:
            from tqdm import tqdm
            iterator = tqdm(filing_list, desc="Extracting Item 1A", unit="filing")
        except ImportError:
            iterator = filing_list

        for filing in iterator:
            cik: str = str(filing["cik"])
            fiscal_year: int = int(filing["fiscal_year"])
            accession: str = str(filing["accession_number"])
            html_filename: str = str(filing.get("html_filename", "10k.htm"))

            html_path = bronze_dir / cik / accession / html_filename

            try:
                result = self.extract_and_save(
                    cik=cik,
                    fiscal_year=fiscal_year,
                    accession_number=accession,
                    html_path=html_path,
                )
            except Exception as exc:  # noqa: BLE001 — never crash the batch
                logger.error(
                    "Unexpected error for CIK %s FY%d: %s", cik, fiscal_year, exc, exc_info=True
                )
                result = {
                    "success": False,
                    "char_count": 0,
                    "token_count": 0,
                    "extraction_method": "none",
                    "failure_reason": f"Unexpected exception: {exc}",
                }

            rows.append(
                {
                    "cik": cik,
                    "fiscal_year": fiscal_year,
                    "accession_number": accession,
                    "success": result["success"],
                    "char_count": result["char_count"],
                    "token_count": result.get("token_count", 0),
                    "extraction_method": result["extraction_method"],
                    "failure_reason": result["failure_reason"],
                }
            )

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Ensure column types
        df["fiscal_year"] = df["fiscal_year"].astype(int)
        df["success"] = df["success"].astype(bool)
        df["char_count"] = df["char_count"].astype(int)
        df["token_count"] = df["token_count"].astype(int)

        logger.info(
            "batch_extract complete: %d/%d succeeded",
            df["success"].sum(),
            len(df),
        )
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def compute_success_rate(self, results_df: pd.DataFrame) -> dict:
        """Compute extraction success metrics from a batch results DataFrame.

        Parameters
        ----------
        results_df:
            DataFrame as returned by :meth:`batch_extract`.

        Returns
        -------
        dict
            Keys:

            * ``success_rate``   — float in [0, 1]
            * ``total``          — int
            * ``succeeded``      — int
            * ``failed``         — int
            * ``failure_reasons``— :class:`collections.Counter` mapping reason → count
            * ``method_counts``  — :class:`collections.Counter` mapping method → count
            * ``avg_char_count`` — float (mean chars among successful extractions)
            * ``avg_token_count``— float
        """
        if results_df.empty:
            return {
                "success_rate": 0.0,
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "failure_reasons": Counter(),
                "method_counts": Counter(),
                "avg_char_count": 0.0,
                "avg_token_count": 0.0,
            }

        total = len(results_df)
        succeeded = int(results_df["success"].sum())
        failed = total - succeeded

        failure_reasons: Counter = Counter(
            results_df.loc[~results_df["success"], "failure_reason"]
            .dropna()
            .tolist()
        )
        method_counts: Counter = Counter(
            results_df.loc[results_df["success"], "extraction_method"]
            .tolist()
        )

        successful_rows = results_df[results_df["success"]]
        avg_chars = float(successful_rows["char_count"].mean()) if not successful_rows.empty else 0.0
        avg_tokens = (
            float(successful_rows["token_count"].mean())
            if "token_count" in successful_rows.columns and not successful_rows.empty
            else 0.0
        )

        return {
            "success_rate": succeeded / total if total > 0 else 0.0,
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "failure_reasons": failure_reasons,
            "method_counts": method_counts,
            "avg_char_count": avg_chars,
            "avg_token_count": avg_tokens,
        }
