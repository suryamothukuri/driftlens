"""Change detection, YoY delta calculation, centroid drift, and materiality ranking."""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import cosine_distances

logger = logging.getLogger("driftlens.drift.change_detector")


def compute_materiality(delta: float, chunk_count: int) -> float:
    """materiality = abs(delta) * log(1 + chunk_count)"""
    return float(abs(delta) * np.log1p(chunk_count))


def classify_change_type(
    intensity_prev: Optional[float],
    intensity_curr: Optional[float],
    delta: float,
    intensifying_threshold: float = 0.02,
    fading_threshold: float = -0.02,
) -> str:
    """Classify year-over-year change type."""
    if intensity_prev is None or (isinstance(intensity_prev, float) and np.isnan(intensity_prev)) or intensity_prev == 0.0:
        return "new"
    if intensity_curr is None or (isinstance(intensity_curr, float) and np.isnan(intensity_curr)) or intensity_curr == 0.0:
        return "disappeared"
    if delta > intensifying_threshold:
        return "intensifying"
    if delta < fading_threshold:
        return "fading"
    return "stable"


def compute_yoy_changes(intensity_df: pd.DataFrame) -> pd.DataFrame:
    """Computes Year-over-Year changes, classification, and calibrated materiality scores."""
    if intensity_df is None or intensity_df.empty:
        return pd.DataFrame(
            columns=[
                "cik",
                "cluster_id",
                "fiscal_year",
                "year",
                "intensity",
                "prev_intensity",
                "intensity_delta",
                "delta",
                "chunk_count",
                "materiality_score",
                "materiality",
                "change_type",
                "first_appearance",
                "disappeared",
            ]
        )

    df = intensity_df.copy()
    if "fiscal_year" not in df.columns and "year" in df.columns:
        df["fiscal_year"] = df["year"]
    if "intensity" not in df.columns and "chunk_count" in df.columns and "total_chunks" in df.columns:
        df["intensity"] = df["chunk_count"] / df["total_chunks"]

    records = []
    df_sorted = df.sort_values(["cik", "cluster_id", "fiscal_year"])

    for (cik, cluster_id), group in df_sorted.groupby(["cik", "cluster_id"]):
        group = group.reset_index(drop=True)
        for i in range(len(group)):
            row = group.iloc[i]
            year = int(row["fiscal_year"])
            curr_intensity = float(row["intensity"])
            curr_count = int(row.get("chunk_count", 0))

            if i == 0:
                prev_intensity = 0.0
                intensity_delta = curr_intensity
                first_appearance = True
                disappeared = False
                change_type = "new"
            else:
                prev_row = group.iloc[i - 1]
                prev_year = int(prev_row["fiscal_year"])
                if prev_year == year - 1:
                    prev_intensity = float(prev_row["intensity"])
                else:
                    prev_intensity = 0.0

                intensity_delta = curr_intensity - prev_intensity
                first_appearance = (prev_intensity == 0.0 and curr_intensity > 0.0)
                disappeared = (curr_intensity == 0.0 and prev_intensity > 0.0)

                if first_appearance:
                    change_type = "new"
                elif disappeared:
                    change_type = "disappeared"
                elif intensity_delta > 0.02:
                    change_type = "intensifying"
                elif intensity_delta < -0.02:
                    change_type = "fading"
                else:
                    change_type = "stable"

            materiality_score = float(abs(intensity_delta) * np.log1p(curr_count))

            records.append({
                "cik": str(cik),
                "cluster_id": int(cluster_id),
                "fiscal_year": year,
                "year": year,
                "intensity": float(curr_intensity),
                "prev_intensity": float(prev_intensity),
                "intensity_delta": float(intensity_delta),
                "delta": float(intensity_delta),
                "chunk_count": curr_count,
                "materiality_score": float(materiality_score),
                "materiality": float(materiality_score),
                "change_type": change_type,
                "first_appearance": first_appearance,
                "disappeared": disappeared,
            })

    return pd.DataFrame(records)


def compute_centroid_drift(
    chunks_df: pd.DataFrame,
    embeddings: np.ndarray,
    chunk_ids_list: List[str],
) -> pd.DataFrame:
    """Compute year-over-year cosine drift of theme centroids per (cik, cluster_id)."""
    if not isinstance(embeddings, np.ndarray) or embeddings.ndim != 2:
        raise ValueError("embeddings must be a 2-D array")
    if len(embeddings) != len(chunk_ids_list):
        raise ValueError("chunk_ids_list length does not match embeddings")

    if chunks_df is None or chunks_df.empty:
        return pd.DataFrame(columns=["cik", "cluster_id", "fiscal_year", "centroid_drift"])

    id_to_idx = {cid: idx for idx, cid in enumerate(chunk_ids_list)}
    results = []

    for (cik, cluster_id), group in chunks_df.groupby(["cik", "cluster_id"]):
        years = sorted(group["fiscal_year"].unique())
        for i in range(1, len(years)):
            y_curr = years[i]
            y_prev = years[i - 1]

            ids_curr = group[group["fiscal_year"] == y_curr]["chunk_id"].tolist()
            ids_prev = group[group["fiscal_year"] == y_prev]["chunk_id"].tolist()

            idx_curr = [id_to_idx[cid] for cid in ids_curr if cid in id_to_idx]
            idx_prev = [id_to_idx[cid] for cid in ids_prev if cid in id_to_idx]

            if not idx_curr or not idx_prev:
                continue

            emb_curr = embeddings[idx_curr]
            emb_prev = embeddings[idx_prev]

            mean_curr = np.mean(emb_curr, axis=0, keepdims=True)
            mean_prev = np.mean(emb_prev, axis=0, keepdims=True)
            drift = float(cosine_distances(mean_curr, mean_prev)[0, 0])

            results.append({
                "cik": str(cik),
                "cluster_id": int(cluster_id),
                "fiscal_year": int(y_curr),
                "centroid_drift": round(drift, 4),
            })

    if not results:
        return pd.DataFrame(columns=["cik", "cluster_id", "fiscal_year", "centroid_drift"])
    return pd.DataFrame(results)


