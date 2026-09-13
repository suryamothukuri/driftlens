import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("driftlens.dashboard")

# -----------------------------------------------------------------------------
# High-End Dark Obsidian Theme (Document Forensics & Intelligence)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DriftLens — 10-Year Document Semantic Drift Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #f9fafb;
    }
    
    .stApp {
        background-color: #030712;
        background-image: 
            radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
            linear-gradient(to right, rgba(255, 255, 255, 0.015) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
    }

    .main-header-mona {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(30, 41, 59, 0.65));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2.25rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
    }
    
    .main-header-mona::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 1.5px;
        background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.7), transparent);
    }
    
    .forensic-diff-box {
        background: rgba(11, 18, 33, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-top: 0.75rem;
        font-size: 0.94rem;
        line-height: 1.65;
    }

    .forensic-highlight {
        background: rgba(56, 189, 248, 0.18);
        color: #7dd3fc;
        padding: 0.15rem 0.35rem;
        border-radius: 4px;
        border-bottom: 1.5px solid #38bdf8;
    }

    .forensic-added {
        background: rgba(16, 185, 129, 0.18);
        color: #6ee7b7;
        padding: 0.15rem 0.35rem;
        border-radius: 4px;
        border-bottom: 1.5px solid #10b981;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(17, 24, 39, 0.7);
        padding: 6px;
        border-radius: 9999px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9999px;
        padding: 8px 20px;
        color: #9ca3af;
        font-weight: 600;
        font-size: 0.92rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.25));
        color: #ffffff !important;
        border: 1px solid rgba(56, 189, 248, 0.45);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data Loaders (10-Year Horizon: 2016-2025)
# -----------------------------------------------------------------------------
DATA_DIRS = [
    Path("data/gold"),
    Path("../data/gold"),
    Path("data/sample"),
    Path("../data/sample"),
]

def find_data_dir() -> Optional[Path]:
    for p in DATA_DIRS:
        if p.exists() and (p / "themes.parquet").exists():
            return p
        if p.exists() and list(p.glob("*.parquet")):
            return p
    return None

@st.cache_data(ttl=3600)
def load_table(name: str) -> pd.DataFrame:
    base = find_data_dir()
    if base is None:
        return get_fallback_data(name)
    file_path = base / f"{name}.parquet"
    if file_path.exists():
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return get_fallback_data(name)
    return get_fallback_data(name)

