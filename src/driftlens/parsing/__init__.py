"""DriftLens parsing subpackage."""

from driftlens.parsing.section_extractor import SectionExtractor
from driftlens.parsing.text_cleaning import (
    clean_text,
    dehyphenate,
    is_grammatical_prose,
    normalize_whitespace,
    remove_html_artifacts,
    remove_nonascii_artifacts,
    remove_page_number_artifacts,
    token_count,
)
from driftlens.parsing.xbrl_parser import XBRLParser, extract_facts_for_universe

__all__ = [
    "clean_text",
    "dehyphenate",
    "is_grammatical_prose",
    "normalize_whitespace",
    "remove_html_artifacts",
    "remove_nonascii_artifacts",
    "remove_page_number_artifacts",
    "token_count",
    "SectionExtractor",
    "XBRLParser",
    "extract_facts_for_universe",
]
