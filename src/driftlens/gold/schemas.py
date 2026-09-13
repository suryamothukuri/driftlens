"""Pandera validation schemas for DriftLens Gold Parquet tables."""

import pandera as pa

companies_schema = pa.DataFrameSchema({
    "cik": pa.Column(str, nullable=False),
    "ticker": pa.Column(str, nullable=True),
    "name": pa.Column(str, nullable=False),
    "sector": pa.Column(str, nullable=True),
    "first_year": pa.Column(int, nullable=False),
    "last_year": pa.Column(int, nullable=False),
}, coerce=True)

themes_schema = pa.DataFrameSchema({
    "cluster_id": pa.Column(int, nullable=False),
    "label": pa.Column(str, nullable=False),
    "n_companies_ever": pa.Column(int, nullable=False),
    "first_seen_year": pa.Column(int, nullable=False),
    "last_seen_year": pa.Column(int, nullable=False),
    "override_flag": pa.Column(bool, nullable=False, default=False),
}, coerce=True)

theme_intensity_schema = pa.DataFrameSchema({
    "cik": pa.Column(str, nullable=False),
    "fiscal_year": pa.Column(int, nullable=False),
    "cluster_id": pa.Column(int, nullable=False),
    "intensity": pa.Column(float, checks=pa.Check.in_range(0.0, 1.0), nullable=False),
    "chunk_count": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
}, coerce=True)

theme_changes_schema = pa.DataFrameSchema({
    "cik": pa.Column(str, nullable=False),
    "cluster_id": pa.Column(int, nullable=False),
    "fiscal_year": pa.Column(int, nullable=False),
    "intensity_delta": pa.Column(float, nullable=False),
    "centroid_drift": pa.Column(float, nullable=True),
    "materiality_score": pa.Column(float, checks=pa.Check.ge(0.0), nullable=False),
    "change_type": pa.Column(str, checks=pa.Check.isin(["new", "intensifying", "fading", "disappeared", "stable"]), nullable=False),
}, coerce=True)

explanations_schema = pa.DataFrameSchema({
    "change_id": pa.Column(str, nullable=False),
    "cik": pa.Column(str, nullable=False),
    "cluster_id": pa.Column(int, nullable=False),
    "fiscal_year": pa.Column(int, nullable=False),
    "explanation_text": pa.Column(str, nullable=False),
    "evidence_chunk_ids": pa.Column(object, nullable=True),
    "model_used": pa.Column(str, nullable=False),
    "generated_at": pa.Column(str, nullable=False),
}, coerce=True)

evidence_chunks_schema = pa.DataFrameSchema({
    "chunk_id": pa.Column(str, nullable=False),
    "cik": pa.Column(str, nullable=False),
    "fiscal_year": pa.Column(int, nullable=False),
    "cluster_id": pa.Column(int, nullable=False),
    "text": pa.Column(str, nullable=False),
    "char_start_note": pa.Column(str, nullable=True),
}, coerce=True)

data_quality_schema = pa.DataFrameSchema({
    "fiscal_year": pa.Column(int, nullable=False),
    "extraction_success_rate": pa.Column(float, checks=pa.Check.in_range(0.0, 1.0), nullable=False),
    "noise_fraction": pa.Column(float, checks=pa.Check.in_range(0.0, 1.0), nullable=False),
    "total_chunks": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
    "total_filings": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
    "failed_extractions": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
}, coerce=True)