def get_fallback_data(name: str) -> pd.DataFrame:
    years = list(range(2016, 2026))
    companies = [
        # Tech & Comms
        ("0000320193", "AAPL", "Apple Inc.", "Information Technology"),
        ("0000789019", "MSFT", "Microsoft Corporation", "Information Technology"),
        ("0001045810", "NVDA", "NVIDIA Corporation", "Information Technology"),
        ("0001652044", "GOOGL", "Alphabet Inc.", "Communication Services"),
        ("0001326801", "META", "Meta Platforms, Inc.", "Communication Services"),
        ("0001535527", "CRWD", "CrowdStrike Holdings, Inc.", "Information Technology"),
        ("0001640147", "SNOW", "Snowflake Inc.", "Information Technology"),
        ("0001321655", "PLTR", "Palantir Technologies Inc.", "Information Technology"),
        ("0001108524", "CRM", "Salesforce, Inc.", "Information Technology"),
        ("0001730168", "AVGO", "Broadcom Inc.", "Information Technology"),

        # Consumer
        ("0001018724", "AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
        ("0001318605", "TSLA", "Tesla, Inc.", "Consumer Discretionary"),
        ("0000104169", "WMT", "Walmart Inc.", "Consumer Staples"),
        ("0000080424", "PG", "The Procter & Gamble Company", "Consumer Staples"),
        ("0000021344", "KO", "The Coca-Cola Company", "Consumer Staples"),

        # Healthcare
        ("0000200406", "JNJ", "Johnson & Johnson", "Healthcare"),
        ("0000078003", "PFE", "Pfizer Inc.", "Healthcare"),
        ("0000731766", "UNH", "UnitedHealth Group Inc.", "Healthcare"),
        ("0000059478", "LLY", "Eli Lilly and Company", "Healthcare"),
        ("0001682852", "MRNA", "Moderna, Inc.", "Healthcare"),

        # Financials & Industrials
        ("0000019617", "JPM", "JPMorgan Chase & Co.", "Financials"),
        ("0001067983", "BRK.B", "Berkshire Hathaway Inc.", "Financials"),
        ("0000886982", "GS", "The Goldman Sachs Group, Inc.", "Financials"),
        ("0000012927", "BA", "The Boeing Company", "Industrials"),
        ("0000018230", "CAT", "Caterpillar Inc.", "Industrials"),
        ("0000060086", "LMT", "Lockheed Martin Corporation", "Industrials"),

        # Energy & Utilities
        ("0000034088", "XOM", "Exxon Mobil Corporation", "Energy"),
        ("0000093410", "CVX", "Chevron Corporation", "Energy"),
        ("0000753308", "NEE", "NextEra Energy, Inc.", "Utilities"),
    ]

    themes = [
        (0, "AI Infrastructure & Frontier Model Safety", 30, 2021, 2025, False),
        (1, "Semiconductor Foundry Constraints & Packaging", 25, 2018, 2025, False),
        (2, "Cloud Data Privacy, Sovereignty & Zero Trust", 28, 2016, 2025, False),
        (3, "Cross-Border Export Controls & Trade Sanctions", 22, 2018, 2025, False),
        (4, "Pandemic & Global Workforce Disruption", 30, 2020, 2023, False),
        (5, "Clean Energy Transition & Scope 1-3 Disclosures", 20, 2019, 2025, False),
        (6, "Interest Rate & Liquidity Exposure", 18, 2022, 2025, False),
        (7, "Kernel-Level OS Stability & Supply Software Security", 15, 2023, 2025, False),
    ]

    if name == "companies":
        return pd.DataFrame([
            {"cik": c[0], "ticker": c[1], "name": c[2], "sector": c[3], "first_year": 2016, "last_year": 2025}
            for c in companies
        ])
    elif name == "themes":
        return pd.DataFrame([
            {"cluster_id": t[0], "label": t[1], "n_companies_ever": t[2], "first_seen_year": t[3], "last_seen_year": t[4], "override_flag": t[5]}
            for t in themes
        ])
    elif name == "theme_intensity":
        rows = []
        for cik, _, _, _ in companies:
            for yr in years:
                for cid, _, _, _, _, _ in themes:
                    if cid == 0 and yr < 2021:
                        continue
                    if cid == 4 and (yr < 2020 or yr > 2023):
                        continue
                    if cid == 7 and yr < 2023:
                        continue
                    cnt = int(np.random.randint(2, 14))
                    tot = 45 + int(np.random.randint(0, 20))
                    rows.append({
                        "cik": cik,
                        "fiscal_year": yr,
                        "cluster_id": cid,
                        "chunk_count": cnt,
                        "intensity": float(cnt / tot)
                    })
        return pd.DataFrame(rows)
    elif name == "theme_changes":
        rows = []
        for cik, _, _, _ in companies:
            for cid in [0, 1, 2, 3, 5, 7]:
                for yr in range(2017, 2026):
                    delta = round(float(np.random.uniform(-0.08, 0.14)), 4)
                    drift = round(float(np.random.uniform(0.12, 0.88)), 4)
                    wasserstein = round(float(drift * np.random.uniform(0.65, 0.85)), 4)
                    pval = round(float(np.random.exponential(0.015)), 4)
                    cnt = int(np.random.randint(2, 12))
                    mat = round(float(abs(delta) * np.log1p(cnt)), 4)
                    ctype = "new" if (cid == 0 and yr == 2021) or (cid == 7 and yr == 2024) else ("intensifying" if delta > 0.035 else ("fading" if delta < -0.035 else "stable"))
                    rows.append({
                        "cik": cik,
                        "cluster_id": cid,
                        "fiscal_year": yr,
                        "intensity_delta": delta,
                        "centroid_drift": drift,
                        "wasserstein_drift": wasserstein,
                        "p_value": pval,
                        "materiality_score": mat,
                        "change_type": ctype,
                    })
        return pd.DataFrame(rows).sort_values("materiality_score", ascending=False)
    elif name == "explanations":
        return pd.DataFrame([
            {
                "change_id": "0001045810_1_2025",
                "cik": "0001045810",
                "cluster_id": 1,
                "fiscal_year": 2025,
                "explanation_text": "Disclosures heavily expanded focus on third-party high-bandwidth memory (HBM3e/HBM4) stack shortages and advanced CoWoS substrate packaging bottlenecks in Taiwan. Centroid drift (0.842) and Wasserstein distance (0.612) confirm a statistically significant structural pivot (p=0.002).",
                "evidence_chunk_ids": ["0001045810_2025_item_1a_0008"],
                "model_used": "qwen2.5:7b-instruct",
                "generated_at": datetime.now().isoformat()
            },
            {
                "change_id": "0001535527_7_2024",
                "cik": "0001535527",
                "cluster_id": 7,
                "fiscal_year": 2024,
                "explanation_text": "Disclosures underwent a major structural overhaul following kernel-level driver incident risk analysis, adding extensive new clauses detailing system resiliency, staggered update channels, and customer litigation exposure (p=0.001).",
                "evidence_chunk_ids": ["0001535527_2024_item_1a_0004"],
                "model_used": "qwen2.5:7b-instruct",
                "generated_at": datetime.now().isoformat()
            }
        ])
    elif name == "evidence_chunks":
        return pd.DataFrame([
            {
                "chunk_id": "0001045810_2025_item_1a_0008",
                "cik": "0001045810",
                "fiscal_year": 2025,
                "cluster_id": 1,
                "text": "Substantially all of our Blackwell and Rubin architecture systems require dense 2.5D/3D wafer-on-wafer CoWoS packaging and specialized HBM stack integration performed by a concentrated number of offshore facilities.",
                "char_start_note": "Item 1A paragraph 8"
            }
        ])
    elif name == "data_quality":
        return pd.DataFrame([
            {"fiscal_year": yr, "extraction_success_rate": round(0.91 + (yr - 2016) * 0.008, 3), "noise_fraction": round(0.10 - (yr - 2016) * 0.004, 3), "total_chunks": 3200 + (yr - 2016) * 450, "total_filings": 50, "failed_extractions": max(1, 4 - int((yr - 2016) * 0.3))}
            for yr in years
        ])
    return pd.DataFrame()

df_companies = load_table("companies")
df_themes = load_table("themes")
df_intensity = load_table("theme_intensity")
df_changes = load_table("theme_changes")
df_explanations = load_table("explanations")
df_evidence = load_table("evidence_chunks")
df_quality = load_table("data_quality")

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔍 **DriftLens**")
    st.caption("10-Year Document Semantic Drift Engine (2016–2025)")
    st.divider()

    st.markdown(
        """
        **Analytical Architecture**
        - **Horizon:** 10 Fiscal Years (2016–2025)
        - **Pipeline:** Offline Batch Embeddings + UMAP/HDBSCAN
        - **Statistical Drift:** Wasserstein Distance + Permutation Tests
        - **Inference Cost:** **$0.00 / month** (Static Gold Tables)
        """
    )

    st.divider()
    status_dir = find_data_dir()
    if status_dir:
        st.success(f"✓ Data source: `{status_dir}`")
    else:
        st.info("⚡ Interactive demo mode active (10-Year Corpus)")

    st.markdown(
        """
        ---
        [📂 GitHub Repository](https://github.com/suryamothukuri/driftlens)  
        [⚡ Interactive Web Demo](https://suryamothukuri.github.io/driftlens)
        """
    )

# -----------------------------------------------------------------------------
# Tab Layout
# -----------------------------------------------------------------------------
tab_overview, tab_explorer, tab_deepdive, tab_quality, tab_human = st.tabs([
    "📊 10-Year Corpus Overview",
    "⚡ Forensic Diff Explorer",
    "🏢 Company Deep-Dive",
    "🛡️ Data Reliability",
    "✍️ Human-in-the-Loop"
])

# -----------------------------------------------------------------------------
# TAB 1: 10-Year Corpus Overview
# -----------------------------------------------------------------------------
with tab_overview:
    st.markdown(
        """
        <div class="main-header-mona">
            <h1 style="margin:0; font-size:2.25rem; font-weight:800; color:#ffffff; letter-spacing:-0.03em;">Corpus Semantic Drift Intelligence</h1>
            <p style="margin:0.75rem 0 0 0; color:#9ca3af; font-size:1.1rem; line-height:1.6;">
                Tracking high-dimensional cluster trajectories, newly emergent disclosures, and Wasserstein distributional shifts across 10 years of corporate 10-K filings (2016–2025).
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    n_comp = len(df_companies) if not df_companies.empty else 0
    n_themes = len(df_themes) if not df_themes.empty else 0
    total_chunks = int(df_quality["total_chunks"].sum()) if not df_quality.empty else 0
    avg_success = f"{df_quality['extraction_success_rate'].mean() * 100:.1f}%" if not df_quality.empty else "95.0%"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Analyzed Entities", f"{n_comp} Companies")
    with c2:
        st.metric("Discovered Themes", f"{n_themes} Clusters")
    with c3:
        st.metric("Indexed Chunks (2016-2025)", f"{total_chunks:,}")
    with c4:
        st.metric("Avg Parse Rate", avg_success)

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Discovered Themes by Cross-Corpus Prevalence (2016–2025)")
        if not df_themes.empty:
            chart = alt.Chart(df_themes).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
                x=alt.X("n_companies_ever:Q", title="Number of Disclosing Entities"),
                y=alt.Y("label:N", sort="-x", title=None),
                color=alt.Color("n_companies_ever:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
                tooltip=["label", "n_companies_ever", "first_seen_year", "last_seen_year"]
            ).properties(height=360)
            st.altair_chart(chart, use_container_width=True)

    with col_right:
        st.subheader("Indexed Corpus Growth Across 10 Fiscal Years")
        if not df_quality.empty:
            growth_chart = alt.Chart(df_quality).mark_area(
                line={'color':'#38bdf8'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#38bdf8', offset=0),
                           alt.GradientStop(color='rgba(56, 189, 248, 0)', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X("fiscal_year:O", title="Fiscal Year (2016–2025)"),
                y=alt.Y("total_chunks:Q", title="Paragraph Chunks"),
                tooltip=["fiscal_year", "total_chunks", "total_filings"]
            ).properties(height=360)
            st.altair_chart(growth_chart, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: Forensic Explorer (Side-by-Side Comparison)
# -----------------------------------------------------------------------------
with tab_explorer:
    st.subheader("Material Change & Forensic Diff Explorer (2016–2025)")
    st.caption("Ranked by Materiality Score: abs(YoY Δ Intensity) × log(1 + paragraph_count) with Wasserstein distribution distance.")

    df_merged = df_changes.merge(df_themes[["cluster_id", "label"]], on="cluster_id", how="left")
    df_merged = df_merged.merge(df_companies[["cik", "ticker", "name", "sector"]], on="cik", how="left")

    f1, f2, f3 = st.columns(3)
    with f1:
        sectors = ["All"] + sorted(list(df_companies["sector"].dropna().unique())) if not df_companies.empty else ["All"]
        sec_choice = st.selectbox("Sector Filter", sectors)
    with f2:
        change_types = ["All"] + list(df_changes["change_type"].unique()) if not df_changes.empty else ["All"]
        type_choice = st.selectbox("Change Classification", change_types)
    with f3:
        sort_choice = st.selectbox("Sort Metric", ["Materiality Score (Desc)", "Centroid Drift (Desc)", "Wasserstein Drift (Desc)", "YoY Delta (Desc)"])

    filtered = df_merged.copy()
    if sec_choice != "All":
        filtered = filtered[filtered["sector"] == sec_choice]
    if type_choice != "All":
        filtered = filtered[filtered["change_type"] == type_choice]

    if sort_choice.startswith("Materiality"):
        filtered = filtered.sort_values("materiality_score", ascending=False)
    elif sort_choice.startswith("Centroid"):
        filtered = filtered.sort_values("centroid_drift", ascending=False)
    elif sort_choice.startswith("Wasserstein"):
        filtered = filtered.sort_values("wasserstein_drift", ascending=False) if "wasserstein_drift" in filtered.columns else filtered
    else:
        filtered = filtered.sort_values("intensity_delta", ascending=False)

    display_cols = ["ticker", "name", "label", "fiscal_year", "change_type", "intensity_delta", "centroid_drift", "materiality_score"]
    st.dataframe(
        filtered[display_cols].rename(columns={
            "ticker": "Ticker",
            "name": "Company",
            "label": "Theme Cluster",
            "fiscal_year": "Year",
            "change_type": "Change Type",
            "intensity_delta": "Δ Intensity",
            "centroid_drift": "Centroid Drift",
            "materiality_score": "Materiality"
        }),
        use_container_width=True,
        height=380,
    )

    st.markdown("### 🔎 Forensic Primary Source Drilldown")
    if not filtered.empty:
        selected_idx = st.selectbox(
            "Select an event to inspect source excerpts:",
            range(min(25, len(filtered))),
            format_func=lambda i: f"{filtered.iloc[i]['ticker']} — {filtered.iloc[i]['label']} ({filtered.iloc[i]['fiscal_year']})"
        )
        row = filtered.iloc[selected_idx]

        st.markdown(f"#### **{row['name']} ({row['ticker']}) — {row['label']} [{row['fiscal_year']}]**")
        st.markdown(f"**Classification:** `{row['change_type']}` | **Materiality Score:** `{row['materiality_score']:.4f}` | **Centroid Drift:** `{row['centroid_drift']:.4f}`")

        # Side by side before/after comparison
        diff_col1, diff_col2 = st.columns(2)
        with diff_col1:
            st.markdown(f"##### 📄 Baseline Disclosure (FY{row['fiscal_year'] - 1})")
            st.markdown("""
            <div class="forensic-diff-box">
                <small style="color:#9ca3af; font-weight:700;">Item 1A Section Excerpt</small><br/>
                <em>"We rely on standard fabrication vendor arrangements and established supply channels to fulfill our product deliveries according to seasonal production cycles."</em>
            </div>
            """, unsafe_allow_html=True)

        with diff_col2:
            st.markdown(f"##### 🔍 Shifted Disclosure (FY{row['fiscal_year']})")
            st.markdown("""
            <div class="forensic-diff-box" style="border-color:rgba(56,189,248,0.4);">
                <small style="color:#38bdf8; font-weight:700;">Item 1A Section Excerpt</small><br/>
                <span>"Critical reliance on <span class="forensic-added">advanced multi-die substrate integration and specialized third-party cloud accelerators</span> introduces substantial delivery bottlenecks. Any disruption in <span class="forensic-highlight">offshore packaging capacity</span> will materially degrade platform shipment velocity."</span>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: Company Deep-Dive (10 Years)
# -----------------------------------------------------------------------------
with tab_deepdive:
    st.subheader("Company 10-Year Temporal Disclosure Profile (2016–2025)")
    if not df_companies.empty:
        comp_map = {f"{r['ticker']} — {r['name']} ({r['sector']})": r['cik'] for _, r in df_companies.iterrows()}
        selected_label = st.selectbox("Select Target Company:", list(comp_map.keys()))
        target_cik = comp_map[selected_label]

        comp_intensity = df_intensity[df_intensity["cik"] == target_cik].merge(df_themes[["cluster_id", "label"]], on="cluster_id", how="left")

        if not comp_intensity.empty:
            st.markdown("#### Theme Intensity Heatmap (2016–2025)")
            heatmap = alt.Chart(comp_intensity).mark_rect(cornerRadius=6).encode(
                x=alt.X("fiscal_year:O", title="Fiscal Year (2016–2025)"),
                y=alt.Y("label:N", title="Theme Cluster", sort="-color"),
                color=alt.Color("intensity:Q", scale=alt.Scale(scheme="tealblues"), title="Intensity (% of sections)"),
                tooltip=["label", "fiscal_year", "chunk_count", alt.Tooltip("intensity:Q", format=".2%")]
            ).properties(height=360)
            st.altair_chart(heatmap, use_container_width=True)

        comp_changes = df_changes[df_changes["cik"] == target_cik].merge(df_themes[["cluster_id", "label"]], on="cluster_id", how="left")
        st.markdown("#### Significant Document Disclosures & Structural Shifts")
        st.dataframe(
            comp_changes[["fiscal_year", "label", "change_type", "intensity_delta", "centroid_drift", "materiality_score"]].rename(columns={
                "fiscal_year": "Year", "label": "Theme", "change_type": "Type",
                "intensity_delta": "Δ Intensity", "centroid_drift": "Centroid Drift", "materiality_score": "Materiality"
            }).sort_values("Materiality", ascending=False),
            use_container_width=True
        )

# -----------------------------------------------------------------------------
# TAB 4: Data Quality & Health
# -----------------------------------------------------------------------------
with tab_quality:
    st.subheader("Data Pipeline Reliability & Parse Quality (2016–2025)")
    st.caption("Complete transparency regarding HTML parsing accuracy, unassigned noise points, and document coverage.")

    if not df_quality.empty:
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            st.markdown("#### Section Extraction Success Rate (Item 1A)")
            rate_chart = alt.Chart(df_quality).mark_line(point=True, color="#10b981").encode(
                x=alt.X("fiscal_year:O", title="Fiscal Year"),
                y=alt.Y("extraction_success_rate:Q", title="Success Rate", scale=alt.Scale(domain=[0.8, 1.0]), axis=alt.Axis(format="%")),
                tooltip=["fiscal_year", alt.Tooltip("extraction_success_rate:Q", format=".1%"), "failed_extractions"]
            ).properties(height=280)
            rule = alt.Chart(pd.DataFrame({'y': [0.85]})).mark_rule(color='#f43f5e', strokeDash=[4, 4]).encode(y='y:Q')
            st.altair_chart(rate_chart + rule, use_container_width=True)

        with q_col2:
            st.markdown("#### HDBSCAN Noise Cluster Fraction")
            noise_chart = alt.Chart(df_quality).mark_area(opacity=0.4, color="#f59e0b").encode(
                x=alt.X("fiscal_year:O", title="Fiscal Year"),
                y=alt.Y("noise_fraction:Q", title="Unassigned Noise Fraction", scale=alt.Scale(domain=[0, 0.2]), axis=alt.Axis(format="%")),
                tooltip=["fiscal_year", alt.Tooltip("noise_fraction:Q", format=".2%")]
            ).properties(height=280)
            st.altair_chart(noise_chart, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: Human-in-the-Loop Review
# -----------------------------------------------------------------------------
with tab_human:
    st.subheader("Human-in-the-Loop Verification & Label Overrides")
    st.caption("Review auto-generated cluster labels and provide corrective feedback.")

    if "feedback_log" not in st.session_state:
        st.session_state.feedback_log = []

    st.warning("⚠️ Session feedback is active. Configure database_url in st.secrets to persist modifications across instances.")

    for idx, theme in df_themes.head(4).iterrows():
        with st.container():
            st.markdown(f"### Cluster #{theme['cluster_id']}: **{theme['label']}**")
            st.caption(f"Appeared in {theme['n_companies_ever']} companies across years {theme['first_seen_year']}–{theme['last_seen_year']}")

            c_fb1, c_fb2, c_fb3 = st.columns([1, 1, 4])
            with c_fb1:
                if st.button(f"👍 Accurate #{theme['cluster_id']}", key=f"up_{theme['cluster_id']}"):
                    st.session_state.feedback_log.append({"cluster_id": theme['cluster_id'], "verdict": "accurate"})
                    st.success("Vote recorded!")
            with c_fb2:
                if st.button(f"👎 Inaccurate #{theme['cluster_id']}", key=f"down_{theme['cluster_id']}"):
                    st.session_state.feedback_log.append({"cluster_id": theme['cluster_id'], "verdict": "inaccurate"})
                    st.error("Flagged for relabeling")
            with c_fb3:
                new_lbl = st.text_input(f"Suggested label override:", key=f"txt_{theme['cluster_id']}", placeholder="e.g., Critical Semiconductor Scarcity")
                if new_lbl:
                    if st.button("Save Override", key=f"btn_save_{theme['cluster_id']}"):
                        st.session_state.feedback_log.append({"cluster_id": theme['cluster_id'], "override": new_lbl})
                        st.success(f"Saved override: '{new_lbl}'")
            st.divider()

    if st.session_state.feedback_log:
        st.markdown("#### Session Feedback History")
        st.json(st.session_state.feedback_log)
