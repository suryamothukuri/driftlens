# DriftLens

> A general-purpose semantic drift detection engine for large, versioned document corpora.

[![Tests](https://github.com/suryamothukuri/driftlens/actions/workflows/tests.yml/badge.svg)](https://github.com/suryamothukuri/driftlens/actions/workflows/tests.yml)
[![Pipeline](https://github.com/suryamothukuri/driftlens/actions/workflows/pipeline.yml/badge.svg)](https://github.com/suryamothukuri/driftlens/actions/workflows/pipeline.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Live Demo](https://suryamothukuri.github.io/driftlens) · [Review Dashboard](https://your-streamlit-app.streamlit.app) · [Source](https://github.com/suryamothukuri/driftlens)

---

## What is this?

DriftLens is a batch intelligence pipeline that detects when the *meaning* of recurring document sections changes across versions — not just the words. It treats annual SEC 10-K filings as its demonstration corpus (specifically Item 1A, Risk Factors), but the architecture is domain-agnostic: any large collection of recurring, versioned text sections works the same way. The pipeline ingests raw filings, embeds paragraphs with a local sentence-transformer model, clusters them into semantic themes via HDBSCAN, and then measures "centroid drift" — the cosine distance between a theme cluster's mean embedding in year N versus year N-1. When drift is material, a local LLM (running entirely on-device with Ollama) generates a grounded natural-language explanation backed by verbatim excerpts. All outputs are serialized to static Apache Parquet files and served from GitHub Pages and Streamlit Community Cloud with zero per-request inference cost.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DriftLens Pipeline                          │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐  │
│  │  Phase 1  │    │  Phase 2  │    │  Phase 3  │    │   Phase 4   │  │
│  │  Ingest   │───▶│  Embed   │───▶│  Cluster  │───▶│  Drift Calc │  │
│  │           │    │          │    │           │    │             │  │
│  │ SEC EDGAR │    │ bge-small │    │  HDBSCAN  │    │  Centroid   │  │
│  │ 10-K HTML │    │   UMAP   │    │  Themes   │    │  Cosine Δ   │  │
│  └──────────┘    └──────────┘    └──────────┘    └─────────────┘  │
│                                                          │           │
│  ┌──────────────────────────────────────────────────────▼────────┐  │
│  │                          Phase 5                              │  │
│  │                     LLM Explanation                           │  │
│  │        Ollama (qwen2.5:7b-instruct) · grounded excerpts       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                    │                                │
│              ┌─────────────────────┼──────────────────┐            │
│              ▼                     ▼                  ▼            │
│        data/bronze/          data/silver/        data/gold/        │
│        (raw HTML)           (embeddings,         (drift scores,    │
│                              clusters)            explanations)    │
└─────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼────────────────────┐
              ▼                       ▼                     ▼
       GitHub Pages            Streamlit Cloud        GitHub Actions
       (static site,           (interactive dash-     (monthly cron
        DuckDB-Wasm SQL         board, altair charts)  pipeline refresh)
        over Parquet)
```

---

## Why this is harder than it looks

- **Semantic diffing, not lexical**: Standard text diff tells you *what words changed*. DriftLens measures cosine distance between year-N and year-N-1 mean embeddings for the same theme cluster — "centroid drift" — to detect when a company is *saying something meaningfully different* about a topic even if the vocabulary is similar. Two paragraphs can share 80% of their tokens and still drift significantly in embedding space if the emphasis or framing shifts.

- **Evidence-grounded explanations**: LLM explanations are constructed with verbatim excerpts as the only allowed evidence source, with source chunk IDs stored alongside each explanation. The UI links generated text back to the exact filing paragraphs it was derived from — every claim in the explanation is auditable.

- **Materiality scoring**: `abs(intensity_delta) × log(1 + chunk_count)` weights magnitude of change by the substantiveness of discussion, preventing a 1-paragraph theme from outranking a 15-paragraph one with the same relative shift. This scoring function surfaces genuinely significant changes rather than statistical artifacts from thin coverage.

- **Zero-cost permanent deployment**: All LLM inference runs once, offline, during the monthly pipeline batch. The live site and dashboard read only static Parquet files and never call a paid API at request time. A site serving thousands of readers per month costs exactly \$0 in compute beyond the GitHub Actions minutes used to refresh the data.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Embeddings | sentence-transformers (BAAI/bge-small-en-v1.5) | Local, no API key, strong retrieval quality for financial text |
| Dimensionality reduction | UMAP | Better cluster separation than PCA for high-dimensional embedding spaces |
| Clustering | HDBSCAN | Density-based, noise-tolerant, no need to specify k in advance |
| LLM explanations | Ollama (qwen2.5:7b-instruct) | Fully local, zero per-call cost, permissive license, strong instruction following |
| Storage | Apache Parquet | Columnar, compressed, typed schema, fast predicate pushdown |
| In-browser analytics | DuckDB-Wasm | Full SQL over Parquet files in the browser — no backend server needed |
| Dashboard | Streamlit Community Cloud | Free Python deployment, reads Parquet natively, rapid iteration |
| CI/CD | GitHub Actions | Monthly pipeline refresh + automatic Pages deployment on data change |

---

## Scale Options

| Scale | Companies | Years | Filings | Est. Runtime | Est. Disk (bronze) |
|---|---|---|---|---|---|
| `--scale small` | 30 | 5 | ~150 | 30–60 min | ~1.5 GB |
| `--scale medium` | 150 | 6 | ~900 | 3–5 hours | ~8 GB |
| `--scale full` | 500 | 7 | ~3,500 | 6–10 hours | ~15 GB |

All scales share identical pipeline logic. `small` is the default and is suitable for local development and demos. The monthly GitHub Actions job runs at `medium` scale. `full` scale is documented for completeness and intended for manual, local execution.

---

## Data Quality & Limitations

- **Target extraction success rate**: ≥85% (Item 1A section localization from raw HTML). Success rates are tracked per filing and surfaced in the dashboard's Data Quality page.
- **Non-standard filers**: Some companies use unusual HTML structures or embed sections inside iframes or JavaScript — extraction failures are logged with the specific error class and filing accession number.
- **Noise cluster**: HDBSCAN assigns ~5–15% of paragraphs to the noise cluster (label `-1`). These are intentionally excluded from theme aggregation — they represent fragments that don't belong to any coherent theme.
- **Pre-2015 XBRL**: Structured XBRL financial facts are unavailable for some filings before 2015. Affected filings fall back to HTML-only extraction.
- **Embedding model context window**: bge-small-en-v1.5 has a 512-token context window. Paragraphs longer than this are chunked with a 50-token overlap before embedding.

---

## Local Setup

### Prerequisites

1. **Python 3.11+** — the pipeline uses `tomllib` (stdlib in 3.11) and typed `TypeAlias` hints.
2. **Ollama** — required for Phases 3 (theme labeling) and 5 (explanation generation) only. Install from [https://ollama.ai](https://ollama.ai).
3. ~10 GB free disk space for a `small`-scale run (bronze layer + model weights).

### Install

```bash
git clone https://github.com/your-github-username/driftlens.git
cd driftlens
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# For LLM features (theme labeling + explanation generation)
ollama pull qwen2.5:7b-instruct
```

### Run the pipeline

```bash
# Verify environment, credentials, and disk space
python -m driftlens.pipeline check-setup

# Small scale — recommended for a first run (~30–60 min)
python -m driftlens.pipeline run --scale small

# Medium scale — used by the monthly CI job (~3–5 hours)
python -m driftlens.pipeline run --scale medium

# Full scale — run locally when you need the complete corpus (~6–10 hours)
python -m driftlens.pipeline run --scale full
```

Each `run` command is fully idempotent: already-fetched filings are not re-downloaded, and already-embedded chunks are not re-processed. Re-running after a partial failure resumes from the last completed phase.

### Run the dashboard locally

```bash
pip install streamlit altair
streamlit run dashboard/streamlit_app.py
```

The dashboard reads from `data/gold/` by default. Point it at a different directory with `DRIFTLENS_GOLD_PATH=/path/to/gold streamlit run dashboard/streamlit_app.py`.

### Run the tests

```bash
pip install pytest pytest-cov ruff
ruff check src/          # lint
pytest tests/ -v --cov=src/driftlens --cov-report=term-missing
```

---

## Deployment

### Connect DriftLens to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/driftlens.git
git push -u origin main
```

### Deploy GitHub Pages

1. In your GitHub repo → **Settings → Pages**, set **Source** to `GitHub Actions`.
2. Trigger the initial deployment: **Actions → Deploy to GitHub Pages → Run workflow**.
3. Subsequent deployments fire automatically whenever `data/gold/**` or `web/**` changes on `main`.

### Deploy the Streamlit dashboard

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
2. **New app → select your repo → main branch → `dashboard/streamlit_app.py`**.
3. The dashboard reads the gold Parquet files directly from the repo. No secrets or environment variables are required.

### Monthly pipeline (automated)

The `.github/workflows/pipeline.yml` workflow runs automatically on the 1st of every month at 02:00 UTC. It:
1. Installs Ollama and pulls `qwen2.5:7b-instruct` (cached between runs).
2. Executes `python -m driftlens.pipeline run --scale medium`.
3. Commits updated `data/gold/*.parquet` files back to `main` with `[skip ci]`.
4. Dispatches `deploy-pages.yml` to publish the refreshed data to GitHub Pages.

You can also trigger it manually from the **Actions** tab at any time.

---

## Project Structure

```
driftlens/
├── .github/
│   └── workflows/
│       ├── pipeline.yml       # Monthly data refresh + Pages deploy trigger
│       ├── deploy-pages.yml   # Static site deployment to GitHub Pages
│       └── tests.yml          # Lint + test on every push and PR
├── src/
│   └── driftlens/
│       ├── pipeline.py        # CLI entrypoint (check-setup, run)
│       ├── ingest.py          # Phase 1: SEC EDGAR fetch + HTML extraction
│       ├── embed.py           # Phase 2: sentence-transformer embeddings + UMAP
│       ├── cluster.py         # Phase 3: HDBSCAN clustering + theme labeling
│       ├── drift.py           # Phase 4: centroid drift scoring + materiality
│       └── explain.py         # Phase 5: Ollama-backed grounded explanations
├── dashboard/
│   └── streamlit_app.py       # Streamlit dashboard (reads gold Parquet)
├── web/                       # Static site served by GitHub Pages
│   ├── index.html
│   └── data/                  # Gold Parquet files copied here at deploy time
├── data/
│   ├── bronze/                # Raw HTML filings (gitignored)
│   ├── silver/                # Embeddings and cluster assignments (gitignored)
│   └── gold/                  # Drift scores + explanations (committed to repo)
├── tests/
│   ├── test_ingest.py
│   ├── test_embed.py
│   ├── test_cluster.py
│   ├── test_drift.py
│   └── test_explain.py
├── requirements.txt
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).
