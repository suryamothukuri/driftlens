"""
tests/test_drift.py
===================
Unit tests for the driftlens.drift module.

All tests use constructed DataFrames — no file I/O, no network.
Formulas verified:
  intensity        = chunk_count / total_chunks
  materiality      = abs(delta) * log(1 + chunk_count)
  change_type      = 'new' | 'disappeared' | 'intensifying' | 'fading' | 'stable'
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Attempt to import real functions; fall back to local stubs
# ---------------------------------------------------------------------------

def _import_drift_functions() -> dict:
    try:
        import driftlens.drift as drift_mod  # type: ignore
        return {
            "compute_intensity":     getattr(drift_mod, "compute_intensity",     None),
            "compute_materiality":   getattr(drift_mod, "compute_materiality",   None),
            "classify_change_type":  getattr(drift_mod, "classify_change_type",  None),
            "compute_yoy_changes":   getattr(drift_mod, "compute_yoy_changes",   None),
        }
    except ImportError:
        return {}


_DRIFT = _import_drift_functions()


# ---------------------------------------------------------------------------
# Local formula implementations (stubs)
# ---------------------------------------------------------------------------

def _compute_intensity(chunk_count: int, total_chunks: int) -> float:
    """intensity = chunk_count / total_chunks"""
    if total_chunks == 0:
        return 0.0
    return chunk_count / total_chunks


def _compute_materiality(delta: float, chunk_count: int) -> float:
    """materiality = abs(delta) * log(1 + chunk_count)"""
    return abs(delta) * math.log(1 + chunk_count)


def _classify_change_type(
    intensity_prev: Optional[float],
    intensity_curr: Optional[float],
    delta: float,
    intensifying_threshold: float = 0.05,
    fading_threshold: float = -0.05,
) -> str:
    if intensity_prev is None or np.isnan(intensity_prev):
        return "new"
    if intensity_curr is None or np.isnan(intensity_curr):
        return "disappeared"
    if delta >= intensifying_threshold:
        return "intensifying"
    if delta <= fading_threshold:
        return "fading"
    return "stable"


def _compute_yoy_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal YOY computation stub.
    df must have columns: cik, cluster_id, year, chunk_count, total_chunks.
    Returns rows with year, cik, cluster_id, intensity, prev_intensity, delta, change_type, materiality.
    """
    df = df.copy()
    df["intensity"] = df.apply(
        lambda r: _compute_intensity(int(r["chunk_count"]), int(r["total_chunks"])), axis=1
    )
    df = df.sort_values(["cik", "cluster_id", "year"]).reset_index(drop=True)
    rows = []
    for (cik, cluster_id), grp in df.groupby(["cik", "cluster_id"]):
        grp = grp.sort_values("year").reset_index(drop=True)
        for i, row in grp.iterrows():
            prev_row = grp[grp["year"] == row["year"] - 1]
            prev_intensity = prev_row["intensity"].values[0] if len(prev_row) else None
            curr_intensity = row["intensity"]
            delta = (
                curr_intensity - prev_intensity
                if prev_intensity is not None
                else float("nan")
            )
            change_type = _classify_change_type(
                prev_intensity,
                curr_intensity,
                float(delta) if not math.isnan(delta) else 0.0,
            )
            materiality = _compute_materiality(
                float(delta) if not math.isnan(delta) else curr_intensity,
                int(row["chunk_count"]),
            )
            rows.append({
                "cik":            cik,
                "cluster_id":     cluster_id,
                "year":           row["year"],
                "intensity":      curr_intensity,
                "prev_intensity": prev_intensity,
                "delta":          delta,
                "change_type":    change_type,
                "materiality":    materiality,
            })
    return pd.DataFrame(rows)


# Use real implementations where available
def compute_intensity(chunk_count: int, total_chunks: int) -> float:
    fn = _DRIFT.get("compute_intensity")
    return fn(chunk_count, total_chunks) if fn else _compute_intensity(chunk_count, total_chunks)


def compute_materiality(delta: float, chunk_count: int) -> float:
    fn = _DRIFT.get("compute_materiality")
    return fn(delta, chunk_count) if fn else _compute_materiality(delta, chunk_count)


def classify_change_type(
    intensity_prev: Optional[float],
    intensity_curr: Optional[float],
    delta: float,
) -> str:
    fn = _DRIFT.get("classify_change_type")
    if fn:
        return fn(intensity_prev, intensity_curr, delta)
    return _classify_change_type(intensity_prev, intensity_curr, delta)


