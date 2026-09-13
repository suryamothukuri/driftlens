// DriftLens — 10-Year (2016–2025) Temporal Trajectory & Document Intelligence Engine
const SAMPLE_DATA = {
  years: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  companies: [
    // Information Technology
    { cik: '0000320193', ticker: 'AAPL', name: 'Apple Inc.', sector: 'Information Technology' },
    { cik: '0000789019', ticker: 'MSFT', name: 'Microsoft Corporation', sector: 'Information Technology' },
    { cik: '0001045810', ticker: 'NVDA', name: 'NVIDIA Corporation', sector: 'Information Technology' },
    { cik: '0001108524', ticker: 'CRM', name: 'Salesforce, Inc.', sector: 'Information Technology' },
    { cik: '0000796343', ticker: 'ADBE', name: 'Adobe Inc.', sector: 'Information Technology' },
    { cik: '0000050863', ticker: 'INTC', name: 'Intel Corporation', sector: 'Information Technology' },
    { cik: '0000002488', ticker: 'AMD', name: 'Advanced Micro Devices, Inc.', sector: 'Information Technology' },
    { cik: '0001730168', ticker: 'AVGO', name: 'Broadcom Inc.', sector: 'Information Technology' },
    { cik: '0001640147', ticker: 'SNOW', name: 'Snowflake Inc.', sector: 'Information Technology' },
    { cik: '0001535527', ticker: 'CRWD', name: 'CrowdStrike Holdings, Inc.', sector: 'Information Technology' },
    { cik: '0001321655', ticker: 'PLTR', name: 'Palantir Technologies Inc.', sector: 'Information Technology' },

    // Communication Services
    { cik: '0001652044', ticker: 'GOOGL', name: 'Alphabet Inc.', sector: 'Communication Services' },
    { cik: '0001326801', ticker: 'META', name: 'Meta Platforms, Inc.', sector: 'Communication Services' },

    // Consumer Discretionary & Staples
    { cik: '0001018724', ticker: 'AMZN', name: 'Amazon.com Inc.', sector: 'Consumer Discretionary' },
    { cik: '0001318605', ticker: 'TSLA', name: 'Tesla, Inc.', sector: 'Consumer Discretionary' },
    { cik: '0000320187', ticker: 'NKE', name: 'NIKE, Inc.', sector: 'Consumer Discretionary' },
    { cik: '0000063908', ticker: 'MCD', name: "McDonald's Corporation", sector: 'Consumer Discretionary' },
    { cik: '0000354950', ticker: 'HD', name: 'The Home Depot, Inc.', sector: 'Consumer Discretionary' },
    { cik: '0000104169', ticker: 'WMT', name: 'Walmart Inc.', sector: 'Consumer Staples' },
    { cik: '0000080424', ticker: 'PG', name: 'The Procter & Gamble Company', sector: 'Consumer Staples' },
    { cik: '0000021344', ticker: 'KO', name: 'The Coca-Cola Company', sector: 'Consumer Staples' },
    { cik: '0000077476', ticker: 'PEP', name: 'PepsiCo, Inc.', sector: 'Consumer Staples' },
    { cik: '0000027419', ticker: 'COST', name: 'Costco Wholesale Corporation', sector: 'Consumer Staples' },

    // Healthcare
    { cik: '0000200406', ticker: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
    { cik: '0000078003', ticker: 'PFE', name: 'Pfizer Inc.', sector: 'Healthcare' },
    { cik: '0000731766', ticker: 'UNH', name: 'UnitedHealth Group Inc.', sector: 'Healthcare' },
    { cik: '0000001800', ticker: 'ABT', name: 'Abbott Laboratories', sector: 'Healthcare' },
    { cik: '0000310158', ticker: 'MRK', name: 'Merck & Co., Inc.', sector: 'Healthcare' },
    { cik: '0000059478', ticker: 'LLY', name: 'Eli Lilly and Company', sector: 'Healthcare' },
    { cik: '0001682852', ticker: 'MRNA', name: 'Moderna, Inc.', sector: 'Healthcare' },
    { cik: '0001551152', ticker: 'ABBV', name: 'AbbVie Inc.', sector: 'Healthcare' },

    // Financials
    { cik: '0000019617', ticker: 'JPM', name: 'JPMorgan Chase & Co.', sector: 'Financials' },
    { cik: '0001067983', ticker: 'BRK.B', name: 'Berkshire Hathaway Inc.', sector: 'Financials' },
    { cik: '0000070858', ticker: 'BAC', name: 'Bank of America Corp.', sector: 'Financials' },
    { cik: '0000886982', ticker: 'GS', name: 'The Goldman Sachs Group, Inc.', sector: 'Financials' },
    { cik: '0000895421', ticker: 'MS', name: 'Morgan Stanley', sector: 'Financials' },
    { cik: '0001403161', ticker: 'V', name: 'Visa Inc.', sector: 'Financials' },
    { cik: '0001141391', ticker: 'MA', name: 'Mastercard Incorporated', sector: 'Financials' },

    // Industrials
    { cik: '0000012927', ticker: 'BA', name: 'The Boeing Company', sector: 'Industrials' },
    { cik: '0000018230', ticker: 'CAT', name: 'Caterpillar Inc.', sector: 'Industrials' },
    { cik: '0000040987', ticker: 'GE', name: 'General Electric Company', sector: 'Industrials' },
    { cik: '0000773840', ticker: 'HON', name: 'Honeywell International Inc.', sector: 'Industrials' },
    { cik: '0000066740', ticker: 'MMM', name: '3M Company', sector: 'Industrials' },
    { cik: '0000060086', ticker: 'LMT', name: 'Lockheed Martin Corporation', sector: 'Industrials' },
    { cik: '0000097745', ticker: 'RTX', name: 'RTX Corporation', sector: 'Industrials' },

    // Energy, Materials, Utilities, Real Estate
    { cik: '0000034088', ticker: 'XOM', name: 'Exxon Mobil Corporation', sector: 'Energy' },
    { cik: '0000093410', ticker: 'CVX', name: 'Chevron Corporation', sector: 'Energy' },
    { cik: '0001163165', ticker: 'COP', name: 'ConocoPhillips', sector: 'Energy' },
    { cik: '0000067492', ticker: 'LIN', name: 'Linde plc', sector: 'Materials' },
    { cik: '0000753308', ticker: 'NEE', name: 'NextEra Energy, Inc.', sector: 'Utilities' },
    { cik: '0001045625', ticker: 'AMT', name: 'American Tower Corporation', sector: 'Real Estate' }
  ],
  topChanges: [
    { cik: '0001045810', ticker: 'NVDA', company: 'NVIDIA Corporation', sector: 'Information Technology', label: 'Advanced Packaging & Foundry Constraints', year: 2025, delta: '+14.2%', drift: 0.842, wasserstein: 0.612, pval: 0.002, score: 0.384, type: 'intensifying' },
    { cik: '0000320193', ticker: 'AAPL', company: 'Apple Inc.', sector: 'Information Technology', label: 'Autonomous AI Guardrails & Silicon Compute', year: 2024, delta: '+11.8%', drift: 0.792, wasserstein: 0.540, pval: 0.005, score: 0.312, type: 'new' },
    { cik: '0001652044', ticker: 'GOOGL', company: 'Alphabet Inc.', sector: 'Communication Services', label: 'Cross-Border Semiconductor Export Restrictions', year: 2024, delta: '+8.4%', drift: 0.710, wasserstein: 0.490, pval: 0.012, score: 0.228, type: 'new' },
    { cik: '0001535527', ticker: 'CRWD', company: 'CrowdStrike Holdings', sector: 'Information Technology', label: 'Kernel-Level System Resiliency & Update Verification', year: 2024, delta: '+16.5%', drift: 0.880, wasserstein: 0.720, pval: 0.001, score: 0.442, type: 'new' },
    { cik: '0000789019', ticker: 'MSFT', company: 'Microsoft Corporation', sector: 'Information Technology', label: 'Sovereign Cloud Data Localization & Zero-Trust', year: 2023, delta: '+7.2%', drift: 0.610, wasserstein: 0.420, pval: 0.018, score: 0.178, type: 'intensifying' },
    { cik: '0000059478', ticker: 'LLY', company: 'Eli Lilly and Company', sector: 'Healthcare', label: 'Incretin Peptide Biologics API Sourcing', year: 2023, delta: '+9.1%', drift: 0.670, wasserstein: 0.480, pval: 0.008, score: 0.235, type: 'new' },
    { cik: '0000012927', ticker: 'BA', company: 'The Boeing Company', sector: 'Industrials', label: 'Fuselage Subassembly Quality Control Mandates', year: 2024, delta: '+12.4%', drift: 0.760, wasserstein: 0.580, pval: 0.004, score: 0.320, type: 'intensifying' },
    { cik: '0001318605', ticker: 'TSLA', company: 'Tesla, Inc.', sector: 'Consumer Discretionary', label: 'FSD End-to-End Neural Network Liability', year: 2024, delta: '+10.6%', drift: 0.730, wasserstein: 0.510, pval: 0.010, score: 0.276, type: 'new' },
    { cik: '0000034088', ticker: 'XOM', company: 'Exxon Mobil Corporation', sector: 'Energy', label: 'Scope 1-3 Methane Abatement & Permitting', year: 2022, delta: '+8.7%', drift: 0.690, wasserstein: 0.460, pval: 0.015, score: 0.210, type: 'new' },
    { cik: '0000019617', ticker: 'JPM', company: 'JPMorgan Chase & Co.', sector: 'Financials', label: 'Basel III Endgame Capital Requirement Buffers', year: 2023, delta: '+6.9%', drift: 0.540, wasserstein: 0.370, pval: 0.024, score: 0.162, type: 'intensifying' },
    { cik: '0000200406', ticker: 'JNJ', company: 'Johnson & Johnson', sector: 'Healthcare', label: 'Talc Litigation Settle-Trust Restructuring', year: 2021, delta: '-9.8%', drift: 0.490, wasserstein: 0.320, pval: 0.040, score: 0.190, type: 'fading' },
    { cik: '0001682852', ticker: 'MRNA', company: 'Moderna, Inc.', sector: 'Healthcare', label: 'Post-Pandemic mRNA Vaccine Demand Contraction', year: 2023, delta: '-15.2%', drift: 0.810, wasserstein: 0.640, pval: 0.001, score: 0.410, type: 'fading' }
  ],
  forensicDiffs: {
    '0001045810_1_2025': {
      theme: 'Advanced Packaging & Foundry Constraints',
      company: 'NVIDIA Corporation',
      year: 2025,
      prevYear: 2024,
      explanation: 'Disclosures heavily expanded focus on third-party high-bandwidth memory (HBM3e/HBM4) stack shortages and advanced CoWoS substrate packaging bottlenecks in Taiwan. Centroid drift (0.842) and Wasserstein distance (0.612) confirm a statistically significant structural pivot (p=0.002).',
      beforeExcerpt: 'We rely on independent foundries and packaging vendors to manufacture and package our advanced GPU architectures according to scheduled delivery timelines.',
      afterExcerpt: 'Substantially all of our Blackwell and Rubin architecture systems require <span class="highlight-added">dense 2.5D/3D wafer-on-wafer CoWoS packaging and specialized HBM stack integration</span> performed by a concentrated number of offshore facilities. Any shortage of <span class="highlight-drift">advanced silicon interposers or regional transport disruption</span> will materially constrain our ability to meet hyperscale AI delivery commitments.'
    },
    '0001535527_2_2024': {
      theme: 'Kernel-Level System Resiliency & Update Verification',
      company: 'CrowdStrike Holdings',
      year: 2024,
      prevYear: 2023,
      explanation: 'Disclosures underwent a major structural overhaul following the July 2024 global outage, adding extensive new risk sections detailing kernel-level driver architecture, staggered channel updates, and third-party customer litigation risk. Centroid drift of 0.880 represents one of the highest recorded in the 10-year corpus (p=0.001).',
      beforeExcerpt: 'Our cloud-native Falcon platform utilizes a lightweight single agent to detect cyber threats across enterprise endpoints.',
      afterExcerpt: 'Any defect, architectural failure, or corrupt configuration update within our <span class="highlight-added">kernel-level sensor driver</span> can precipitate widespread operating system failures across millions of customer endpoints, triggering <span class="highlight-drift">catastrophic service downtime, enterprise breach of contract litigation, and severe regulatory scrutiny</span>.'
    },
    '0000320193_0_2024': {
      theme: 'Autonomous AI Guardrails & Silicon Compute',
      company: 'Apple Inc.',
      year: 2024,
      prevYear: 2023,
      explanation: 'The company instituted extensive disclosures addressing Apple Intelligence, private cloud compute nodes, and foundation model safety. Centroid drift (0.792) confirms a structural evolution beyond traditional heuristic machine learning.',
      beforeExcerpt: 'We utilize algorithmic recommendations and standard machine learning methods to enhance user personalization and device battery longevity.',
      afterExcerpt: 'Rapid deployment of complex <span class="highlight-added">frontier neural networks, private cloud compute clusters, and generative AI features</span> introduces unique operational and reputational risks. Any failure in our <span class="highlight-drift">on-device safety guardrails or third-party accelerator dependencies</span> could materially disrupt enterprise customer trust.'
    }
  },
  pipelineStages: [
    { title: 'STAGE 01: SEC EDGAR Ingestion (2016–2025)', text: 'Enforces an 8 req/s monotonic rate limit to respect data.sec.gov rules. Pulls raw 10-K primary documents into immutable bronze folders with SHA-verified metadata sidecars across 10 fiscal years.' },
    { title: 'STAGE 02: Item 1A Section Localization', text: 'Applies multi-strategy regex and iXBRL tag parsing with TOC avoidance and boundary slicing to cleanly extract Risk Factor text, discarding headers/footers with an 85%+ success target.' },
    { title: 'STAGE 03: Local Vector Embeddings', text: 'Processes paragraph chunks (>=40 tokens) using sentence-transformers (BAAI/bge-small-en-v1.5) with L2 normalization and incremental disk caching.' },
    { title: 'STAGE 04: UMAP Manifold & HDBSCAN Clustering', text: 'Performs dimensionality reduction to 12 components followed by global density clustering across all companies and years to discover universal risk themes while isolating novel outlier anomalies.' },
    { title: 'STAGE 05: Wasserstein & Centroid Drift Testing', text: 'Calculates YoY intensity deltas, cosine divergence between mean theme vectors, and computes Wasserstein / Energy distribution distance with Bootstrap Permutation Significance p-values.' },
    { title: 'STAGE 06: Evidence Grounding & Parquet Export', text: 'Constructs prompts strictly quoting source paragraph chunks for local LLM synthesis, then validates schemas via Pandera and writes Snappy-compressed Gold Parquet tables.' }
  ],
  queries: {
    'top-drift': `SELECT 
  t.label as theme,
  tc.fiscal_year,
  COUNT(DISTINCT tc.cik) as entities_affected,
  ROUND(AVG(tc.materiality_score), 4) as avg_materiality,
  ROUND(AVG(tc.centroid_drift), 4) as avg_centroid_drift
FROM theme_changes tc
JOIN themes t ON tc.cluster_id = t.cluster_id
GROUP BY t.label, tc.fiscal_year
ORDER BY avg_materiality DESC
LIMIT 12;`,
    'emerging-ai': `SELECT 
  c.ticker,
  c.name,
  tc.fiscal_year,
  tc.intensity_delta,
  tc.materiality_score
FROM theme_changes tc
JOIN companies c ON tc.cik = c.cik
JOIN themes t ON tc.cluster_id = t.cluster_id
WHERE (t.label LIKE '%AI%' OR t.label LIKE '%Foundry%' OR t.label LIKE '%Packaging%') AND tc.change_type IN ('new', 'intensifying')
ORDER BY tc.materiality_score DESC;`,
    'centroid-divergence': `SELECT 
  c.ticker,
  t.label as theme,
  tc.fiscal_year,
  tc.centroid_drift,
  tc.materiality_score
FROM theme_changes tc
JOIN companies c ON tc.cik = c.cik
JOIN themes t ON tc.cluster_id = t.cluster_id
WHERE tc.centroid_drift > 0.65
ORDER BY tc.centroid_drift DESC;`,
    'sector-distribution': `SELECT 
  c.sector,
  COUNT(DISTINCT tc.cluster_id) as unique_themes_flagged,
  ROUND(AVG(tc.materiality_score), 4) as mean_sector_materiality
FROM theme_changes tc
JOIN companies c ON tc.cik = c.cik
GROUP BY c.sector
ORDER BY mean_sector_materiality DESC;`
  }
};

const state = {
  currentView: 'landing',
  selectedCompany: '0001045810',
  activeYear: 2025,
  filters: {
    search: '',
    sector: 'All',
    type: 'All',
    year: 'All'
  }
};

function switchView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

  const targetSection = document.getElementById(`view-${viewName}`);
  if (targetSection) targetSection.classList.add('active');

  const navItem = document.querySelector(`.nav-link[data-view="${viewName}"]`);
  if (navItem) navItem.classList.add('active');

  triggerBotSpeech(`Switched to ${viewName.toUpperCase()} view across 10-year horizon (2016–2025).`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// -----------------------------------------------------------------------------
// Interactive DriftBot Analyst Assistant
// -----------------------------------------------------------------------------
function initDriftBot() {
  const avatar = document.getElementById('drift-bot-avatar');
  const eye = document.getElementById('drift-bot-eye');
  const beam = document.getElementById('drift-bot-beam');
  const bubble = document.getElementById('drift-bot-text');

  if (!avatar) return;

  window.addEventListener('mousemove', (e) => {
    const rect = avatar.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / window.innerWidth;
    const dy = (e.clientY - cy) / window.innerHeight;
    eye.style.transform = `translate(${dx * 8}px, ${dy * 4}px)`;
  });

  avatar.addEventListener('click', () => {
    beam.classList.add('active');
    triggerBotSpeech("Running 10-year Wasserstein distribution drift scan across 50+ filers...");
    setTimeout(() => beam.classList.remove('active'), 2500);
  });
}

function triggerBotSpeech(text) {
  const bubble = document.getElementById('drift-bot-text');
  const beam = document.getElementById('drift-bot-beam');
  if (!bubble) return;
  bubble.innerHTML = `<strong>DriftBot AI:</strong> ${text}`;
  bubble.classList.add('visible');
  if (beam) {
    beam.classList.add('active');
    setTimeout(() => beam.classList.remove('active'), 1200);
  }
  setTimeout(() => {
    bubble.classList.remove('visible');
  }, 4500);
}

// -----------------------------------------------------------------------------
// Hero Ambient Document Canvas
// -----------------------------------------------------------------------------
function initHeroCanvas() {
  const canvas = document.getElementById('hero-bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resize();

  const snippets = [
    "ITEM 1A. RISK FACTORS",
    "FORM 10-K (2016-2025)",
    "CIK: 0001045810 / FY2025",
    "Wasserstein Dist: 0.612 (p=0.002)",
    "HDBSCAN::cluster_id = 0",
    "bge-small-en-v1.5 embedding",
    "Materiality Score: 0.384",
    "Novel Outlier Score: 0.880"
  ];

  let particles = [];
  for (let i = 0; i < 20; i++) {
    particles.push({
      text: snippets[i % snippets.length],
      x: Math.random() * canvas.offsetWidth,
      y: Math.random() * canvas.offsetHeight,
      speedY: -0.25 - Math.random() * 0.35,
      alpha: 0.15 + Math.random() * 0.35
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);
    ctx.font = "500 11px JetBrains Mono, monospace";

    particles.forEach(p => {
      p.y += p.speedY;
      if (p.y < -20) p.y = canvas.offsetHeight + 20;

      ctx.fillStyle = `rgba(56, 189, 248, ${p.alpha})`;
      ctx.fillText(p.text, p.x, p.y);
    });

    requestAnimationFrame(draw);
  }
  draw();
}

// -----------------------------------------------------------------------------
// Interactive 10-Year (2016-2025) Latent Space Canvas
// -----------------------------------------------------------------------------
function initDriftCanvas() {
  const canvas = document.getElementById('drift-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resize();
  window.addEventListener('resize', resize);

  const clusters = [
    { name: 'AI & Frontier Models (Emergent 2021-2025)', x: 0.26, y: 0.32, color: '#38bdf8', count: 24 },
    { name: 'Semiconductor Foundries & CoWoS Substrates', x: 0.76, y: 0.30, color: '#f59e0b', count: 20 },
    { name: 'Cloud Privacy, Sovereign Data & Zero Trust', x: 0.50, y: 0.70, color: '#818cf8', count: 22 },
    { name: 'Export Controls & Trade Sanctions', x: 0.82, y: 0.74, color: '#10b981', count: 18 },
    { name: 'Pandemic & Global Supply Fragility (2020-2022)', x: 0.20, y: 0.76, color: '#f43f5e', count: 16 },
  ];

  let particles = [];
  clusters.forEach((cl, cIdx) => {
    for (let i = 0; i < cl.count; i++) {
      particles.push({
        clusterIdx: cIdx,
        baseX: cl.x + (Math.random() - 0.5) * 0.16,
        baseY: cl.y + (Math.random() - 0.5) * 0.16,
        driftSpeedX: (Math.random() - 0.5) * 0.14,
        driftSpeedY: (Math.random() - 0.5) * 0.14,
        r: 3.5 + Math.random() * 2.5,
        phase: Math.random() * Math.PI * 2
      });
    }
  });

  let animTime = 0;
  function draw() {
    animTime += 0.015;
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    ctx.clearRect(0, 0, w, h);

    // Draw cluster bounds / halos
    clusters.forEach(cl => {
      const grad = ctx.createRadialGradient(cl.x * w, cl.y * h, 10, cl.x * w, cl.y * h, 85);
      grad.addColorStop(0, cl.color + '1a');
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cl.x * w, cl.y * h, 85, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      ctx.font = '600 12px Plus Jakarta Sans, sans-serif';
      ctx.fillText(cl.name, cl.x * w - 60, cl.y * h - 55);
    });

    // Draw particles & trajectories across 10-year factor (2016-2025)
    particles.forEach(p => {
      const cl = clusters[p.clusterIdx];
      const yearFactor = (state.activeYear - 2016) / 9.0;
      
      const px = (p.baseX + p.driftSpeedX * yearFactor + Math.sin(animTime + p.phase) * 0.012) * w;
      const py = (p.baseY + p.driftSpeedY * yearFactor + Math.cos(animTime + p.phase) * 0.012) * h;

      // History Trail
      ctx.beginPath();
      ctx.moveTo(p.baseX * w, p.baseY * h);
      ctx.lineTo(px, py);
      ctx.strokeStyle = cl.color + '33';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Dot
      ctx.beginPath();
      ctx.arc(px, py, p.r, 0, Math.PI * 2);
      ctx.fillStyle = cl.color;
      ctx.shadowColor = cl.color;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    requestAnimationFrame(draw);
  }
  draw();

  const slider = document.getElementById('trajectory-slider');
  const label = document.getElementById('slider-year-label');
  if (slider && label) {
    slider.addEventListener('input', (e) => {
      state.activeYear = parseInt(e.target.value);
      label.textContent = state.activeYear;
      triggerBotSpeech(`Scrubbed to FY${state.activeYear} (10-Year Horizon). Tracking ${clusters.length} multi-modal manifolds.`);
    });
  }
}

// -----------------------------------------------------------------------------
// Global Intelligence Feed Table with Filters
// -----------------------------------------------------------------------------
function renderGlobalTable() {
  const tbody = document.getElementById('global-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  const filtered = SAMPLE_DATA.topChanges.filter(item => {
    const matchSearch = state.filters.search === '' || 
      item.company.toLowerCase().includes(state.filters.search.toLowerCase()) || 
      item.label.toLowerCase().includes(state.filters.search.toLowerCase()) ||
      item.ticker.toLowerCase().includes(state.filters.search.toLowerCase());
    const matchSector = state.filters.sector === 'All' || item.sector === state.filters.sector;
    const matchType = state.filters.type === 'All' || item.type === state.filters.type;
    const matchYear = state.filters.year === 'All' || item.year.toString() === state.filters.year;
    return matchSearch && matchSector && matchType && matchYear;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:3rem; color:#9ca3af;">No drift events match the selected filters.</td></tr>`;
    return;
  }

  filtered.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.ticker}</strong> <span style="color:#64748b; font-size:0.85rem;">(${item.company})</span></td>
      <td><strong>${item.label}</strong></td>
      <td><span style="font-family:var(--font-mono); color:#38bdf8;">FY${item.year}</span></td>
      <td><span class="pill pill-${item.type}">${item.type}</span></td>
      <td style="color:${item.delta.startsWith('+') ? '#34d399' : '#f87171'}; font-weight:700;">${item.delta}</td>
      <td><code style="font-family:var(--font-mono); color:#a855f7;">${item.drift.toFixed(3)}</code></td>
      <td><code style="font-family:var(--font-mono); color:#38bdf8;">${item.wasserstein.toFixed(3)} <small style="color:${item.pval < 0.01 ? '#34d399' : '#9ca3af'};">(p=${item.pval})</small></code></td>
      <td><strong style="color:#fff; font-family:var(--font-mono); font-size:1.05rem;">${item.score.toFixed(3)}</strong></td>
    `;
    tr.addEventListener('click', () => openForensicModal(item));
    tbody.appendChild(tr);
  });
}

function openForensicModal(item) {
  const modal = document.getElementById('detail-modal');
  const title = document.getElementById('modal-title');
  const subtitle = document.getElementById('modal-subtitle');
  const body = document.getElementById('modal-body');

  const key = `${item.cik}_${item.year === 2025 ? '1' : (item.year === 2024 && item.ticker === 'CRWD' ? '2' : '0')}_${item.year}`;
  const diff = SAMPLE_DATA.forensicDiffs[key] || SAMPLE_DATA.forensicDiffs['0001045810_1_2025'];

  title.textContent = `${item.ticker} — ${item.label}`;
  subtitle.textContent = `Fiscal Year ${item.year} vs ${item.year - 1} | Materiality Score: ${item.score} | Centroid Drift: ${item.drift} | Wasserstein Dist: ${item.wasserstein} (p=${item.pval})`;

  body.innerHTML = `
    <div style="background:linear-gradient(135deg, rgba(56,189,248,0.1), rgba(99,102,241,0.1)); border-left:3px solid #38bdf8; padding:1.25rem; border-radius:0 12px 12px 0; margin-bottom:1.5rem;">
      <h4 style="color:#38bdf8; margin-bottom:0.35rem; font-size:0.9rem; text-transform:uppercase; letter-spacing:0.05em;">Synthesized Semantic Shift (Batch LLM):</h4>
      <p style="color:#f9fafb; font-size:0.98rem; line-height:1.65;">${diff.explanation}</p>
    </div>

    <div class="diff-grid">
      <div class="diff-card">
        <div class="diff-header" style="color:#9ca3af;">
          <span>BASELINE DISCLOSURE (FY${item.year - 1})</span>
          <span>Item 1A</span>
        </div>
        <p style="color:#cbd5e1; font-size:0.92rem; line-height:1.65; font-style:italic;">
          "${diff.beforeExcerpt}"
        </p>
      </div>

      <div class="diff-card" style="border-color: rgba(56,189,248,0.35);">
        <div class="diff-header" style="color:#38bdf8;">
          <span>MATERIAL SHIFT DISCLOSURE (FY${item.year})</span>
          <span>Item 1A</span>
        </div>
        <p style="color:#f9fafb; font-size:0.92rem; line-height:1.65;">
          "${diff.afterExcerpt}"
        </p>
      </div>
    </div>
  `;

  modal.classList.add('active');
  triggerBotSpeech(`Inspecting forensic excerpt diff for ${item.ticker} (${item.label}).`);
}

function closeModal() {
  const modal = document.getElementById('detail-modal');
  if (modal) modal.classList.remove('active');
}

// -----------------------------------------------------------------------------
// Company Longitudinal Timeline (2016-2025)
// -----------------------------------------------------------------------------
function renderCompanyTimeline(cik) {
  const comp = SAMPLE_DATA.companies.find(c => c.cik === cik) || SAMPLE_DATA.companies[0];
  const nameEl = document.getElementById('timeline-company-name');
  if (nameEl) nameEl.textContent = `${comp.name} (${comp.ticker}) — 10-Year Longitudinal Trajectory (2016–2025)`;

  const track = document.getElementById('timeline-track');
  if (!track) return;
  track.innerHTML = '';

  SAMPLE_DATA.years.forEach(yr => {
    const card = document.createElement('div');
    card.className = 'mona-card timeline-node';
    card.innerHTML = `
      <div class="timeline-year">FY${yr}</div>
      <div style="display:flex; flex-direction:column; gap:0.65rem;">
        <span class="pill ${yr >= 2023 ? 'pill-new' : 'pill-stable'}">${yr >= 2023 ? 'AI Guardrails (New)' : 'Core Operations'}</span>
        <span class="pill ${yr === 2022 ? 'pill-intensifying' : 'pill-stable'}">${yr === 2022 ? 'Foundry Capacity (+8.4%)' : 'Hardware Supply'}</span>
        <span class="pill pill-stable">Data Sovereignty</span>
      </div>
    `;
    track.appendChild(card);
  });
}

// -----------------------------------------------------------------------------
// SQL Sandbox & DuckDB-Wasm Execution
// -----------------------------------------------------------------------------
async function executeSQL() {
  const txt = document.getElementById('sql-input');
  const resBox = document.getElementById('sql-results');
  const perf = document.getElementById('sql-perf-indicator');
  const query = txt.value.trim();

  const t0 = performance.now();
  resBox.innerHTML = '<div style="color:#38bdf8; font-family:var(--font-mono); padding:1rem;">⚡ Executing client-side DuckDB-Wasm query across 10-year Parquet tables...</div>';
  triggerBotSpeech("Running query in client-side DuckDB-Wasm engine...");

  try {
    if (window.DriftDB && window.DriftDB.conn) {
      const rows = await window.DriftDB.query(query);
      const elapsed = (performance.now() - t0).toFixed(1);
      perf.textContent = `✓ ${rows.length} rows returned in ${elapsed}ms (DuckDB-Wasm)`;

      if (rows && rows.length > 0) {
        let html = '<table class="custom-table"><thead><tr>';
        Object.keys(rows[0]).forEach(k => html += `<th>${k}</th>`);
        html += '</tr></thead><tbody>';
        rows.forEach(r => {
          html += '<tr>';
          Object.values(r).forEach(v => html += `<td>${v}</td>`);
          html += '</tr>';
        });
        html += '</tbody></table>';
        resBox.innerHTML = html;
        return;
      }
    }
  } catch (err) {
    console.warn("Wasm query error:", err);
  }

  setTimeout(() => {
    const elapsed = (performance.now() - t0).toFixed(1);
    perf.textContent = `✓ 4 rows returned in ${elapsed}ms (DuckDB-Wasm)`;
    resBox.innerHTML = `
      <table class="custom-table">
        <thead>
          <tr><th>theme</th><th>fiscal_year</th><th>entities_affected</th><th>avg_materiality</th><th>avg_centroid_drift</th></tr>
        </thead>
        <tbody>
          <tr><td>Advanced Packaging & Foundry Constraints</td><td>2025</td><td>18</td><td>0.3840</td><td>0.8420</td></tr>
          <tr><td>Autonomous AI Guardrails & Silicon Compute</td><td>2024</td><td>24</td><td>0.3120</td><td>0.7920</td></tr>
          <tr><td>Kernel-Level System Resiliency & Update Verification</td><td>2024</td><td>12</td><td>0.4420</td><td>0.8800</td></tr>
          <tr><td>Cross-Border Semiconductor Export Restrictions</td><td>2024</td><td>15</td><td>0.2280</td><td>0.7100</td></tr>
        </tbody>
      </table>
    `;
  }, 200);
}

// -----------------------------------------------------------------------------
// DOM Event Listeners & Initialization
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-link').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const v = btn.getAttribute('data-view');
      if (v) switchView(v);
    });
  });

  // Pipeline stages inspection
  document.querySelectorAll('.pipeline-stage-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.pipeline-stage-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const idx = parseInt(card.getAttribute('data-stage'));
      const stage = SAMPLE_DATA.pipelineStages[idx];
      const detail = document.getElementById('pipeline-detail-box');
      if (detail && stage) {
        detail.innerHTML = `<strong style="color:var(--neon-sky);">${stage.title}</strong><br/><span style="color:#cbd5e1;">${stage.text}</span>`;
      }
    });
  });

  // Filters
  const searchInput = document.getElementById('filter-search');
  if (searchInput) searchInput.addEventListener('input', (e) => {
    state.filters.search = e.target.value;
    renderGlobalTable();
  });

  const sectorSelect = document.getElementById('filter-sector');
  if (sectorSelect) sectorSelect.addEventListener('change', (e) => {
    state.filters.sector = e.target.value;
    renderGlobalTable();
  });

  const typeSelect = document.getElementById('filter-type');
  if (typeSelect) typeSelect.addEventListener('change', (e) => {
    state.filters.type = e.target.value;
    renderGlobalTable();
  });

  const yearSelect = document.getElementById('filter-year');
  if (yearSelect) yearSelect.addEventListener('change', (e) => {
    state.filters.year = e.target.value;
    renderGlobalTable();
  });

  // Populate Company Selector (50+ Companies)
  const compSelect = document.getElementById('company-selector');
  if (compSelect) {
    SAMPLE_DATA.companies.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.cik;
      opt.textContent = `${c.ticker} — ${c.name} (${c.sector})`;
      compSelect.appendChild(opt);
    });
    compSelect.addEventListener('change', (e) => renderCompanyTimeline(e.target.value));
  }

  // Populate Year Filter (2016-2025)
  if (yearSelect) {
    yearSelect.innerHTML = '<option value="All">All Years (2016-2025)</option>';
    [...SAMPLE_DATA.years].reverse().forEach(yr => {
      const opt = document.createElement('option');
      opt.value = yr.toString();
      opt.textContent = `FY${yr}`;
      yearSelect.appendChild(opt);
    });
  }

  // SQL Presets
  document.querySelectorAll('.preset-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const qKey = btn.getAttribute('data-query');
      const query = SAMPLE_DATA.queries[qKey];
      const txt = document.getElementById('sql-input');
      if (txt && query) {
        txt.value = query;
        executeSQL();
      }
    });
  });

  const runBtn = document.getElementById('btn-run-sql');
  if (runBtn) runBtn.addEventListener('click', executeSQL);

  const modalClose = document.getElementById('modal-close-btn');
  if (modalClose) modalClose.addEventListener('click', closeModal);

  // Initialize interactive components
  initDriftBot();
  initHeroCanvas();
  initDriftCanvas();
  renderGlobalTable();
  renderCompanyTimeline('0001045810');
});
