"""
tests/test_drift_layer.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Unit and integration tests for the driftlens drift detection layer.

Run with:
    pytest tests/test_drift_layer.py -v
"""

import numpy as np
import pandas as pd
import pytest

from driftlens.drift.intensity import compute_intensity, build_presence_matrix
from driftlens.drift.change_detector import (
    compute_yoy_changes,
    compute_centroid_drift,
    rank_changes,
    get_top_changes,
)
from driftlens.drift.theme_tracker import ThemeTracker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LABELS = {0: "Cybersecurity Risk", 1: "Climate Disclosure", 2: "Executive Comp"}


def _make_chunks_df() -> pd.DataFrame:
    """Small synthetic dataset: 2 companies, 2 years, 3 clusters."""
    rows = []
    chunk_id = 0
    for cik in ["0001234", "0005678"]:
        for year in [2022, 2023]:
            for cluster_id, count in [(0, 5), (1, 3), (2, 2)]:
                for _ in range(count):
                    rows.append(
                        {
                            "chunk_id": f"c{chunk_id}",
                            "cik": cik,
                            "fiscal_year": year,
                            "accession_number": f"acc-{cik}-{year}",
                            "cluster_id": cluster_id,
                        }
                    )
                    chunk_id += 1
    # Add noise chunks (should be excluded)
    rows.append(
        {
            "chunk_id": f"c{chunk_id}",
            "cik": "0001234",
            "fiscal_year": 2023,
            "accession_number": "acc-noise",
            "cluster_id": -1,
        }
    )
    return pd.DataFrame(rows)


def _make_embeddings(chunks_df: pd.DataFrame, dim: int = 8):
    """Generate deterministic unit-norm embeddings per chunk_id."""
    rng = np.random.default_rng(42)
    ids = chunks_df["chunk_id"].tolist()
    vecs = rng.standard_normal((len(ids), dim)).astype(np.float32)
    # Unit-normalise rows
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    vecs /= np.where(norms == 0, 1.0, norms)
    return vecs, ids


# ---------------------------------------------------------------------------
# compute_intensity
# ---------------------------------------------------------------------------


class TestComputeIntensity:
    def test_basic_shape(self):
        df = _make_chunks_df()
        result = compute_intensity(df, LABELS)
        assert isinstance(result, pd.DataFrame)
        expected_cols = {
            "cik", "fiscal_year", "cluster_id", "cluster_label",
            "chunk_count", "total_chunks", "intensity", "is_present",
        }
        assert expected_cols.issubset(result.columns)

    def test_noise_excluded(self):
        df = _make_chunks_df()
        result = compute_intensity(df, LABELS)
        assert -1 not in result["cluster_id"].values

    def test_intensity_sum_per_year(self):
        """Intensities for all clusters of a filing year must sum to 1."""
        df = _make_chunks_df()
        result = compute_intensity(df, LABELS)
        totals = (
            result.groupby(["cik", "fiscal_year"])["intensity"].sum().reset_index()
        )
        for _, row in totals.iterrows():
            assert abs(row["intensity"] - 1.0) < 1e-9, (
                f"Intensities don't sum to 1 for {row['cik']} {row['fiscal_year']}: "
                f"{row['intensity']}"
            )

    def test_chunk_counts(self):
        df = _make_chunks_df()
        result = compute_intensity(df, LABELS)
        cik0_2023_c0 = result[
            (result["cik"] == "0001234")
            & (result["fiscal_year"] == 2023)
            & (result["cluster_id"] == 0)
        ]
        assert len(cik0_2023_c0) == 1
        assert int(cik0_2023_c0["chunk_count"].iloc[0]) == 5

    def test_labels_attached(self):
        df = _make_chunks_df()
        result = compute_intensity(df, LABELS)
        assert "Cybersecurity Risk" in result["cluster_label"].values

    def test_unknown_label_warning(self, caplog):
        df = _make_chunks_df()
        with caplog.at_level("WARNING"):
            result = compute_intensity(df, {})  # empty labels -> all unknown
        assert "unknown" in result["cluster_label"].values

    def test_is_present_boolean(self):
        df = _make_chunks_df()
        result = compute_intensity(df, LABELS)
        assert result["is_present"].all()  # every cluster has at least 1 chunk

    def test_missing_columns_raises(self):
        bad_df = pd.DataFrame({"chunk_id": [1], "cik": ["x"]})
        with pytest.raises(ValueError, match="missing required columns"):
            compute_intensity(bad_df, LABELS)

    def test_empty_after_noise_removal(self):
        df = pd.DataFrame(
            [{"chunk_id": "c0", "cik": "x", "fiscal_year": 2023,
              "accession_number": "a", "cluster_id": -1}]
        )
        result = compute_intensity(df, LABELS)
        assert result.empty


