"""
filing_fetcher.py
=================
Bronze-layer writer for SEC EDGAR 10-K filings.

Every file written by :class:`FilingFetcher` is *immutable* in the sense
that it is never overwritten unless ``force=True`` is passed.  Alongside
each content file a JSON sidecar (``<filename>.meta.json``) is written that
records provenance metadata required for auditing and reproducibility.

Directory layout
----------------
::

    data/bronze/
    └── {cik}/
        └── {accession_number}/
            ├── filing-index.json
            ├── filing-index.json.meta.json
            ├── <primary_document>.htm
            └── <primary_document>.htm.meta.json

Public API
----------
- :class:`FilingFetcher`     — per-CIK download orchestrator
- :func:`fetch_all_filings`  — batch helper with tqdm progress bar
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tqdm import tqdm

from driftlens.ingestion.edgar_client import EdgarClient, EdgarClientError

__all__ = ["FilingFetcher", "fetch_all_filings"]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL templates
# ---------------------------------------------------------------------------

_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"
_FILING_ARCHIVE_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodash}/{filename}"
)
_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pad_cik(cik: str | int) -> str:
    """Zero-pad *cik* to exactly 10 digits."""
    return str(int(cik)).zfill(10)


def _strip_dashes(accession_number: str) -> str:
    """Remove dashes: ``0001193125-20-123456`` -> ``000119312520123456``."""
    return accession_number.replace("-", "")


def _add_dashes(accession_nodash: str) -> str:
    """Restore dashes: ``000119312520123456`` -> ``0001193125-20-123456``."""
    s = accession_nodash.replace("-", "")
    if len(s) == 18:
        return f"{s[:10]}-{s[10:12]}-{s[12:]}"
    return s


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# FilingFetcher
# ---------------------------------------------------------------------------


class FilingFetcher:
    """Fetches and stores individual 10-K filings in the bronze layer.

    Parameters
    ----------
    client:
        Configured :class:`~driftlens.ingestion.edgar_client.EdgarClient`.
    bronze_dir:
        Root directory for bronze-layer storage.  Sub-directories are
        created automatically.

    Examples
    --------
    >>> from pathlib import Path
    >>> from driftlens.ingestion.edgar_client import EdgarClient
    >>> from driftlens.ingestion.filing_fetcher import FilingFetcher
    >>>
    >>> client = EdgarClient()
    >>> fetcher = FilingFetcher(client, bronze_dir=Path("data/bronze"))
    >>> result = fetcher.fetch_filing(
    ...     cik="320193",
    ...     accession_number="0000320193-23-000106",
    ...     primary_document="aapl-20230930.htm",
    ... )
    """

    def __init__(self, client: EdgarClient, bronze_dir: Path) -> None:
        self.client = client
        self.bronze_dir = Path(bronze_dir)
        self.bronze_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("FilingFetcher initialised with bronze_dir=%s", self.bronze_dir)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _get_bronze_path(
        self,
        cik: str,
        accession_number: str,
        filename: str,
    ) -> Path:
        """Return the canonical bronze path for a filing artifact.

        Parameters
        ----------
        cik:
            Company CIK (will be zero-padded internally).
        accession_number:
            Accession number in any format (dashes optional).
        filename:
            Name of the file to store (e.g. ``filing-index.json``).

        Returns
        -------
        pathlib.Path
            ``bronze_dir / {cik_padded} / {accession_nodash} / {filename}``
        """
        cik_padded = _pad_cik(cik)
        accession_nodash = _strip_dashes(accession_number)
        path = self.bronze_dir / cik_padded / accession_nodash / filename
        return path

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def _write_with_meta(
        self,
        path: Path,
        content: bytes,
        url: str,
        status_code: int,
    ) -> None:
        """Atomically write *content* to *path* and its ``.meta.json`` sidecar.

        The sidecar records:
        - ``url``         — the exact URL that was fetched
        - ``fetched_at``  — UTC timestamp (ISO-8601)
        - ``status_code`` — HTTP status code of the successful response
        - ``user_agent``  — User-Agent header used during the request

        Parameters
        ----------
        path:
            Destination file path.  Parent directories are created if absent.
        content:
            Raw bytes to write.
        url:
            Source URL (recorded in the sidecar).
        status_code:
            HTTP status code (recorded in the sidecar).
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        path.write_bytes(content)
        logger.debug("Wrote %d bytes to %s", len(content), path)

        # Write sidecar
        meta: dict[str, Any] = {
            "url": url,
            "fetched_at": _utc_now_iso(),
            "status_code": status_code,
            "user_agent": self.client.user_agent,
        }
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        logger.debug("Wrote sidecar metadata to %s", meta_path)

    def _is_cached(self, path: Path) -> bool:
        """Return ``True`` if both *path* and its ``.meta.json`` sidecar exist.

        Parameters
        ----------
        path:
            Content file path to check.

        Returns
        -------
        bool
            ``True`` iff both ``path`` and ``path + ".meta.json"`` are present
            on disk.
        """
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        cached = path.exists() and meta_path.exists()
        if cached:
            logger.debug("Cache hit: %s", path)
        return cached

    # ------------------------------------------------------------------
    # Fetch methods
    # ------------------------------------------------------------------

    def fetch_filing_index(
        self,
        cik: str,
        accession_number: str,
    ) -> dict:
        """Fetch the filing index JSON for a single accession and cache it.

        The filing index is retrieved from the EDGAR submissions endpoint
        (``data.sec.gov/submissions/CIK{cik_padded}.json``) which contains
        metadata about all filings.  The raw JSON is stored in the bronze
        layer as ``filing-index.json``.

        Parameters
        ----------
        cik:
            Company CIK.
        accession_number:
            Accession number (dashes optional).

        Returns
        -------
        dict
            Parsed JSON from the EDGAR submissions endpoint.
        """
        cik_padded = _pad_cik(cik)
        dest = self._get_bronze_path(cik, accession_number, "filing-index.json")

        if self._is_cached(dest):
            logger.info("Filing index already cached: %s", dest)
            return json.loads(dest.read_text(encoding="utf-8"))

        url = _SUBMISSIONS_URL.format(cik_padded=cik_padded)
        logger.info("Fetching filing index for CIK %s from %s", cik_padded, url)

        response = self.client.get(url)
        data: dict = response.json()

        self._write_with_meta(
            path=dest,
            content=response.content,
            url=url,
            status_code=response.status_code,
        )
        logger.info("Cached filing index to %s", dest)
        return data

    def fetch_primary_document(
        self,
        cik: str,
        accession_number: str,
        primary_document: str,
    ) -> Path:
        """Fetch the primary HTML document for a 10-K filing.

        Parameters
        ----------
        cik:
            Company CIK.
        accession_number:
            Accession number (dashes optional).
        primary_document:
            Filename of the primary document (e.g. ``aapl-20230930.htm``).

        Returns
        -------
        pathlib.Path
            Path to the locally cached file.
        """
        cik_padded = _pad_cik(cik)
        accession_nodash = _strip_dashes(accession_number)
        cik_int = int(cik_padded)  # EDGAR archive URLs use the integer CIK

        dest = self._get_bronze_path(cik, accession_number, primary_document)

        if self._is_cached(dest):
            logger.info("Primary document already cached: %s", dest)
            return dest

        url = _FILING_ARCHIVE_URL.format(
            cik_int=cik_int,
            accession_nodash=accession_nodash,
            filename=primary_document,
        )
        logger.info(
            "Fetching primary document %r for CIK %s accession %s",
            primary_document,
            cik_padded,
            accession_number,
        )

        response = self.client.get(url)

        self._write_with_meta(
            path=dest,
            content=response.content,
            url=url,
            status_code=response.status_code,
        )
        logger.info("Cached primary document to %s (%d bytes)", dest, len(response.content))
        return dest

    def fetch_filing(
        self,
        cik: str,
        accession_number: str,
        primary_document: str,
        force: bool = False,
    ) -> dict:
        """Orchestrate a full filing fetch: index JSON + primary HTML document.

        If ``force=False`` (the default) and both the index and primary
        document are already cached, no network requests are made.

        Parameters
        ----------
        cik:
            Company CIK.
        accession_number:
            Accession number (dashes optional).
        primary_document:
            Filename of the primary 10-K document.
        force:
            If ``True``, re-fetch and overwrite even if already cached.

        Returns
        -------
        dict
            ::

                {
                    "index_path":        str,   # absolute path to filing-index.json
                    "doc_path":          str,   # absolute path to primary document
                    "cik":               str,   # zero-padded CIK
                    "accession_number":  str,   # original accession number
                }
        """
        cik_padded = _pad_cik(cik)

        if force:
            logger.info(
                "force=True: re-fetching CIK %s / %s", cik_padded, accession_number
            )
            # Remove cached files so the helpers will re-download
            for fname in ("filing-index.json", primary_document):
                path = self._get_bronze_path(cik, accession_number, fname)
                meta_path = path.with_suffix(path.suffix + ".meta.json")
                for p in (path, meta_path):
                    if p.exists():
                        p.unlink()
                        logger.debug("Removed cached file: %s", p)

        index_data = self.fetch_filing_index(cik=cik, accession_number=accession_number)
        doc_path = self.fetch_primary_document(
            cik=cik,
            accession_number=accession_number,
            primary_document=primary_document,
        )
        index_path = self._get_bronze_path(cik, accession_number, "filing-index.json")

        return {
            "index_path": str(index_path.resolve()),
            "doc_path": str(doc_path.resolve()),
            "cik": cik_padded,
            "accession_number": accession_number,
        }


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------


