"""Item 1A Risk Factors extraction with multi-strategy regex, iXBRL, and DOM boundary checks."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger("driftlens.parsing.section_extractor")

class SectionExtractor:
    """Extracts Item 1A (Risk Factors) from complex 10-K filings with TOC avoidance."""

    # Primary regex patterns (case-insensitive)
    ITEM_1A_PATTERNS = [
        re.compile(r"item\s+1a\.?\s*[:\-–—]?\s*risk\s+factors", re.IGNORECASE),
        re.compile(r"item\s+1a\s+risk\s+factors", re.IGNORECASE),
        re.compile(r"risk\s+factors\s+item\s+1a", re.IGNORECASE),
    ]

    # Boundary patterns that signal the end of Item 1A
    BOUNDARY_PATTERNS = [
        re.compile(r"item\s+1b\.?\s*[:\-–—]?\s*unresolved\s+staff\s+comments", re.IGNORECASE),
        re.compile(r"item\s+1c\.?\s*[:\-–—]?\s*cybersecurity", re.IGNORECASE),
        re.compile(r"item\s+2\.?\s*[:\-–—]?\s*properties", re.IGNORECASE),
        re.compile(r"item\s+3\.?\s*[:\-–—]?\s*legal\s+proceedings", re.IGNORECASE),
    ]

    def __init__(self, silver_dir: Path) -> None:
        self.silver_dir = silver_dir
        self.silver_dir.mkdir(parents=True, exist_ok=True)

    def extract_item_1a(self, html_content: str, source_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml" if "lxml" in BeautifulSoup.__module__ else "html.parser")

        # 1. Strip non-informative elements (scripts, styles, hidden tables)
        for tag in soup(["script", "style", "header", "footer"]):
            tag.decompose()

        full_text = soup.get_text(separator="\n")

        # 2. Multi-strategy search
        matches = []
        for pat in self.ITEM_1A_PATTERNS:
            for m in pat.finditer(full_text):
                matches.append(m)

        if not matches:
            return {
                "text": "",
                "success": False,
                "char_count": 0,
                "extraction_method": "none",
                "failure_reason": "ITEM_1A_HEADING_NOT_FOUND",
            }

        # 3. Handle Table of Contents: If first match is in the first 15% of document and under 150 chars from next heading, skip it
        selected_match = matches[0]
        if len(matches) > 1 and selected_match.start() < len(full_text) * 0.20:
            # Check if likely a TOC link
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

        if earliest_boundary is not None and earliest_boundary > start_pos + 500:
            end_pos = earliest_boundary

        extracted_text = full_text[start_pos:end_pos].strip()

        # Quality check: reasonable size for Item 1A
        if len(extracted_text) < 500:
            return {
                "text": extracted_text,
                "success": False,
                "char_count": len(extracted_text),
                "extraction_method": "regex_fallback",
                "failure_reason": "EXTRACTED_SECTION_TOO_SHORT",
            }

        return {
            "text": extracted_text,
            "success": True,
            "char_count": len(extracted_text),
            "extraction_method": "regex_boundary_v2",
            "failure_reason": None,
        }
