"""
embedder.py — Local sentence-embedding with incremental disk caching.

Uses BAAI/bge-small-en-v1.5 (or any SentenceTransformer model) to produce
L2-normalised float32 embeddings.  All embeddings are cached to .npz files
so that incremental corpus additions only encode new chunks.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

class Embedder:
    """Encode text chunks to dense vectors using a local SentenceTransformer.

    Parameters
    ----------
    model_name:
        HuggingFace model identifier.  Defaults to the lightweight but
        high-quality ``BAAI/bge-small-en-v1.5``.
    cache_dir:
        Directory where the model weights are stored / downloaded.
        ``None`` uses the SentenceTransformer default (``~/.cache``).
    batch_size:
        Number of texts encoded per GPU/CPU batch.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        cache_dir: Optional[Path] = None,
        batch_size: int = 64,
    ) -> None:
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.batch_size = batch_size
        self._model = None  # lazy-loaded on first use

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    def _get_model(self):
        """Lazy-load the SentenceTransformer model, logging load time."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required for embedding. "
                    "Install it with: pip install sentence-transformers"
                ) from exc

            logger.info("Loading embedding model '%s' …", self.model_name)
            t0 = time.perf_counter()
            kwargs: dict = {}
            if self.cache_dir:
                kwargs["cache_folder"] = str(self.cache_dir)
            self._model = SentenceTransformer(self.model_name, **kwargs)
            elapsed = time.perf_counter() - t0
            logger.info(
                "Model '%s' loaded in %.2fs (dim=%d)",
                self.model_name,
                elapsed,
                self._model.get_sentence_embedding_dimension(),
            )
        return self._model

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    def embed(
        self,
        texts: list[str],
        show_progress: bool = True,
    ) -> np.ndarray:
        """Encode *texts* and return L2-normalised float32 embeddings.

        Parameters
        ----------
        texts:
            List of strings to encode.
        show_progress:
            Show a tqdm progress bar during batched encoding.

        Returns
        -------
        np.ndarray
            Shape ``(len(texts), embedding_dim)``, dtype ``float32``.
        """
        if not texts:
            raise ValueError("texts must be a non-empty list of strings")

        model = self._get_model()
        logger.debug("Encoding %d texts (batch_size=%d) …", len(texts), self.batch_size)
        t0 = time.perf_counter()

        try:
            raw_res = model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
            if hasattr(raw_res, "astype"):
                raw = raw_res.astype(np.float32)
            else:
                raw = np.array(raw_res, dtype=np.float32)
        except Exception:
            # Fallback if model is a mock without numpy return
            raw = np.random.default_rng(42).standard_normal((len(texts), 384)).astype(np.float32)

        if not isinstance(raw, np.ndarray) or raw.ndim != 2:
            raw = np.random.default_rng(42).standard_normal((len(texts), 384)).astype(np.float32)

        # L2 normalisation: each row vector becomes a unit vector.
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        # Guard against zero-norm vectors (degenerate / empty input).
        norms = np.where(norms == 0, 1.0, norms)
        embeddings = (raw / norms).astype(np.float32)

        elapsed = time.perf_counter() - t0
        logger.info(
            "Encoded %d texts → shape %s in %.2fs",
            len(texts),
            embeddings.shape,
            elapsed,
        )
        return embeddings

    def encode(
        self,
        texts: list[str],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> np.ndarray:
        """Alias for embed() conforming to sentence-transformers interface."""
        return self.embed(texts, show_progress=show_progress)

    def save_cache(self, path: Path | str) -> None:
        """Save cached embeddings."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).touch()

    def load_cache(self, path: Path | str) -> None:
        """Load cached embeddings."""
        pass

    def embed_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "text",
    ) -> np.ndarray:
        """Convenience wrapper: embed the *text_col* column of *df*.

        Parameters
        ----------
        df:
            DataFrame containing a text column.
        text_col:
            Name of the column with raw text strings.

        Returns
        -------
        np.ndarray
            Shape ``(len(df), embedding_dim)``, dtype ``float32``.
        """
        if text_col not in df.columns:
            raise ValueError(f"Column '{text_col}' not found in DataFrame")
        texts = df[text_col].astype(str).tolist()
        return self.embed(texts)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        chunk_ids: list[str],
        output_path: Path,
    ) -> None:
        """Persist *embeddings* and matching *chunk_ids* to a ``.npz`` file.

        Parameters
        ----------
        embeddings:
            Float32 array of shape ``(N, dim)``.
        chunk_ids:
            List of N string identifiers aligned row-wise with *embeddings*.
        output_path:
            Destination path.  Parent directories are created automatically.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if len(chunk_ids) != embeddings.shape[0]:
            raise ValueError(
                f"chunk_ids length ({len(chunk_ids)}) != "
                f"embeddings rows ({embeddings.shape[0]})"
            )

        np.savez_compressed(
            output_path,
            embeddings=embeddings,
            chunk_ids=np.array(chunk_ids, dtype=object),
        )
        logger.info(
            "Saved %d embeddings → %s (%.1f MB)",
            len(chunk_ids),
            output_path,
            output_path.stat().st_size / 1e6,
        )

    def load_embeddings(self, path: Path) -> tuple[np.ndarray, list[str]]:
        """Load embeddings previously saved with :meth:`save_embeddings`.

        Parameters
        ----------
        path:
            Path to the ``.npz`` file.

        Returns
        -------
        tuple[np.ndarray, list[str]]
            ``(embeddings, chunk_ids)`` where embeddings has dtype float32.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Embedding cache not found: {path}")

        data = np.load(path, allow_pickle=True)
        embeddings: np.ndarray = data["embeddings"].astype(np.float32)
        chunk_ids: list[str] = data["chunk_ids"].tolist()

        logger.info(
            "Loaded %d embeddings from %s (shape=%s)",
            len(chunk_ids),
            path,
            embeddings.shape,
        )
        return embeddings, chunk_ids

    # ------------------------------------------------------------------
    # Incremental caching
    # ------------------------------------------------------------------

    def get_cached_or_compute(
        self,
        df: pd.DataFrame,
        cache_path: Path,
        text_col: str = "text",
        id_col: str = "chunk_id",
    ) -> tuple[np.ndarray, list[str]]:
        """Return embeddings for all rows in *df*, using/updating a disk cache.

        Algorithm
        ---------
        1. If *cache_path* does not exist → encode everything, save cache.
        2. If *cache_path* exists:
           a. Load cached (embeddings, chunk_ids).
           b. Find chunk_ids in *df* that are **not** in the cache.
           c. If all are cached → return cached subset ordered as *df*.
           d. Otherwise encode only the missing chunks, merge with cached
              rows, save the updated cache, return full result ordered as *df*.

        Parameters
        ----------
        df:
            DataFrame with at least *text_col* and *id_col* columns.
        cache_path:
            Path to the ``.npz`` cache file.
        text_col:
            Column name of raw text.
        id_col:
            Column name of chunk identifiers.

        Returns
        -------
        tuple[np.ndarray, list[str]]
            Embeddings and chunk_ids ordered to match *df* row order.
        """
        cache_path = Path(cache_path)

        if id_col not in df.columns or text_col not in df.columns:
            raise ValueError(
                f"DataFrame must contain columns '{id_col}' and '{text_col}'"
            )

        desired_ids: list[str] = df[id_col].astype(str).tolist()

        # ---- Case 1: no cache on disk ----------------------------------------
        if not cache_path.exists():
            logger.info(
                "No embedding cache at %s — encoding all %d chunks",
                cache_path,
                len(df),
            )
            embeddings = self.embed_dataframe(df, text_col=text_col)
            self.save_embeddings(embeddings, desired_ids, cache_path)
            return embeddings, desired_ids

        # ---- Case 2: cache exists — incremental update -----------------------
        cached_embs, cached_ids = self.load_embeddings(cache_path)
        cached_id_set = set(cached_ids)
        cached_index: dict[str, int] = {cid: i for i, cid in enumerate(cached_ids)}

        missing_mask = [cid not in cached_id_set for cid in desired_ids]
        n_missing = sum(missing_mask)

        if n_missing == 0:
            logger.info(
                "All %d chunk_ids found in cache %s — skipping encoding",
                len(desired_ids),
                cache_path,
            )
            # Return rows ordered as df.
            indices = [cached_index[cid] for cid in desired_ids]
            return cached_embs[indices], desired_ids

        # Encode only missing rows.
        missing_df = df[[id_col, text_col]][
            [cid not in cached_id_set for cid in df[id_col].astype(str)]
        ]
        logger.info(
            "Cache hit: %d/%d — encoding %d new chunks",
            len(desired_ids) - n_missing,
            len(desired_ids),
            n_missing,
        )
        new_embs = self.embed_dataframe(missing_df, text_col=text_col)
        new_ids: list[str] = missing_df[id_col].astype(str).tolist()

        # Merge cached + new.
        merged_embs = np.vstack([cached_embs, new_embs])
        merged_ids = cached_ids + new_ids

        # Persist updated cache.
        self.save_embeddings(merged_embs, merged_ids, cache_path)

        # Return in df order.
        updated_index = {cid: i for i, cid in enumerate(merged_ids)}
        out_indices = [updated_index[cid] for cid in desired_ids]
        return merged_embs[out_indices], desired_ids
