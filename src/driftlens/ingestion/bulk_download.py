"""
bulk_download.py
================
Utilities for downloading and querying EDGAR bulk-data archives.

EDGAR publishes two large ZIP archives that contain machine-readable metadata
for every registered entity:

* ``submissions.zip``    — filing submission history for all companies.
* ``companyfacts.zip``   — XBRL-tagged financial facts for all companies.

Downloading the full archives once (rather than hitting per-company endpoints
repeatedly) is more polite to EDGAR's infrastructure and much faster for
bulk research.

Public API
----------
- :func:`get_company_tickers`          — ticker / CIK mapping (with cache)
- :func:`download_bulk_submissions`    — download submissions.zip
- :func:`download_bulk_companyfacts`   — download companyfacts.zip
- :func:`extract_company_submissions`  — read one company from the ZIP
- :func:`extract_company_facts`        — read one company's facts from the ZIP
- :func:`get_10k_filings_for_cik`      — filtered, sorted 10-K filing list
"""

from __future__ import annotations

import json
import logging
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from driftlens.ingestion.edgar_client import EdgarClient

__all__ = [
    "get_company_tickers",
    "download_bulk_submissions",
    "download_bulk_companyfacts",
    "extract_company_submissions",
    "extract_company_facts",
    "get_10k_filings_for_cik",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = (
    "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
)
_COMPANYFACTS_URL = (
    "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/companyfacts.zip"
)

_CACHE_MAX_AGE = timedelta(days=7)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_fresh(path: Path, max_age: timedelta = _CACHE_MAX_AGE) -> bool:
    """Return ``True`` if *path* exists and was modified within *max_age*."""
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(tz=timezone.utc) - mtime
    fresh = age < max_age
    if not fresh:
        logger.debug("Cache file %s is stale (age=%s, max_age=%s)", path, age, max_age)
    return fresh


def _pad_cik(cik: str | int) -> str:
    """Zero-pad *cik* to exactly 10 digits."""
    return str(int(cik)).zfill(10)


def _strip_dashes(accession_number: str) -> str:
    """Remove dashes from *accession_number* (e.g. ``0001193125-20-123456`` ->
    ``000119312520123456``)."""
    return accession_number.replace("-", "")


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def get_company_tickers(
    client: EdgarClient,
    cache_path: Path,
) -> pd.DataFrame:
    """Download the SEC company-ticker mapping and return it as a DataFrame.

    The JSON is cached at *cache_path*; if the file exists and is younger
    than 7 days the network is not touched.

    Parameters
    ----------
    client:
        Configured :class:`~driftlens.ingestion.edgar_client.EdgarClient`.
    cache_path:
        Local path where the raw JSON will be cached.

    Returns
    -------
    pandas.DataFrame
        Columns: ``cik`` (int64), ``ticker`` (str), ``name`` (str).
        Sorted by ``cik``.
    """
    cache_path = Path(cache_path)

    if _is_fresh(cache_path):
        logger.info("Loading company tickers from cache: %s", cache_path)
        raw: dict[str, Any] = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        logger.info("Downloading company tickers from %s", _TICKERS_URL)
        raw = client.get_json(_TICKERS_URL)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(raw), encoding="utf-8")
        logger.info("Company tickers cached to %s", cache_path)

    records = [
        {
            "cik": int(entry["cik_str"]),
            "ticker": entry["ticker"],
            "name": entry["title"],
        }
        for entry in raw.values()
    ]
    df = pd.DataFrame(records).sort_values("cik").reset_index(drop=True)
    logger.debug("Loaded %d company tickers", len(df))
    return df


def download_bulk_submissions(
    client: EdgarClient,
    output_dir: Path,
    force: bool = False,
) -> Path:
    """Download the EDGAR bulk submissions ZIP archive.

    Parameters
    ----------
    client:
        Configured :class:`~driftlens.ingestion.edgar_client.EdgarClient`.
    output_dir:
        Directory where ``submissions.zip`` will be written.
    force:
        If ``True``, re-download even if the file already exists.

    Returns
    -------
    pathlib.Path
        Absolute path to the downloaded (or cached) ZIP file.
    """
    return _download_bulk_zip(
        client=client,
        url=_SUBMISSIONS_URL,
        filename="submissions.zip",
        output_dir=Path(output_dir),
        force=force,
    )


