"""UMAP dimensionality reduction and HDBSCAN theme clustering with Outlier Anomaly Discovery."""

import logging
from typing import Any, Dict, List, Optional

import hdbscan
import numpy as np
import umap
from sklearn.metrics.pairwise import cosine_distances

from driftlens.parsing.text_cleaning import is_grammatical_prose

logger = logging.getLogger("driftlens.nlp.clustering")

class ThemeClusterer:
    """Fits UMAP + HDBSCAN pipeline and extracts cluster manifolds + sanitized black-swan anomalies."""

    def __init__(
        self,
        umap_components: int = 12,
        umap_metric: str = "cosine",
        umap_n_neighbors: int = 15,
        hdbscan_min_cluster_size: int = 20,
        hdbscan_min_samples: int = 5,
        random_state: int = 42,
    ) -> None:
        self.umap_components = umap_components
        self.umap_metric = umap_metric
        self.umap_n_neighbors = umap_n_neighbors
        self.hdbscan_min_cluster_size = hdbscan_min_cluster_size
        self.hdbscan_min_samples = hdbscan_min_samples
        self.random_state = random_state

        self.umap_model: Optional[umap.UMAP] = None
        self.hdbscan_model: Optional[hdbscan.HDBSCAN] = None
        self.labels_: Optional[np.ndarray] = None
        self.probabilities_: Optional[np.ndarray] = None
        self.reduced_embeddings_: Optional[np.ndarray] = None
        self.cluster_centroids_: Dict[int, np.ndarray] = {}

    def fit(self, embeddings: np.ndarray) -> "ThemeClusterer":
        logger.info(f"Reducing {embeddings.shape[0]} embeddings to {self.umap_components}D with UMAP...")
        self.umap_model = umap.UMAP(
            n_components=self.umap_components,
            metric=self.umap_metric,
            n_neighbors=self.umap_n_neighbors,
            random_state=self.random_state,
            min_dist=0.05,
        )
        self.reduced_embeddings_ = self.umap_model.fit_transform(embeddings)

        logger.info("Running global HDBSCAN clustering across all company-years...")
        self.hdbscan_model = hdbscan.HDBSCAN(
            min_cluster_size=self.hdbscan_min_cluster_size,
            min_samples=self.hdbscan_min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )
        self.labels_ = self.hdbscan_model.fit_predict(self.reduced_embeddings_)
        self.probabilities_ = self.hdbscan_model.probabilities_

        self.cluster_centroids_ = self._compute_centroids(embeddings)
        return self

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        self.fit(embeddings)
        return self.labels_

    def _compute_centroids(self, original_embeddings: np.ndarray) -> Dict[int, np.ndarray]:
        centroids = {}
        unique_labels = set(self.labels_) - {-1}
        for label in unique_labels:
            mask = self.labels_ == label
            centroids[int(label)] = np.mean(original_embeddings[mask], axis=0)
        return centroids

    def get_cluster_stats(self) -> Dict[str, Any]:
        unique_labels = set(self.labels_) - {-1}
        noise_count = int(np.sum(self.labels_ == -1))
        total_count = len(self.labels_)
        noise_frac = float(noise_count / total_count) if total_count > 0 else 0.0

        cluster_sizes = {
            int(lbl): int(np.sum(self.labels_ == lbl)) for lbl in sorted(unique_labels)
        }
        return {
            "n_clusters": len(unique_labels),
            "noise_fraction": round(noise_frac, 4),
            "noise_count": noise_count,
            "total_points": total_count,
            "cluster_sizes": cluster_sizes,
        }

    def detect_novel_outlier_anomalies(
        self,
        embeddings: np.ndarray,
        chunk_ids: List[str],
        chunk_texts: List[str],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """Identifies isolated black-swan risks from HDBSCAN noise, filtering out non-prose formatting junk."""
        if len(self.cluster_centroids_) == 0 or self.labels_ is None:
            return []

        noise_indices = np.where(self.labels_ == -1)[0]
        if len(noise_indices) == 0:
            return []

        # Filter for grammatical prose to avoid tabular junk
        valid_noise_indices = [
            idx for idx in noise_indices
            if idx < len(chunk_texts) and is_grammatical_prose(chunk_texts[idx])
        ]

        if not valid_noise_indices:
            return []

        noise_embeddings = embeddings[valid_noise_indices]
        centroid_matrix = np.array(list(self.cluster_centroids_.values()))

        # Distance to closest known theme centroid
        dist_matrix = cosine_distances(noise_embeddings, centroid_matrix)
        min_distances = np.min(dist_matrix, axis=1)

        sorted_order = np.argsort(-min_distances)[:top_k]

        anomalies = []
        for rank_idx in sorted_order:
            orig_idx = valid_noise_indices[rank_idx]
            anomalies.append({
                "chunk_id": chunk_ids[orig_idx],
                "anomaly_score": round(float(min_distances[rank_idx]), 4),
                "is_outlier": True,
                "text": chunk_texts[orig_idx],
                "embedding_index": int(orig_idx)
            })
        return anomalies