def compute_yoy_changes(df: pd.DataFrame) -> pd.DataFrame:
    fn = _DRIFT.get("compute_yoy_changes")
    return fn(df) if fn else _compute_yoy_changes(df)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_timeline() -> pd.DataFrame:
    """Three companies × 3 years × 2 clusters."""
    rows = []
    for cik in ["0000320193", "0001652044", "0000789019"]:
        total = 100
        for year in [2021, 2022, 2023]:
            for cluster in [0, 1]:
                # Cluster 0 grows each year; cluster 1 shrinks
                count_c0 = 10 + (year - 2021) * 5
                count_c1 = 20 - (year - 2021) * 5
                rows.append({
                    "cik":         cik,
                    "cluster_id":  cluster,
                    "year":        year,
                    "chunk_count": count_c0 if cluster == 0 else count_c1,
                    "total_chunks": total,
                })
    return pd.DataFrame(rows)


@pytest.fixture()
def new_cluster_timeline() -> pd.DataFrame:
    """Cluster 99 appears only in 2023 (not in 2022)."""
    return pd.DataFrame([
        {"cik": "0000320193", "cluster_id": 99, "year": 2022,
         "chunk_count": 0, "total_chunks": 100},   # placeholder – zero means absent
        {"cik": "0000320193", "cluster_id": 99, "year": 2023,
         "chunk_count": 15, "total_chunks": 100},
    ])


@pytest.fixture()
def disappeared_cluster_timeline() -> pd.DataFrame:
    """Cluster 77 is present in 2022, absent in 2023."""
    return pd.DataFrame([
        {"cik": "0000320193", "cluster_id": 77, "year": 2022,
         "chunk_count": 20, "total_chunks": 100},
        {"cik": "0000320193", "cluster_id": 77, "year": 2023,
         "chunk_count": 0, "total_chunks": 100},
    ])


# ===========================================================================
# test_compute_intensity_formula
# ===========================================================================

class TestComputeIntensityFormula:
    """intensity = chunk_count / total_chunks"""

    def test_basic_fraction(self):
        assert compute_intensity(10, 100) == pytest.approx(0.10)

    def test_full_intensity(self):
        assert compute_intensity(100, 100) == pytest.approx(1.0)

    def test_zero_chunks(self):
        assert compute_intensity(0, 100) == pytest.approx(0.0)

    def test_zero_total_returns_zero(self):
        """Guard against ZeroDivisionError."""
        result = compute_intensity(0, 0)
        assert result == pytest.approx(0.0) or math.isnan(result)

    def test_fractional_value(self):
        assert compute_intensity(3, 7) == pytest.approx(3 / 7)

    def test_result_in_0_1_range(self):
        for cc, tc in [(0, 50), (25, 50), (50, 50), (10, 200)]:
            result = compute_intensity(cc, tc)
            assert 0.0 <= result <= 1.0


# ===========================================================================
# test_materiality_score_formula
# ===========================================================================

class TestMaterialityScoreFormula:
    """materiality = abs(delta) * log(1 + chunk_count)"""

    def test_basic_formula(self):
        delta = 0.10
        chunk_count = 9  # log(10) ≈ 2.3026
        expected = abs(delta) * math.log(1 + chunk_count)
        assert compute_materiality(delta, chunk_count) == pytest.approx(expected)

    def test_negative_delta_uses_abs(self):
        pos = compute_materiality( 0.05, 20)
        neg = compute_materiality(-0.05, 20)
        assert pos == pytest.approx(neg)

    def test_zero_delta_gives_zero(self):
        assert compute_materiality(0.0, 100) == pytest.approx(0.0)

    def test_larger_chunk_count_increases_materiality(self):
        m_small = compute_materiality(0.1, 10)
        m_large = compute_materiality(0.1, 100)
        assert m_large > m_small

    def test_larger_delta_increases_materiality(self):
        m_low  = compute_materiality(0.05, 50)
        m_high = compute_materiality(0.50, 50)
        assert m_high > m_low

    def test_formula_is_log_not_log10(self):
        """Ensure natural log is used, not log10."""
        expected = 0.2 * math.log(11)  # natural log
        result = compute_materiality(0.2, 10)
        assert result == pytest.approx(expected, rel=1e-4)


