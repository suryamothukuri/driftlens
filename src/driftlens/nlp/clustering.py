"""
clustering.py — UMAP + HDBSCAN theme discovery for DriftLens.

Reduces high-dimensional embeddings with UMAP, then clusters the reduced
space with HDBSCAN.  The resulting cluster labels are stable across runs
(deterministic random_state) and are used downstream for drift detection.

Serialisation:
  output_dir/
    umap_model.joblib
    hdbscan_model.joblib
    labels.npy
    probabilities.npy
    reduced_embeddings.npy
    centroids.npz          # {cluster_id: centroid_vector}
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_distances

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parameter presets
# ---------------------------------------------------------------------------

def select_hdbscan_params(scale: str) -> dict:
    """Return sensible HDBSCAN hyperparameters for corpus size.

    Parameters
    ----------
    scale:
        One of ``'small'`` (< 1 000 chunks), ``'medium'`` (1 000–10 000),
        ``'full'`` (> 10 000).

    Returns
    -------
    dict
        ``{'min_cluster_size': int, 'min_samples': int}``
    """
    presets = {
        "small":  {"min_cluster_size": 10,  "min_samples": 3},
        "medium": {"min_cluster_size": 20,  "min_samples": 5},
        "full":   {"min_cluster_size": 50,  "min_samples": 10},
    }
    if scale not in presets:
        raise ValueError(f"scale must be one of {list(presets)}; got '{scale}'")
    return presets[scale]


# ---------------------------------------------------------------------------
# ThemeClusterer
# ---------------------------------------------------------------------------

class ThemeClusterer:
    """Unsupervised theme discovery via UMAP dimensionality reduction + HDBSCAN.

    Parameters
    ----------
    umap_components:
        Number of UMAP output dimensions.
    umap_metric:
        Distance metric for UMAP (``'cosine'`` recommended for normalised embeddings).
    umap_n_neighbors:
        UMAP neighbourhood size controlling global vs. local structure trade-off.
    hdbscan_min_cluster_size:
        Minimum number of points to form a cluster.
    hdbscan_min_samples:
        HDBSCAN robustness parameter.
    random_state:
        Seed for reproducibility (applied to UMAP).
    """

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

        # Set after fit().
        self.umap_model = None
        self.hdbscan_model = None
        self.labels_: Optional[np.ndarray] = None
        self.probabilities_: Optional[np.ndarray] = None
        self.reduced_embeddings_: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit(self, embeddings: np.ndarray) -> "ThemeClusterer":
        """Fit UMAP then HDBSCAN on *embeddings*.

        Parameters
        ----------
        embeddings:
            Float32 array of shape ``(N, dim)``.

        Returns
        -------
        ThemeClusterer
            Self (for chaining).
        """
        self._check_imports()
        import umap as umap_lib      # noqa: PLC0415
        import hdbscan as hdbscan_lib  # noqa: PLC0415

        if embeddings.ndim != 2:
            raise ValueError(f"embeddings must be 2-D; got shape {embeddings.shape}")
        n_samples = embeddings.shape[0]
        logger.info(
            "Fitting UMAP on %d embeddings (dim %d → %d) …",
            n_samples,
            embeddings.shape[1],
            self.umap_components,
        )

        # ---- Step 1: UMAP ------------------------------------------------
        t0 = time.perf_counter()
        self.umap_model = umap_lib.UMAP(
            n_components=self.umap_components,
            metric=self.umap_metric,
            n_neighbors=min(self.umap_n_neighbors, n_samples - 1),
            random_state=self.random_state,
            low_memory=False,
            verbose=False,
        )
        self.reduced_embeddings_ = self.umap_model.fit_transform(
            embeddings.astype(np.float32)
        )
        umap_elapsed = time.perf_counter() - t0
        logger.info("UMAP complete in %.2fs → shape %s", umap_elapsed, self.reduced_embeddings_.shape)

        # ---- Step 2: HDBSCAN on reduced space ----------------------------
        logger.info(
            "Fitting HDBSCAN (min_cluster_size=%d, min_samples=%d) …",
            self.hdbscan_min_cluster_size,
            self.hdbscan_min_samples,
        )
        t1 = time.perf_counter()
        self.hdbscan_model = hdbscan_lib.HDBSCAN(
            min_cluster_size=self.hdbscan_min_cluster_size,
            min_samples=self.hdbscan_min_samples,
            metric="euclidean",  # UMAP output is already in low-dim Euclidean space
            cluster_selection_method="eom",
            prediction_data=True,  # required for approximate_predict later
        )
        self.hdbscan_model.fit(self.reduced_embeddings_)
        self.labels_ = self.hdbscan_model.labels_.copy()
        self.probabilities_ = self.hdbscan_model.probabilities_.copy()
        hdbscan_elapsed = time.perf_counter() - t1

        stats = self.get_cluster_stats()
        logger.info(
            "HDBSCAN complete in %.2fs — %d clusters, %.1f%% noise",
            hdbscan_elapsed,
            stats["n_clusters"],
            stats["noise_fraction"] * 100,
        )
        return self

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """Fit and return cluster label array (``-1`` = noise).

        Parameters
        ----------
        embeddings:
            Float32 array of shape ``(N, dim)``.

        Returns
        -------
        np.ndarray
            Integer label array of shape ``(N,)``.
        """
        self.fit(embeddings)
        return self.labels_

    # ------------------------------------------------------------------
    # Cluster analytics
    # ------------------------------------------------------------------

    def get_cluster_stats(self) -> dict:
        """Summarise clustering results.

        Returns
        -------
        dict
            ``{'n_clusters': int, 'noise_fraction': float,
               'noise_count': int, 'cluster_sizes': dict[int, int]}``
        """
        self._require_fit()
        labels = self.labels_
        unique = set(labels)
        noise_count = int(np.sum(labels == -1))
        cluster_ids = sorted(uid for uid in unique if uid != -1)
        cluster_sizes = {
            int(cid): int(np.sum(labels == cid)) for cid in cluster_ids
        }
        return {
            "n_clusters": len(cluster_ids),
            "noise_fraction": noise_count / len(labels) if len(labels) else 0.0,
            "noise_count": noise_count,
            "cluster_sizes": cluster_sizes,
        }

    def get_cluster_centroids(
        self, embeddings: np.ndarray
    ) -> dict[int, np.ndarray]:
        """Compute the mean **original-space** embedding for each cluster.

        Noise points (label ``-1``) are excluded.  Using original embeddings
        (not UMAP projections) ensures centroids are meaningful for cosine
        drift detection.

        Parameters
        ----------
        embeddings:
            The same float32 array passed to :meth:`fit`, shape ``(N, dim)``.

        Returns
        -------
        dict[int, np.ndarray]
            Mapping from cluster id to centroid vector of shape ``(dim,)``.
        """
        self._require_fit()
        centroids: dict[int, np.ndarray] = {}
        for cid in np.unique(self.labels_):
            if cid == -1:
                continue
            mask = self.labels_ == cid
            centroids[int(cid)] = embeddings[mask].mean(axis=0).astype(np.float32)
        return centroids

    def get_top_chunks_per_cluster(
        self,
        embeddings: np.ndarray,
        chunk_ids: list[str],
        n_top: int = 8,
    ) -> dict[int, list[str]]:
        """Find the *n_top* chunk IDs closest (cosine) to each cluster centroid.

        Parameters
        ----------
        embeddings:
            Float32 array of shape ``(N, dim)``, L2-normalised.
        chunk_ids:
            List of N string identifiers aligned with *embeddings*.
        n_top:
            Number of representative chunks per cluster.

        Returns
        -------
        dict[int, list[str]]
            Mapping from cluster id to list of chunk ids (closest first).
        """
        self._require_fit()
        if len(chunk_ids) != embeddings.shape[0]:
            raise ValueError("chunk_ids length must equal embeddings.shape[0]")

        centroids = self.get_cluster_centroids(embeddings)
        chunk_ids_arr = np.array(chunk_ids)
        result: dict[int, list[str]] = {}

        for cid, centroid in centroids.items():
            mask = self.labels_ == cid
            cluster_embs = embeddings[mask]
            cluster_ids = chunk_ids_arr[mask]

            # cosine_distances expects 2-D arrays
            centroid_2d = centroid.reshape(1, -1)
            dists = cosine_distances(centroid_2d, cluster_embs)[0]  # shape (n_cluster,)

            top_k = min(n_top, len(dists))
            top_indices = np.argpartition(dists, top_k - 1)[:top_k]
            # Sort the top-k by distance ascending.
            top_indices = top_indices[np.argsort(dists[top_indices])]
            result[cid] = cluster_ids[top_indices].tolist()

        return result

    # ------------------------------------------------------------------
    # Incremental assignment
    # ------------------------------------------------------------------

    def assign_new_chunks(self, new_embeddings: np.ndarray) -> np.ndarray:
        """Assign cluster labels to *new_embeddings* without refitting.

        Transforms via the fitted UMAP model, then uses HDBSCAN's
        ``approximate_predict`` for out-of-sample assignment.

        Parameters
        ----------
        new_embeddings:
            Float32 array of shape ``(M, dim)``.

        Returns
        -------
        np.ndarray
            Integer label array of shape ``(M,)``; ``-1`` = noise/unassigned.
        """
        self._require_fit()
        import hdbscan as hdbscan_lib  # noqa: PLC0415

        reduced = self.umap_model.transform(new_embeddings.astype(np.float32))
        labels, _ = hdbscan_lib.approximate_predict(self.hdbscan_model, reduced)
        return labels

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def save(self, output_dir: Path) -> None:
        """Persist fitted models and arrays to *output_dir*.

        Creates the directory if necessary.  Files written:

        * ``umap_model.joblib``
        * ``hdbscan_model.joblib``
        * ``labels.npy``
        * ``probabilities.npy``
        * ``reduced_embeddings.npy``
        * ``centroids.npz``  — only if embeddings were passed to
          :meth:`get_cluster_centroids` separately; call that first if needed.
        """
        self._require_fit()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.umap_model,    output_dir / "umap_model.joblib")
        joblib.dump(self.hdbscan_model, output_dir / "hdbscan_model.joblib")
        np.save(output_dir / "labels.npy",             self.labels_)
        np.save(output_dir / "probabilities.npy",      self.probabilities_)
        np.save(output_dir / "reduced_embeddings.npy", self.reduced_embeddings_)

        logger.info("ThemeClusterer saved to %s", output_dir)

    def save_with_centroids(
        self, output_dir: Path, embeddings: np.ndarray
    ) -> None:
        """Save model + centroids computed from *embeddings*."""
        self.save(output_dir)
        centroids = self.get_cluster_centroids(embeddings)
        centroid_arrays = {
            str(cid): vec for cid, vec in centroids.items()
        }
        np.savez_compressed(Path(output_dir) / "centroids.npz", **centroid_arrays)
        logger.info("Centroids saved (%d clusters)", len(centroids))

    @classmethod
    def load(cls, output_dir: Path) -> "ThemeClusterer":
        """Restore a :class:`ThemeClusterer` from *output_dir*.

        Parameters
        ----------
        output_dir:
            Directory previously written by :meth:`save`.

        Returns
        -------
        ThemeClusterer
            Fully restored instance ready for :meth:`assign_new_chunks`.
        """
        output_dir = Path(output_dir)
        required = [
            "umap_model.joblib",
            "hdbscan_model.joblib",
            "labels.npy",
            "probabilities.npy",
            "reduced_embeddings.npy",
        ]
        for fname in required:
            fpath = output_dir / fname
            if not fpath.exists():
                raise FileNotFoundError(f"Missing expected file: {fpath}")

        instance = cls.__new__(cls)
        instance.umap_model           = joblib.load(output_dir / "umap_model.joblib")
        instance.hdbscan_model        = joblib.load(output_dir / "hdbscan_model.joblib")
        instance.labels_              = np.load(output_dir / "labels.npy")
        instance.probabilities_       = np.load(output_dir / "probabilities.npy")
        instance.reduced_embeddings_  = np.load(output_dir / "reduced_embeddings.npy")

        # Restore scalar hyper-params from UMAP/HDBSCAN objects where possible.
        instance.umap_components      = instance.umap_model.n_components
        instance.umap_metric          = instance.umap_model.metric
        instance.umap_n_neighbors     = instance.umap_model.n_neighbors
        instance.hdbscan_min_cluster_size = instance.hdbscan_model.min_cluster_size
        instance.hdbscan_min_samples  = instance.hdbscan_model.min_samples
        instance.random_state         = getattr(instance.umap_model, "random_state", 42)

        logger.info("ThemeClusterer loaded from %s", output_dir)
        return instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_fit(self) -> None:
        if self.labels_ is None:
            raise RuntimeError(
                "ThemeClusterer has not been fitted yet. Call fit() first."
            )

    @staticmethod
    def _check_imports() -> None:
        missing = []
        try:
            import umap  # noqa: F401
        except ImportError:
            missing.append("umap-learn")
        try:
            import hdbscan  # noqa: F401
        except ImportError:
            missing.append("hdbscan")
        if missing:
            raise ImportError(
                f"Required packages not installed: {missing}. "
                "Install with: pip install " + " ".join(missing)
            )