def fetch_all_filings(
    fetcher: FilingFetcher,
    filing_list: list[dict],
    cik: str,
    desc: str = "",
) -> list[dict]:
    """Fetch all filings in *filing_list* with a tqdm progress bar.

    Individual failures are caught, logged, and skipped — they do **not**
    abort the entire batch.

    Parameters
    ----------
    fetcher:
        A configured :class:`FilingFetcher` instance.
    filing_list:
        List of filing dicts as returned by
        :func:`~driftlens.ingestion.bulk_download.get_10k_filings_for_cik`.
        Each dict must contain ``accession_number`` and ``primary_document``.
    cik:
        Company CIK shared by all filings in the list.
    desc:
        Optional label shown in the tqdm progress bar.

    Returns
    -------
    list[dict]
        Results for successfully fetched filings.  Each item is the dict
        returned by :meth:`FilingFetcher.fetch_filing` augmented with
        ``filing_date``, ``fiscal_year``, and ``report_date`` from the
        original ``filing_list`` entry.
    """
    results: list[dict] = []
    label = desc or f"CIK {_pad_cik(cik)}"

    for filing in tqdm(filing_list, desc=label, unit="filing"):
        accession_number: str = filing["accession_number"]
        primary_document: str = filing.get("primary_document", "")

        if not primary_document:
            logger.warning(
                "Skipping accession %s — no primary_document specified",
                accession_number,
            )
            continue

        try:
            result = fetcher.fetch_filing(
                cik=cik,
                accession_number=accession_number,
                primary_document=primary_document,
            )
            # Enrich with filing metadata
            result.update(
                {
                    "filing_date": filing.get("filing_date"),
                    "fiscal_year": filing.get("fiscal_year"),
                    "report_date": filing.get("report_date"),
                }
            )
            results.append(result)
            logger.info(
                "Fetched filing %s / %s (fiscal_year=%s)",
                _pad_cik(cik),
                accession_number,
                filing.get("fiscal_year"),
            )
        except EdgarClientError as exc:
            logger.error(
                "EDGAR error for accession %s (CIK %s): %s",
                accession_number,
                cik,
                exc,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unexpected error for accession %s (CIK %s): %r",
                accession_number,
                cik,
                exc,
            )

    logger.info(
        "fetch_all_filings complete: %d/%d filings fetched for CIK %s",
        len(results),
        len(filing_list),
        _pad_cik(cik),
    )
    return results
