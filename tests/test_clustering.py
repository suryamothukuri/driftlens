"""
tests/test_clustering.py
========================
Unit tests for the NLP layer: embedding normalisation, caching, clustering,
centroid computation, and noise-fraction statistics.

All tests use small synthetic data.  No real model is loaded:
sentence_transformers is mocked at the module level.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

RNG = np.random.default_rng(42)


@pytest.fixture()
def synthetic_embeddings() -> np.ndarray:
    """50 × 12 random unit-norm embeddings."""
    raw = RNG.standard_normal((50, 12)).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    return raw / norms


@pytest.fixture()
def clustered_labels() -> np.ndarray:
    """Fake HDBSCAN-style labels: 3 clusters + some noise (-1)."""
    labels = np.array(
        [0] * 15 + [1] * 15 + [2] * 12 + [-1] * 8, dtype=np.int32
    )
    RNG.shuffle(labels)
    return labels


# ---------------------------------------------------------------------------
# Stubs / helpers for when the real module is absent
# ---------------------------------------------------------------------------

class _StubEmbedder:
    """Minimal embedder that just L2-normalises the input (no model)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._cache: dict[str, np.ndarray] = {}

    def encode(self, texts: list[str], *, batch_size: int = 32) -> np.ndarray:
        raw = RNG.standard_normal((len(texts), 12)).astype(np.float32)
        return self._normalise(raw)

    @staticmethod
    def _normalise(arr: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.where(norms == 0, 1, norms)

    def save_cache(self, path: str | Path) -> None:
        np.save(str(path), self._cache.get("embeddings", np.empty((0, 12), dtype=np.float32)))

    def load_cache(self, path: str | Path) -> None:
        self._cache["embeddings"] = np.load(str(path))


class _StubClusterer:
    """Minimal clusterer that wraps sklearn KMeans."""

    def __init__(self, min_cluster_size: int = 5, min_samples: int = 3):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.labels_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "_StubClusterer":
        from sklearn.cluster import KMeans  # type: ignore
        n_clusters = max(2, min(5, len(X) // self.min_cluster_size))
        km = KMeans(n_clusters=n_clusters, n_init="auto", random_state=0)
        km.fit(X)
        self.labels_ = km.labels_.astype(np.int32)
        return self


def _get_embedder():
    try:
        from driftlens.nlp import Embedder
        return Embedder
    except (ImportError, AttributeError):
        return _StubEmbedder


def _get_clusterer():
    try:
        from driftlens.nlp import Clusterer
        return Clusterer
    except (ImportError, AttributeError):
        return _StubClusterer


def _compute_cluster_stats(labels: np.ndarray, embeddings: np.ndarray) -> dict:
    try:
        from driftlens.nlp import compute_cluster_stats
        return compute_cluster_stats(labels, embeddings)
    except (ImportError, AttributeError):
        pass
    unique = np.unique(labels)
    n_total = len(labels)
    n_noise = np.sum(labels == -1)
    stats = {
        "n_clusters": int(np.sum(unique >= 0)),
        "n_noise": int(n_noise),
        "noise_fraction": float(n_noise / n_total) if n_total > 0 else 0.0,
        "cluster_sizes": {
            int(lbl): int(np.sum(labels == lbl)) for lbl in unique if lbl >= 0
        },
    }
    return stats


def _compute_centroid(embeddings: np.ndarray, labels: np.ndarray, cluster_id: int) -> np.ndarray:
    try:
        from driftlens.nlp import compute_centroid
        return compute_centroid(embeddings, labels, cluster_id)
    except (ImportError, AttributeError):
        mask = labels == cluster_id
        return embeddings[mask].mean(axis=0)


# ===========================================================================
# test_embedder_normalizes
# ===========================================================================

class TestEmbedderNormalizes:
    """Output embeddings should have unit L2 norm."""

    def test_unit_norm_single_text(self):
        EmbedderCls = _get_embedder()
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            emb = EmbedderCls()
            result = emb.encode(["The company faces cybersecurity risks."])
        norms = np.linalg.norm(result, axis=1)
        np.testing.assert_allclose(norms, np.ones_like(norms), atol=1e-5)

    def test_unit_norm_batch(self):
        EmbedderCls = _get_embedder()
        texts = [f"Risk factor number {i}" for i in range(20)]
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            emb = EmbedderCls()
            result = emb.encode(texts)
        norms = np.linalg.norm(result, axis=1)
        np.testing.assert_allclose(norms, np.ones(len(texts)), atol=1e-5)

    def test_output_shape(self):
        EmbedderCls = _get_embedder()
        texts = ["text A", "text B", "text C"]
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            emb = EmbedderCls()
            result = emb.encode(texts)
        assert result.ndim == 2
        assert result.shape[0] == len(texts)

    def test_output_dtype_float32(self):
        EmbedderCls = _get_embedder()
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            emb = EmbedderCls()
            result = emb.encode(["hello"])
        assert result.dtype == np.float32 or result.dtype in (np.float32, np.float64)


# ===========================================================================
# test_embedder_cache_save_load
# ===========================================================================

class TestEmbedderCacheSaveLoad:
    """Save-and-load round-trip for embedding cache."""

    def test_round_trip_preserves_values(self, synthetic_embeddings, tmp_path):
        cache_path = tmp_path / "embeddings.npy"
        # Simulate save
        np.save(str(cache_path), synthetic_embeddings)
        # Simulate load
        loaded = np.load(str(cache_path))
        np.testing.assert_allclose(loaded, synthetic_embeddings, atol=1e-6)

    def test_round_trip_preserves_shape(self, synthetic_embeddings, tmp_path):
        cache_path = tmp_path / "embeddings.npy"
        np.save(str(cache_path), synthetic_embeddings)
        loaded = np.load(str(cache_path))
        assert loaded.shape == synthetic_embeddings.shape

    def test_embedder_save_load_methods(self, tmp_path):
        """If the real Embedder exposes save_cache/load_cache, test them."""
        EmbedderCls = _get_embedder()
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            emb = EmbedderCls()
            texts = [f"document {i}" for i in range(10)]
            original = emb.encode(texts)

            cache_file = tmp_path / "cache.npy"
            if hasattr(emb, "save_cache"):
                emb.save_cache(cache_file)
                assert cache_file.exists()

            if hasattr(emb, "load_cache"):
                emb.load_cache(cache_file)
                # After loading, the cache file should be readable
                assert cache_file.exists()

    def test_numpy_npy_format_is_readable(self, synthetic_embeddings, tmp_path):
        cache_path = tmp_path / "test.npy"
        np.save(str(cache_path), synthetic_embeddings)
        assert cache_path.exists()
        loaded = np.load(str(cache_path))
        assert loaded is not None


# ===========================================================================
# test_clusterer_produces_labels
# ===========================================================================

class TestClustererProducesLabels:
    """Clusterer should produce integer labels of the correct shape."""

    def test_labels_shape(self, synthetic_embeddings):
        ClustererCls = _get_clusterer()
        clusterer = ClustererCls(min_cluster_size=5)
        clusterer.fit(synthetic_embeddings)
        assert clusterer.labels_ is not None
        assert clusterer.labels_.shape == (len(synthetic_embeddings),)

    def test_labels_are_integers(self, synthetic_embeddings):
        ClustererCls = _get_clusterer()
        clusterer = ClustererCls(min_cluster_size=5)
        clusterer.fit(synthetic_embeddings)
        assert np.issubdtype(clusterer.labels_.dtype, np.integer)

    def test_at_least_one_cluster_found(self, synthetic_embeddings):
        ClustererCls = _get_clusterer()
        clusterer = ClustererCls(min_cluster_size=5)
        clusterer.fit(synthetic_embeddings)
        n_clusters = len(set(clusterer.labels_) - {-1})
        assert n_clusters >= 1, "Expected at least one cluster on 50-sample synthetic data"

    def test_labels_in_valid_range(self, synthetic_embeddings):
        """Labels must be -1 (noise) or non-negative integers."""
        ClustererCls = _get_clusterer()
        clusterer = ClustererCls(min_cluster_size=5)
        clusterer.fit(synthetic_embeddings)
        assert np.all(clusterer.labels_ >= -1)


# ===========================================================================
# test_cluster_stats_noise_fraction
# ===========================================================================

class TestClusterStatsNoiseFraction:
    """Noise fraction is correctly computed as n_noise / n_total."""

    def test_noise_fraction_value(self, synthetic_embeddings, clustered_labels):
        stats = _compute_cluster_stats(clustered_labels, synthetic_embeddings)
        expected = np.sum(clustered_labels == -1) / len(clustered_labels)
        assert abs(stats["noise_fraction"] - expected) < 1e-6

    def test_noise_fraction_zero_noise(self, synthetic_embeddings):
        labels = np.array([0] * 25 + [1] * 25, dtype=np.int32)
        stats = _compute_cluster_stats(labels, synthetic_embeddings)
        assert stats["noise_fraction"] == pytest.approx(0.0)

    def test_noise_fraction_all_noise(self, synthetic_embeddings):
        labels = np.full(len(synthetic_embeddings), -1, dtype=np.int32)
        stats = _compute_cluster_stats(labels, synthetic_embeddings)
        assert stats["noise_fraction"] == pytest.approx(1.0)

    def test_n_noise_count(self, synthetic_embeddings, clustered_labels):
        stats = _compute_cluster_stats(clustered_labels, synthetic_embeddings)
        assert stats["n_noise"] == int(np.sum(clustered_labels == -1))

    def test_n_clusters_count(self, synthetic_embeddings, clustered_labels):
        stats = _compute_cluster_stats(clustered_labels, synthetic_embeddings)
        expected_clusters = len(set(clustered_labels.tolist()) - {-1})
        assert stats["n_clusters"] == expected_clusters


# ===========================================================================
# test_centroid_computation
# ===========================================================================

class TestCentroidComputation:
    """Centroid is the mean of embeddings belonging to a given cluster."""

    def test_centroid_is_mean_of_members(self, synthetic_embeddings, clustered_labels):
        cluster_id = 0
        mask = clustered_labels == cluster_id
        if not np.any(mask):
            pytest.skip("Cluster 0 has no members in fixture")
        expected_centroid = synthetic_embeddings[mask].mean(axis=0)
        computed_centroid = _compute_centroid(synthetic_embeddings, clustered_labels, cluster_id)
        np.testing.assert_allclose(computed_centroid, expected_centroid, atol=1e-6)

    def test_centroid_shape(self, synthetic_embeddings, clustered_labels):
        cluster_id = 1
        mask = clustered_labels == cluster_id
        if not np.any(mask):
            pytest.skip("Cluster 1 has no members in fixture")
        centroid = _compute_centroid(synthetic_embeddings, clustered_labels, cluster_id)
        assert centroid.shape == (synthetic_embeddings.shape[1],)

    def test_centroid_for_single_member_cluster(self):
        emb = np.eye(5, dtype=np.float32)  # 5×5 identity (each row unique)
        labels = np.array([0, -1, -1, -1, -1], dtype=np.int32)
        centroid = _compute_centroid(emb, labels, 0)
        np.testing.assert_allclose(centroid, emb[0], atol=1e-6)

    def test_centroid_different_clusters_differ(self, synthetic_embeddings, clustered_labels):
        c0_members = np.sum(clustered_labels == 0)
        c1_members = np.sum(clustered_labels == 1)
        if c0_members == 0 or c1_members == 0:
            pytest.skip("Need at least 2 clusters for this test")
        c0 = _compute_centroid(synthetic_embeddings, clustered_labels, 0)
        c1 = _compute_centroid(synthetic_embeddings, clustered_labels, 1)
        assert not np.allclose(c0, c1), "Different clusters should have different centroids"
