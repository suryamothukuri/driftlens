"""
text_cleaning.py
================
Low-level text normalization utilities for SEC 10-K filings.

All functions are pure (no side-effects) and safe to call on empty strings.
The canonical pipeline is :func:`clean_text`, which applies every step in
the correct order.
"""

from __future__ import annotations

import html
import math
import re
import unicodedata

# ---------------------------------------------------------------------------
# Internal compiled patterns  (compiled once at import time for speed)
# ---------------------------------------------------------------------------

# Collapse horizontal whitespace (spaces + tabs) to a single space.
# We keep newlines intact here so that later steps can detect line structure.
_RE_HORIZ_WS = re.compile(r"[ \t]+")

# Normalize Windows/old-Mac line endings → Unix \n
_RE_LINE_ENDINGS = re.compile(r"\r\n|\r")

# Reduce more than two consecutive blank lines to two.
_RE_BLANK_LINES = re.compile(r"\n{3,}")

# Soft-hyphen at end of line: "environ-\nment" → "environment"
# The hyphen may be a regular hyphen, en-dash (U+2013), or soft-hyphen (U+00AD).
_RE_DEHYPHEN = re.compile(r"([\u00AD\-\u2013])[ \t]*\n[ \t]*(\S)")

# Page-number patterns (PDF-to-HTML artefacts).
# Matches lines that contain only a page number, optionally surrounded by dashes.
_RE_PAGE_NUM_LINE = re.compile(
    r"^\s*"
    r"(?:"
    r"(?:page\s*)?\d{1,4}"          # "45"  or  "Page 45"
    r"|"
    r"-+\s*\d{1,4}\s*-+"            # "- 45 -"
    r"|"
    r"\d{1,4}\s*of\s*\d{1,4}"       # "45 of 120"
    r")"
    r"\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Leftover HTML entities we want to keep (converted to their literal
# ASCII/Unicode equivalents by html.unescape, but we add a few extras).
# This pattern catches anything html.unescape misses.
_RE_HTML_ENTITY = re.compile(r"&[a-zA-Z]{2,8};|&#\d{1,6};|&#x[0-9a-fA-F]{1,6};")

# Characters we explicitly keep even though they are non-ASCII:
#   \u2013  en-dash
#   \u2014  em-dash
#   \u2018/\u2019  curly single quotes
#   \u201C/\u201D  curly double quotes
#   \u2022  bullet
#   \u00A9  copyright
#   \u00AE  registered trademark
#   \u2122  trademark
#   \u00B0  degree sign
#   \u00B7  middle dot (common list bullet in filings)
#   \u00B5  micro sign
#   \u00A3/\u00A5/\u20AC  £, ¥, €
_KEEP_CHARS = frozenset(
    "\u2013\u2014\u2018\u2019\u201C\u201D"
    "\u2022\u00A9\u00AE\u2122\u00B0\u00B7\u00B5"
    "\u00A3\u00A5\u20AC"
)

# Replacement map: map certain non-ASCII to ASCII equivalents before stripping
_CHAR_MAP: dict[str, str] = {
    "\u2013": "-",   # en-dash → hyphen
    "\u2014": "--",  # em-dash → double hyphen
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote / apostrophe
    "\u201C": '"',   # left double quote
    "\u201D": '"',   # right double quote
    "\u2022": "*",   # bullet
    "\u00A9": "(c)", # copyright
    "\u00AE": "(R)", # registered
    "\u2122": "(TM)",# trademark
    "\u00B0": "deg", # degree
    "\u00B7": "*",   # middle dot
    "\u00AD": "",    # soft hyphen (invisible, just remove)
    "\u00A0": " ",   # non-breaking space
    "\u2003": " ",   # em space
    "\u2002": " ",   # en space
    "\u200B": "",    # zero-width space
    "\u200C": "",    # zero-width non-joiner
    "\u200D": "",    # zero-width joiner
    "\uFEFF": "",    # BOM / zero-width no-break space
}

# Trailing/leading whitespace on each line
_RE_LINE_STRIP = re.compile(r"^[ \t]+|[ \t]+$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def normalize_whitespace(text: str) -> str:
    """Collapse horizontal whitespace and normalize line endings.

    Steps:
    1. Normalize ``\\r\\n`` / ``\\r`` → ``\\n``.
    2. Collapse runs of spaces and tabs (but *not* newlines) to a single space.
    3. Strip leading/trailing whitespace on each line.
    4. Collapse 3+ consecutive blank lines to 2.
    5. Strip overall leading/trailing whitespace.

    Parameters
    ----------
    text:
        Raw input text; may be empty.

    Returns
    -------
    str
        Whitespace-normalized text.
    """
    if not text:
        return ""
    text = _RE_LINE_ENDINGS.sub("\n", text)
    text = _RE_HORIZ_WS.sub(" ", text)
    text = _RE_LINE_STRIP.sub("", text)
    text = _RE_BLANK_LINES.sub("\n\n", text)
    return text.strip()


def dehyphenate(text: str) -> str:
    """Rejoin words that were broken across lines with a hyphen.

    Handles:
    * Regular hyphen ``-``
    * Soft-hyphen ``\\u00AD``
    * En-dash ``\\u2013`` (occasionally misused as line-break marker)

    Example::

        "environ-\\nment"  →  "environment"
        "multi-\\nstep"    →  "multistep"
        "state-of-\\nthe-art" →  "state-of-the-art"

    Parameters
    ----------
    text:
        Input text.

    Returns
    -------
    str
        De-hyphenated text.
    """
    if not text:
        return ""
    # Keep the second character as-is (preserves capitalisation in proper nouns)
    return _RE_DEHYPHEN.sub(r"\2", text)


def remove_nonascii_artifacts(text: str) -> str:
    """Replace non-ASCII characters with ASCII equivalents or spaces.

    The function first applies :data:`_CHAR_MAP` for known substitutions,
    then attempts Unicode NFKD decomposition (which converts accented
    letters to their base form), and finally replaces any remaining
    non-ASCII code-points with a space.

    Parameters
    ----------
    text:
        Input text potentially containing non-ASCII characters.

    Returns
    -------
    str
        ASCII-clean text.
    """
    if not text:
        return ""

    # Apply explicit character map first
    result: list[str] = []
    for ch in text:
        if ord(ch) < 128:
            result.append(ch)
        elif ch in _CHAR_MAP:
            result.append(_CHAR_MAP[ch])
        else:
            # Try NFKD decomposition to strip diacritics
            normalized = unicodedata.normalize("NFKD", ch)
            ascii_part = normalized.encode("ascii", errors="ignore").decode("ascii")
            if ascii_part:
                result.append(ascii_part)
            else:
                result.append(" ")

    return "".join(result)


def remove_page_number_artifacts(text: str) -> str:
    """Remove standalone page-number lines common in PDF-to-HTML conversions.

    Patterns removed (full-line matches only):
    * ``45``  — a bare integer on its own line
    * ``Page 45``
    * ``- 45 -``  or  ``-- 45 --``
    * ``45 of 120``

    Parameters
    ----------
    text:
        Input text.

    Returns
    -------
    str
        Text with page-number lines removed.
    """
    if not text:
        return ""
    return _RE_PAGE_NUM_LINE.sub("", text)


def remove_html_artifacts(text: str) -> str:
    """Unescape HTML entities and remove any residual markup artefacts.

    Uses :func:`html.unescape` for standard named/numeric entities, then
    handles a small set of edge cases that ``html.unescape`` may miss.

    Common conversions:
    * ``&amp;``  → ``&``
    * ``&nbsp;``  → space
    * ``&lt;`` / ``&gt;``  → ``<`` / ``>``
    * ``&mdash;``  → ``--``
    * ``&ndash;``  → ``-``
    * ``&#160;``  → space  (non-breaking space)

    Parameters
    ----------
    text:
        Text that may contain HTML entities.

    Returns
    -------
    str
        Text with HTML entities resolved to their character equivalents.
    """
    if not text:
        return ""

    # Standard library handles the vast majority of cases
    text = html.unescape(text)

    # Replace non-breaking space that may have survived as literal char
    text = text.replace("\u00A0", " ")
    text = text.replace("\u200B", "")  # zero-width space
    text = text.replace("\uFEFF", "")  # BOM

    # Strip any orphaned entity-like tokens that html.unescape left behind
    # (e.g. vendor-specific entities like &rsquo; if not in the HTML5 table)
    text = _RE_HTML_ENTITY.sub(" ", text)

    return text


def clean_text(text: str) -> str:
    """Full normalization pipeline for SEC 10-K extracted text.

    Pipeline (in order):
    1. :func:`remove_html_artifacts`    — unescape entities first
    2. :func:`dehyphenate`              — rejoin wrapped words before WS collapse
    3. :func:`remove_nonascii_artifacts`— ASCII-ify
    4. :func:`remove_page_number_artifacts` — strip page numbers
    5. :func:`normalize_whitespace`     — final WS cleanup

    Parameters
    ----------
    text:
        Raw extracted text from an SEC filing.

    Returns
    -------
    str
        Production-clean text ready for silver-layer storage.
    """
    if not text:
        return ""
    text = remove_html_artifacts(text)
    text = dehyphenate(text)
    text = remove_nonascii_artifacts(text)
    text = remove_page_number_artifacts(text)
    text = normalize_whitespace(text)
    return text


def token_count(text: str) -> int:
    """Approximate LLM token count using a word-based heuristic.

    Uses the rule-of-thumb that 1 token ≈ 0.75 words (i.e., ≈ 4 characters
    per token for English prose).  Suitable for quick budget checks before
    calling a language model API.

    Parameters
    ----------
    text:
        Any string.

    Returns
    -------
    int
        Estimated token count, minimum 1 (returns 1 for empty/whitespace).
    """
    if not text or not text.strip():
        return 1
    words = len(text.split())
    return max(1, math.ceil(words / 0.75))
