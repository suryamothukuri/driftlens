"""
tests/test_gold_schemas.py
==========================
Unit tests for the Pandera gold-layer schemas.

All tests use in-memory DataFrames — no file I/O.
Pandera is used for schema validation; a minimal stub schema is used
when the real driftlens.gold.schemas module is not yet implemented.
"""

from __future__ import annotations

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Try to import real schemas; build stubs if the module isn't ready yet
# ---------------------------------------------------------------------------

def _import_schemas() -> dict:
    try:
        from driftlens.gold import schemas  # type: ignore
        return {
            "CompaniesSchema":      getattr(schemas, "CompaniesSchema",      None),
            "ThemeIntensitySchema": getattr(schemas, "ThemeIntensitySchema", None),
            "DriftEventsSchema":    getattr(schemas, "DriftEventsSchema",    None),
        }
    except ImportError:
        return {}


_SCHEMAS = _import_schemas()


# ---------------------------------------------------------------------------
# Build Pandera stub schemas (used when real module is absent)
# ---------------------------------------------------------------------------

try:
    import pandera as pa
    from pandera import Column, DataFrameSchema, Check

    _COMPANIES_SCHEMA = (_SCHEMAS.get("CompaniesSchema") or DataFrameSchema(
        {
            "cik":          Column(str,   nullable=False),
            "company_name": Column(str,   nullable=False),
            "sic_code":     Column(int,   nullable=True),
            "exchange":     Column(str,   nullable=True),
        },
        coerce=True,
    ))

    _THEME_INTENSITY_SCHEMA = (_SCHEMAS.get("ThemeIntensitySchema") or DataFrameSchema(
        {
            "cik":        Column(str,   nullable=False),
            "year":       Column(int,   nullable=False),
            "cluster_id": Column(int,   nullable=False),
            "intensity":  Column(float, nullable=False,
                                checks=[Check.ge(0.0), Check.le(1.0)]),
            "label":      Column(str,   nullable=True),
        },
        coerce=True,
    ))

    _DRIFT_EVENTS_SCHEMA = (_SCHEMAS.get("DriftEventsSchema") or DataFrameSchema(
        {
            "cik":         Column(str,   nullable=False),
            "year":        Column(int,   nullable=False),
            "cluster_id":  Column(int,   nullable=False),
            "change_type": Column(str,   nullable=False,
                                 checks=[Check.isin([
                                     "new", "disappeared",
                                     "intensifying", "fading", "stable",
                                 ])]),
            "materiality": Column(float, nullable=False),
            "delta":       Column(float, nullable=True),
        },
        coerce=True,
    ))

    _PANDERA_AVAILABLE = True

except ImportError:
    _PANDERA_AVAILABLE = False
    _COMPANIES_SCHEMA      = None
    _THEME_INTENSITY_SCHEMA = None
    _DRIFT_EVENTS_SCHEMA    = None


pandera_required = pytest.mark.skipif(
    not _PANDERA_AVAILABLE, reason="pandera not installed"
)


# ---------------------------------------------------------------------------
# Helper: validate and catch SchemaError
# ---------------------------------------------------------------------------

def _validate(schema, df: pd.DataFrame) -> tuple[bool, str]:
    try:
        schema.validate(df, lazy=True)
        return True, ""
    except Exception as exc:  # noqa: BLE001  – pandera.SchemaErrors or SchemaError
        return False, str(exc)


# ===========================================================================
# test_companies_schema_valid
# ===========================================================================

