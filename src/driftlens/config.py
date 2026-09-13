"""Configuration module for DriftLens semantic drift detection engine."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# Find project root by walking up
def find_project_root() -> Path:
    curr = Path(__file__).resolve().parent
    while curr != curr.parent:
        if (curr / "pyproject.toml").exists() or (curr / ".git").exists():
            return curr
        curr = curr.parent
    return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = find_project_root()

# -----------------------------------------------------------------------------
# Scale Presets (10-Year Horizon: 2016–2025)
# -----------------------------------------------------------------------------
SCALE_PRESETS: Dict[str, Dict[str, Any]] = {
    "small": {
        "n_companies": 50,
        "years": 10,
        "start_year": 2016,
        "end_year": 2025,
        "chunk_sample_rate": 1.0,
        "min_cluster_size": 15,
        "min_samples": 4,
    },
    "medium": {
        "n_companies": 200,
        "years": 10,
        "start_year": 2016,
        "end_year": 2025,
        "chunk_sample_rate": 1.0,
        "min_cluster_size": 25,
        "min_samples": 5,
    },
    "full": {
        "n_companies": 500,
        "years": 10,
        "start_year": 2016,
        "end_year": 2025,
        "chunk_sample_rate": 1.0,
        "min_cluster_size": 35,
        "min_samples": 6,
    },
}

# -----------------------------------------------------------------------------
# Expanded Company Universe (50+ Leading Entities Across All 11 GICS Sectors)
# -----------------------------------------------------------------------------
DEFAULT_COMPANIES: List[Dict[str, str]] = [
    # 1. Technology
    {"cik": "0000320193", "ticker": "AAPL", "name": "Apple Inc.", "sector": "Information Technology"},
    {"cik": "0000789019", "ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Information Technology"},
    {"cik": "0001045810", "ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Information Technology"},
    {"cik": "0001652044", "ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services"},
    {"cik": "0001326801", "ticker": "META", "name": "Meta Platforms, Inc.", "sector": "Communication Services"},
    {"cik": "0001018724", "ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
    {"cik": "0001318605", "ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Consumer Discretionary"},
    {"cik": "0001108524", "ticker": "CRM", "name": "Salesforce, Inc.", "sector": "Information Technology"},
    {"cik": "0000796343", "ticker": "ADBE", "name": "Adobe Inc.", "sector": "Information Technology"},
    {"cik": "0000050863", "ticker": "INTC", "name": "Intel Corporation", "sector": "Information Technology"},
    {"cik": "0000002488", "ticker": "AMD", "name": "Advanced Micro Devices, Inc.", "sector": "Information Technology"},
    {"cik": "0001730168", "ticker": "AVGO", "name": "Broadcom Inc.", "sector": "Information Technology"},
    {"cik": "0001640147", "ticker": "SNOW", "name": "Snowflake Inc.", "sector": "Information Technology"},
    {"cik": "0001535527", "ticker": "CRWD", "name": "CrowdStrike Holdings, Inc.", "sector": "Information Technology"},
    {"cik": "0001321655", "ticker": "PLTR", "name": "Palantir Technologies Inc.", "sector": "Information Technology"},

    # 2. Healthcare & Life Sciences
    {"cik": "0000200406", "ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"cik": "0000078003", "ticker": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"cik": "0000731766", "ticker": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare"},
    {"cik": "0000001800", "ticker": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare"},
    {"cik": "0000310158", "ticker": "MRK", "name": "Merck & Co., Inc.", "sector": "Healthcare"},
    {"cik": "0000059478", "ticker": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare"},
    {"cik": "0001682852", "ticker": "MRNA", "name": "Moderna, Inc.", "sector": "Healthcare"},
    {"cik": "0001551152", "ticker": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare"},
    {"cik": "0000882095", "ticker": "GILD", "name": "Gilead Sciences, Inc.", "sector": "Healthcare"},
    {"cik": "0000092230", "ticker": "TMO", "name": "Thermo Fisher Scientific Inc.", "sector": "Healthcare"},

    # 3. Financials & Payments
    {"cik": "0000019617", "ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials"},
    {"cik": "0001067983", "ticker": "BRK.B", "name": "Berkshire Hathaway Inc.", "sector": "Financials"},
    {"cik": "0000070858", "ticker": "BAC", "name": "Bank of America Corp.", "sector": "Financials"},
    {"cik": "0000886982", "ticker": "GS", "name": "The Goldman Sachs Group, Inc.", "sector": "Financials"},
    {"cik": "0000895421", "ticker": "MS", "name": "Morgan Stanley", "sector": "Financials"},
    {"cik": "0001403161", "ticker": "V", "name": "Visa Inc.", "sector": "Financials"},
    {"cik": "0001141391", "ticker": "MA", "name": "Mastercard Incorporated", "sector": "Financials"},

    # 4. Industrials & Aerospace
    {"cik": "0000012927", "ticker": "BA", "name": "The Boeing Company", "sector": "Industrials"},
    {"cik": "0000018230", "ticker": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials"},
    {"cik": "0000040987", "ticker": "GE", "name": "General Electric Company", "sector": "Industrials"},
    {"cik": "0000773840", "ticker": "HON", "name": "Honeywell International Inc.", "sector": "Industrials"},
    {"cik": "0000066740", "ticker": "MMM", "name": "3M Company", "sector": "Industrials"},
    {"cik": "0000060086", "ticker": "LMT", "name": "Lockheed Martin Corporation", "sector": "Industrials"},
    {"cik": "0000097745", "ticker": "RTX", "name": "RTX Corporation", "sector": "Industrials"},

    # 5. Consumer Staples & Discretionary
    {"cik": "0000104169", "ticker": "WMT", "name": "Walmart Inc.", "sector": "Consumer Staples"},
    {"cik": "0000080424", "ticker": "PG", "name": "The Procter & Gamble Company", "sector": "Consumer Staples"},
    {"cik": "0000021344", "ticker": "KO", "name": "The Coca-Cola Company", "sector": "Consumer Staples"},
    {"cik": "0000077476", "ticker": "PEP", "name": "PepsiCo, Inc.", "sector": "Consumer Staples"},
    {"cik": "0000027419", "ticker": "COST", "name": "Costco Wholesale Corporation", "sector": "Consumer Staples"},
    {"cik": "0000320187", "ticker": "NKE", "name": "NIKE, Inc.", "sector": "Consumer Discretionary"},
    {"cik": "0000063908", "ticker": "MCD", "name": "McDonald's Corporation", "sector": "Consumer Discretionary"},
    {"cik": "0000354950", "ticker": "HD", "name": "The Home Depot, Inc.", "sector": "Consumer Discretionary"},

    # 6. Energy, Materials, Utilities, Real Estate
    {"cik": "0000034088", "ticker": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy"},
    {"cik": "0000093410", "ticker": "CVX", "name": "Chevron Corporation", "sector": "Energy"},
    {"cik": "0001163165", "ticker": "COP", "name": "ConocoPhillips", "sector": "Energy"},
    {"cik": "0000067492", "ticker": "LIN", "name": "Linde plc", "sector": "Materials"},
    {"cik": "0000753308", "ticker": "NEE", "name": "NextEra Energy, Inc.", "sector": "Utilities"},
    {"cik": "0001045625", "ticker": "AMT", "name": "American Tower Corporation", "sector": "Real Estate"},
]

# -----------------------------------------------------------------------------
# Base Directories
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class BasePaths:
    root: Path = PROJECT_ROOT
    bronze: Path = PROJECT_ROOT / "data" / "bronze"
    silver: Path = PROJECT_ROOT / "data" / "silver"
    gold: Path = PROJECT_ROOT / "data" / "gold"
    sample: Path = PROJECT_ROOT / "data" / "sample"
    overrides: Path = PROJECT_ROOT / "data" / "overrides"

    def ensure_all(self) -> None:
        for p in (self.bronze, self.silver, self.gold, self.sample, self.overrides):
            p.mkdir(parents=True, exist_ok=True)

PATHS = BasePaths()

# -----------------------------------------------------------------------------
# Service & Client Configurations
# -----------------------------------------------------------------------------
EDGAR_CONFIG = {
    "user_agent": "DriftLens research-project suryatejam2312@gmail.com",
    "min_interval": 0.125,  # 8 requests/sec
    "max_retries": 5,
    "bulk_tickers_url": "https://www.sec.gov/files/company_tickers.json",
    "bulk_submissions_url": "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip",
    "bulk_facts_url": "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/companyfacts.zip",
    "data_base_url": "https://data.sec.gov",
}

EMBEDDING_CONFIG = {
    "model_name": "BAAI/bge-small-en-v1.5",
    "fallback_model": "all-MiniLM-L6-v2",
    "batch_size": 128,
    "normalize_l2": True,
}

DRIFT_METRICS_CONFIG = {
    "materiality_threshold": 0.05,
    "centroid_drift_threshold": 0.25,
    "wasserstein_distance_weight": 0.4,
    "bootstrap_permutations": 100,
    "significance_alpha": 0.05,
    "boilerplate_penalty_threshold": 0.70,
}

OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:7b-instruct",
    "fallback_model": "llama3.1:8b-instruct",
    "timeout": 120,
}
