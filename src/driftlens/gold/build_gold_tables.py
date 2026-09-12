"""
GoldTableBuilder — orchestrates all DriftLens gold-layer Parquet writes.

Each ``build_*`` method produces a validated, schema-conformant DataFrame.
All writes go through ``write_table`` which runs pandera validation before
calling PyArrow to serialise with Snappy compression.

Typical usage::

    builder = GoldTableBuilder(gold_dir=Path("data/gold"), silver_dir=Path("data/silver"))
    paths = builder.build_all(
        cik_list=cik_list,
        tickers_df=tickers_df,
        intensity_df=intensity_df,
        cluster_labels=cluster_labels,
        changes_df=changes_df,
        centroid_df=centroid_df,
        explanations_df=explanations_df,
        chunks_df=chunks_df,
        extraction_results=extraction_results,
        clustering_stats=clustering_stats,
        overrides_path=None,
        max_evidence_chunks=50_000,
    )
    builder.check_sizes(paths)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import pandera as pa
import pyarrow as arrow
import pyarrow.parquet as pq

from .schemas import (
    companies_schema,
    themes_schema,
    theme_intensity_schema,
    theme_changes_schema,
    explanations_schema,
    evidence_chunks_schema,
    data_quality_schema,
)

logger = logging.getLogger(__name__)

_MB = 1024 * 1024
_SIZE_WARN_MB = 20.0


class GoldTableBuilder:
    """Build, validate, and write DriftLens gold-layer Parquet tables.

    Parameters
    ----------
    gold_dir:
        Output directory for gold Parquet files.  Created on first write
        if it does not exist.
    silver_dir:
        Silver data directory (used as a source reference; not written to).
    """

    def __init__(self, gold_dir: Path, silver_dir: Path) -> None:
        self.gold_dir = Path(gold_dir)
        self.silver_dir = Path(silver_dir)
        self.gold_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("GoldTableBuilder: gold_dir=%s silver_dir=%s", self.gold_dir, self.silver_dir)

    # ------------------------------------------------------------------
    # write_table (core)
    # ------------------------------------------------------------------

    def write_table(
        self,
        df: pd.DataFrame,
        name: str,
        schema: pa.DataFrameSchema,
    ) -> Path:
        """Validate *df* against *schema*, then write Parquet to gold_dir.

        Parameters
        ----------
        df:
            DataFrame to write.
        name:
            Table name (file will be ``{gold_dir}/{name}.parquet``).
        schema:
            Pandera schema used for validation (``coerce=True`` schemas
            will cast types automatically).

        Returns
        -------
        Path
            Absolute path to the written Parquet file.

        Raises
        ------
        pa.errors.SchemaError
            If validation fails after coercion.
        """
        logger.info("Validating schema for table '%s' (%d rows)…", name, len(df))
        validated_df: pd.DataFrame = schema.validate(df, lazy=True)

        out_path = self.gold_dir / f"{name}.parquet"
        table = arrow.Table.from_pandas(validated_df, preserve_index=False)
        pq.write_table(table, out_path, compression="snappy")

        size_mb = out_path.stat().st_size / _MB
        logger.info("Wrote '%s' → %s (%.2f MB, %d rows)", name, out_path, size_mb, len(validated_df))
        return out_path

    # ------------------------------------------------------------------
    # Individual build methods
    # ------------------------------------------------------------------

    def build_companies_table(
        self,
        cik_list: list[str],
        tickers_df: pd.DataFrame,
        intensity_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build the ``companies`` gold table.

        Parameters
        ----------
        cik_list:
            Ordered list of CIK strings to include.
        tickers_df:
            DataFrame with at least ``cik`` + optionally ``ticker``, ``name``,
            ``sector`` columns.  Extra columns are ignored.
        intensity_df:
            Silver-layer intensity table used to derive ``first_year`` /
            ``last_year`` per company.

        Returns
        -------
        pd.DataFrame
            Validated companies DataFrame.
        """
        # Derive year ranges from intensity data
        year_stats = (
            intensity_df.groupby("cik")["fiscal_year"]
            .agg(first_year="min", last_year="max")
            .reset_index()
        )

        # Merge ticker/metadata
        base = pd.DataFrame({"cik": [str(c) for c in cik_list]})

        ticker_cols = [c for c in ("cik", "ticker", "name", "sector") if c in tickers_df.columns]
        meta = tickers_df[ticker_cols].copy()
        meta["cik"] = meta["cik"].astype(str)

        merged = base.merge(meta, on="cik", how="left").merge(year_stats, on="cik", how="left")

        # Fill required columns
        for col in ("ticker", "sector"):
            if col not in merged.columns:
                merged[col] = None
        if "name" not in merged.columns:
            merged["name"] = merged["cik"]  # fallback
        merged["name"] = merged["name"].fillna(merged["cik"])

        # year columns must be int; fill missing with sentinel then cast
        merged["first_year"] = merged["first_year"].fillna(1993).astype(int)
        merged["last_year"] = merged["last_year"].fillna(1993).astype(int)

        result = merged[["cik", "ticker", "name", "sector", "first_year", "last_year"]].copy()
        logger.debug("build_companies_table: %d rows", len(result))
        return result

    def build_themes_table(
        self,
        cluster_labels: dict[int, str],
        intensity_df: pd.DataFrame,
        overrides_path: Optional[Path] = None,
    ) -> pd.DataFrame:
        """Build the ``themes`` gold table.

        Parameters
        ----------
        cluster_labels:
            Mapping of ``cluster_id`` → human-readable label (from NLP pipeline).
        intensity_df:
            Silver intensity table; used to derive per-cluster appearance stats.
        overrides_path:
            Optional path to a CSV with columns ``cluster_id, label`` that
            overrides auto-generated labels.

        Returns
        -------
        pd.DataFrame
            Validated themes DataFrame.
        """
        # Aggregate stats from intensity data
        stats = (
            intensity_df.groupby("cluster_id")
            .agg(
                n_companies_ever=("cik", "nunique"),
                first_seen_year=("fiscal_year", "min"),
                last_seen_year=("fiscal_year", "max"),
            )
            .reset_index()
        )
        stats["cluster_id"] = stats["cluster_id"].astype(int)

        # Build label series
        stats["label"] = stats["cluster_id"].map(cluster_labels).fillna(
            stats["cluster_id"].astype(str).apply(lambda x: f"cluster_{x}")
        )
        stats["override_flag"] = False

        # Apply manual overrides
        if overrides_path is not None and Path(overrides_path).exists():
            overrides = pd.read_csv(overrides_path)
            overrides["cluster_id"] = overrides["cluster_id"].astype(int)
            overrides_map: dict[int, str] = dict(zip(overrides["cluster_id"], overrides["label"]))
            mask = stats["cluster_id"].isin(overrides_map)
            stats.loc[mask, "label"] = stats.loc[mask, "cluster_id"].map(overrides_map)
            stats.loc[mask, "override_flag"] = True
            logger.info("Applied %d label overrides from %s", mask.sum(), overrides_path)

        result = stats[
            ["cluster_id", "label", "n_companies_ever", "first_seen_year", "last_seen_year", "override_flag"]
        ].copy()
        logger.debug("build_themes_table: %d rows", len(result))
        return result

    def build_theme_intensity_table(
        self,
        intensity_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build the ``theme_intensity`` gold table.

        Selects and coerces the required columns from the silver intensity
        DataFrame.  ``chunk_count`` defaults to 0 if the column is absent.
        """
        df = intensity_df.copy()
        df["cik"] = df["cik"].astype(str)
        df["cluster_id"] = df["cluster_id"].astype(int)
        df["fiscal_year"] = df["fiscal_year"].astype(int)
        df["intensity"] = df["intensity"].astype(float).clip(0.0, 1.0)

        if "chunk_count" not in df.columns:
            logger.warning("'chunk_count' column absent from intensity_df; defaulting to 0")
            df["chunk_count"] = 0
        df["chunk_count"] = df["chunk_count"].fillna(0).astype(int)

        result = df[["cik", "fiscal_year", "cluster_id", "intensity", "chunk_count"]].copy()
        logger.debug("build_theme_intensity_table: %d rows", len(result))
        return result

    def build_theme_changes_table(
        self,
        changes_df: pd.DataFrame,
        centroid_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build the ``theme_changes`` gold table.

        Parameters
        ----------
        changes_df:
            Output of the drift-scoring pipeline.  Must contain: ``cik``,
            ``cluster_id``, ``fiscal_year``, ``intensity_delta``,
            ``materiality_score``, ``change_type``.
        centroid_df:
            DataFrame with ``cik``, ``cluster_id``, ``fiscal_year``,
            ``centroid_drift`` columns.  Left-joined onto *changes_df*.

        Returns
        -------
        pd.DataFrame
            Validated theme_changes DataFrame.
        """
        df = changes_df.copy()
        df["cik"] = df["cik"].astype(str)
        df["cluster_id"] = df["cluster_id"].astype(int)
        df["fiscal_year"] = df["fiscal_year"].astype(int)
        df["intensity_delta"] = df["intensity_delta"].astype(float)
        df["materiality_score"] = df["materiality_score"].astype(float)

        # Merge centroid drift
        if not centroid_df.empty and "centroid_drift" in centroid_df.columns:
            centroid = centroid_df[["cik", "cluster_id", "fiscal_year", "centroid_drift"]].copy()
            centroid["cik"] = centroid["cik"].astype(str)
            centroid["cluster_id"] = centroid["cluster_id"].astype(int)
            centroid["fiscal_year"] = centroid["fiscal_year"].astype(int)
            df = df.merge(centroid, on=["cik", "cluster_id", "fiscal_year"], how="left")
        else:
            logger.warning("centroid_df is empty or lacks 'centroid_drift'; setting column to NaN")
            df["centroid_drift"] = float("nan")

        # Validate / normalise change_type
        valid_types = {"new", "intensifying", "fading", "disappeared", "stable"}
        if "change_type" not in df.columns:
            logger.warning("'change_type' column missing; defaulting to 'stable'")
            df["change_type"] = "stable"
        bad_mask = ~df["change_type"].isin(valid_types)
        if bad_mask.any():
            logger.warning(
                "%d rows have invalid change_type values; replacing with 'stable'",
                bad_mask.sum(),
            )
            df.loc[bad_mask, "change_type"] = "stable"

        result = df[
            ["cik", "cluster_id", "fiscal_year", "intensity_delta", "centroid_drift",
             "materiality_score", "change_type"]
        ].copy()
        logger.debug("build_theme_changes_table: %d rows", len(result))
        return result

    def build_explanations_table(
        self,
        explanations_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build the ``explanations`` gold table.

        Accepts the DataFrame returned by ``ExplanationBuilder.build_batch_explanations``
        and ensures it conforms to the gold schema.
        """
        df = explanations_df.copy()

        required = {"change_id", "cik", "cluster_id", "fiscal_year",
                    "explanation_text", "evidence_chunk_ids", "model_used", "generated_at"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"explanations_df is missing required columns: {missing}")

        df["cik"] = df["cik"].astype(str)
        df["cluster_id"] = df["cluster_id"].astype(int)
        df["fiscal_year"] = df["fiscal_year"].astype(int)
        df["explanation_text"] = df["explanation_text"].astype(str)
        df["change_id"] = df["change_id"].astype(str)
        df["model_used"] = df["model_used"].astype(str)
        df["generated_at"] = df["generated_at"].astype(str)

        # evidence_chunk_ids must be kept as Python list objects
        if "evidence_chunk_ids" in df.columns:
            df["evidence_chunk_ids"] = df["evidence_chunk_ids"].apply(
                lambda v: v if isinstance(v, list) else ([] if pd.isna(v) else list(v))
            )

        result = df[
            ["change_id", "cik", "cluster_id", "fiscal_year",
             "explanation_text", "evidence_chunk_ids", "model_used", "generated_at"]
        ].copy()
        logger.debug("build_explanations_table: %d rows", len(result))
        return result

    def build_evidence_chunks_table(
        self,
        chunks_df: pd.DataFrame,
        referenced_chunk_ids: set[str],
    ) -> pd.DataFrame:
        """Build the ``evidence_chunks`` gold table.

        Only chunks whose ``chunk_id`` appears in *referenced_chunk_ids* are
        included, keeping the gold table small and relevant.

        Parameters
        ----------
        chunks_df:
            Full silver-layer chunks DataFrame.
        referenced_chunk_ids:
            Set of ``chunk_id`` strings that appear in explanations or the
            top-500 changes.  Only these rows are written to gold.
        """
        df = chunks_df.copy()

        required = {"chunk_id", "cik", "fiscal_year", "cluster_id", "text"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"chunks_df is missing required columns: {missing}")

        df["chunk_id"] = df["chunk_id"].astype(str)
        filtered = df[df["chunk_id"].isin(referenced_chunk_ids)].copy()

        if "char_start_note" not in filtered.columns:
            filtered["char_start_note"] = None

        filtered["cik"] = filtered["cik"].astype(str)
        filtered["fiscal_year"] = filtered["fiscal_year"].astype(int)
        filtered["cluster_id"] = filtered["cluster_id"].astype(int)
        filtered["text"] = filtered["text"].astype(str)

        result = filtered[["chunk_id", "cik", "fiscal_year", "cluster_id", "text", "char_start_note"]].copy()
        logger.debug(
            "build_evidence_chunks_table: %d / %d chunks retained",
            len(result),
            len(df),
        )
        return result

    def build_data_quality_table(
        self,
        extraction_results: pd.DataFrame,
        clustering_stats: dict[str, Any],
    ) -> pd.DataFrame:
        """Build the ``data_quality`` gold table.

        Parameters
        ----------
        extraction_results:
            One row per filing attempt.  Expected columns: ``fiscal_year``,
            ``success`` (bool), ``failed`` (bool or derivable).  Extra columns
            are ignored.
        clustering_stats:
            Dict keyed by fiscal year (int or str) → dict with optional keys
            ``noise_fraction`` and ``total_chunks``.

        Returns
        -------
        pd.DataFrame
            Validated data_quality DataFrame with one row per fiscal year.
        """
        ext = extraction_results.copy()
        ext["fiscal_year"] = ext["fiscal_year"].astype(int)

        # Derive success / failure from boolean columns
        if "success" in ext.columns:
            grouped = (
                ext.groupby("fiscal_year")["success"]
                .agg(
                    total_filings="count",
                    success_count="sum",
                )
                .reset_index()
            )
            grouped["failed_extractions"] = grouped["total_filings"] - grouped["success_count"]
            grouped["extraction_success_rate"] = (
                grouped["success_count"] / grouped["total_filings"].replace(0, float("nan"))
            ).fillna(0.0)
        else:
            logger.warning(
                "extraction_results lacks 'success' column; "
                "defaulting extraction_success_rate to 1.0"
            )
            grouped = (
                ext.groupby("fiscal_year")
                .size()
                .reset_index(name="total_filings")
            )
            grouped["failed_extractions"] = 0
            grouped["extraction_success_rate"] = 1.0

        # Merge clustering stats
        rows: list[dict[str, Any]] = []
        for _, row in grouped.iterrows():
            year = int(row["fiscal_year"])
            ystats: dict[str, Any] = clustering_stats.get(year, clustering_stats.get(str(year), {}))
            rows.append(
                {
                    "fiscal_year": year,
                    "extraction_success_rate": float(row["extraction_success_rate"]),
                    "noise_fraction": float(ystats.get("noise_fraction", 0.0)),
                    "total_chunks": int(ystats.get("total_chunks", 0)),
                    "total_filings": int(row["total_filings"]),
                    "failed_extractions": int(row["failed_extractions"]),
                }
            )

        result = pd.DataFrame(rows)
        if result.empty:
            result = pd.DataFrame(
                columns=[
                    "fiscal_year", "extraction_success_rate", "noise_fraction",
                    "total_chunks", "total_filings", "failed_extractions",
                ]
            )
        logger.debug("build_data_quality_table: %d rows", len(result))
        return result

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def check_sizes(self, paths: dict[str, Path]) -> dict[str, float]:
        """Return file sizes in MB and warn for any table exceeding 20 MB.

        Parameters
        ----------
        paths:
            Mapping of ``table_name`` → ``Path`` as returned by ``build_all``.

        Returns
        -------
        dict[str, float]
            Same keys, values are sizes in megabytes.
        """
        sizes: dict[str, float] = {}
        for name, path in paths.items():
            p = Path(path)
            if p.exists():
                mb = p.stat().st_size / _MB
                sizes[name] = mb
                if mb > _SIZE_WARN_MB:
                    logger.warning(
                        "Table '%s' is %.1f MB (> %.0f MB threshold). "
                        "Consider partitioning or filtering.",
                        name,
                        mb,
                        _SIZE_WARN_MB,
                    )
            else:
                logger.warning("check_sizes: path not found for table '%s': %s", name, path)
                sizes[name] = 0.0
        return sizes

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def build_all(
        self,
        *,
        cik_list: list[str],
        tickers_df: pd.DataFrame,
        intensity_df: pd.DataFrame,
        cluster_labels: dict[int, str],
        changes_df: pd.DataFrame,
        centroid_df: pd.DataFrame,
        explanations_df: pd.DataFrame,
        chunks_df: pd.DataFrame,
        extraction_results: pd.DataFrame,
        clustering_stats: dict[str, Any],
        overrides_path: Optional[Path] = None,
        max_evidence_chunks: int = 50_000,
    ) -> dict[str, Path]:
        """Orchestrate all gold table builds and writes.

        All parameters are passed through to the individual ``build_*``
        methods.  See those methods for detailed parameter documentation.

        Parameters
        ----------
        max_evidence_chunks:
            Safety cap on the number of evidence chunk rows written to gold.
            Chunks are filtered first to those referenced in explanations or
            top-500 changes; this cap is a secondary guard.

        Returns
        -------
        dict[str, Path]
            Mapping of table name → written Parquet path.
        """
        paths: dict[str, Path] = {}

        # --- companies -----------------------------------------------------
        logger.info("Building companies table…")
        companies_df = self.build_companies_table(cik_list, tickers_df, intensity_df)
        paths["companies"] = self.write_table(companies_df, "companies", companies_schema)

        # --- themes --------------------------------------------------------
        logger.info("Building themes table…")
        themes_df = self.build_themes_table(cluster_labels, intensity_df, overrides_path)
        paths["themes"] = self.write_table(themes_df, "themes", themes_schema)

        # --- theme_intensity -----------------------------------------------
        logger.info("Building theme_intensity table…")
        ti_df = self.build_theme_intensity_table(intensity_df)
        paths["theme_intensity"] = self.write_table(ti_df, "theme_intensity", theme_intensity_schema)

        # --- theme_changes -------------------------------------------------
        logger.info("Building theme_changes table…")
        tc_df = self.build_theme_changes_table(changes_df, centroid_df)
        paths["theme_changes"] = self.write_table(tc_df, "theme_changes", theme_changes_schema)

        # --- explanations --------------------------------------------------
        logger.info("Building explanations table…")
        exp_df = self.build_explanations_table(explanations_df)
        paths["explanations"] = self.write_table(exp_df, "explanations", explanations_schema)

        # --- evidence_chunks -----------------------------------------------
        logger.info("Building evidence_chunks table…")
        # Collect all chunk IDs referenced in explanations
        referenced: set[str] = set()
        if not exp_df.empty and "evidence_chunk_ids" in exp_df.columns:
            for ids in exp_df["evidence_chunk_ids"]:
                if isinstance(ids, (list, tuple)):
                    referenced.update(str(i) for i in ids)

        ec_df = self.build_evidence_chunks_table(chunks_df, referenced)
        if len(ec_df) > max_evidence_chunks:
            logger.warning(
                "evidence_chunks has %d rows; truncating to %d (max_evidence_chunks).",
                len(ec_df),
                max_evidence_chunks,
            )
            ec_df = ec_df.head(max_evidence_chunks)
        paths["evidence_chunks"] = self.write_table(ec_df, "evidence_chunks", evidence_chunks_schema)

        # --- data_quality --------------------------------------------------
        logger.info("Building data_quality table…")
        dq_df = self.build_data_quality_table(extraction_results, clustering_stats)
        paths["data_quality"] = self.write_table(dq_df, "data_quality", data_quality_schema)

        logger.info("build_all complete. Tables written: %s", list(paths.keys()))
        return paths
