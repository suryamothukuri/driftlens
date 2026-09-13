"""
driftlens.drift.theme_tracker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
High-level query interface over intensity and change data.

ThemeTracker sits above the computation layer and provides analyst-friendly
methods for exploring how themes evolve: timelines per company, trajectories
per theme, lists of emerging / fading topics, cross-corpus prevalence
statistics, and corpus-level summary metrics.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ThemeTracker
# ---------------------------------------------------------------------------


class ThemeTracker:
    """Query interface for theme lifecycle analysis.

    Parameters
    ----------
    intensity_df:
        Output of :func:`~driftlens.drift.intensity.compute_intensity`.
        Required columns: ``cik``, ``fiscal_year``, ``cluster_id``,
        ``cluster_label``, ``chunk_count``, ``total_chunks``,
        ``intensity``, ``is_present``.

    changes_df:
        Output of :func:`~driftlens.drift.change_detector.compute_yoy_changes`.
        Required columns: ``cik``, ``cluster_id``, ``fiscal_year``,
        ``intensity``, ``prev_intensity``, ``intensity_delta``,
        ``chunk_count``, ``materiality_score``, ``change_type``,
        ``first_appearance``, ``disappeared``.

    themes_df:
        A DataFrame mapping cluster IDs to metadata.
        Required columns: ``cluster_id``, ``cluster_label``.
        Optional additional columns (e.g. ``description``, ``keywords``) are
        preserved and surfaced in :meth:`get_theme_prevalence`.

    Raises
    ------
    ValueError
        If required columns are missing from any input DataFrame.
    """

    # ------------------------------------------------------------------
    # Required columns per input
    # ------------------------------------------------------------------
    _INTENSITY_REQUIRED = {
        "cik",
        "fiscal_year",
        "cluster_id",
        "cluster_label",
        "chunk_count",
        "total_chunks",
        "intensity",
        "is_present",
    }
    _CHANGES_REQUIRED = {
        "cik",
        "cluster_id",
        "fiscal_year",
        "change_type",
        "first_appearance",
        "disappeared",
        "materiality_score",
    }
    _THEMES_REQUIRED = {"cluster_id", "cluster_label"}

    def __init__(
        self,
        intensity_df: pd.DataFrame,
        changes_df: pd.DataFrame,
        themes_df: pd.DataFrame,
    ) -> None:
        _validate_columns(intensity_df, self._INTENSITY_REQUIRED, "ThemeTracker:intensity_df")
        _validate_columns(changes_df, self._CHANGES_REQUIRED, "ThemeTracker:changes_df")
        _validate_columns(themes_df, self._THEMES_REQUIRED, "ThemeTracker:themes_df")

        self._intensity: pd.DataFrame = intensity_df.copy()
        self._changes: pd.DataFrame = changes_df.copy()
        self._themes: pd.DataFrame = themes_df.copy()

        logger.debug(
            "ThemeTracker initialised: %d intensity rows, %d change rows, %d themes.",
            len(self._intensity),
            len(self._changes),
            len(self._themes),
        )

    # ------------------------------------------------------------------
    # Company-centric queries
    # ------------------------------------------------------------------

    def get_company_timeline(self, cik: str) -> pd.DataFrame:
        """Return all theme intensities for a single company across years.

        Parameters
        ----------
        cik:
            SEC Central Index Key identifying the company.

        Returns
        -------
        pd.DataFrame
            Subset of the intensity DataFrame filtered to *cik*, sorted by
            ``fiscal_year`` then ``cluster_id``.  Contains all standard
            intensity columns.

        Raises
        ------
        KeyError
            If *cik* is not found in the intensity data.
        """
        mask = self._intensity["cik"] == cik
        if not mask.any():
            raise KeyError(
                f"CIK '{cik}' not found in intensity data. "
                f"Known CIKs (sample): {self._intensity['cik'].unique()[:5].tolist()}"
            )

        result = (
            self._intensity[mask]
            .sort_values(["fiscal_year", "cluster_id"])
            .reset_index(drop=True)
        )

        logger.debug(
            "get_company_timeline: cik=%s | %d rows across %d years.",
            cik,
            len(result),
            result["fiscal_year"].nunique(),
        )

        return result

    # ------------------------------------------------------------------
    # Theme-centric queries
    # ------------------------------------------------------------------

    def get_theme_trajectory(
        self,
        cluster_id: int,
        cik: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return intensity over time for a single theme.

        Parameters
        ----------
        cluster_id:
            The integer cluster identifier for the theme of interest.
        cik:
            If provided, restrict the trajectory to a single company.

        Returns
        -------
        pd.DataFrame
            Rows from the intensity DataFrame for the given *cluster_id*
            (and optionally *cik*), sorted by ``fiscal_year``.
            Columns include ``cik``, ``fiscal_year``, ``cluster_id``,
            ``cluster_label``, ``chunk_count``, ``intensity``, ``is_present``.

        Raises
        ------
        KeyError
            If *cluster_id* is not found, or if *cik* is not found when
            provided.
        """
        mask = self._intensity["cluster_id"] == cluster_id
        if not mask.any():
            raise KeyError(
                f"cluster_id {cluster_id} not found in intensity data."
            )

        if cik is not None:
            cik_mask = self._intensity["cik"] == cik
            if not (mask & cik_mask).any():
                raise KeyError(
                    f"No data for cluster_id={cluster_id} and cik='{cik}'."
                )
            mask = mask & cik_mask

        result = (
            self._intensity[mask]
            .sort_values(["cik", "fiscal_year"])
            .reset_index(drop=True)
        )

        logger.debug(
            "get_theme_trajectory: cluster_id=%d cik=%s | %d rows.",
            cluster_id,
            cik or "all",
            len(result),
        )

        return result

    def get_emerging_themes(
        self,
        year: int,
        min_companies: int = 3,
    ) -> pd.DataFrame:
        """Themes that made their first appearance in *year* for at least
        *min_companies* distinct companies.

        A "first appearance" is defined by ``first_appearance == True`` in the
        changes DataFrame.

        Parameters
        ----------
        year:
            The fiscal year to check for new appearances.
        min_companies:
            Minimum number of distinct companies required for a theme to be
            considered "emerging".  Defaults to 3.

        Returns
        -------
        pd.DataFrame
            Columns: ``cluster_id``, ``cluster_label``, ``company_count``,
            ``mean_intensity``, ``total_chunk_count``.
            Sorted by ``company_count`` descending.
        """
        new_mask = (
            (self._changes["fiscal_year"] == year)
            & (self._changes["first_appearance"] == True)  # noqa: E712
        )
        new_changes = self._changes[new_mask]

        if new_changes.empty:
            logger.info("get_emerging_themes: no first-appearances in year %d.", year)
            return _empty_emerging_df()

        # Count distinct companies per cluster
        company_counts = (
            new_changes.groupby("cluster_id")["cik"]
            .nunique()
            .reset_index()
            .rename(columns={"cik": "company_count"})
        )

        # Apply threshold
        qualifying = company_counts[company_counts["company_count"] >= min_companies]

        if qualifying.empty:
            logger.info(
                "get_emerging_themes: year=%d, no themes met min_companies=%d.",
                year,
                min_companies,
            )
            return _empty_emerging_df()

        # Supplement with intensity stats
        intensity_year = self._intensity[
            (self._intensity["fiscal_year"] == year)
            & (self._intensity["cluster_id"].isin(qualifying["cluster_id"]))
        ]

        intensity_stats = (
            intensity_year.groupby("cluster_id")
            .agg(
                mean_intensity=("intensity", "mean"),
                total_chunk_count=("chunk_count", "sum"),
                cluster_label=("cluster_label", "first"),
            )
            .reset_index()
        )

        result = (
            qualifying.merge(intensity_stats, on="cluster_id", how="left")
            .sort_values("company_count", ascending=False)
            .reset_index(drop=True)
        )

        out_cols = [
            "cluster_id",
            "cluster_label",
            "company_count",
            "mean_intensity",
            "total_chunk_count",
        ]
        # Preserve only columns that exist
        out_cols = [c for c in out_cols if c in result.columns]
        result = result[out_cols]

        logger.info(
            "get_emerging_themes: year=%d | %d emerging themes (min_companies=%d).",
            year,
            len(result),
            min_companies,
        )

        return result

    def get_fading_themes(self, year: int) -> pd.DataFrame:
        """Themes that are disappearing or fading in *year*.

        Includes rows where ``change_type`` is ``'disappeared'`` or
        ``'fading'`` (or equivalently where ``disappeared == True``).

        Parameters
        ----------
        year:
            The fiscal year of interest.

        Returns
        -------
        pd.DataFrame
            All change records for fading/disappeared themes in *year*, merged
            with theme labels.  Sorted by ``materiality_score`` descending.
        """
        mask = (self._changes["fiscal_year"] == year) & (
            self._changes["change_type"].isin(["disappeared", "fading"])
        )
        fading = self._changes[mask].copy()

        if fading.empty:
            logger.info("get_fading_themes: no fading/disappeared themes in year %d.", year)
            return fading

        # Attach theme labels if not already present
        if "cluster_label" not in fading.columns:
            label_map = (
                self._themes[["cluster_id", "cluster_label"]]
                .drop_duplicates("cluster_id")
                .set_index("cluster_id")["cluster_label"]
                .to_dict()
            )
            fading["cluster_label"] = fading["cluster_id"].map(label_map)

        result = fading.sort_values("materiality_score", ascending=False).reset_index(drop=True)

        logger.info(
            "get_fading_themes: year=%d | %d fading/disappeared records.",
            year,
            len(result),
        )

        return result

    # ------------------------------------------------------------------
    # Corpus-level analysis
    # ------------------------------------------------------------------

    def get_theme_prevalence(self) -> pd.DataFrame:
        """Summary statistics per theme across the full corpus.

        Returns
        -------
        pd.DataFrame
            One row per ``cluster_id`` with columns:

            * ``cluster_id``
            * ``cluster_label``
            * ``unique_companies``  – number of distinct CIKs that ever had
              this cluster present
            * ``first_year``        – earliest fiscal year the theme appeared
            * ``last_year``         – most recent fiscal year observed
            * ``peak_intensity_year`` – fiscal year with the highest mean
              intensity across companies
            * ``mean_intensity``    – overall mean intensity (across all
              company-years where the theme was present)
            * Any extra columns from *themes_df* (e.g. ``description``)

            Sorted by ``unique_companies`` descending.
        """
        present = self._intensity[self._intensity["is_present"] == True].copy()  # noqa: E712

        if present.empty:
            logger.warning("get_theme_prevalence: no present clusters found.")
            return pd.DataFrame()

        # Per-cluster stats
        prevalence = (
            present.groupby("cluster_id")
            .agg(
                unique_companies=("cik", "nunique"),
                first_year=("fiscal_year", "min"),
                last_year=("fiscal_year", "max"),
                mean_intensity=("intensity", "mean"),
            )
            .reset_index()
        )

        # Peak intensity year: year with highest cross-company mean intensity
        year_mean = (
            present.groupby(["cluster_id", "fiscal_year"])["intensity"]
            .mean()
            .reset_index()
            .rename(columns={"intensity": "_year_mean"})
        )
        peak_year = (
            year_mean.loc[
                year_mean.groupby("cluster_id")["_year_mean"].idxmax()
            ][["cluster_id", "fiscal_year"]]
            .rename(columns={"fiscal_year": "peak_intensity_year"})
        )

        prevalence = prevalence.merge(peak_year, on="cluster_id", how="left")

        # Join theme metadata
        theme_meta = self._themes.drop_duplicates("cluster_id")
        prevalence = prevalence.merge(theme_meta, on="cluster_id", how="left")

        # Move cluster_label to second position for readability
        cols = list(prevalence.columns)
        if "cluster_label" in cols:
            cols.remove("cluster_label")
            cols.insert(1, "cluster_label")
        prevalence = prevalence[cols]

        prevalence = prevalence.sort_values("unique_companies", ascending=False).reset_index(drop=True)

        logger.info(
            "get_theme_prevalence: %d themes summarised.", len(prevalence)
        )

        return prevalence

    def get_corpus_stats(self) -> dict:
        """High-level summary statistics for the corpus.

        Returns
        -------
        dict
            Keys:

            * ``total_companies``   – unique CIKs in the intensity data
            * ``total_years``       – unique fiscal years
            * ``total_themes``      – unique cluster IDs (excl. noise)
            * ``total_filings``     – unique (cik, fiscal_year) pairs
            * ``total_chunks``      – sum of chunk_count (unique chunk rows)
            * ``mean_themes_per_filing`` – average number of distinct themes
              per filing
            * ``mean_intensity_per_theme`` – mean intensity across all
              present (cik, year, cluster) rows
            * ``change_type_counts``   – dict of change_type -> count from
              the changes DataFrame
        """
        intensity = self._intensity
        changes = self._changes

        total_companies = int(intensity["cik"].nunique())
        total_years = int(intensity["fiscal_year"].nunique())
        total_themes = int(intensity["cluster_id"].nunique())

        # Unique (cik, fiscal_year) pairs
        total_filings = int(
            intensity[["cik", "fiscal_year"]].drop_duplicates().shape[0]
        )

        # Total chunk count (sum of chunk_count column, which already
        # aggregated individual chunks at intensity computation time)
        total_chunks = int(intensity["chunk_count"].sum())

        # Average themes per filing
        themes_per_filing = (
            intensity[intensity["is_present"] == True]  # noqa: E712
            .groupby(["cik", "fiscal_year"])["cluster_id"]
            .nunique()
        )
        mean_themes_per_filing = float(
            themes_per_filing.mean() if not themes_per_filing.empty else 0.0
        )

        # Mean intensity where theme is present
        present_mask = intensity["is_present"] == True  # noqa: E712
        mean_intensity_per_theme = float(
            intensity.loc[present_mask, "intensity"].mean()
            if present_mask.any()
            else 0.0
        )

        # Change type distribution
        change_type_counts: dict[str, int] = {}
        if not changes.empty and "change_type" in changes.columns:
            change_type_counts = (
                changes["change_type"].value_counts().to_dict()
            )

        stats = {
            "total_companies": total_companies,
            "total_years": total_years,
            "total_themes": total_themes,
            "total_filings": total_filings,
            "total_chunks": total_chunks,
            "mean_themes_per_filing": round(mean_themes_per_filing, 4),
            "mean_intensity_per_theme": round(mean_intensity_per_theme, 6),
            "change_type_counts": change_type_counts,
        }

        logger.info(
            "get_corpus_stats: %d companies, %d years, %d themes, %d filings.",
            total_companies,
            total_years,
            total_themes,
            total_filings,
        )

        return stats


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_columns(
    df: pd.DataFrame,
    required: set[str],
    context: str = "",
) -> None:
    """Raise ValueError if *df* is missing any column in *required*."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"[{context}] Input DataFrame is missing required columns: "
            f"{sorted(missing)}. "
            f"Available columns: {sorted(df.columns.tolist())}."
        )


def _empty_emerging_df() -> pd.DataFrame:
    """Return an empty DataFrame with the emerging-themes schema."""
    return pd.DataFrame(
        columns=[
            "cluster_id",
            "cluster_label",
            "company_count",
            "mean_intensity",
            "total_chunk_count",
        ]
    )
