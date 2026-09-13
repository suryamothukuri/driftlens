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
# High-End Dark Obsidian Theme (GitHub Next / Linear aesthetic)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DriftLens — Document Intelligence Dashboard",
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
        background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px;
    }

    .main-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.65));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2.25rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.6), transparent);
    }
    
    .metric-card-mona {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease;
    }
    
    .evidence-box-mona {
        background: rgba(11, 15, 25, 0.8);
        border-left: 3px solid #38bdf8;
        padding: 1.25rem 1.5rem;
        border-radius: 0 12px 12px 0;
        margin-top: 1rem;
        font-size: 0.95rem;
        line-height: 1.65;
        border-top: 1px solid rgba(255, 255, 255, 0.04);
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        border-right: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    /* Tabs custom styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(17, 24, 39, 0.6);
        padding: 6px;
        border-radius: 9999px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9999px;
        padding: 8px 18px;
        color: #9ca3af;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.25));
        color: #ffffff !important;
        border: 1px solid rgba(56, 189, 248, 0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data Loaders
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
    years = [2019, 2020, 2021, 2022, 2023]
    companies = [
        ("0000320193", "AAPL", "Apple Inc.", "Technology"),
        ("0000789019", "MSFT", "Microsoft Corporation", "Technology"),
        ("0001652044", "GOOGL", "Alphabet Inc.", "Technology"),
        ("0001045810", "NVDA", "NVIDIA Corporation", "Technology"),
        ("0000200406", "JNJ", "Johnson & Johnson", "Healthcare"),
        ("0000078003", "PFE", "Pfizer Inc.", "Healthcare"),
        ("0000012927", "BA", "The Boeing Company", "Industrials"),
        ("0001018724", "AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
        ("0000034088", "XOM", "Exxon Mobil Corporation", "Energy"),
        ("0000019617", "JPM", "JPMorgan Chase & Co.", "Financials"),
    ]
    themes = [
        (0, "AI Infrastructure & Frontier Model Safety", 10, 2021, 2023, False),
        (1, "Advanced Semiconductor Foundry Constraints", 8, 2019, 2023, False),
        (2, "Cloud Data Privacy & Cross-Border Sovereignty", 9, 2019, 2023, False),
        (3, "Cross-Border Regulatory & Export Controls", 7, 2020, 2023, False),
        (4, "Pandemic & Global Workforce Disruption", 10, 2020, 2022, False),
        (5, "Clean Energy Transition & Scope Disclosures", 6, 2021, 2023, False),
        (6, "Interest Rate & Liquidity Exposure", 5, 2022, 2023, False),
    ]

    if name == "companies":
        return pd.DataFrame([
            {"cik": c[0], "ticker": c[1], "name": c[2], "sector": c[3], "first_year": 2019, "last_year": 2023}
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
                    if cid == 4 and yr > 2022:
                        continue
                    cnt = int(np.random.randint(1, 12))
                    tot = 40 + int(np.random.randint(0, 15))
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
            for cid in [0, 1, 2, 3, 4, 5]:
                for yr in [2020, 2021, 2022, 2023]:
                    delta = round(float(np.random.uniform(-0.08, 0.12)), 4)
                    drift = round(float(np.random.uniform(0.1, 0.85)), 4)
                    cnt = int(np.random.randint(2, 10))
                    mat = round(float(abs(delta) * np.log1p(cnt)), 4)
                    ctype = "new" if (cid == 0 and yr == 2021) else ("intensifying" if delta > 0.03 else ("fading" if delta < -0.03 else "stable"))
                    rows.append({
                        "cik": cik,
                        "cluster_id": cid,
                        "fiscal_year": yr,
                        "intensity_delta": delta,
                        "centroid_drift": drift,
                        "materiality_score": mat,
                        "change_type": ctype,
                    })
        return pd.DataFrame(rows).sort_values("materiality_score", ascending=False)
    elif name == "explanations":
        return pd.DataFrame([
            {
                "change_id": "0000320193_0_2023",
                "cik": "0000320193",
                "cluster_id": 0,
                "fiscal_year": 2023,
                "explanation_text": "The company dramatically expanded disclosures regarding deep learning model safety, compute cluster dependencies, and generative AI service reliability in FY2023. Centroid drift (0.742) highlights a structural pivot from algorithmic recommendations to proprietary foundation models.",
                "evidence_chunk_ids": ["0000320193_2023_item_1a_0012", "0000320193_2023_item_1a_0014"],
                "model_used": "qwen2.5:7b-instruct",
                "generated_at": datetime.now().isoformat()
            },
            {
                "change_id": "0001045810_1_2022",
                "cik": "0001045810",
                "cluster_id": 1,
                "fiscal_year": 2022,
                "explanation_text": "Disclosures in FY2022 underscored severe foundry capacity constraints and packaging bottlenecks. Centroid drift reveals that risk phrasing shifted from generalized fab utilization to specific geographical wafer fabrication concentration.",
                "evidence_chunk_ids": ["0001045810_2022_item_1a_0008"],
                "model_used": "qwen2.5:7b-instruct",
                "generated_at": datetime.now().isoformat()
            }
        ])
    elif name == "evidence_chunks":
        return pd.DataFrame([
            {
                "chunk_id": "0000320193_2023_item_1a_0012",
                "cik": "0000320193",
                "fiscal_year": 2023,
                "cluster_id": 0,
                "text": "Rapid development and deployment of complex machine learning systems introduce unique operational and reputational challenges. Any failure in our generative AI safety guardrails or unforeseen latency across distributed accelerator clusters could adversely impact user adoption and enterprise customer trust.",
                "char_start_note": "Item 1A paragraph 12"
            },
            {
                "chunk_id": "0000320193_2023_item_1a_0014",
                "cik": "0000320193",
                "fiscal_year": 2023,
                "cluster_id": 0,
                "text": "We rely on specialized third-party cloud infrastructure and proprietary silicon hardware to train and serve frontier neural networks. Supply shortages or architectural changes by key compute vendors may hinder our ability to scale intelligent features across operating system releases.",
                "char_start_note": "Item 1A paragraph 14"
            },
            {
                "chunk_id": "0001045810_2022_item_1a_0008",
                "cik": "0001045810",
                "fiscal_year": 2022,
                "cluster_id": 1,
                "text": "Substantially all of our advanced node GPUs and network processors are manufactured by a concentrated number of independent foundries located in Asia. Any disruption to advanced packaging, substrate availability, or regional trade transport can materially delay product launches.",
                "char_start_note": "Item 1A paragraph 8"
            }
        ])
    elif name == "data_quality":
        return pd.DataFrame([
            {"fiscal_year": 2019, "extraction_success_rate": 0.92, "noise_fraction": 0.08, "total_chunks": 4200, "total_filings": 30, "failed_extractions": 2},
            {"fiscal_year": 2020, "extraction_success_rate": 0.94, "noise_fraction": 0.09, "total_chunks": 4850, "total_filings": 30, "failed_extractions": 2},
            {"fiscal_year": 2021, "extraction_success_rate": 0.96, "noise_fraction": 0.07, "total_chunks": 5100, "total_filings": 30, "failed_extractions": 1},
            {"fiscal_year": 2022, "extraction_success_rate": 0.95, "noise_fraction": 0.08, "total_chunks": 5300, "total_filings": 30, "failed_extractions": 1},
            {"fiscal_year": 2023, "extraction_success_rate": 0.97, "noise_fraction": 0.06, "total_chunks": 5620, "total_filings": 30, "failed_extractions": 1},
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
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔍 **DriftLens**")
    st.caption("Document Semantic Drift & Intelligence Engine")
    st.divider()

    st.markdown(
        """
        **Architecture Summary**
        - **Pipeline:** Offline Batch Embeddings + UMAP/HDBSCAN
        - **Inference Cost:** **$0.00 / month** (Static Parquet Artifacts)
        - **Drift Metric:** YoY Intensity Delta × Centroid Drift Cosine
        """
    )

    st.divider()
    status_dir = find_data_dir()
    if status_dir:
        st.success(f"✓ Data source: `{status_dir}`")
    else:
        st.info("⚡ Running interactive demo mode")

    st.markdown(
        """
        ---
        [📂 GitHub Repository](https://github.com/suryamothukuri/driftlens)  
        [⚡ Interactive Web Demo](https://suryamothukuri.github.io/driftlens)
        """
    )

# -----------------------------------------------------------------------------
# Main Content Tabs
# -----------------------------------------------------------------------------
tab_overview, tab_explorer, tab_deepdive, tab_quality, tab_human = st.tabs([
    "📊 Corpus Overview",
    "⚡ Theme Explorer",
    "🏢 Company Deep-Dive",
    "🛡️ Data Quality & Health",
    "✍️ Human-in-the-Loop"
])

# -----------------------------------------------------------------------------
# TAB 1: Corpus Overview
# -----------------------------------------------------------------------------
with tab_overview:
    st.markdown(
        """
        <div class="main-header">
            <h1 style="margin:0; font-size:2.25rem; font-weight:800; color:#ffffff; letter-spacing:-0.03em;">Corpus Semantic Drift Intelligence</h1>
            <p style="margin:0.75rem 0 0 0; color:#9ca3af; font-size:1.1rem; line-height:1.6;">
                Tracking high-dimensional cluster trajectories, newly emergent disclosures, and structural phrasing evolution across versioned document histories.
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
        st.metric("Indexed Chunks", f"{total_chunks:,}")
    with c4:
        st.metric("Avg Parse Rate", avg_success)

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Discovered Themes by Cross-Corpus Prevalence")
        if not df_themes.empty:
            chart = alt.Chart(df_themes).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
                x=alt.X("n_companies_ever:Q", title="Number of Disclosing Entities"),
                y=alt.Y("label:N", sort="-x", title=None),
                color=alt.Color("n_companies_ever:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
                tooltip=["label", "n_companies_ever", "first_seen_year", "last_seen_year"]
            ).properties(height=340)
            st.altair_chart(chart, use_container_width=True)

    with col_right:
        st.subheader("Indexed Corpus Growth Across Versions")
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
                x=alt.X("fiscal_year:O", title="Fiscal Year"),
                y=alt.Y("total_chunks:Q", title="Paragraph Chunks"),
                tooltip=["fiscal_year", "total_chunks", "total_filings"]
            ).properties(height=340)
            st.altair_chart(growth_chart, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: Theme Explorer
# -----------------------------------------------------------------------------
with tab_explorer:
    st.subheader("Material Change & Drift Detection Explorer")
    st.caption("Ranked by Materiality Score: abs(YoY Δ Intensity) × log(1 + paragraph_count)")

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
        sort_choice = st.selectbox("Sort Metric", ["Materiality Score (Desc)", "Centroid Drift (Desc)", "YoY Delta (Desc)"])

    filtered = df_merged.copy()
    if sec_choice != "All":
        filtered = filtered[filtered["sector"] == sec_choice]
    if type_choice != "All":
        filtered = filtered[filtered["change_type"] == type_choice]

    if sort_choice.startswith("Materiality"):
        filtered = filtered.sort_values("materiality_score", ascending=False)
    elif sort_choice.startswith("Centroid"):
        filtered = filtered.sort_values("centroid_drift", ascending=False)
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

    st.markdown("### 🔎 Grounded Explanation & Evidence Excerpt")
    if not filtered.empty:
        selected_idx = st.selectbox(
            "Select an event to inspect source excerpts:",
            range(min(20, len(filtered))),
            format_func=lambda i: f"{filtered.iloc[i]['ticker']} — {filtered.iloc[i]['label']} ({filtered.iloc[i]['fiscal_year']})"
        )
        row = filtered.iloc[selected_idx]

        exp_match = df_explanations[
            (df_explanations["cik"] == row["cik"]) &
            (df_explanations["cluster_id"] == row["cluster_id"]) &
            (df_explanations["fiscal_year"] == row["fiscal_year"])
        ]

        st.markdown(f"#### **{row['name']} ({row['ticker']}) — {row['label']} [{row['fiscal_year']}]**")
        st.markdown(f"**Classification:** `{row['change_type']}` | **Materiality Score:** `{row['materiality_score']:.4f}` | **Centroid Drift:** `{row['centroid_drift']:.4f}`")

        if not exp_match.empty:
            exp_text = exp_match.iloc[0]["explanation_text"]
            st.info(f"💡 **Synthesized Change Explanation (Batch Cached):**\n\n{exp_text}")
        else:
            st.info(f"💡 **Algorithmic Summary:** Theme '{row['label']}' underwent a {row['change_type']} shift in FY{row['fiscal_year']} with delta of {row['intensity_delta']:+.2%}.")

        ev_matches = df_evidence[
            (df_evidence["cik"] == row["cik"]) &
            (df_evidence["cluster_id"] == row["cluster_id"]) &
            (df_evidence["fiscal_year"] == row["fiscal_year"])
        ]
        if not ev_matches.empty:
            st.markdown("**Grounded Excerpts (Primary Source Verification):**")
            for _, ev in ev_matches.iterrows():
                st.markdown(f"""
                <div class="evidence-box-mona">
                    <small style="color:#38bdf8; font-weight:700; text-transform:uppercase;">{ev.get('char_start_note', 'Item 1A Section Excerpt')}</small><br/>
                    <em>"{ev['text']}"</em>
                </div>
                """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: Company Deep-Dive
# -----------------------------------------------------------------------------
with tab_deepdive:
    st.subheader("Company Temporal Disclosure Profile")
    if not df_companies.empty:
        comp_map = {f"{r['ticker']} — {r['name']}": r['cik'] for _, r in df_companies.iterrows()}
        selected_label = st.selectbox("Select Target Company:", list(comp_map.keys()))
        target_cik = comp_map[selected_label]

        comp_intensity = df_intensity[df_intensity["cik"] == target_cik].merge(df_themes[["cluster_id", "label"]], on="cluster_id", how="left")

        if not comp_intensity.empty:
            st.markdown("#### Theme Intensity Heatmap Over Fiscal Years")
            heatmap = alt.Chart(comp_intensity).mark_rect(cornerRadius=6).encode(
                x=alt.X("fiscal_year:O", title="Fiscal Year"),
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
    st.subheader("Data Pipeline Reliability & Parse Quality")
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