def download_bulk_companyfacts(
    client: EdgarClient,
    output_dir: Path,
    force: bool = False,
) -> Path:
    """Download the EDGAR bulk company-facts ZIP archive.

    Parameters
    ----------
    client:
        Configured :class:`~driftlens.ingestion.edgar_client.EdgarClient`.
    output_dir:
        Directory where ``companyfacts.zip`` will be written.
    force:
        If ``True``, re-download even if the file already exists.

    Returns
    -------
    pathlib.Path
        Absolute path to the downloaded (or cached) ZIP file.
    """
    return _download_bulk_zip(
        client=client,
        url=_COMPANYFACTS_URL,
        filename="companyfacts.zip",
        output_dir=Path(output_dir),
        force=force,
    )


def _download_bulk_zip(
    client: EdgarClient,
    url: str,
    filename: str,
    output_dir: Path,
    force: bool,
) -> Path:
    """Internal helper: download a large ZIP if not already present."""
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / filename

    if dest.exists() and not force:
        logger.info("Skipping download; file already exists: %s", dest)
        return dest

    logger.info("Downloading %s -> %s", url, dest)
    data = client.get_bytes(url)
    dest.write_bytes(data)
    logger.info("Saved %d bytes to %s", len(data), dest)
    return dest


# ---------------------------------------------------------------------------
# ZIP-based extraction helpers
# ---------------------------------------------------------------------------


def extract_company_submissions(submissions_zip: Path, cik: str) -> dict:
    """Read one company's submission record directly from the bulk ZIP.

    No full extraction is performed — only the matching member is read.

    Parameters
    ----------
    submissions_zip:
        Path to the ``submissions.zip`` archive.
    cik:
        Company CIK (will be zero-padded to 10 digits automatically).

    Returns
    -------
    dict
        Parsed JSON content of ``CIK{cik_padded}.json``.

    Raises
    ------
    KeyError
        If the CIK is not found inside the archive.
    """
    return _extract_from_zip(
        zip_path=submissions_zip,
        cik=cik,
        prefix="CIK",
    )


def extract_company_facts(facts_zip: Path, cik: str) -> dict:
    """Read one company's XBRL facts directly from the bulk facts ZIP.

    Parameters
    ----------
    facts_zip:
        Path to the ``companyfacts.zip`` archive.
    cik:
        Company CIK (will be zero-padded to 10 digits automatically).

    Returns
    -------
    dict
        Parsed JSON content of ``CIK{cik_padded}.json``.

    Raises
    ------
    KeyError
        If the CIK is not found inside the archive.
    """
    return _extract_from_zip(
        zip_path=facts_zip,
        cik=cik,
        prefix="CIK",
    )


