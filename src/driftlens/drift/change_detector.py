"""Change detection and statistical materiality ranking module."""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import cosine_distances, cosine_similarity

logger = logging.getLogger("driftlens.drift.change_detector")

def compute_yoy_changes(intensity_df: pd.DataFrame) -> pd.DataFrame:
    """Computes Year-over-Year changes, classification, and calibrated materiality scores."""
    records = []
    
    # Sort chronologically
    df_sorted = intensity_df.sort_values(["cik", "cluster_id", "fiscal_year"])
    
    for (cik, cluster_id), group in df_sorted.groupby(["cik", "cluster_id"]):
        group = group.reset_index(drop=True)
        for i in range(len(group)):
            row = group.iloc[i]
            year = int(row["fiscal_year"])
            curr_intensity = float(row["intensity"])
            curr_count = int(row["chunk_count"])
            
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
                elif intensity_delta > 0.025:
                    change_type = "intensifying"
                elif intensity_delta < -0.025:
                    change_type = "fading"
                else:
                    change_type = "stable"

            # Calibrated Materiality Score
            materiality_score = float(abs(intensity_delta) * np.log1p(curr_count))

            records.append({
                "cik": str(cik).zfill(10),
                "cluster_id": int(cluster_id),
                "fiscal_year": year,
                "intensity": round(curr_intensity, 4),
                "prev_intensity": round(prev_intensity, 4),
                "intensity_delta": round(intensity_delta, 4),
                "chunk_count": curr_count,
                "materiality_score": round(materiality_score, 4),
                "change_type": change_type,
                "first_appearance": first_appearance,
                "disappeared": disappeared,
            })

    return pd.DataFrame(records)

def compute_centroid_and_wasserstein_drift(
    chunks_df: pd.DataFrame,
    embeddings: np.ndarray,
    chunk_ids_list: List[str]
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

            # 2. Wasserstein / Energy Distance Approximation (Distributional Shape Shift)
            # Energy distance: 2 * E[||X - Y||] - E[||X - X'||] - E[||Y - Y'||]
            d_cross = np.mean(cdist(emb_curr, emb_prev, metric="cosine"))
            d_curr = np.mean(cdist(emb_curr, emb_curr, metric="cosine")) if len(emb_curr) > 1 else 0.0
            d_prev = np.mean(cdist(emb_prev, emb_prev, metric="cosine")) if len(emb_prev) > 1 else 0.0
            wasserstein_approx = max(0.0, float(2 * d_cross - d_curr - d_prev))

            # 3. Permutation Significance Test (p-value)
            p_val = _permutation_test(emb_curr, emb_prev, observed_stat=centroid_drift, n_iter=50)

            results.append({
                "cik": str(cik).zfill(10),
                "cluster_id": int(cluster_id),
                "fiscal_year": int(y_curr),
                "centroid_drift": round(centroid_drift, 4),
                "wasserstein_drift": round(wasserstein_approx, 4),
                "p_value": round(p_val, 4),
                "is_statistically_significant": (p_val < 0.05),
            })

    return pd.DataFrame(results)

def _permutation_test(emb_a: np.ndarray, emb_b: np.ndarray, observed_stat: float, n_iter: int = 50) -> float:
    """Permutation test to assess statistical significance of observed semantic shift."""
    combined = np.vstack([emb_a, emb_b])
    n_a = len(emb_a)
    count_greater = 0

    for _ in range(n_iter):
        permuted = np.random.permutation(combined)
        fake_a = np.mean(permuted[:n_a], axis=0, keepdims=True)
        fake_b = np.mean(permuted[n_a:], axis=0, keepdims=True)
        fake_drift = float(cosine_distances(fake_a, fake_b)[0, 0])
        if fake_drift >= observed_stat:
            count_greater += 1

    return float(count_greater / n_iter)
