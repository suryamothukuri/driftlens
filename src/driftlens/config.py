"""
DriftLens configuration module.

All project-wide constants, presets, and path definitions live here.
Downstream modules should import from this module rather than hard-coding values.

Usage
-----
>>> from driftlens.config import EDGAR_CONFIG, DEFAULT_COMPANIES, PROJECT_ROOT
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Project root — walk upward from this file until we find pyproject.toml
# ─────────────────────────────────────────────────────────────────────────────

def _find_project_root(start: Path) -> Path:
    """Walk up the directory tree to find the project root (contains pyproject.toml)."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback: four levels up from src/driftlens/config.py → project root
    return start.resolve().parents[3]


PROJECT_ROOT: Path = _find_project_root(Path(__file__).parent)

# ─────────────────────────────────────────────────────────────────────────────
# Scale presets
# ─────────────────────────────────────────────────────────────────────────────

SCALE_PRESETS: dict[str, dict[str, int]] = {
    "small": {
        "n_companies": 30,
        "n_years": 5,
    },
    "medium": {
        "n_companies": 150,
        "n_years": 6,
    },
    "full": {
        "n_companies": 500,
        "n_years": 7,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Default company CIKs (SEC EDGAR Central Index Keys)
# Covers 5 GICS super-sectors: Technology, Healthcare, Industrials, Consumer, Energy, Finance
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_COMPANIES: list[str] = [
    # ── Technology ─────────────────────────────────────────────────────────
    "0000320193",   # Apple Inc.
    "0000789019",   # Microsoft Corporation
    "0001652044",   # Alphabet Inc. (Google)
    "0001326801",   # Meta Platforms Inc. (Facebook)
    "0001045810",   # NVIDIA Corporation
    "0000050863",   # Intel Corporation
    "0001108524",   # Salesforce Inc.
    "0000796343",   # Adobe Inc.
    # ── Healthcare ─────────────────────────────────────────────────────────
    "0000200406",   # Johnson & Johnson
    "0000078003",   # Pfizer Inc.
    "0000731766",   # UnitedHealth Group
    "0000001800",   # Abbott Laboratories
    "0000310158",   # Merck & Co.
    "0000059478",   # Eli Lilly and Company
    # ── Industrials ────────────────────────────────────────────────────────
    "0000012927",   # Boeing Company
    "0000018230",   # Caterpillar Inc.
    "0000040987",   # General Electric Company
    "0000773840",   # Honeywell International Inc.
    "0000066740",   # 3M Company
    # ── Consumer (Staples & Discretionary) ────────────────────────────────
    "0001018724",   # Amazon.com Inc.
    "0000104169",   # Walmart Inc.
    "0000320187",   # Nike Inc.
    "0000080424",   # Procter & Gamble Company
    "0000021344",   # Coca-Cola Company
    "0000063908",   # McDonald's Corporation
    # ── Energy ────────────────────────────────────────────────────────────
    "0000034088",   # ExxonMobil Corporation
    "0000093410",   # Chevron Corporation
    "0001163165",   # ConocoPhillips
    "0000087347",   # SLB (formerly Schlumberger)
    # ── Finance ───────────────────────────────────────────────────────────
    "0000019617",   # JPMorgan Chase & Co.
    "0001067983",   # Berkshire Hathaway Inc.
]

# ─────────────────────────────────────────────────────────────────────────────
# Data-lake path configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BasePaths:
    """Paths to each data-lake layer, all relative to PROJECT_ROOT."""

    # Raw EDGAR filing downloads (HTML/XML/text)
    bronze: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "bronze")
    # Cleaned, sentence-split parquet tables
    silver: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "silver")
    # Final analytics tables (embeddings, clusters, drift scores)
    gold: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "gold")
    # Small, committed sample data for tests and demos
    sample: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "sample")
    # Manual override CSVs (committed to git)
    overrides: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "overrides")

    def ensure_all(self) -> None:
        """Create all data directories if they don't already exist."""
        for path_field in (self.bronze, self.silver, self.gold, self.sample, self.overrides):
            path_field.mkdir(parents=True, exist_ok=True)


BASE_PATHS: BasePaths = BasePaths()

# ─────────────────────────────────────────────────────────────────────────────
# EDGAR configuration
# ─────────────────────────────────────────────────────────────────────────────

