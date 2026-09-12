"""
driftlens.drift.change_detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Year-over-year drift detection: intensity deltas, materiality scoring,
centroid (semantic phrasing) drift, and ranked change summaries.

Key formulas
------------
* intensity_delta      = intensity[year_n] - intensity[year_n-1]
* materiality_score    = abs(intensity_delta) * log(1 + chunk_count_year_n)
* centroid_drift       = 1 - cosine_similarity(mean_embedding_n, mean_embedding_n-1)

Change type classification (applied per (cik, cluster_id) transition):
  'new'          – first appearance (cluster present now, never seen before)
  'intensifying' – intensity_delta  >  0.02
  'fading'       – intensity_delta  < -0.02
  'disappeared'  – intensity == 0 and prev_intensity > 0
  'stable'       – abs(intensity_delta) <= 0.02
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTENSIFYING_THRESHOLD: float = 0.02
FADING_THRESHOLD: float = -0.02


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_yoy_changes(intensity_df: pd.DataFrame) -> pd.DataFrame:
    """Compute year-over-year intensity changes for every (cik, cluster_id) pair.

    For each company × theme combination the function walks the sorted fiscal
    year sequence and produces one output row per consecutive year-pair.  The
    first year a cluster is ever observed is treated as having a previous
    intensity of 0.

    Parameters
    ----------
    intensity_df:
        Output of :func:`~driftlens.drift.intensity.compute_intensity`.
        Required columns: ``cik``, ``fiscal_year``, ``cluster_id``,
        ``intensity``, ``chunk_count``.

    Returns
    -------
    pd.DataFrame
        One row per (cik, cluster_id, fiscal_year) with columns:

        ``cik``, ``cluster_id``, ``fiscal_year``, ``intensity``,
        ``prev_intensity``, ``intensity_delta``, ``chunk_count``,
        ``materiality_score``, ``change_type``, ``first_appearance``,
        ``disappeared``.

        Sorted by (cik, cluster_id, fiscal_year).

    Raises
    ------
    ValueError
        If required columns are missing.
    """
    required_cols = {"cik", "fiscal_year", "cluster_id", "intensity", "chunk_count"}
    _validate_columns(intensity_df, required_cols, context="compute_yoy_changes")

    if intensity_df.empty:
        logger.warning("compute_yoy_changes received empty intensity DataFrame.")
        return _empty_changes_df()

    # Work on a sorted copy; keep only columns we need to avoid bloat.
    df = (
        intensity_df[["cik", "fiscal_year", "cluster_id", "intensity", "chunk_count"]]
        .sort_values(["cik", "cluster_id", "fiscal_year"])
        .copy()
    )

    # ------------------------------------------------------------------
    # Previous-year intensity via group-wise shift
    # ------------------------------------------------------------------
    df["prev_intensity"] = (
        df.groupby(["cik", "cluster_id"])["intensity"].shift(1).fillna(0.0)
    )

    # ------------------------------------------------------------------
    # Delta and materiality
    # ------------------------------------------------------------------
    df["intensity_delta"] = df["intensity"] - df["prev_intensity"]
    df["materiality_score"] = (
        df["intensity_delta"].abs() * np.log1p(df["chunk_count"])
    )

    # ------------------------------------------------------------------
    # Boolean flags
    # ------------------------------------------------------------------
    # first_appearance: cluster is present now AND prev_intensity was 0
    df["first_appearance"] = (df["intensity"] > 0) & (df["prev_intensity"] == 0.0)
    # disappeared: was present before, now at zero
    df["disappeared"] = (df["intensity"] == 0.0) & (df["prev_intensity"] > 0)

    # ------------------------------------------------------------------
    # Change type classification
    # ------------------------------------------------------------------
    df["change_type"] = df.apply(_classify_change, axis=1)

    # ------------------------------------------------------------------
    # Output column order
    # ------------------------------------------------------------------
    out_cols = [
        "cik",
        "cluster_id",
        "fiscal_year",
        "intensity",
        "prev_intensity",
        "intensity_delta",
        "chunk_count",
        "materiality_score",
        "change_type",
        "first_appearance",
        "disappeared",
    ]
    result = df[out_cols].reset_index(drop=True)

    logger.info(
        "compute_yoy_changes: %d transitions | %d companies, %d clusters.",
        len(result),
        result["cik"].nunique(),
        result["cluster_id"].nunique(),
    )

    return result


def compute_centroid_drift(
    chunks_df: pd.DataFrame,
    embeddings: np.ndarray,
    chunk_ids_list: list[str],
) -> pd.DataFrame:
    """Compute cosine centroid drift for every (cik, cluster_id, fiscal_year) pair.

    For each (cik, cluster_id) that exists in consecutive years the function
    computes the cosine distance between the mean embedding of year N and the
    mean embedding of year N-1.

        centroid_drift = 1 - cosine_similarity(mean_N, mean_N-1)

    A value of 0.0 means the semantic centre did not shift at all; 1.0 means
    it moved to an orthogonal direction; 2.0 (theoretical maximum) means exact
    opposite direction.

    Parameters
    ----------
    chunks_df:
        DataFrame containing at minimum: ``chunk_id``, ``cik``,
        ``fiscal_year``, ``cluster_id``.
    embeddings:
        2-D numpy array of shape ``(N, embedding_dim)`` where N aligns with
        *chunk_ids_list*.
    chunk_ids_list:
        Ordered list of chunk IDs corresponding to rows of *embeddings*.

    Returns
    -------
    pd.DataFrame
        Columns: ``cik``, ``cluster_id``, ``fiscal_year``, ``centroid_drift``.
        Only rows where a prior year exists are included (no drift for the
        first year of a cluster).

    Raises
    ------
    ValueError
        If required columns are missing or array / list lengths are inconsistent.
    """
    required_cols = {"chunk_id", "cik", "fiscal_year", "cluster_id"}
    _validate_columns(chunks_df, required_cols, context="compute_centroid_drift")

    embeddings = np.asarray(embeddings)
    if embeddings.ndim != 2:
        raise ValueError(
            f"embeddings must be a 2-D array; got shape {embeddings.shape}."
        )
    if len(chunk_ids_list) != len(embeddings):
        raise ValueError(
            f"chunk_ids_list length ({len(chunk_ids_list)}) must equal "
            f"embeddings first dimension ({len(embeddings)})."
        )

    # Build chunk_id -> row index lookup
    id_to_idx: dict[str, int] = {cid: i for i, cid in enumerate(chunk_ids_list)}

    # Attach embedding row index to chunk metadata
    df = chunks_df[["chunk_id", "cik", "fiscal_year", "cluster_id"]].copy()
    df["emb_idx"] = df["chunk_id"].map(id_to_idx)

    missing_embeddings = df["emb_idx"].isna().sum()
    if missing_embeddings:
        logger.warning(
            "%d chunks have no embedding row; they will be excluded from "
            "centroid computation.",
            int(missing_embeddings),
        )
    df = df.dropna(subset=["emb_idx"])
    df["emb_idx"] = df["emb_idx"].astype(int)

    # Noise cluster excluded
    df = df[df["cluster_id"] != -1]

    if df.empty:
        logger.warning("compute_centroid_drift: no usable chunks; returning empty.")
        return _empty_centroid_df()

    # ------------------------------------------------------------------
    # Compute mean embedding per (cik, cluster_id, fiscal_year)
    # ------------------------------------------------------------------
    groups = df.groupby(["cik", "cluster_id", "fiscal_year"])
    centroid_records: list[dict] = []

    for (cik, cluster_id, fiscal_year), group in groups:
        indices = group["emb_idx"].tolist()
        mean_vec = embeddings[indices].mean(axis=0)
        centroid_records.append(
            {
                "cik": cik,
                "cluster_id": cluster_id,
                "fiscal_year": int(fiscal_year),
                "mean_embedding": mean_vec,
            }
        )

    centroid_df = pd.DataFrame(centroid_records)

    # ------------------------------------------------------------------
    # For each (cik, cluster_id) compute drift between consecutive years
    # ------------------------------------------------------------------
    drift_records: list[dict] = []
    centroid_df = centroid_df.sort_values(["cik", "cluster_id", "fiscal_year"])

    for (cik, cluster_id), grp in centroid_df.groupby(["cik", "cluster_id"]):
        grp = grp.sort_values("fiscal_year").reset_index(drop=True)
        for i in range(1, len(grp)):
            vec_n = grp.at[i, "mean_embedding"].reshape(1, -1)
            vec_prev = grp.at[i - 1, "mean_embedding"].reshape(1, -1)
            sim = float(cosine_similarity(vec_n, vec_prev)[0, 0])
            # Clamp to [-1, 1] to guard against floating-point drift
            sim = max(-1.0, min(1.0, sim))
            drift = 1.0 - sim
            drift_records.append(
                {
                    "cik": cik,
                    "cluster_id": cluster_id,
                    "fiscal_year": int(grp.at[i, "fiscal_year"]),
                    "centroid_drift": drift,
                }
            )

    if not drift_records:
        logger.info(
            "compute_centroid_drift: no consecutive year pairs found; "
            "each (cik, cluster_id) may only have one year of data."
        )
        return _empty_centroid_df()

    result = pd.DataFrame(drift_records).reset_index(drop=True)

    logger.info(
        "compute_centroid_drift: %d drift scores computed.",
        len(result),
    )

    return result


def rank_changes(
    changes_df: pd.DataFrame,
    centroid_drift_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge YoY changes with centroid drift and rank by materiality.

    The two DataFrames are joined on ``(cik, cluster_id, fiscal_year)``.
    Rows without a centroid drift value (e.g. first-year appearances where no
    prior year exists) receive ``NaN`` for ``centroid_drift``.

    A global ``rank`` column is added where ``1`` denotes the most material
    change across the entire corpus.

    Parameters
    ----------
    changes_df:
        Output of :func:`compute_yoy_changes`.
    centroid_drift_df:
        Output of :func:`compute_centroid_drift`.

    Returns
    -------
    pd.DataFrame
        All columns from *changes_df* plus ``centroid_drift`` and ``rank``,
        sorted by ``materiality_score`` descending.

    Raises
    ------
    ValueError
        If required columns are missing from either input.
    """
    _validate_columns(
        changes_df,
        {"cik", "cluster_id", "fiscal_year", "materiality_score"},
        context="rank_changes:changes_df",
    )

    if not centroid_drift_df.empty:
        _validate_columns(
            centroid_drift_df,
            {"cik", "cluster_id", "fiscal_year", "centroid_drift"},
            context="rank_changes:centroid_drift_df",
        )

    if changes_df.empty:
        logger.warning("rank_changes: changes_df is empty.")
        return changes_df.assign(centroid_drift=pd.Series(dtype=float), rank=pd.Series(dtype=int))

    # Left join: every change row is kept; drift is nullable
    if centroid_drift_df.empty:
        merged = changes_df.copy()
        merged["centroid_drift"] = np.nan
    else:
        merged = changes_df.merge(
            centroid_drift_df[["cik", "cluster_id", "fiscal_year", "centroid_drift"]],
            on=["cik", "cluster_id", "fiscal_year"],
            how="left",
        )

    # Sort descending by materiality and assign dense rank
    merged = merged.sort_values("materiality_score", ascending=False).reset_index(drop=True)
    merged["rank"] = merged["materiality_score"].rank(
        method="min", ascending=False
    ).astype(int)

    logger.info(
        "rank_changes: %d ranked rows; top materiality_score = %.4f.",
        len(merged),
        merged["materiality_score"].iloc[0] if len(merged) else 0.0,
    )

    return merged


