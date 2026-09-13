# DriftLens — Design System & Product Architecture Specification

**Product Identity:** Document Forensics × Semantic AI × Longitudinal Trajectories  
**Core Proposition:** "Detect when documents change meaning over time — not merely wording."

---

## 1. Visual Foundation & Color System

All interfaces (GitHub Pages static frontend and Streamlit review dashboard) adhere to a shared semantic design token system:

### 1.1 Color Tokens
| Semantic Role | Token Variable | Hex / RGBA Value | Usage |
|---|---|---|---|
| **Deep Obsidian Canvas** | `--bg-deep` | `#030712` | Primary page background |
| **Surface Layer (Cards)** | `--bg-card` | `rgba(17, 24, 39, 0.75)` | Elevated glass cards with backdrop blur |
| **Document Surface** | `--bg-doc` | `rgba(11, 18, 33, 0.9)` | Primary source document text containers |
| **Subtle Border** | `--border-subtle` | `rgba(255, 255, 255, 0.08)` | Default card and container borders |
| **Border Glow** | `--border-glow` | `rgba(56, 189, 248, 0.35)` | Active/hover border illumination |
| **Primary Text** | `--text-primary` | `#f9fafb` | Headlines, primary data values |
| **Secondary Text** | `--text-secondary` | `#9ca3af` | Descriptions, labels, chart axes |
| **Technical Muted** | `--text-muted` | `#6b7280` | Timestamps, CIKs, file hashes |
| **Drift Accent (Sky/Cyan)** | `--neon-sky` | `#38bdf8` | Centroid drift, vector paths, active highlights |
| **Forensic Emerald (New)** | `--accent-new` | `#10b981` | Newly emerged disclosure themes (`new`) |
| **Intensity Blue (Intensifying)** | `--accent-intensifying` | `#3b82f6` | YoY expanding disclosure themes |
| **Fading Amber (Fading)** | `--accent-fading` | `#f59e0b` | Decreasing disclosure intensity |
| **Divergence Rose (Disappeared)** | `--accent-disappeared` | `#f43f5e` | Completely eliminated risk factors |
| **Stable Slate (Stable)** | `--accent-stable` | `#94a3b8` | Constant intensity and low centroid drift |

---

## 2. Typography Hierarchy

| Role | Font Family | Weights | Usage |
|---|---|---|---|
| **Display / Headlines** | `Syne`, `Plus Jakarta Sans` | 700, 800 | Hero title, section headers, big statistics |
| **Product / Body** | `Plus Jakarta Sans`, sans-serif | 400, 500, 600 | Navigation, card text, excerpts, explanations |
| **Technical / Monospace** | `JetBrains Mono`, monospace | 400, 500, 700 | SQL queries, CIKs, cosine distances, metrics |

---

## 3. Signature Feature: The DriftLens Analyst Bot

The **DriftLens Analyst Bot** ("DriftBot") is an autonomous, ambient document forensics assistant:
- **Form:** Sleek geometric micro-drone with a luminous scanner visor and gentle particle thruster.
- **Behavior:**
  - Ambient slow floating in the bottom-right or contextual viewport.
  - Emits a subtle cyan laser scanning beam when user inspects a drift event or runs SQL queries.
  - Turns eye gaze smoothly toward mouse cursor or active data rows.
  - Automatically respects `prefers-reduced-motion` (remains stationary with no looping animations).
  - Collapsible/dockable to ensure zero obstruction of analytical data.

---

## 4. Latent Space & Trajectory Visualization

- **Projection:** Global 2D UMAP projection of sentence embeddings across all company-years.
- **Temporal Interpolation:** Scrubbing across fiscal years (2019 → 2023) smoothly transitions particle coordinates with velocity damping and history trail lines.
- **Cluster Manifolds:** Color-coded density regions (AI Infrastructure, Semiconductor Foundries, Cloud Privacy, Export Controls, Workforce Disruption) with live centroid markers.

---

## 5. Forensic Document Diffing (Before vs After)

When inspecting a drift event:
- **Year N-1 (Baseline):** Raw extracted excerpt from previous fiscal filing Item 1A.
- **Year N (Current):** Raw extracted excerpt from current fiscal filing Item 1A.
- **Visual Highlighting:** Newly introduced statements (green), rephrased statements with centroid drift (blue), and omitted statements (red strikethrough).
- **Grounded Synthesis:** Batch-cached explanation strictly referencing cited chunk IDs.

---

## 6. Architecture & Platform Alignment

- **GitHub Pages Frontend:** 100% static HTML5/CSS3/Vanilla JS + DuckDB-Wasm for in-browser client-side analytics. Zero metered API costs.
- **Streamlit Dashboard:** Python-native analytical console sharing identical dark obsidian palette, typography, Altair themes, and forensic drilldowns.