# ---------------------------------------------------------------------------
# build_presence_matrix
# ---------------------------------------------------------------------------


class TestBuildPresenceMatrix:
    def test_shape(self):
        df = _make_chunks_df()
        intensity_df = compute_intensity(df, LABELS)
        matrix = build_presence_matrix(intensity_df)
        # 3 clusters x (2 companies * 2 years)
        assert matrix.shape == (3, 4)

    def test_no_negative_values(self):
        df = _make_chunks_df()
        intensity_df = compute_intensity(df, LABELS)
        matrix = build_presence_matrix(intensity_df)
        assert (matrix.values >= 0).all()

    def test_empty_input(self):
        empty = pd.DataFrame(
            columns=["cik", "fiscal_year", "cluster_id", "intensity"]
        )
        matrix = build_presence_matrix(empty)
        assert matrix.empty


# ---------------------------------------------------------------------------
# compute_yoy_changes
# ---------------------------------------------------------------------------


class TestComputeYoyChanges:
    def _get_intensity(self):
        df = _make_chunks_df()
        return compute_intensity(df, LABELS)

    def test_output_columns(self):
        intensity_df = self._get_intensity()
        changes = compute_yoy_changes(intensity_df)
        expected = {
            "cik", "cluster_id", "fiscal_year", "intensity",
            "prev_intensity", "intensity_delta", "chunk_count",
            "materiality_score", "change_type", "first_appearance", "disappeared",
        }
        assert expected.issubset(changes.columns)

    def test_first_year_prev_intensity_zero(self):
        intensity_df = self._get_intensity()
        changes = compute_yoy_changes(intensity_df)
        first_years = changes.groupby(["cik", "cluster_id"])["fiscal_year"].min()
        for (cik, cid), yr in first_years.items():
            row = changes[
                (changes["cik"] == cik) & (changes["cluster_id"] == cid)
                & (changes["fiscal_year"] == yr)
            ]
            assert float(row["prev_intensity"].iloc[0]) == 0.0, (
                f"First year prev_intensity should be 0 for cik={cik} cluster={cid}"
            )

    def test_first_year_marked_new(self):
        intensity_df = self._get_intensity()
        changes = compute_yoy_changes(intensity_df)
        first_year_rows = changes[changes["first_appearance"] == True]
        assert (first_year_rows["change_type"] == "new").all()

    def test_stable_classification(self):
        """Identical intensities across years → stable."""
        rows = []
        for yr in [2021, 2022, 2023]:
            rows.append(
                {"cik": "A", "fiscal_year": yr, "cluster_id": 0,
                 "cluster_label": "X", "chunk_count": 10,
                 "total_chunks": 100, "intensity": 0.10, "is_present": True}
            )
        intensity_df = pd.DataFrame(rows)
        changes = compute_yoy_changes(intensity_df)
        # 2022 and 2023 should be stable
        non_first = changes[changes["first_appearance"] == False]
        assert (non_first["change_type"] == "stable").all()

    def test_intensifying_classification(self):
        rows = [
            {"cik": "A", "fiscal_year": 2022, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 5, "total_chunks": 100,
             "intensity": 0.05, "is_present": True},
            {"cik": "A", "fiscal_year": 2023, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 10, "total_chunks": 100,
             "intensity": 0.10, "is_present": True},  # delta = +0.05 > 0.02
        ]
        intensity_df = pd.DataFrame(rows)
        changes = compute_yoy_changes(intensity_df)
        row_2023 = changes[changes["fiscal_year"] == 2023]
        assert row_2023["change_type"].iloc[0] == "intensifying"

    def test_fading_classification(self):
        rows = [
            {"cik": "A", "fiscal_year": 2022, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 10, "total_chunks": 100,
             "intensity": 0.10, "is_present": True},
            {"cik": "A", "fiscal_year": 2023, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 3, "total_chunks": 100,
             "intensity": 0.03, "is_present": True},  # delta = -0.07 < -0.02
        ]
        intensity_df = pd.DataFrame(rows)
        changes = compute_yoy_changes(intensity_df)
        row_2023 = changes[changes["fiscal_year"] == 2023]
        assert row_2023["change_type"].iloc[0] == "fading"

    def test_disappeared_classification(self):
        rows = [
            {"cik": "A", "fiscal_year": 2022, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 5, "total_chunks": 100,
             "intensity": 0.05, "is_present": True},
            {"cik": "A", "fiscal_year": 2023, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 0, "total_chunks": 100,
             "intensity": 0.0, "is_present": False},
        ]
        intensity_df = pd.DataFrame(rows)
        changes = compute_yoy_changes(intensity_df)
        row_2023 = changes[changes["fiscal_year"] == 2023]
        assert row_2023["change_type"].iloc[0] == "disappeared"
        assert bool(row_2023["disappeared"].iloc[0]) is True

    def test_materiality_score_non_negative(self):
        intensity_df = self._get_intensity()
        changes = compute_yoy_changes(intensity_df)
        assert (changes["materiality_score"] >= 0).all()

    def test_materiality_formula(self):
        """materiality_score = abs(delta) * log1p(chunk_count)."""
        rows = [
            {"cik": "A", "fiscal_year": 2022, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 4, "total_chunks": 100,
             "intensity": 0.04, "is_present": True},
            {"cik": "A", "fiscal_year": 2023, "cluster_id": 0,
             "cluster_label": "X", "chunk_count": 9, "total_chunks": 100,
             "intensity": 0.09, "is_present": True},
        ]
        intensity_df = pd.DataFrame(rows)
        changes = compute_yoy_changes(intensity_df)
        row_2023 = changes[changes["fiscal_year"] == 2023].iloc[0]
        expected = abs(0.09 - 0.04) * np.log1p(9)
        assert abs(row_2023["materiality_score"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# compute_centroid_drift
# ---------------------------------------------------------------------------


class TestComputeCentroidDrift:
    def test_basic_output(self):
        df = _make_chunks_df()
        df = df[df["cluster_id"] != -1]
        embeddings, chunk_ids_list = _make_embeddings(df)
        result = compute_centroid_drift(df, embeddings, chunk_ids_list)
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == {"cik", "cluster_id", "fiscal_year", "centroid_drift"}

    def test_drift_in_range(self):
        df = _make_chunks_df()
        df = df[df["cluster_id"] != -1]
        embeddings, chunk_ids_list = _make_embeddings(df)
        result = compute_centroid_drift(df, embeddings, chunk_ids_list)
        # Cosine distance in [0, 2]; for unit-norm random vecs typically in [0, 1]
        assert (result["centroid_drift"] >= 0.0).all()
        assert (result["centroid_drift"] <= 2.0).all()

    def test_identical_embeddings_give_zero_drift(self):
        """If year N and year N-1 have the same embedding, drift must be 0."""
        df = pd.DataFrame(
            [
                {"chunk_id": "a", "cik": "X", "fiscal_year": 2022, "cluster_id": 0},
                {"chunk_id": "b", "cik": "X", "fiscal_year": 2023, "cluster_id": 0},
            ]
        )
        vec = np.array([[1.0, 0.0, 0.0]])  # same direction
        embeddings = np.vstack([vec, vec])
        chunk_ids_list = ["a", "b"]
        result = compute_centroid_drift(df, embeddings, chunk_ids_list)
        assert len(result) == 1
        assert abs(result["centroid_drift"].iloc[0]) < 1e-6

    def test_bad_embedding_shape_raises(self):
        df = _make_chunks_df()
        with pytest.raises(ValueError, match="2-D array"):
            compute_centroid_drift(df, np.ones(10), [])

    def test_length_mismatch_raises(self):
        df = _make_chunks_df()
        embeddings = np.ones((5, 4))
        chunk_ids_list = ["a", "b", "c"]  # length mismatch
        with pytest.raises(ValueError, match="chunk_ids_list length"):
            compute_centroid_drift(df, embeddings, chunk_ids_list)


# ---------------------------------------------------------------------------
# rank_changes / get_top_changes
# ---------------------------------------------------------------------------


class TestRankChanges:
    def _make_changes_and_drift(self):
        chunks_df = _make_chunks_df()
        intensity_df = compute_intensity(chunks_df, LABELS)
        changes_df = compute_yoy_changes(intensity_df)
        non_noise = chunks_df[chunks_df["cluster_id"] != -1]
        embeddings, chunk_ids_list = _make_embeddings(non_noise)
        drift_df = compute_centroid_drift(non_noise, embeddings, chunk_ids_list)
        return changes_df, drift_df

    def test_rank_column_present(self):
        changes_df, drift_df = self._make_changes_and_drift()
        ranked = rank_changes(changes_df, drift_df)
        assert "rank" in ranked.columns

    def test_sorted_by_materiality_descending(self):
        changes_df, drift_df = self._make_changes_and_drift()
        ranked = rank_changes(changes_df, drift_df)
        scores = ranked["materiality_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_centroid_drift_column_present(self):
        changes_df, drift_df = self._make_changes_and_drift()
        ranked = rank_changes(changes_df, drift_df)
        assert "centroid_drift" in ranked.columns

    def test_empty_drift_df_handled(self):
        chunks_df = _make_chunks_df()
        intensity_df = compute_intensity(chunks_df, LABELS)
        changes_df = compute_yoy_changes(intensity_df)
        empty_drift = pd.DataFrame(
            columns=["cik", "cluster_id", "fiscal_year", "centroid_drift"]
        )
        ranked = rank_changes(changes_df, empty_drift)
        assert (ranked["centroid_drift"].isna()).all()

    def test_get_top_changes_limits_rows(self):
        changes_df, drift_df = self._make_changes_and_drift()
        ranked = rank_changes(changes_df, drift_df)
        top3 = get_top_changes(ranked, n=3)
        assert len(top3) <= 3

    def test_get_top_changes_order(self):
        changes_df, drift_df = self._make_changes_and_drift()
        ranked = rank_changes(changes_df, drift_df)
        top = get_top_changes(ranked, n=10)
        scores = top["materiality_score"].tolist()
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# ThemeTracker
# ---------------------------------------------------------------------------


class TestThemeTracker:
    def _build_tracker(self):
        chunks_df = _make_chunks_df()
        intensity_df = compute_intensity(chunks_df, LABELS)
        changes_df = compute_yoy_changes(intensity_df)
        themes_df = pd.DataFrame(
            [{"cluster_id": k, "cluster_label": v} for k, v in LABELS.items()]
        )
        return ThemeTracker(intensity_df, changes_df, themes_df), intensity_df, changes_df

    def test_init_succeeds(self):
        tracker, _, _ = self._build_tracker()
        assert tracker is not None

    def test_missing_column_raises(self):
        chunks_df = _make_chunks_df()
        intensity_df = compute_intensity(chunks_df, LABELS)
        changes_df = compute_yoy_changes(intensity_df)
        bad_intensity = intensity_df.drop(columns=["is_present"])
        themes_df = pd.DataFrame(
            [{"cluster_id": k, "cluster_label": v} for k, v in LABELS.items()]
        )
        with pytest.raises(ValueError, match="is_present"):
            ThemeTracker(bad_intensity, changes_df, themes_df)

    def test_get_company_timeline_known_cik(self):
        tracker, _, _ = self._build_tracker()
        tl = tracker.get_company_timeline("0001234")
        assert not tl.empty
        assert (tl["cik"] == "0001234").all()
        years = tl["fiscal_year"].unique().tolist()
        assert sorted(years) == years

    def test_get_company_timeline_unknown_cik_raises(self):
        tracker, _, _ = self._build_tracker()
        with pytest.raises(KeyError, match="not found"):
            tracker.get_company_timeline("XXXX")

    def test_get_theme_trajectory(self):
        tracker, _, _ = self._build_tracker()
        traj = tracker.get_theme_trajectory(cluster_id=0)
        assert not traj.empty
        assert (traj["cluster_id"] == 0).all()

    def test_get_theme_trajectory_with_cik_filter(self):
        tracker, _, _ = self._build_tracker()
        traj = tracker.get_theme_trajectory(cluster_id=1, cik="0005678")
        assert (traj["cik"] == "0005678").all()
        assert (traj["cluster_id"] == 1).all()

    def test_get_theme_trajectory_unknown_cluster_raises(self):
        tracker, _, _ = self._build_tracker()
        with pytest.raises(KeyError, match="cluster_id 999 not found"):
            tracker.get_theme_trajectory(cluster_id=999)

    def test_get_emerging_themes_year(self):
        tracker, _, _ = self._build_tracker()
        # First year (2022): all clusters are 'new'; both companies have them
        emerging = tracker.get_emerging_themes(year=2022, min_companies=2)
        assert not emerging.empty
        assert "cluster_id" in emerging.columns
        assert "company_count" in emerging.columns

    def test_get_emerging_themes_high_threshold_returns_empty(self):
        tracker, _, _ = self._build_tracker()
        # Only 2 companies in the dataset; threshold of 99 should return empty
        emerging = tracker.get_emerging_themes(year=2022, min_companies=99)
        assert emerging.empty

    def test_get_fading_themes_returns_df(self):
        tracker, _, _ = self._build_tracker()
        # May be empty if nothing is fading in stable test data
        result = tracker.get_fading_themes(year=2023)
        assert isinstance(result, pd.DataFrame)

    def test_get_theme_prevalence_structure(self):
        tracker, _, _ = self._build_tracker()
        prev = tracker.get_theme_prevalence()
        expected_cols = {
            "cluster_id", "cluster_label", "unique_companies",
            "first_year", "last_year", "peak_intensity_year", "mean_intensity",
        }
        assert expected_cols.issubset(prev.columns)
        assert len(prev) == len(LABELS)

    def test_get_corpus_stats_keys(self):
        tracker, _, _ = self._build_tracker()
        stats = tracker.get_corpus_stats()
        expected_keys = {
            "total_companies", "total_years", "total_themes",
            "total_filings", "total_chunks",
            "mean_themes_per_filing", "mean_intensity_per_theme",
            "change_type_counts",
        }
        assert expected_keys.issubset(stats.keys())

    def test_get_corpus_stats_values(self):
        tracker, _, _ = self._build_tracker()
        stats = tracker.get_corpus_stats()
        assert stats["total_companies"] == 2
        assert stats["total_years"] == 2
        assert stats["total_themes"] == 3
        assert stats["total_filings"] == 4  # 2 companies * 2 years