@pandera_required
class TestCompaniesSchemaValid:
    """A well-formed companies DataFrame should pass validation."""

    @pytest.fixture()
    def valid_companies_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "cik":          ["0000320193", "0001652044", "0000789019"],
            "company_name": ["Apple Inc.", "Alphabet Inc.", "Microsoft Corp."],
            "sic_code":     [3674, 7372, 7372],
            "exchange":     ["NASDAQ", "NASDAQ", "NASDAQ"],
        })

    def test_valid_df_passes(self, valid_companies_df):
        ok, err = _validate(_COMPANIES_SCHEMA, valid_companies_df)
        assert ok, f"Valid companies DataFrame failed validation:\n{err}"

    def test_all_rows_retained(self, valid_companies_df):
        validated = _COMPANIES_SCHEMA.validate(valid_companies_df, lazy=True)
        assert len(validated) == len(valid_companies_df)

    def test_column_names_preserved(self, valid_companies_df):
        validated = _COMPANIES_SCHEMA.validate(valid_companies_df, lazy=True)
        assert set(valid_companies_df.columns).issubset(set(validated.columns))


# ===========================================================================
# test_companies_schema_invalid_type
# ===========================================================================

@pandera_required
class TestCompaniesSchemaInvalidType:
    """Wrong column types should fail validation."""

    def test_sic_code_float_not_coercible_to_int_fails(self):
        """Non-numeric sic_code that can't be coerced should fail."""
        df = pd.DataFrame({
            "cik":          ["0000320193"],
            "company_name": ["Apple Inc."],
            "sic_code":     ["not_a_number"],
            "exchange":     ["NASDAQ"],
        })
        ok, _ = _validate(_COMPANIES_SCHEMA, df)
        assert not ok, "Expected validation to fail for non-numeric sic_code"

    def test_empty_cik_fails(self):
        """Empty/null CIK should fail nullable=False check."""
        df = pd.DataFrame({
            "cik":          [None],
            "company_name": ["Test Corp"],
            "sic_code":     [1234],
            "exchange":     ["NYSE"],
        })
        ok, _ = _validate(_COMPANIES_SCHEMA, df)
        assert not ok, "Expected validation to fail for null CIK"

    def test_missing_required_column_fails(self):
        """A DataFrame missing 'cik' should fail."""
        df = pd.DataFrame({
            "company_name": ["Apple Inc."],
            "sic_code":     [3674],
            "exchange":     ["NASDAQ"],
        })
        ok, _ = _validate(_COMPANIES_SCHEMA, df)
        assert not ok, "Expected validation to fail for missing 'cik' column"


# ===========================================================================
# test_theme_intensity_range
# ===========================================================================

@pandera_required
class TestThemeIntensityRange:
    """Intensity values must be in [0, 1]."""

    def _valid_base(self) -> dict:
        return {
            "cik":        ["0000320193"],
            "year":       [2023],
            "cluster_id": [0],
            "intensity":  [0.25],
            "label":      ["Cybersecurity"],
        }

    def test_boundary_zero_passes(self):
        d = self._valid_base()
        d["intensity"] = [0.0]
        ok, err = _validate(_THEME_INTENSITY_SCHEMA, pd.DataFrame(d))
        assert ok, f"intensity=0.0 should pass: {err}"

    def test_boundary_one_passes(self):
        d = self._valid_base()
        d["intensity"] = [1.0]
        ok, err = _validate(_THEME_INTENSITY_SCHEMA, pd.DataFrame(d))
        assert ok, f"intensity=1.0 should pass: {err}"

    def test_above_one_fails(self):
        d = self._valid_base()
        d["intensity"] = [1.01]
        ok, _ = _validate(_THEME_INTENSITY_SCHEMA, pd.DataFrame(d))
        assert not ok, "intensity=1.01 should fail validation"

    def test_negative_fails(self):
        d = self._valid_base()
        d["intensity"] = [-0.01]
        ok, _ = _validate(_THEME_INTENSITY_SCHEMA, pd.DataFrame(d))
        assert not ok, "intensity=-0.01 should fail validation"

    def test_mid_range_passes(self):
        d = self._valid_base()
        d["intensity"] = [0.55]
        ok, err = _validate(_THEME_INTENSITY_SCHEMA, pd.DataFrame(d))
        assert ok, f"intensity=0.55 should pass: {err}"


