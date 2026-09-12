"""
pipeline.py
===========
DriftLens CLI orchestrator.  Ties together every pipeline stage from
raw EDGAR ingestion through gold-table production.

Usage examples
--------------
    driftlens run --scale small
    driftlens run --scale medium --skip-ingestion
    driftlens run --scale full --companies /path/to/ciks.txt
    driftlens check-setup
    driftlens status
"""

from __future__ import annotations

import importlib
import logging
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import click

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("driftlens.pipeline")

# ---------------------------------------------------------------------------
# Project-root resolution (repo root is three levels above this file:
# src/driftlens/pipeline.py  →  repo root)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # src/driftlens/
_SRC  = _HERE.parent                             # src/
_ROOT = _SRC.parent                              # repo root
DATA_DIR   = _ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR   = DATA_DIR / "gold"

# ---------------------------------------------------------------------------
# Scale configurations
# ---------------------------------------------------------------------------
SCALE_CONFIG = {
    "small": {
        "description": "Top-10 S&P 500 companies, 3 fiscal years",
        "ciks": [
            "0000320193",  # Apple
            "0001652044",  # Alphabet
            "0000789019",  # Microsoft
            "0001018724",  # Amazon
            "0001326801",  # Meta
            "0001045810",  # NVIDIA
            "0000730469",  # Berkshire Hathaway
            "0000200406",  # Johnson & Johnson
            "0000078814",  # Procter & Gamble
            "0000086312",  # ExxonMobil
        ],
        "years": list(range(2021, 2024)),
        "max_workers": 2,
    },
    "medium": {
        "description": "Top-100 S&P 500 companies, 5 fiscal years",
        "ciks": None,   # loaded from data/sample/medium_ciks.txt
        "years": list(range(2019, 2024)),
        "max_workers": 4,
    },
    "full": {
        "description": "Russell 1000, 10 fiscal years",
        "ciks": None,   # loaded from data/sample/full_ciks.txt
        "years": list(range(2014, 2024)),
        "max_workers": 8,
    },
}


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class OllamaNotAvailableError(Exception):
    """Raised when the Ollama service cannot be reached."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_cik_list(scale: str, companies_file: Optional[str]) -> List[str]:
    """Return the list of CIKs to process."""
    if companies_file:
        path = Path(companies_file)
        if not path.exists():
            raise FileNotFoundError(f"Companies file not found: {path}")
        ciks = [line.strip().zfill(10) for line in path.read_text().splitlines() if line.strip()]
        log.info("Loaded %d CIKs from %s", len(ciks), path)
        return ciks

    cfg = SCALE_CONFIG[scale]
    if cfg["ciks"] is not None:
        return cfg["ciks"]

    # Fallback: look for a text file under data/sample/
    fallback = DATA_DIR / "sample" / f"{scale}_ciks.txt"
    if fallback.exists():
        ciks = [line.strip().zfill(10) for line in fallback.read_text().splitlines() if line.strip()]
        log.info("Loaded %d CIKs from %s", len(ciks), fallback)
        return ciks

    raise FileNotFoundError(
        f"No CIK list found for scale='{scale}'. "
        f"Expected file: {fallback}  or pass --companies."
    )


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s:02d}s"


def _stage_header(name: str) -> None:
    click.echo()
    click.echo(click.style(f"{'─' * 60}", fg="bright_black"))
    click.echo(click.style(f"  STAGE: {name}", fg="cyan", bold=True))
    click.echo(click.style(f"{'─' * 60}", fg="bright_black"))


def _check_ollama() -> dict:
    """
    Returns {"available": bool, "models": list[str]}.
    Does NOT import at module level to keep the CLI fast when Ollama is absent.
    """
    try:
        import requests  # type: ignore
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return {"available": True, "models": models}
    except Exception:
        pass
    return {"available": False, "models": []}


def _run_ingestion(ciks: List[str], years: List[int], max_workers: int) -> dict:
    """Execute the EDGAR ingestion stage."""
    log.info("Ingestion: fetching filings for %d CIKs × %d years", len(ciks), len(years))
    try:
        from driftlens.ingestion import run_ingestion  # type: ignore
        metrics = run_ingestion(ciks=ciks, years=years, max_workers=max_workers)
    except ImportError:
        log.warning("driftlens.ingestion not yet implemented – using stub")
        metrics = {"filings_downloaded": 0, "bytes_written": 0}
    return metrics


def _run_parsing(ciks: List[str], years: List[int]) -> dict:
    """Execute the HTML → silver parsing stage."""
    log.info("Parsing: extracting Item 1A sections and cleaning text")
    try:
        from driftlens.parsing import run_parsing  # type: ignore
        metrics = run_parsing(ciks=ciks, years=years)
    except ImportError:
        log.warning("driftlens.parsing.run_parsing not yet implemented – using stub")
        metrics = {"documents_parsed": 0, "chunks_produced": 0}
    return metrics


def _run_nlp(ciks: List[str], years: List[int]) -> dict:
    """Execute the NLP (embedding + clustering) stage."""
    log.info("NLP: embedding chunks and clustering into semantic themes")
    try:
        from driftlens.nlp import run_nlp  # type: ignore
        metrics = run_nlp(ciks=ciks, years=years)
    except ImportError:
        log.warning("driftlens.nlp.run_nlp not yet implemented – using stub")
        metrics = {"chunks_embedded": 0, "clusters_found": 0}
    return metrics


def _run_drift(ciks: List[str], years: List[int]) -> dict:
    """Execute the year-over-year drift computation stage."""
    log.info("Drift: computing year-over-year intensity shifts")
    try:
        from driftlens.drift import run_drift  # type: ignore
        metrics = run_drift(ciks=ciks, years=years)
    except ImportError:
        log.warning("driftlens.drift.run_drift not yet implemented – using stub")
        metrics = {"theme_year_pairs_analysed": 0, "significant_changes": 0}
    return metrics


def _run_explain(
    ciks: List[str],
    years: List[int],
    max_explanations: int,
    ollama_info: dict,
) -> dict:
    """
    Execute the LLM explanation stage.

    Falls back to template-based explanations if Ollama is unavailable;
    never raises OllamaNotAvailableError to the caller.
    """
    log.info("Explain: generating natural-language explanations (max=%d)", max_explanations)

    if not ollama_info["available"]:
        log.warning(
            "OllamaNotAvailableError: Ollama service not reachable at localhost:11434. "
            "Falling back to template-based explanations."
        )
        try:
            from driftlens.explain import run_explain_templates  # type: ignore
            metrics = run_explain_templates(ciks=ciks, years=years, max_explanations=max_explanations)
        except ImportError:
            log.warning("driftlens.explain.run_explain_templates not yet implemented – using stub")
            metrics = {"explanations_generated": 0, "mode": "template-fallback"}
        return metrics

    try:
        from driftlens.explain import run_explain  # type: ignore
        metrics = run_explain(
            ciks=ciks,
            years=years,
            max_explanations=max_explanations,
            model=ollama_info["models"][0] if ollama_info["models"] else "llama3",
        )
    except OllamaNotAvailableError as exc:
        log.warning("OllamaNotAvailableError during explain stage: %s. Using template fallback.", exc)
        try:
            from driftlens.explain import run_explain_templates  # type: ignore
            metrics = run_explain_templates(ciks=ciks, years=years, max_explanations=max_explanations)
        except ImportError:
            metrics = {"explanations_generated": 0, "mode": "template-fallback"}
    except ImportError:
        log.warning("driftlens.explain.run_explain not yet implemented – using stub")
        metrics = {"explanations_generated": 0, "mode": "ollama"}
    return metrics


def _run_gold(ciks: List[str], years: List[int]) -> dict:
    """Execute the gold-table production stage."""
    log.info("Gold: assembling final analytical tables")
    try:
        from driftlens.gold import run_gold  # type: ignore
        metrics = run_gold(ciks=ciks, years=years)
    except ImportError:
        log.warning("driftlens.gold.run_gold not yet implemented – using stub")
        metrics = {"tables_written": 0, "total_rows": 0}
    return metrics


def _print_summary_table(stage_results: list) -> None:
    """Print a formatted table of stage durations and key metrics."""
    click.echo()
    click.echo(click.style("╔" + "═" * 68 + "╗", fg="green"))
    click.echo(click.style("║  PIPELINE SUMMARY", fg="green", bold=True))
    click.echo(click.style("╠" + "═" * 68 + "╣", fg="green"))
    header = f"{'Stage':<20} {'Duration':>10}  {'Key Metrics'}"
    click.echo(click.style(f"║  {header}", fg="green"))
    click.echo(click.style("╠" + "─" * 68 + "╣", fg="green"))
    for row in stage_results:
        stage   = row["stage"]
        status  = row["status"]
        dur_str = _fmt_duration(row["duration_s"]) if row["duration_s"] is not None else "skipped"
        metrics = row.get("metrics", {})
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items()) if metrics else "—"
        color = "green" if status == "ok" else ("yellow" if status == "skipped" else "red")
        click.echo(
            click.style(f"║  {stage:<20} {dur_str:>10}  ", fg="green")
            + click.style(metrics_str, fg=color)
        )
    click.echo(click.style("╚" + "═" * 68 + "╝", fg="green"))
    click.echo()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="driftlens")
def cli():
    """DriftLens: Semantic drift detection for versioned document corpora."""


@cli.command("run")
@click.option(
    "--scale",
    type=click.Choice(["small", "medium", "full"]),
    default="small",
    show_default=True,
    help="Pre-defined scale: small (10 cos), medium (100 cos), full (Russell 1000).",
)
@click.option(
    "--companies",
    type=click.Path(),
    default=None,
    help="Path to a file containing CIKs, one per line. Overrides --scale CIK list.",
)
@click.option("--skip-ingestion",  is_flag=True, help="Skip the EDGAR ingestion stage.")
@click.option("--skip-parsing",    is_flag=True, help="Skip the HTML parsing stage.")
@click.option("--skip-nlp",        is_flag=True, help="Skip the NLP (embedding/clustering) stage.")
@click.option("--skip-drift",      is_flag=True, help="Skip the drift computation stage.")
@click.option("--skip-explain",    is_flag=True, help="Skip the LLM explanation stage.")
@click.option("--skip-gold",       is_flag=True, help="Skip the gold-table production stage.")
@click.option(
    "--max-explanations",
    default=500,
    type=int,
    show_default=True,
    help="Maximum number of LLM explanations to generate.",
)
def run(
    scale: str,
    companies: Optional[str],
    skip_ingestion: bool,
    skip_parsing: bool,
    skip_nlp: bool,
    skip_drift: bool,
    skip_explain: bool,
    skip_gold: bool,
    max_explanations: int,
) -> None:
    """Run the full DriftLens pipeline.

    Stages run in order:

      ingestion → parsing → nlp → drift → explain → gold

    Use --skip-<stage> flags to restart from a specific checkpoint.
    """
    pipeline_start = time.monotonic()
    start_ts = datetime.now(tz=timezone.utc).isoformat()

    click.echo(click.style("\n🔭  DriftLens Pipeline", fg="cyan", bold=True))
    click.echo(click.style(f"    Started  : {start_ts}", fg="bright_black"))
    click.echo(click.style(f"    Scale    : {scale} – {SCALE_CONFIG[scale]['description']}", fg="bright_black"))

    # ---- Load company list -------------------------------------------------
    try:
        ciks = _load_cik_list(scale=scale, companies_file=companies)
    except FileNotFoundError as exc:
        click.echo(click.style(f"\n[ERROR] {exc}", fg="red"), err=True)
        sys.exit(1)

    years = SCALE_CONFIG[scale]["years"]
    max_workers = SCALE_CONFIG[scale]["max_workers"]

    click.echo(click.style(f"    Companies: {len(ciks)}", fg="bright_black"))
    click.echo(click.style(f"    Years    : {years[0]}–{years[-1]}", fg="bright_black"))

    # ---- Ollama availability (checked once, shared across stages) ----------
    ollama_info = _check_ollama()

    # ---- Stage dispatcher -------------------------------------------------
    stage_results = []

    def run_stage(name: str, skip: bool, fn, *args, **kwargs) -> Optional[dict]:
        if skip:
            click.echo(click.style(f"  ↩  {name} skipped", fg="yellow"))
            stage_results.append({"stage": name, "status": "skipped", "duration_s": None, "metrics": {}})
            return None
        _stage_header(name)
        t0 = time.monotonic()
        try:
            metrics = fn(*args, **kwargs)
            duration = time.monotonic() - t0
            log.info("%s completed in %s", name, _fmt_duration(duration))
            stage_results.append({"stage": name, "status": "ok", "duration_s": duration, "metrics": metrics})
            return metrics
        except Exception as exc:  # noqa: BLE001
            duration = time.monotonic() - t0
            log.exception("%s FAILED after %s: %s", name, _fmt_duration(duration), exc)
            stage_results.append({"stage": name, "status": "error", "duration_s": duration, "metrics": {}})
            click.echo(click.style(f"\n[FATAL] Stage '{name}' failed: {exc}", fg="red"), err=True)
            sys.exit(1)

    run_stage("ingestion", skip_ingestion, _run_ingestion, ciks, years, max_workers)
    run_stage("parsing",   skip_parsing,   _run_parsing,   ciks, years)
    run_stage("nlp",       skip_nlp,       _run_nlp,       ciks, years)
    run_stage("drift",     skip_drift,     _run_drift,     ciks, years)
    run_stage(
        "explain", skip_explain, _run_explain,
        ciks, years, max_explanations, ollama_info,
    )
    run_stage("gold",      skip_gold,      _run_gold,      ciks, years)

    # ---- Final summary ----------------------------------------------------
    total_duration = time.monotonic() - pipeline_start
    _print_summary_table(stage_results)
    click.echo(click.style(f"✅  Pipeline complete in {_fmt_duration(total_duration)}", fg="green", bold=True))
    click.echo()


@cli.command("check-setup")
def check_setup() -> None:
    """Check that all dependencies and services are available."""
    click.echo(click.style("\n🔍  DriftLens Environment Check\n", fg="cyan", bold=True))

    # --- Python version ---
    pv = sys.version_info
    py_ok = pv >= (3, 10)
    sym = click.style("✓", fg="green") if py_ok else click.style("✗", fg="red")
    click.echo(f"  {sym}  Python {platform.python_version()} (need ≥ 3.10)")
    if not py_ok:
        click.echo("      → Install Python 3.10+ from https://python.org")

    click.echo()
    click.echo(click.style("  Dependencies:", bold=True))

    deps = [
        ("click",                  "click"),
        ("requests",               "requests"),
        ("pandas",                 "pandas"),
        ("numpy",                  "numpy"),
        ("bs4",                    "beautifulsoup4"),
        ("lxml",                   "lxml"),
        ("sentence_transformers",  "sentence-transformers"),
        ("sklearn",                "scikit-learn"),
        ("hdbscan",                "hdbscan"),
        ("pandera",                "pandera"),
        ("pyarrow",                "pyarrow"),
        ("rich",                   "rich"),
        ("tqdm",                   "tqdm"),
    ]

    missing = []
    for module, pip_name in deps:
        try:
            importlib.import_module(module)
            click.echo(f"    {click.style('✓', fg='green')}  {pip_name}")
        except ImportError:
            click.echo(f"    {click.style('✗', fg='red')}  {pip_name}")
            missing.append(pip_name)

    if missing:
        click.echo()
        click.echo(click.style("  Missing packages – run:", fg="yellow"))
        click.echo(f"      pip install {' '.join(missing)}")

    # --- Ollama ---
    click.echo()
    click.echo(click.style("  Ollama:", bold=True))
    ollama = _check_ollama()
    if ollama["available"]:
        click.echo(f"    {click.style('✓', fg='green')}  Ollama running at localhost:11434")
        if ollama["models"]:
            click.echo(f"       Models: {', '.join(ollama['models'])}")
        else:
            click.echo(click.style("       No models pulled yet – run: ollama pull llama3", fg="yellow"))
    else:
        click.echo(f"    {click.style('✗', fg='red')}  Ollama not reachable at localhost:11434")
        click.echo("       → Install: https://ollama.ai")
        click.echo("       → Start  : ollama serve")
        click.echo("       → Pull   : ollama pull llama3")

    # --- Data directories ---
    click.echo()
    click.echo(click.style("  Data directories:", bold=True))
    required_dirs = [
        (BRONZE_DIR,          "bronze (raw filings)"),
        (SILVER_DIR,          "silver (parsed text)"),
        (GOLD_DIR,            "gold (analytical tables)"),
        (DATA_DIR / "sample", "sample (CIK lists)"),
    ]
    for d, label in required_dirs:
        if d.exists():
            click.echo(f"    {click.style('✓', fg='green')}  {label}: {d}")
        else:
            click.echo(f"    {click.style('✗', fg='red')}  {label}: {d}")
            click.echo(f"       → mkdir -p {d}")

    click.echo()
    if missing or not ollama["available"]:
        click.echo(click.style("  ⚠  Some checks failed – see instructions above.", fg="yellow"))
    else:
        click.echo(click.style("  ✅  All checks passed – ready to run the pipeline!", fg="green", bold=True))
    click.echo()


@cli.command("status")
def status() -> None:
    """Show current pipeline status (what data exists in bronze/silver/gold)."""
    click.echo(click.style("\n📊  DriftLens Pipeline Status\n", fg="cyan", bold=True))

    layers = [
        ("bronze", BRONZE_DIR),
        ("silver", SILVER_DIR),
        ("gold",   GOLD_DIR),
    ]

    for layer_name, layer_dir in layers:
        click.echo(click.style(f"  {layer_name.upper()}  ({layer_dir})", bold=True))
        if not layer_dir.exists():
            click.echo(f"    {click.style('✗', fg='red')}  Directory does not exist")
            click.echo()
            continue

        all_files = list(layer_dir.rglob("*"))
        files     = [f for f in all_files if f.is_file()]
        if not files:
            click.echo(f"    {click.style('·', fg='yellow')}  Empty – no data produced yet")
        else:
            total_bytes = sum(f.stat().st_size for f in files)
            total_mb    = total_bytes / (1024 * 1024)
            # Count unique CIK prefixes to approximate company count
            cik_dirs = {f.parts[len(layer_dir.parts)] for f in files if len(f.parts) > len(layer_dir.parts)}
            click.echo(f"    {click.style('✓', fg='green')}  {len(files):,} files  ({total_mb:.1f} MB)")
            click.echo(f"       Companies (dirs): {len(cik_dirs)}")
            # Most recently modified file
            newest = max(files, key=lambda f: f.stat().st_mtime)
            mtime  = datetime.fromtimestamp(newest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"       Newest file: {newest.name} ({mtime})")
        click.echo()

    # Gold-layer parquet tables
    if GOLD_DIR.exists():
        parquets = list(GOLD_DIR.glob("*.parquet"))
        if parquets:
            click.echo(click.style("  Gold tables:", bold=True))
            try:
                import pandas as pd  # type: ignore
                for p in sorted(parquets):
                    try:
                        df = pd.read_parquet(p)
                        click.echo(f"    • {p.name:<40} {len(df):>8,} rows  ×  {len(df.columns)} cols")
                    except Exception:  # noqa: BLE001
                        click.echo(f"    • {p.name} (unreadable)")
            except ImportError:
                for p in sorted(parquets):
                    click.echo(f"    • {p.name}")
            click.echo()


# ---------------------------------------------------------------------------
# Main entry-point (also wired up via pyproject.toml console_scripts)
# ---------------------------------------------------------------------------

def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