EDGAR_CONFIG: dict[str, Any] = {
    # Base URL for the EDGAR full-text search API (EFTS)
    "efts_base_url": "https://efts.sec.gov/LATEST/search-index",
    # Base URL for browsing company filings
    "submissions_base_url": "https://data.sec.gov/submissions",
    # Base URL for raw filing documents
    "archives_base_url": "https://www.sec.gov/Archives/edgar",
    # Company facts / financial data API
    "company_facts_url": "https://data.sec.gov/api/xbrl/companyfacts",
    # EDGAR XBRL viewer
    "viewer_base_url": "https://www.sec.gov/cgi-bin/viewer",
    # Polite rate limit imposed by SEC EDGAR fair-access policy (max 10 req/s)
    "rate_limit_rps": 8,
    # SEC EDGAR requires a descriptive User-Agent per their access policy:
    # https://www.sec.gov/os/accessing-edgar-data
    "user_agent": "DriftLens/0.1.0 (research project; contact suryatejam2312@gmail.com)",
    # Default filing type to ingest
    "default_form_type": "10-K",
    # Timeout for HTTP requests (seconds)
    "request_timeout": 30,
    # Number of retries on transient failures (429 / 5xx)
    "max_retries": 5,
    # Back-off base in seconds between retries (exponential back-off)
    "retry_backoff_base": 2.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# Embedding model configuration
# ─────────────────────────────────────────────────────────────────────────────

EMBEDDING_CONFIG: dict[str, Any] = {
    # Sentence-transformers model — compact, English-focused BGE model
    # Produces 384-dim embeddings; good speed/quality tradeoff for large corpora
    "model_name": "BAAI/bge-small-en-v1.5",
    # Number of sentences per forward pass. Tune to VRAM / RAM available.
    "batch_size": 256,
    # Local cache directory for downloaded model weights
    "cache_path": PROJECT_ROOT / ".cache" / "embeddings",
    # Maximum sequence length (tokens) — sentences longer than this are truncated
    "max_seq_length": 512,
    # Whether to normalize embeddings to unit sphere (recommended for cosine similarity)
    "normalize_embeddings": True,
    # Device override: "cpu", "cuda", "mps" or None (auto-detect)
    "device": None,
    # Whether to show a progress bar during encode()
    "show_progress_bar": True,
}

# ─────────────────────────────────────────────────────────────────────────────
# Clustering configuration
# ─────────────────────────────────────────────────────────────────────────────

CLUSTERING_CONFIG: dict[str, Any] = {
    # ── UMAP dimensionality reduction ─────────────────────────────────────
    "umap": {
        # Target number of components (dimensions) after reduction
        "n_components": 12,
        # Number of nearest neighbours considered during graph construction
        # Higher = more global structure preserved; lower = more local
        "n_neighbors": 15,
        # Controls how tightly points are packed in the low-dim space
        "min_dist": 0.0,
        # Distance metric used on the high-dim embeddings
        "metric": "cosine",
        # Random seed for reproducibility
        "random_state": 42,
        # Whether to use a low-memory algorithm (slower but fits large data)
        "low_memory": False,
    },
    # ── HDBSCAN clustering ────────────────────────────────────────────────
    "hdbscan": {
        # Minimum cluster sizes per scale preset (tune based on corpus size)
        "min_cluster_size": {
            "small": 10,
            "medium": 20,
            "full": 40,
        },
        # Minimum number of samples in a neighbourhood for a point to be core
        "min_samples": 5,
        # Cluster selection method: "eom" (excess of mass) or "leaf"
        "cluster_selection_method": "eom",
        # Distance metric for HDBSCAN (should match UMAP output space)
        "metric": "euclidean",
        # Predict soft membership probabilities for each point
        "prediction_data": True,
    },
    # ── Post-processing ───────────────────────────────────────────────────
    # Fraction of the corpus flagged as noise (label == -1) above which
    # we emit a warning suggesting smaller min_cluster_size
    "noise_fraction_warn_threshold": 0.25,
}

# ─────────────────────────────────────────────────────────────────────────────
# Ollama (local LLM) configuration
# ─────────────────────────────────────────────────────────────────────────────

OLLAMA_CONFIG: dict[str, Any] = {
    # Base URL of the local Ollama API server
    "base_url": "http://localhost:11434",
    # API endpoint for chat completions
    "chat_endpoint": "/api/chat",
    # API endpoint for generating completions
    "generate_endpoint": "/api/generate",
    # Primary model for cluster theme labelling and drift explanation
    "model": "qwen2.5:7b-instruct",
    # Fallback model if primary is unavailable or OOM
    "fallback_model": "llama3.1:8b",
    # Maximum tokens in the LLM response
    "max_tokens": 512,
    # Sampling temperature (0.0 = deterministic, 1.0 = creative)
    "temperature": 0.2,
    # HTTP timeout for Ollama requests (seconds) — allow longer for cold starts
    "request_timeout": 120,
    # Number of sentences to include in the context window per cluster sample
    "context_sentences_per_cluster": 10,
    # Prompt template for cluster labelling (use {sentences} placeholder)
    "label_prompt_template": (
        "You are an expert at analysing SEC 10-K annual reports. "
        "Below are {n} representative sentences from a cluster of semantically similar passages.\n\n"
        "{sentences}\n\n"
        "Respond with a concise 2–5 word topic label that captures the shared theme of these passages. "
        "Return ONLY the label, nothing else."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Convenience re-exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "PROJECT_ROOT",
    "SCALE_PRESETS",
    "DEFAULT_COMPANIES",
    "BasePaths",
    "BASE_PATHS",
    "EDGAR_CONFIG",
    "EMBEDDING_CONFIG",
    "CLUSTERING_CONFIG",
    "OLLAMA_CONFIG",
]
