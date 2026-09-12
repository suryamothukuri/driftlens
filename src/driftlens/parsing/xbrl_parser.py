"""
xbrl_parser.py
==============
Extracts standardized financial facts from the SEC EDGAR
``companyfacts.zip`` archive (XBRL inline data) and returns tidy
pandas DataFrames for downstream analysis.

The zip file is the bulk data download available at:
    https://data.sec.gov/api/xbrl/companyfacts.zip

Typical usage::

    from pathlib import Path
    from driftlens.parsing.xbrl_parser import XBRLParser, extract_facts_for_universe

    parser = XBRLParser(Path("data/bronze/companyfacts.zip"))
    df = extract_facts_for_universe(parser, cik_list=["0000320193"], fiscal_years=[2020, 2021, 2022])
"""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Primary us-gaap concepts we want to extract, with optional fallback names.
# Format: (primary_concept, fallback_concept_or_None)
_CONCEPTS: list[tuple[str, Optional[str]]] = [
    ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("NetIncomeLoss", None),
    ("Assets", None),
    ("Liabilities", None),
    ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    ("EarningsPerShareBasic", None),
]

# Form types that count as annual 10-K filings
_ANNUAL_FORMS: frozenset[str] = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _zero_pad_cik(cik: str) -> str:
    """Return a zero-padded 10-digit CIK string."""
    return str(cik).strip().lstrip("0").zfill(10)


def _find_annual_unit_entries(
    concept_facts: dict,
    fiscal_year: int,
    accepted_units: tuple[str, ...] = ("USD", "shares", "USD/shares"),
) -> list[dict]:
    """Return all unit entries that are 10-K annual filings for *fiscal_year*.

    Parameters
    ----------
    concept_facts:
        The ``facts["us-gaap"][concept]`` dict from the companyfacts JSON.
    fiscal_year:
        Calendar fiscal year (e.g. 2021).
    accepted_units:
        Tuple of acceptable unit strings (default covers most us-gaap facts).

    Returns
    -------
    list[dict]
        Matching entries (may be empty).
    """
    units_dict: dict = concept_facts.get("units", {})
    entries: list[dict] = []

    for unit_label, unit_entries in units_dict.items():
        if unit_label not in accepted_units:
            continue
        for entry in unit_entries:
            form = entry.get("form", "")
            fy = entry.get("fy")
            fp = entry.get("fp", "")
            if form in _ANNUAL_FORMS and fy == fiscal_year and fp == "FY":
                entries.append({**entry, "_unit": unit_label})

    return entries


def _pick_best_entry(entries: list[dict]) -> Optional[dict]:
    """Among multiple matching entries pick the most-recently *filed* one."""
    if not entries:
        return None
    # Sort by filed date descending, then accn descending as tiebreak
    return sorted(entries, key=lambda e: (e.get("filed", ""), e.get("accn", "")), reverse=True)[0]


# ---------------------------------------------------------------------------
# XBRLParser
# ---------------------------------------------------------------------------