def get_top_changes(ranked_df: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """Return the top-*n* most material changes from a ranked changes DataFrame.

    Parameters
    ----------
    ranked_df:
        Output of :func:`rank_changes`.
    n:
        Maximum number of rows to return.  Defaults to 500.

    Returns
    -------
    pd.DataFrame
        The top *n* rows of *ranked_df* sorted by ``materiality_score``
        descending, with the index reset.
    """
    if ranked_df.empty:
        logger.warning("get_top_changes: received empty DataFrame.")
        return ranked_df

    if "materiality_score" not in ranked_df.columns:
        raise ValueError(
            "get_top_changes expects a 'materiality_score' column; "
            "ensure the input is the output of rank_changes()."
        )

    top = (
        ranked_df.sort_values("materiality_score", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )

    logger.info("get_top_changes: returning %d / %d rows.", len(top), len(ranked_df))

    return top


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _classify_change(row: pd.Series) -> str:
    """Return the change_type string for a single transition row."""
    intensity: float = row["intensity"]
    prev_intensity: float = row["prev_intensity"]
    delta: float = row["intensity_delta"]

    if intensity > 0 and prev_intensity == 0.0:
        return "new"
    if intensity == 0.0 and prev_intensity > 0:
        return "disappeared"
    if delta > INTENSIFYING_THRESHOLD:
        return "intensifying"
    if delta < FADING_THRESHOLD:
        return "fading"
    return "stable"


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


def _empty_changes_df() -> pd.DataFrame:
    """Return an empty DataFrame with the expected changes schema."""
    return pd.DataFrame(
        columns=[
            "cik",
            "cluster_id",
            "fiscal_year",
            "intensity",
            "prev_intensity",
            "intensity_delta",
            "chunk_count",
            "materiality_score",
            "change_type",
            "first_appearance",
            "disappeared",
        ]
    )


def _empty_centroid_df() -> pd.DataFrame:
    """Return an empty DataFrame with the expected centroid drift schema."""
    return pd.DataFrame(
        columns=["cik", "cluster_id", "fiscal_year", "centroid_drift"]
    )
