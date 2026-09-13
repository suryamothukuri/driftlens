"""Item 1A Risk Factors extraction with format detection (legacy HTML vs modern iXBRL) and TOC boundary checks."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from driftlens.parsing.text_cleaning import normalize_whitespace

logger = logging.getLogger("driftlens.parsing.section_extractor")


class SectionExtractor:
    """Format-aware Item 1A extractor handling both legacy HTML (2016-2018) and modern iXBRL (2019-2025)."""

    ITEM_1A_RE = re.compile(
        r"(?:item\s+1a\.?\s*[:\-–—]?\s*risk\s+factors|risk\s+factors\s*[:\-–—]?\s*item\s+1a|item\s+1a\b)",
        re.IGNORECASE,
    )

    BOUNDARY_RE = re.compile(
        r"(?:item\s+1b\.?\s*[:\-–—]?\s*unresolved\s+staff\s+comments|item\s+1b\.?\b|item\s+1c\.?\b|item\s+2\.?\b|item\s+3\.?\b)",
        re.IGNORECASE,
    )

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

        # Decompose TOC anchor links so they don't get selected as the section heading
        for a in soup.find_all("a", href=re.compile(r"^#")):
            if re.search(r"item\s+1a", a.get_text(), re.IGNORECASE):
                a.decompose()

        full_text = soup.get_text(separator="\n")

        # 2. Match Heading
        matches = list(self.ITEM_1A_RE.finditer(full_text))

        if not matches:
            return {
                "text": "",
                "success": False,
                "char_count": 0,
                "is_ixbrl": is_ixbrl,
                "extraction_method": "none",
                "failure_reason": "ITEM_1A_HEADING_NOT_FOUND",
                "error": "ITEM_1A_HEADING_NOT_FOUND",
            }

        # 3. Select match: if first match is very short before the second match, skip TOC entry
        selected_match = matches[0]
        if len(matches) > 1:
            # Check if text between match[0] and match[1] is short (< 150 chars, likely a TOC line)
            if matches[1].start() - matches[0].end() < 150:
                selected_match = matches[1]

        start_pos = selected_match.end()

        # 4. Find end boundary
        end_pos = len(full_text)
        bm = self.BOUNDARY_RE.search(full_text[start_pos:])
        if bm is not None and bm.start() > 0:
            end_pos = start_pos + bm.start()

        extracted_text = full_text[start_pos:end_pos].strip()

        if len(extracted_text) < 30:
            return {
                "text": extracted_text if len(extracted_text) > 0 else "",
                "success": False,
                "char_count": len(extracted_text),
                "is_ixbrl": is_ixbrl,
                "extraction_method": "ixbrl_fallback" if is_ixbrl else "legacy_html_fallback",
                "failure_reason": "EXTRACTED_SECTION_TOO_SHORT",
                "error": "EXTRACTED_SECTION_TOO_SHORT",
            }

        return {
            "text": extracted_text,
            "success": True,
            "char_count": len(extracted_text),
            "is_ixbrl": is_ixbrl,
            "extraction_method": "ixbrl_boundary" if is_ixbrl else "legacy_html_boundary",
            "failure_reason": None,
            "error": None,
        }


def load_html_soup(html_path: Path) -> BeautifulSoup:
    """Load HTML file into BeautifulSoup."""
    content = Path(html_path).read_text(encoding="utf-8", errors="replace")
    return BeautifulSoup(content, "lxml" if "lxml" in BeautifulSoup.__module__ else "html.parser")


def soup_to_text(soup: BeautifulSoup, element=None) -> str:
    """Convert soup or element to clean text."""
    target = element if element is not None else soup
    return normalize_whitespace(target.get_text(separator="\n"))