def rank_changes(
    changes_df: pd.DataFrame,
    centroid_drift_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Merge changes with centroid drift and rank by materiality score descending."""
    if changes_df is None or changes_df.empty:
        return pd.DataFrame()

    if centroid_drift_df is not None and not centroid_drift_df.empty:
        merged = pd.merge(
            changes_df,
            centroid_drift_df[["cik", "cluster_id", "fiscal_year", "centroid_drift"]],
            on=["cik", "cluster_id", "fiscal_year"],
            how="left",
        )
    else:
        merged = changes_df.copy()
        if "centroid_drift" not in merged.columns:
            merged["centroid_drift"] = np.nan

    ranked = merged.sort_values("materiality_score", ascending=False).reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked


def get_top_changes(ranked_df: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """Return top N changes by materiality score."""
    if ranked_df is None or ranked_df.empty:
        return pd.DataFrame()
    return ranked_df.head(n).copy()


def compute_centroid_and_wasserstein_drift(
    chunks_df: pd.DataFrame,
    embeddings: np.ndarray,
    chunk_ids_list: List[str],
) -> pd.DataFrame:
    """Computes both mean Centroid Cosine Drift and multi-modal Wasserstein / Energy distribution distance."""
    id_to_idx = {cid: idx for idx, cid in enumerate(chunk_ids_list)}
    results = []

    for (cik, cluster_id), group in chunks_df.groupby(["cik", "cluster_id"]):
        years = sorted(group["fiscal_year"].unique())
        for i in range(1, len(years)):
            y_curr = years[i]
            y_prev = years[i - 1]
            if y_curr != y_prev + 1:
                continue

            ids_curr = group[group["fiscal_year"] == y_curr]["chunk_id"].tolist()
            ids_prev = group[group["fiscal_year"] == y_prev]["chunk_id"].tolist()

            idx_curr = [id_to_idx[cid] for cid in ids_curr if cid in id_to_idx]
            idx_prev = [id_to_idx[cid] for cid in ids_prev if cid in id_to_idx]

            if not idx_curr or not idx_prev:
                continue

            emb_curr = embeddings[idx_curr]
            emb_prev = embeddings[idx_prev]

            # 1. Centroid Cosine Drift
            mean_curr = np.mean(emb_curr, axis=0, keepdims=True)
            mean_prev = np.mean(emb_prev, axis=0, keepdims=True)
            centroid_drift = float(cosine_distances(mean_curr, mean_prev)[0, 0])

            # 2. Wasserstein / Energy Distance
            d_cross = np.mean(cdist(emb_curr, emb_prev, metric="cosine"))
            d_curr = np.mean(cdist(emb_curr, emb_curr, metric="cosine")) if len(emb_curr) > 1 else 0.0
            d_prev = np.mean(cdist(emb_prev, emb_prev, metric="cosine")) if len(emb_prev) > 1 else 0.0
            wasserstein_approx = max(0.0, float(2 * d_cross - d_curr - d_prev))

            # 3. Vectorized Permutation Test (p-value)
            p_val = _vectorized_permutation_test(emb_curr, emb_prev, observed_stat=centroid_drift, n_iter=60)

            # 4. Boilerplate Convergence Index (intra-cluster dispersion vs cross-filer similarity)
            boilerplate_index = max(0.0, min(1.0, float(1.0 - (d_curr + d_prev) / 2.0)))

            results.append({
                "cik": str(cik),
                "cluster_id": int(cluster_id),
                "fiscal_year": int(y_curr),
                "centroid_drift": round(centroid_drift, 4),
                "wasserstein_drift": round(wasserstein_approx, 4),
                "p_value": round(p_val, 4),
                "boilerplate_index": round(boilerplate_index, 4),
                "is_statistically_significant": (p_val < 0.05),
            })

    return pd.DataFrame(results)


def _vectorized_permutation_test(
    emb_a: np.ndarray, emb_b: np.ndarray, observed_stat: float, n_iter: int = 60
) -> float:
    """Fast vectorized permutation test assessing statistical significance of observed semantic shift."""
    combined = np.vstack([emb_a, emb_b])
    n_a = len(emb_a)
    n_total = len(combined)
    count_greater = 0

    for _ in range(n_iter):
        perm_idx = np.random.permutation(n_total)
        fake_a = np.mean(combined[perm_idx[:n_a]], axis=0, keepdims=True)
        fake_b = np.mean(combined[perm_idx[n_a:]], axis=0, keepdims=True)
        fake_drift = float(cosine_distances(fake_a, fake_b)[0, 0])
        if fake_drift >= observed_stat:
            count_greater += 1

    return float(count_greater / n_iter)