class XBRLParser:
    """Parse SEC XBRL companyfacts.zip to extract financial data.

    Parameters
    ----------
    facts_zip_path:
        Path to the ``companyfacts.zip`` bulk file downloaded from SEC EDGAR.

    Raises
    ------
    FileNotFoundError
        If *facts_zip_path* does not exist.
    """

    def __init__(self, facts_zip_path: Path) -> None:
        self.facts_zip_path = Path(facts_zip_path)
        if not self.facts_zip_path.exists():
            raise FileNotFoundError(
                f"companyfacts.zip not found: {self.facts_zip_path}"
            )
        self._zip: Optional[zipfile.ZipFile] = None
        logger.info("XBRLParser initialised with %s", self.facts_zip_path)

    # ------------------------------------------------------------------
    # Context-manager support so callers can use ``with XBRLParser(...) as p:``
    # ------------------------------------------------------------------

    def __enter__(self) -> "XBRLParser":
        self._zip = zipfile.ZipFile(self.facts_zip_path, "r")
        return self

    def __exit__(self, *args: object) -> None:
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    def _open_zip(self) -> zipfile.ZipFile:
        """Open the zip lazily; reuse if already open."""
        if self._zip is None:
            self._zip = zipfile.ZipFile(self.facts_zip_path, "r")
        return self._zip

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def get_company_facts(self, cik: str) -> dict:
        """Load and return the companyfacts JSON for *cik*.

        The companyfacts.zip uses filenames like ``CIK0000320193.json``.

        Parameters
        ----------
        cik:
            CIK as a string (with or without leading zeros).

        Returns
        -------
        dict
            Parsed JSON dict from the zip.  Returns an empty dict if the
            company is not found in the zip.
        """
        padded = _zero_pad_cik(cik)
        filename = f"CIK{padded}.json"
        zf = self._open_zip()
        try:
            with zf.open(filename) as fh:
                return json.load(fh)
        except KeyError:
            logger.warning("CIK %s not found in companyfacts.zip (looked for %s)", cik, filename)
            return {}
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error for CIK %s: %s", cik, exc)
            return {}

    def get_fiscal_year_value(
        self,
        facts: dict,
        concept: str,
        fiscal_year: int,
    ) -> Optional[float]:
        """Return the 10-K annual value for *concept* in *fiscal_year*.

        Searches the ``us-gaap`` taxonomy first, then ``dei`` as a fallback.
        Picks the most recently filed entry when multiple exist (e.g. amended
        10-K/A filings).

        Parameters
        ----------
        facts:
            Full companyfacts dict (as returned by :meth:`get_company_facts`).
        concept:
            us-gaap concept name, e.g. ``"NetIncomeLoss"``.
        fiscal_year:
            Integer fiscal year (e.g. ``2022``).

        Returns
        -------
        float or None
            The numeric value, or ``None`` if not found / not reported.
        """
        for taxonomy in ("us-gaap", "dei"):
            concept_facts = facts.get("facts", {}).get(taxonomy, {}).get(concept)
            if concept_facts is None:
                continue
            entries = _find_annual_unit_entries(concept_facts, fiscal_year)
            best = _pick_best_entry(entries)
            if best is not None:
                raw = best.get("val")
                if raw is None:
                    continue
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    logger.warning(
                        "Non-numeric value for %s / %d: %r", concept, fiscal_year, raw
                    )
                    return None
        return None

    def extract_standard_facts(
        self,
        cik: str,
        company_facts: dict,
        fiscal_years: list[int],
    ) -> pd.DataFrame:
        """Extract a standard set of financial facts into a tidy DataFrame.

        Parameters
        ----------
        cik:
            Company CIK.
        company_facts:
            Pre-loaded facts dict from :meth:`get_company_facts`.
        fiscal_years:
            List of fiscal years to extract.

        Returns
        -------
        pd.DataFrame
            Columns: ``cik``, ``fiscal_year``, ``concept``, ``value``,
            ``unit``, ``filed_date``.  One row per (fiscal_year, concept).
            Rows where the value is not found are **omitted** (not NaN rows),
            so callers should use pivot/unstack with ``fill_value=None``
            downstream if a wide format is needed.
        """
        if not company_facts:
            logger.warning("Empty company_facts for CIK %s — skipping", cik)
            return pd.DataFrame(columns=["cik", "fiscal_year", "concept", "value", "unit", "filed_date"])

        records: list[dict] = []

        for fiscal_year in fiscal_years:
            for primary_concept, fallback_concept in _CONCEPTS:
                # Try primary concept first, then fallback
                resolved_concept: Optional[str] = None
                entry: Optional[dict] = None

                for candidate in filter(None, [primary_concept, fallback_concept]):
                    for taxonomy in ("us-gaap", "dei"):
                        concept_facts = (
                            company_facts.get("facts", {})
                            .get(taxonomy, {})
                            .get(candidate)
                        )
                        if concept_facts is None:
                            continue
                        entries = _find_annual_unit_entries(concept_facts, fiscal_year)
                        best = _pick_best_entry(entries)
                        if best is not None:
                            resolved_concept = candidate
                            entry = best
                            break
                    if entry is not None:
                        break

                if entry is None:
                    logger.debug(
                        "CIK %s FY%d: concept '%s' not found", cik, fiscal_year, primary_concept
                    )
                    continue

                raw_val = entry.get("val")
                try:
                    value = float(raw_val) if raw_val is not None else None
                except (TypeError, ValueError):
                    value = None

                if value is None:
                    continue

                records.append(
                    {
                        "cik": _zero_pad_cik(cik),
                        "fiscal_year": fiscal_year,
                        "concept": primary_concept,   # always store by primary name
                        "reported_as": resolved_concept,
                        "value": value,
                        "unit": entry.get("_unit", "USD"),
                        "filed_date": entry.get("filed"),
                    }
                )

        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame(
                columns=["cik", "fiscal_year", "concept", "reported_as", "value", "unit", "filed_date"]
            )
        # Ensure correct types
        df["fiscal_year"] = df["fiscal_year"].astype(int)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------


def extract_facts_for_universe(
    parser: XBRLParser,
    cik_list: list[str],
    fiscal_years: list[int],
    show_progress: bool = True,
) -> pd.DataFrame:
    """Batch-extract standard XBRL facts for a list of companies.

    Wraps :meth:`XBRLParser.extract_standard_facts` with a progress bar
    (via ``tqdm`` if installed, plain loop otherwise) and graceful error
    handling — a single bad CIK never aborts the batch.

    Parameters
    ----------
    parser:
        An initialised :class:`XBRLParser` instance.
    cik_list:
        List of CIK strings (order is preserved in output).
    fiscal_years:
        List of fiscal years to extract for every company.
    show_progress:
        Show a ``tqdm`` progress bar when ``True`` (default).

    Returns
    -------
    pd.DataFrame
        Combined DataFrame from all companies.  Columns same as
        :meth:`XBRLParser.extract_standard_facts`.
    """
    try:
        from tqdm import tqdm  # optional dependency
        iterator = tqdm(cik_list, desc="Extracting XBRL facts", unit="cik") if show_progress else cik_list
    except ImportError:
        logger.debug("tqdm not installed — progress bar disabled")
        iterator = cik_list

    all_frames: list[pd.DataFrame] = []

    for cik in iterator:
        try:
            facts = parser.get_company_facts(cik)
            df = parser.extract_standard_facts(cik, facts, fiscal_years)
            if not df.empty:
                all_frames.append(df)
        except Exception as exc:  # noqa: BLE001 — never crash the batch
            logger.error("Unexpected error for CIK %s: %s", cik, exc, exc_info=True)

    if not all_frames:
        logger.warning("extract_facts_for_universe: no data extracted for any CIK")
        return pd.DataFrame(
            columns=["cik", "fiscal_year", "concept", "reported_as", "value", "unit", "filed_date"]
        )

    combined = pd.concat(all_frames, ignore_index=True)
    logger.info(
        "extract_facts_for_universe: extracted %d rows for %d CIKs",
        len(combined),
        len(all_frames),
    )
    return combined
