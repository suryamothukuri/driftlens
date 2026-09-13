"""DriftLens ingestion subpackage."""

import json
from pathlib import Path
from typing import Any

from driftlens.ingestion.bulk_download import (
    download_bulk_companyfacts,
    download_bulk_submissions,
    extract_company_facts,
    extract_company_submissions,
    get_10k_filings_for_cik,
    get_company_tickers,
)
from driftlens.ingestion.edgar_client import EdgarClient, EdgarClientError
from driftlens.ingestion.filing_fetcher import FilingFetcher, fetch_all_filings


def pad_cik(cik: Any) -> str:
    """Pad CIK to 10 digits."""
    return str(cik).zfill(10)


def write_with_meta(path: Path | str, content: bytes, meta: dict) -> None:
    """Write content file and .meta.json sidecar."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    meta_p = p.with_suffix(p.suffix + ".meta.json")
    meta_p.write_text(json.dumps(meta, indent=2))


__all__ = [
    "EdgarClient",
    "EdgarClientError",
    "get_company_tickers",
    "download_bulk_submissions",
    "download_bulk_companyfacts",
    "extract_company_submissions",
    "extract_company_facts",
    "get_10k_filings_for_cik",
    "FilingFetcher",
    "fetch_all_filings",
    "pad_cik",
    "write_with_meta",
]
