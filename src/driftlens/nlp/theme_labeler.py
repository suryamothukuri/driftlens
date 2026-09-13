"""
theme_labeler.py — Assign human-readable labels to HDBSCAN theme clusters.

Primary path  : call a local Ollama LLM (via OllamaClient) with a strict prompt.
Fallback path : TF-IDF top-3 keywords from representative chunks (no Ollama needed).
Override path : pre-populated CSV overrides loaded at construction time.

Label contract
--------------
* Max 50 characters.
* Title-cased after generation.
* Stripped of surrounding whitespace / quotes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    # Only imported for type hints; runtime import is optional.
    pass  # OllamaClient may not exist

logger = logging.getLogger(__name__)

# Maximum label length enforced before persisting.
_MAX_LABEL_LEN = 50

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_label(raw: str) -> str:
    """Strip quotes, newlines, extra whitespace; title-case; truncate."""
    label = raw.strip().strip('"\'').strip()
    # Remove any trailing period that LLMs sometimes add.
    label = label.rstrip(".")
    # Collapse internal whitespace.
    label = re.sub(r"\s+", " ", label)
    label = label.title()
    return label[:_MAX_LABEL_LEN]


def _tfidf_keywords(chunks: list[str], n: int = 3) -> str:
    """Return top-*n* TF-IDF keywords from *chunks* joined with ' / '.

    Falls back gracefully if sklearn is unavailable (returns 'Unknown Theme').
    """
    try:
        from sklearn.feature_extraction.text import CountVectorizer  # noqa: PLC0415
    except ImportError:
        logger.warning("sklearn not available; using 'Unknown Theme' as fallback label")
        return "Unknown Theme"

    if not chunks:
        return "Unknown Theme"

    # Use CountVectorizer with TF weighting (simple frequency) as a cheap
    # keyword extractor.  Stop-word removal handles common English noise.
    try:
        vectorizer = CountVectorizer(
            stop_words="english",
            max_features=200,
            ngram_range=(1, 2),
            min_df=1,
        )
        dtm = vectorizer.fit_transform(chunks)
        # Sum counts across documents to get corpus-level frequency.
        freq = dtm.sum(axis=0).A1
        vocab = vectorizer.get_feature_names_out()
        top_indices = freq.argsort()[::-1][:n]
        keywords = [vocab[i] for i in top_indices]
        label = " / ".join(kw.title() for kw in keywords)
        return label[:_MAX_LABEL_LEN]
    except Exception as exc:
        logger.warning("TF-IDF fallback failed (%s); returning 'Unknown Theme'", exc)
        return "Unknown Theme"


# ---------------------------------------------------------------------------
# ThemeLabeler
# ---------------------------------------------------------------------------

class ThemeLabeler:
    """Assign labels to HDBSCAN clusters using Ollama LLM or TF-IDF fallback.

    Parameters
    ----------
    ollama_client:
        An instance of :class:`driftlens.explain.ollama_client.OllamaClient`,
        or ``None`` to force TF-IDF fallback mode.
    overrides_csv:
        Optional path to a CSV with columns ``cluster_id`` (int) and
        ``label`` (str).  Entries here take precedence over LLM / TF-IDF.
    """

    def __init__(
        self,
        ollama_client,  # OllamaClient | None — kept untyped to avoid hard import
        overrides_csv: Optional[Path] = None,
    ) -> None:
        self.ollama_client = ollama_client
        self.overrides: dict[int, str] = {}
        if overrides_csv is not None:
            self.overrides = self._load_overrides(Path(overrides_csv))

        if self.ollama_client is None:
            logger.info(
                "ThemeLabeler: ollama_client is None — TF-IDF fallback mode active"
            )

    # ------------------------------------------------------------------
    # Override management
    # ------------------------------------------------------------------

    def _load_overrides(self, path: Path) -> dict[int, str]:
        """Read *path* (CSV with cluster_id, label columns) into a dict."""
        if not path.exists():
            logger.warning("Overrides CSV not found: %s — ignoring", path)
            return {}
        try:
            df = pd.read_csv(path)
            if "cluster_id" not in df.columns or "label" not in df.columns:
                raise ValueError("CSV must have 'cluster_id' and 'label' columns")
            overrides = {
                int(row["cluster_id"]): _clean_label(str(row["label"]))
                for _, row in df.iterrows()
            }
            logger.info("Loaded %d label overrides from %s", len(overrides), path)
            return overrides
        except Exception as exc:
            logger.error("Failed to load overrides from %s: %s", path, exc)
            return {}

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(self, chunks: list[str]) -> str:
        """Build a strict LLM prompt for cluster labelling.

        Parameters
        ----------
        chunks:
            Representative text excerpts from the cluster.

        Returns
        -------
        str
            Formatted prompt string.
        """
        n = len(chunks)
        excerpts = "\n\n".join(
            f"[{i+1}] {chunk[:500]}" for i, chunk in enumerate(chunks)
        )
        return (
            f"Here are {n} excerpts from corporate risk disclosures. "
            "In 3-6 words, name the common risk theme. "
            "Respond with only the label and nothing else.\n\n"
            f"{excerpts}"
        )

    # ------------------------------------------------------------------
    # Single-cluster labelling
    # ------------------------------------------------------------------

    def label_cluster(
        self,
        cluster_id: int,
        representative_chunks: list[str],
    ) -> str:
        """Return a label for a single cluster.

        Priority: override CSV > Ollama LLM > TF-IDF keywords.

        Parameters
        ----------
        cluster_id:
            Numeric cluster identifier (``-1`` noise cluster is skipped).
        representative_chunks:
            List of text excerpts from the cluster.

        Returns
        -------
        str
            Clean, title-cased label (≤ 50 chars).
        """
        # 1. Override takes highest priority.
        if cluster_id in self.overrides:
            label = self.overrides[cluster_id]
            logger.debug("Cluster %d → override label: '%s'", cluster_id, label)
            return label

        # 2. Ollama LLM path.
        if self.ollama_client is not None:
            label = self._call_ollama(cluster_id, representative_chunks)
            if label:
                return label
            # Fall through to TF-IDF on Ollama failure.
            logger.warning(
                "Ollama labelling failed for cluster %d; falling back to TF-IDF",
                cluster_id,
            )

        # 3. TF-IDF fallback.
        label = _tfidf_keywords(representative_chunks)
        logger.debug("Cluster %d → TF-IDF label: '%s'", cluster_id, label)
        return label

    def _call_ollama(
        self, cluster_id: int, representative_chunks: list[str]
    ) -> Optional[str]:
        """Attempt to label via Ollama; return cleaned label or None on error."""
        prompt = self._build_prompt(representative_chunks)
        try:
            raw: str = self.ollama_client.generate(prompt)
            label = _clean_label(raw)
            if label:
                logger.debug("Cluster %d → Ollama label: '%s'", cluster_id, label)
                return label
            logger.warning("Ollama returned empty label for cluster %d", cluster_id)
            return None
        except Exception as exc:
            logger.warning(
                "Ollama call failed for cluster %d (%s: %s)",
                cluster_id,
                type(exc).__name__,
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # Batch labelling
    # ------------------------------------------------------------------

    def label_all_clusters(
        self,
        top_chunks_per_cluster: dict[int, list[str]],
        chunks_df: pd.DataFrame,
        text_col: str = "text",
    ) -> dict[int, str]:
        """Label every cluster, logging progress.

        Parameters
        ----------
        top_chunks_per_cluster:
            Output of :meth:`ThemeClusterer.get_top_chunks_per_cluster`:
            ``{cluster_id: [chunk_id, …]}``.
        chunks_df:
            DataFrame with chunk text; must have ``chunk_id`` and *text_col*
            columns.
        text_col:
            Name of the text column in *chunks_df*.

        Returns
        -------
        dict[int, str]
            ``{cluster_id: label}`` for all clusters in *top_chunks_per_cluster*.
        """
        if "chunk_id" not in chunks_df.columns or text_col not in chunks_df.columns:
            raise ValueError(
                f"chunks_df must have 'chunk_id' and '{text_col}' columns"
            )

        # Build a fast lookup: chunk_id → text.
        id_to_text: dict[str, str] = dict(
            zip(chunks_df["chunk_id"].astype(str), chunks_df[text_col].astype(str))
        )

        labels: dict[int, str] = {}
        cluster_ids = sorted(top_chunks_per_cluster.keys())
        total = len(cluster_ids)

        logger.info("Labelling %d clusters …", total)
        for i, cid in enumerate(cluster_ids, 1):
            chunk_id_list = top_chunks_per_cluster[cid]
            representative_texts = [
                id_to_text[cid_str]
                for cid_str in chunk_id_list
                if cid_str in id_to_text
            ]
            if not representative_texts:
                logger.warning(
                    "Cluster %d has no resolvable texts — using 'Unknown Theme'", cid
                )
                labels[cid] = "Unknown Theme"
                continue

            label = self.label_cluster(cid, representative_texts)
            labels[cid] = label
            logger.info("[%d/%d] Cluster %d → '%s'", i, total, cid, label)

        return labels

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_labels(self, labels: dict[int, str], output_path: Path) -> None:
        """Save *labels* as a Parquet file with columns ``cluster_id``, ``label``.

        Parameters
        ----------
        labels:
            ``{cluster_id: label}`` mapping.
        output_path:
            Destination ``.parquet`` file.  Parent directories are created.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(
            [{"cluster_id": cid, "label": lbl} for cid, lbl in sorted(labels.items())]
        )
        df.to_parquet(output_path, index=False)
        logger.info("Saved %d cluster labels → %s", len(labels), output_path)

    @classmethod
    def load_labels(cls, path: Path) -> dict[int, str]:
        """Load labels previously saved with :meth:`save_labels`.

        Parameters
        ----------
        path:
            Path to the ``.parquet`` file.

        Returns
        -------
        dict[int, str]
            ``{cluster_id: label}`` mapping.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Labels file not found: {path}")
        df = pd.read_parquet(path)
        labels = {int(row["cluster_id"]): str(row["label"]) for _, row in df.iterrows()}
        logger.info("Loaded %d cluster labels from %s", len(labels), path)
        return labels