def _extract_from_zip(zip_path: Path, cik: str, prefix: str) -> dict:
    """Generic helper: find ``{prefix}{cik_padded}.json`` in a ZIP and parse it."""
    padded = _pad_cik(cik)
    member_name = f"{prefix}{padded}.json"
    logger.debug("Looking for %s in %s", member_name, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # ZipFile.namelist() respects the ZIP's central directory; no full
        # decompression of other members is needed.
        names = zf.namelist()
        # The file may be at the top level or nested under a directory
        matches = [n for n in names if n.endswith(member_name)]
        if not matches:
            raise KeyError(
                f"{member_name!r} not found in {zip_path}. "
                f"Total members: {len(names)}"
            )
        member = matches[0]
        logger.debug("Extracting %s from %s", member, zip_path)
        with zf.open(member) as fh:
            return json.load(fh)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# 10-K filing list
# ---------------------------------------------------------------------------


def get_10k_filings_for_cik(
    client_or_submissions: Any = None,
    cik: str = "",
    submissions_zip: Path | None = None,
    years: Any = 5,
) -> list[dict]:
    """Return a list of 10-K filing metadata dicts for a given company.

    Accepts either (client, cik, submissions_zip, years) or (submissions_dict, years=years).
    """
    if isinstance(client_or_submissions, dict):
        # Called directly with submissions dictionary
        data = client_or_submissions
        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return []
        
        target_years = years if isinstance(years, (list, tuple, set)) else None
        form_list = recent.get("form", [])
        accession_list = recent.get("accessionNumber", [])
        filing_date_list = recent.get("filingDate", [])
        report_date_list = recent.get("reportDate", [])
        primary_doc_list = recent.get("primaryDocument", [])

        results = []
        for form, accession, filing_date_str, report_date_str, primary_doc in zip(
            form_list, accession_list, filing_date_list, report_date_list, primary_doc_list
        ):
            if form != "10-K":
                continue
            f_year = int(filing_date_str[:4]) if filing_date_str else 0
            if target_years and f_year not in target_years:
                continue
            results.append({
                "accession": accession,
                "accession_number": accession,
                "form": form,
                "filing_date": filing_date_str,
                "primary_doc": primary_doc,
                "primary_document": primary_doc,
                "report_date": report_date_str,
                "fiscal_year": f_year,
            })
        return results

    client = client_or_submissions
    padded_cik = _pad_cik(cik)
    num_years = years if isinstance(years, int) else 5
    cutoff: date = date.today().replace(year=date.today().year - num_years)

    # --- load submission data ------------------------------------------------
    data = _load_submissions(client, cik=padded_cik, submissions_zip=submissions_zip)

    # --- extract recent filings table ----------------------------------------
    filings_section: dict = data.get("filings", {})
    recent: dict = filings_section.get("recent", {})

    if not recent:
        logger.warning("No recent filings found for CIK %s", padded_cik)
        return []

    form_list: list[str] = recent.get("form", [])
    accession_list: list[str] = recent.get("accessionNumber", [])
    filing_date_list: list[str] = recent.get("filingDate", [])
    report_date_list: list[str] = recent.get("reportDate", [])
    primary_doc_list: list[str] = recent.get("primaryDocument", [])

    results: list[dict] = []
    for form, accession, filing_date_str, report_date_str, primary_doc in zip(
        form_list,
        accession_list,
        filing_date_list,
        report_date_list,
        primary_doc_list,
    ):
        if form not in {"10-K", "10-K/A"}:
            continue

        try:
            filing_date_obj = date.fromisoformat(filing_date_str)
        except ValueError:
            logger.debug("Skipping invalid filing date %r", filing_date_str)
            continue

        if filing_date_obj < cutoff:
            continue

        results.append(
            {
                "accession": accession,
                "accession_number": accession,
                "form": form,
                "filing_date": filing_date_str,
                "fiscal_year": filing_date_obj.year,
                "report_date": report_date_str,
                "primary_doc": primary_doc,
                "primary_document": primary_doc,
            }
        )

    results.sort(key=lambda r: r["fiscal_year"], reverse=True)
    logger.info(
        "Found %d 10-K filings for CIK %s in the last %d years",
        len(results),
        padded_cik,
        num_years,
    )
    return results


def _load_submissions(
    client: EdgarClient,
    cik: str,
    submissions_zip: Path | None,
) -> dict:
    """Load submission data from the bulk ZIP or fall back to the live API."""
    # Try bulk ZIP first
    if submissions_zip is not None and Path(submissions_zip).exists():
        try:
            logger.debug("Loading submissions for CIK %s from ZIP", cik)
            return extract_company_submissions(Path(submissions_zip), cik)
        except KeyError:
            logger.warning(
                "CIK %s not found in %s; falling back to live API", cik, submissions_zip
            )

    # Live API fallback
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    logger.info("Fetching submissions for CIK %s from %s", cik, url)
    return client.get_json(url)
