"""Text cleaning, normalization, and linguistic prose validation."""

import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Collapses redundant whitespace while preserving paragraph boundaries."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

def dehyphenate(text: str) -> str:
    """Fixes words split across lines with hyphens."""
    return re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

def remove_nonascii_artifacts(text: str) -> str:
    """Normalizes unicode characters and strips unprintable control chars."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return text

def remove_page_number_artifacts(text: str) -> str:
    """Strips common PDF/HTML page number headers/footers."""
    patterns = [
        r"^\s*-\s*\d+\s*-\s*$",
        r"^\s*Page\s+\d+(\s+of\s+\d+)?\s*$",
        r"^\s*\d+\s*$",
    ]
    lines = []
    for line in text.splitlines():
        if any(re.match(p, line.strip(), re.IGNORECASE) for p in patterns):
            continue
        lines.append(line)
    return "\n".join(lines)

def is_grammatical_prose(text: str, min_words: int = 15) -> bool:
    """Validates that a chunk is genuine English prose and not tabular data or OCR noise."""
    words = text.strip().split()
    if len(words) < min_words:
        return False
    
    # Check word/symbol ratio (reject pure numbers/tables)
    alpha_words = [w for w in words if re.search(r"[a-zA-Z]", w)]
    if len(alpha_words) / len(words) < 0.65:
        return False
    
    # Must contain common English stopwords/structure
    common_markers = {"the", "and", "to", "of", "in", "a", "is", "that", "for", "our", "we", "by", "as", "with"}
    lower_words = {w.lower() for w in words}
    if len(lower_words.intersection(common_markers)) < 3:
        return False
        
    return True

def clean_text(text: str) -> str:
    """Full pipeline for text normalization."""
    text = remove_nonascii_artifacts(text)
    text = dehyphenate(text)
    text = remove_page_number_artifacts(text)
    text = normalize_whitespace(text)
    return text

def token_count(text: str) -> int:
    return max(1, int(len(text.split()) / 0.75))
