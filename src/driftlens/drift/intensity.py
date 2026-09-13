"""
driftlens.drift.intensity
~~~~~~~~~~~~~~~~~~~~~~~~~
Compute per-(company, year, cluster) intensity scores from clustered chunks.

Intensity is defined as the fraction of a filing's chunks that belong to a
given thematic cluster:

    intensity = chunk_count / total_chunks_in_filing_year

This gives a scale-invariant signal: a company that writes 5 000 words about
"cybersecurity risk" in a 50 000-word filing has the same intensity (0.10) as
one that writes 2 000 words in a 20 000-word filing.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NOISE_CLUSTER_ID: int = -1  # HDBSCAN / DBSCAN noise label; always excluded


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_intensity(
    chunks_df: pd.DataFrame,
    labels: dict[int, str],
) -> pd.DataFrame:
    """Compute per-(cik, fiscal_year, cluster_id) intensity scores.

    Parameters
    ----------
    chunks_df:
        DataFrame with at minimum the columns:
            chunk_id         – unique identifier for each text chunk
            cik              – SEC Central Index Key (company identifier)
            fiscal_year      – integer fiscal year (e.g. 2023)
            accession_number – SEC filing accession number
            cluster_id       – integer cluster label from the clustering step

    labels:
        Mapping from ``cluster_id`` (int) to human-readable theme name (str).
        The noise cluster (``-1``) need not be present.

    Returns
    -------
    pd.DataFrame
        Columns: ``cik``, ``fiscal_year``, ``cluster_id``, ``cluster_label``,
        ``chunk_count``, ``total_chunks``, ``intensity``, ``is_present``.
        Rows for the noise cluster are excluded.
        Rows are sorted by (cik, fiscal_year, cluster_id).

    Raises
    ------
    ValueError
        If required columns are missing from *chunks_df*.
    """
    required_cols = {"chunk_id", "cik", "fiscal_year", "accession_number", "cluster_id"}
    _validate_columns(chunks_df, required_cols, context="compute_intensity")

    df = chunks_df.copy()

    # ------------------------------------------------------------------
    # 1. Drop noise cluster
    # ------------------------------------------------------------------
    noise_mask = df["cluster_id"] == NOISE_CLUSTER_ID
    n_noise = int(noise_mask.sum())
    if n_noise:
        logger.debug("Excluding %d noise-cluster (cluster_id=-1) chunks.", n_noise)
    df = df[~noise_mask].copy()

    if df.empty:
        logger.warning(
            "No non-noise chunks found; returning empty intensity DataFrame."
        )
        return _empty_intensity_df()

    # ------------------------------------------------------------------
    # 2. Chunk count per (cik, fiscal_year, cluster_id)
    # ------------------------------------------------------------------
    chunk_counts: pd.DataFrame = (
        df.groupby(["cik", "fiscal_year", "cluster_id"], sort=True)
        .agg(chunk_count=("chunk_id", "count"))
        .reset_index()
    )

    # ------------------------------------------------------------------
    # 3. Total chunks per filing year (cik, fiscal_year)
    # ------------------------------------------------------------------
    total_chunks: pd.DataFrame = (
        df.groupby(["cik", "fiscal_year"], sort=True)
        .agg(total_chunks=("chunk_id", "count"))
        .reset_index()
    )

    # ------------------------------------------------------------------
    # 4. Merge and compute intensity
    # ------------------------------------------------------------------
    intensity_df = chunk_counts.merge(total_chunks, on=["cik", "fiscal_year"], how="left")

    intensity_df["intensity"] = np.where(
        intensity_df["total_chunks"] > 0,
        intensity_df["chunk_count"] / intensity_df["total_chunks"],
        0.0,
    )

    # ------------------------------------------------------------------
    # 5. Attach theme labels
    # ------------------------------------------------------------------
    intensity_df["cluster_label"] = (
        intensity_df["cluster_id"].map(labels).fillna("unknown")
    )
    unmapped = intensity_df["cluster_label"].eq("unknown").sum()
    if unmapped:
        logger.warning(
            "%d rows had no label mapping in the provided labels dict.", int(unmapped)
        )

    # ------------------------------------------------------------------
    # 6. Derived boolean
    # ------------------------------------------------------------------
    intensity_df["is_present"] = intensity_df["intensity"] > 0.0

    # ------------------------------------------------------------------
    # 7. Final column order and sort
    # ------------------------------------------------------------------
    out_cols = [
        "cik",
        "fiscal_year",
        "cluster_id",
        "cluster_label",
        "chunk_count",
        "total_chunks",
        "intensity",
        "is_present",
    ]
    intensity_df = (
        intensity_df[out_cols]
        .sort_values(["cik", "fiscal_year", "cluster_id"])
        .reset_index(drop=True)
    )

    logger.info(
        "compute_intensity: %d rows | %d companies, %d years, %d clusters.",
        len(intensity_df),
        intensity_df["cik"].nunique(),
        intensity_df["fiscal_year"].nunique(),
        intensity_df["cluster_id"].nunique(),
    )

    return intensity_df


def build_presence_matrix(intensity_df: pd.DataFrame) -> pd.DataFrame:
    """Build a wide pivot table of intensity scores.

    Rows correspond to ``cluster_id``; columns are a MultiIndex of
    ``(cik, fiscal_year)``; values are ``intensity`` (``0.0`` where a cluster
    was not present for that company-year).

    Parameters
    ----------
    intensity_df:
        Output of :func:`compute_intensity`.

    Returns
    -------
    pd.DataFrame
        Pivot table indexed by ``cluster_id`` with MultiIndex columns
        ``(cik, fiscal_year)``.  Missing combinations are filled with ``0.0``.

    Raises
    ------
    ValueError
        If required columns are missing.
    """
    required_cols = {"cik", "fiscal_year", "cluster_id", "intensity"}
    _validate_columns(intensity_df, required_cols, context="build_presence_matrix")

    if intensity_df.empty:
        logger.warning("build_presence_matrix received empty DataFrame.")
        return pd.DataFrame()

    matrix = intensity_df.pivot_table(
        index="cluster_id",
        columns=["cik", "fiscal_year"],
        values="intensity",
        aggfunc="sum",
        fill_value=0.0,
    )

    logger.info(
        "build_presence_matrix: shape %s (%d clusters x %d company-years).",
        matrix.shape,
        matrix.shape[0],
        matrix.shape[1],
    )

    return matrix


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_columns(
    df: pd.DataFrame,
    required: set[str],
    context: str = "",
) -> None:
    """Raise ValueError if *df* is missing any column in *required*."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"[{context}] Input DataFrame is missing required columns: "
            f"{sorted(missing)}. "
            f"Available columns: {sorted(df.columns.tolist())}."
        )


def _empty_intensity_df() -> pd.DataFrame:
    """Return an empty DataFrame with the expected intensity schema."""
    return pd.DataFrame(
        columns=[
            "cik",
            "fiscal_year",
            "cluster_id",
            "cluster_label",
            "chunk_count",
            "total_chunks",
            "intensity",
            "is_present",
        ]
    )
