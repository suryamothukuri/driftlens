"""DriftLens ingestion subpackage."""

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
]