# ===========================================================================
# test_change_type_enum
# ===========================================================================

@pandera_required
class TestChangeTypeEnum:
    """change_type must be one of the valid enum values."""

    VALID_TYPES = ["new", "disappeared", "intensifying", "fading", "stable"]

    def _valid_base(self) -> dict:
        return {
            "cik":         ["0000320193"],
            "year":        [2023],
            "cluster_id":  [0],
            "change_type": ["new"],
            "materiality": [0.42],
            "delta":       [0.15],
        }

    def test_all_valid_values_pass(self):
        for ct in self.VALID_TYPES:
            d = self._valid_base()
            d["change_type"] = [ct]
            ok, err = _validate(_DRIFT_EVENTS_SCHEMA, pd.DataFrame(d))
            assert ok, f"change_type='{ct}' should pass: {err}"

    def test_invalid_value_fails(self):
        d = self._valid_base()
        d["change_type"] = ["exploding"]  # not a valid enum value
        ok, _ = _validate(_DRIFT_EVENTS_SCHEMA, pd.DataFrame(d))
        assert not ok, "change_type='exploding' should fail validation"

    def test_empty_string_fails(self):
        d = self._valid_base()
        d["change_type"] = [""]
        ok, _ = _validate(_DRIFT_EVENTS_SCHEMA, pd.DataFrame(d))
        assert not ok, "Empty change_type should fail validation"

    def test_uppercase_fails(self):
        """Schema is case-sensitive; 'NEW' is not 'new'."""
        d = self._valid_base()
        d["change_type"] = ["NEW"]
        ok, _ = _validate(_DRIFT_EVENTS_SCHEMA, pd.DataFrame(d))
        assert not ok, "Uppercase 'NEW' should fail validation (case-sensitive)"


# ===========================================================================
# test_pandera_coercion
# ===========================================================================

@pandera_required
class TestPanderaCoercion:
    """String integers should be coerced to int when coerce=True."""

    def test_string_sic_code_coerced(self):
        """sic_code as string '3674' should be coerced to int 3674."""
        df = pd.DataFrame({
            "cik":          ["0000320193"],
            "company_name": ["Apple Inc."],
            "sic_code":     ["3674"],   # string, not int
            "exchange":     ["NASDAQ"],
        })
        ok, err = _validate(_COMPANIES_SCHEMA, df)
        assert ok, f"String sic_code should be coerced to int: {err}"

    def test_string_year_coerced(self):
        """year as string '2023' should be coerced to int."""
        df = pd.DataFrame({
            "cik":        ["0000320193"],
            "year":       ["2023"],   # string
            "cluster_id": ["0"],      # string
            "intensity":  ["0.25"],   # string
            "label":      ["Cybersecurity"],
        })
        ok, err = _validate(_THEME_INTENSITY_SCHEMA, df)
        assert ok, f"String year/cluster_id/intensity should be coerced: {err}"

    def test_float_string_intensity_coerced(self):
        """intensity='0.75' (string) should be coerced to float 0.75."""
        df = pd.DataFrame({
            "cik":        ["0000320193"],
            "year":       [2023],
            "cluster_id": [1],
            "intensity":  ["0.75"],   # string
            "label":      ["Supply Chain"],
        })
        ok, err = _validate(_THEME_INTENSITY_SCHEMA, df)
        assert ok, f"String intensity should be coerced to float: {err}"

    def test_coercion_preserves_value(self):
        """Coerced value must equal the original numeric value."""
        df = pd.DataFrame({
            "cik":          ["0000789019"],
            "company_name": ["Microsoft Corp."],
            "sic_code":     ["7372"],
            "exchange":     ["NASDAQ"],
        })
        validated = _COMPANIES_SCHEMA.validate(df, lazy=True)
        assert int(validated.iloc[0]["sic_code"]) == 7372