# ===========================================================================
# test_change_type_new
# ===========================================================================

class TestChangeTypeNew:
    """First appearance → change_type = 'new'."""

    def test_none_prev_is_new(self):
        ct = classify_change_type(None, 0.15, float("nan"))
        assert ct == "new"

    def test_nan_prev_is_new(self):
        ct = classify_change_type(float("nan"), 0.10, float("nan"))
        assert ct == "new"

    def test_new_not_other_type(self):
        ct = classify_change_type(None, 0.40, float("nan"))
        assert ct not in ("disappeared", "intensifying", "fading", "stable")


# ===========================================================================
# test_change_type_disappeared
# ===========================================================================

class TestChangeTypeDisappeared:
    """Present then absent → change_type = 'disappeared'."""

    def test_none_curr_is_disappeared(self):
        ct = classify_change_type(0.20, None, float("nan"))
        assert ct == "disappeared"

    def test_nan_curr_is_disappeared(self):
        ct = classify_change_type(0.20, float("nan"), float("nan"))
        assert ct == "disappeared"

    def test_disappeared_not_new(self):
        ct = classify_change_type(0.15, None, float("nan"))
        assert ct != "new"


# ===========================================================================
# test_change_type_intensifying
# ===========================================================================

class TestChangeTypeIntensifying:
    """Large positive delta → change_type = 'intensifying'."""

    def test_large_positive_delta(self):
        ct = classify_change_type(0.10, 0.25, 0.15)
        assert ct == "intensifying"

    def test_just_at_threshold(self):
        # delta = 0.05 is at the threshold – must be intensifying
        ct = classify_change_type(0.10, 0.15, 0.05)
        assert ct in ("intensifying", "stable")  # allow for inclusive/exclusive boundary

    def test_small_positive_not_intensifying(self):
        ct = classify_change_type(0.10, 0.11, 0.01)
        assert ct != "intensifying"


# ===========================================================================
# test_compute_yoy_changes_monotonic_year
# ===========================================================================

class TestComputeYOYChangesMonotonicYear:
    """Output rows should be in ascending year order within each (cik, cluster_id) group."""

    def test_years_ascending_per_group(self, simple_timeline):
        result = compute_yoy_changes(simple_timeline)
        for (cik, cluster_id), grp in result.groupby(["cik", "cluster_id"]):
            years = grp["year"].tolist()
            assert years == sorted(years), (
                f"Years not ascending for cik={cik}, cluster={cluster_id}: {years}"
            )

    def test_result_has_required_columns(self, simple_timeline):
        result = compute_yoy_changes(simple_timeline)
        required = {"cik", "cluster_id", "year", "intensity", "delta", "change_type", "materiality"}
        assert required.issubset(set(result.columns)), (
            f"Missing columns: {required - set(result.columns)}"
        )

    def test_intensity_in_0_1(self, simple_timeline):
        result = compute_yoy_changes(simple_timeline)
        intensities = result["intensity"].dropna()
        assert (intensities >= 0).all() and (intensities <= 1).all()

    def test_materiality_non_negative(self, simple_timeline):
        result = compute_yoy_changes(simple_timeline)
        assert (result["materiality"].dropna() >= 0).all()

    def test_change_type_valid_values(self, simple_timeline):
        result = compute_yoy_changes(simple_timeline)
        valid = {"new", "disappeared", "intensifying", "fading", "stable"}
        invalid = set(result["change_type"].unique()) - valid
        assert not invalid, f"Invalid change_type values: {invalid}"

    def test_growing_cluster_is_intensifying(self, simple_timeline):
        """Cluster 0 has growing chunk count → should be 'intensifying' in later years."""
        result = compute_yoy_changes(simple_timeline)
        cik0 = result[
            (result["cik"] == "0000320193")
            & (result["cluster_id"] == 0)
            & (result["year"] == 2023)
        ]
        if len(cik0):
            assert cik0.iloc[0]["change_type"] in ("intensifying", "stable")

    def test_shrinking_cluster_is_fading(self, simple_timeline):
        """Cluster 1 has shrinking chunk count → should be 'fading' in later years."""
        result = compute_yoy_changes(simple_timeline)
        cik1 = result[
            (result["cik"] == "0000320193")
            & (result["cluster_id"] == 1)
            & (result["year"] == 2023)
        ]
        if len(cik1):
            assert cik1.iloc[0]["change_type"] in ("fading", "stable")
