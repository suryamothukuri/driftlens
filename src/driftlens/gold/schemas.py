"""
Pandera schemas for all DriftLens gold-layer tables.

Each schema is defined with ``coerce=True`` so that column types are
automatically cast at validation time.  Nullable columns are explicitly
marked; everything else is assumed non-null.

Usage example::

    from driftlens.gold.schemas import companies_schema
    validated_df = companies_schema.validate(raw_df)
"""

from __future__ import annotations

import pandera as pa
from pandera import Column, Check, DataFrameSchema

# ---------------------------------------------------------------------------
# companies
# ---------------------------------------------------------------------------
companies_schema = DataFrameSchema(
    columns={
        "cik": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False, error="cik must be non-empty"),
        ),
        "ticker": Column(
            pa.String,
            nullable=True,
        ),
        "name": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False, error="name must be non-empty"),
        ),
        "sector": Column(
            pa.String,
            nullable=True,
        ),
        "first_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "last_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
    },
    coerce=True,
    name="companies",
    checks=Check(
        lambda df: (df["first_year"] <= df["last_year"]).all(),
        error="first_year must be <= last_year",
    ),
)

# ---------------------------------------------------------------------------
# themes
# ---------------------------------------------------------------------------
themes_schema = DataFrameSchema(
    columns={
        "cluster_id": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "label": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False, error="label must be non-empty"),
        ),
        "n_companies_ever": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "first_seen_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "last_seen_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "override_flag": Column(
            pa.Bool,
            nullable=False,
        ),
    },
    coerce=True,
    name="themes",
    checks=Check(
        lambda df: (df["first_seen_year"] <= df["last_seen_year"]).all(),
        error="first_seen_year must be <= last_seen_year",
    ),
)

# ---------------------------------------------------------------------------
# theme_intensity
# ---------------------------------------------------------------------------
theme_intensity_schema = DataFrameSchema(
    columns={
        "cik": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False),
        ),
        "fiscal_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "cluster_id": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "intensity": Column(
            pa.Float,
            nullable=False,
            checks=[
                Check.greater_than_or_equal_to(0.0),
                Check.less_than_or_equal_to(1.0),
            ],
        ),
        "chunk_count": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
    },
    coerce=True,
    name="theme_intensity",
)

# ---------------------------------------------------------------------------
# theme_changes
# ---------------------------------------------------------------------------
_VALID_CHANGE_TYPES = {"new", "intensifying", "fading", "disappeared", "stable"}

theme_changes_schema = DataFrameSchema(
    columns={
        "cik": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False),
        ),
        "cluster_id": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "fiscal_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "intensity_delta": Column(
            pa.Float,
            nullable=False,
        ),
        "centroid_drift": Column(
            pa.Float,
            nullable=True,
            checks=[
                Check.greater_than_or_equal_to(0.0),
                Check.less_than_or_equal_to(1.0),
            ],
        ),
        "materiality_score": Column(
            pa.Float,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0.0),
        ),
        "change_type": Column(
            pa.String,
            nullable=False,
            checks=Check(
                lambda s: s.isin(_VALID_CHANGE_TYPES).all(),
                element_wise=False,
                error=f"change_type must be one of {_VALID_CHANGE_TYPES}",
            ),
        ),
    },
    coerce=True,
    name="theme_changes",
)

# ---------------------------------------------------------------------------
# explanations
# ---------------------------------------------------------------------------
explanations_schema = DataFrameSchema(
    columns={
        "change_id": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False),
        ),
        "cik": Column(
            pa.String,
            nullable=False,
        ),
        "cluster_id": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "fiscal_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "explanation_text": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False, error="explanation_text must be non-empty"),
        ),
        # Stored as object (list of strings when loaded from Parquet)
        "evidence_chunk_ids": Column(
            pa.Object,
            nullable=True,
        ),
        "model_used": Column(
            pa.String,
            nullable=False,
        ),
        "generated_at": Column(
            pa.String,
            nullable=False,
        ),
    },
    coerce=True,
    name="explanations",
)

# ---------------------------------------------------------------------------
# evidence_chunks
# ---------------------------------------------------------------------------
evidence_chunks_schema = DataFrameSchema(
    columns={
        "chunk_id": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False),
        ),
        "cik": Column(
            pa.String,
            nullable=False,
        ),
        "fiscal_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "cluster_id": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "text": Column(
            pa.String,
            nullable=False,
            checks=Check(lambda s: s.str.len() > 0, element_wise=False, error="text must be non-empty"),
        ),
        "char_start_note": Column(
            pa.String,
            nullable=True,
        ),
    },
    coerce=True,
    name="evidence_chunks",
)

# ---------------------------------------------------------------------------
# data_quality
# ---------------------------------------------------------------------------
data_quality_schema = DataFrameSchema(
    columns={
        "fiscal_year": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(1993),
        ),
        "extraction_success_rate": Column(
            pa.Float,
            nullable=False,
            checks=[
                Check.greater_than_or_equal_to(0.0),
                Check.less_than_or_equal_to(1.0),
            ],
        ),
        "noise_fraction": Column(
            pa.Float,
            nullable=False,
            checks=[
                Check.greater_than_or_equal_to(0.0),
                Check.less_than_or_equal_to(1.0),
            ],
        ),
        "total_chunks": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "total_filings": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
        "failed_extractions": Column(
            pa.Int,
            nullable=False,
            checks=Check.greater_than_or_equal_to(0),
        ),
    },
    coerce=True,
    name="data_quality",
)
