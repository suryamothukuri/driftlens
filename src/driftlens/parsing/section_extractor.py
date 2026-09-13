"""Item 1A Risk Factors extraction with format detection (legacy HTML vs modern iXBRL) and TOC boundary checks."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from driftlens.parsing.text_cleaning import clean_text, normalize_whitespace, token_count

logger = logging.getLogger("driftlens.parsing.section_extractor")


class SectionExtractor:
    """Format-aware Item 1A extractor handling both legacy HTML (2016-2018) and modern iXBRL (2019-2025)."""

    ITEM_1A_PATTERNS = [
        re.compile(r"item\s+1a\.?\s*[:\-–—]?\s*risk\s+factors", re.IGNORECASE),
        re.compile(r"item\s+1a\s+risk\s+factors", re.IGNORECASE),
        re.compile(r"risk\s+factors\s+item\s+1a", re.IGNORECASE),
    ]

    BOUNDARY_PATTERNS = [
        re.compile(r"item\s+1b\.?\s*[:\-–—]?\s*unresolved\s+staff\s+comments", re.IGNORECASE),
        re.compile(r"item\s+1c\.?\s*[:\-–—]?\s*cybersecurity", re.IGNORECASE),
        re.compile(r"item\s+2\.?\s*[:\-–—]?\s*properties", re.IGNORECASE),
        re.compile(r"item\s+3\.?\s*[:\-–—]?\s*legal\s+proceedings", re.IGNORECASE),
    ]

    def __init__(self, silver_dir: Optional[Path] = None) -> None:
        self.silver_dir = Path(silver_dir) if silver_dir else None
        if self.silver_dir:
            self.silver_dir.mkdir(parents=True, exist_ok=True)

    def extract_item_1a(self, html_content: str, fiscal_year: int = 2023) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml" if "lxml" in BeautifulSoup.__module__ else "html.parser")

        # 1. Detect iXBRL format vs legacy HTML
        is_ixbrl = bool(soup.find(["ix:nonnumeric", "ix:continuation", "ix:header"]))

        for tag in soup(["script", "style", "header", "footer"]):
            tag.decompose()

        full_text = soup.get_text(separator="\n")

        # 2. Match Heading
        matches = []
        for pat in self.ITEM_1A_PATTERNS:
            for m in pat.finditer(full_text):
                matches.append(m)

        if not matches:
            return {
                "text": "",
                "success": False,
                "char_count": 0,
                "is_ixbrl": is_ixbrl,
                "extraction_method": "none",
                "failure_reason": "ITEM_1A_HEADING_NOT_FOUND",
            }

        # 3. Skip TOC anchor links (if first match is very early in text and another match exists)
        selected_match = matches[0]
        if len(matches) > 1 and selected_match.start() < len(full_text) * 0.40:
            selected_match = matches[1]

        start_pos = selected_match.end()

        # 4. Find end boundary
        end_pos = len(full_text)
        earliest_boundary = None
        for b_pat in self.BOUNDARY_PATTERNS:
            for bm in b_pat.finditer(full_text[start_pos:]):
                b_idx = start_pos + bm.start()
                if earliest_boundary is None or b_idx < earliest_boundary:
                    earliest_boundary = b_idx

        if earliest_boundary is not None and earliest_boundary > start_pos:
            end_pos = earliest_boundary

        extracted_text = full_text[start_pos:end_pos].strip()

        if len(extracted_text) < 30:
            return {
                "text": extracted_text,
                "success": False,
                "char_count": len(extracted_text),
                "is_ixbrl": is_ixbrl,
                "extraction_method": "ixbrl_fallback" if is_ixbrl else "legacy_html_fallback",
                "failure_reason": "EXTRACTED_SECTION_TOO_SHORT",
            }

        return {
            "text": extracted_text,
            "success": True,
            "char_count": len(extracted_text),
            "is_ixbrl": is_ixbrl,
            "extraction_method": "ixbrl_boundary" if is_ixbrl else "legacy_html_boundary",
            "failure_reason": None,
        }


def load_html_soup(html_path: Path) -> BeautifulSoup:
    """Load HTML file into BeautifulSoup."""
    content = Path(html_path).read_text(encoding="utf-8", errors="replace")
    return BeautifulSoup(content, "lxml" if "lxml" in BeautifulSoup.__module__ else "html.parser")


def soup_to_text(soup: BeautifulSoup, element=None) -> str:
    """Convert soup or element to clean text."""
    target = element if element is not None else soup
    return normalize_whitespace(target.get_text(separator="\n"))
