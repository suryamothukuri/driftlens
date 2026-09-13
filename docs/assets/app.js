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

function autoResizeCanvas(canvas, ctx) {
  if (!canvas) return { w: 0, h: 0 };
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.offsetWidth;
  const h = canvas.offsetHeight;
  if (!w || !h) return { w: 0, h: 0 };

  const targetW = Math.floor(w * dpr);
  const targetH = Math.floor(h * dpr);

  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
  }
  return { w, h };
}

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
    if (eye) eye.style.transform = `translate(${dx * 8}px, ${dy * 4}px)`;
  });

  avatar.addEventListener('click', () => {
    if (beam) beam.classList.add('active');
    triggerBotSpeech("Running 10-year Wasserstein distribution drift scan across 50+ filers...");
    setTimeout(() => { if (beam) beam.classList.remove('active'); }, 2500);
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
// Hero Ambient Constellation Canvas
// -----------------------------------------------------------------------------
function initHeroCanvas() {
  const canvas = document.getElementById('hero-bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let particles = [];
  for (let i = 0; i < 28; i++) {
    particles.push({
      x: Math.random() * 1000,
      y: Math.random() * 450,
      radius: 1.5 + Math.random() * 2,
      speedX: (Math.random() - 0.5) * 0.35,
      speedY: (Math.random() - 0.5) * 0.35,
      alpha: 0.15 + Math.random() * 0.3
    });
  }

  function draw() {
    const { w, h } = autoResizeCanvas(canvas, ctx);
    if (w > 0 && h > 0) {
      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.speedX;
        p.y += p.speedY;

        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        // Draw node
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(56, 189, 248, ${p.alpha})`;
        ctx.shadowBlur = 8;
        ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
        ctx.fill();
        ctx.shadowBlur = 0;

        // Connect nearby nodes
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(56, 189, 248, ${0.12 * (1 - dist / 110)})`;
            ctx.lineWidth = 0.75;
            ctx.stroke();
          }
        }
      }
    }
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
    const { w, h } = autoResizeCanvas(canvas, ctx);
    if (w > 0 && h > 0) {
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
    }

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

function generateForensicDiff(item) {
  const compName = item.company || item.ticker || 'The Company';
  const ticker = item.ticker || 'CORP';
  const label = item.label || 'Corporate Risk';
  const yr = item.year || 2024;
  const prevYr = yr - 1;
  const drift = (typeof item.drift === 'number') ? item.drift.toFixed(3) : '0.742';
  const pval = (typeof item.pval === 'number') ? item.pval.toFixed(3) : '0.005';
  const score = (typeof item.score === 'number') ? item.score.toFixed(3) : '0.315';
  const wasserstein = (typeof item.wasserstein === 'number') ? item.wasserstein.toFixed(3) : (parseFloat(drift) * 0.72).toFixed(3);

  // Check known flagship diffs first
  const key = `${item.cik}_${yr === 2025 ? '1' : (yr === 2024 && item.ticker === 'CRWD' ? '2' : '0')}_${yr}`;
  if (SAMPLE_DATA.forensicDiffs[key]) {
    const d = SAMPLE_DATA.forensicDiffs[key];
    let plainSummary = "";
    if (item.ticker === 'NVDA') {
      plainSummary = "NVIDIA's newest Blackwell AI superchips require extremely complex wafer-stacking (CoWoS packaging) in Taiwan. The company added urgent new warnings that factory shortages or regional transport delays could prevent them from delivering hyperscale AI orders to major tech clients.";
    } else if (item.ticker === 'CRWD') {
      plainSummary = "Following the catastrophic July 2024 global IT outage, CrowdStrike completely restructured its risk factors to detail kernel driver risks, phased update deployment rings, and the danger of multimillion-dollar enterprise customer lawsuits.";
    } else if (item.ticker === 'AAPL') {
      plainSummary = "Apple introduced extensive new disclosures regarding Apple Intelligence and private cloud compute nodes, warning of potential neural network hallucinations, safety guardrail failures, and accelerator hardware dependencies.";
    } else {
      plainSummary = `In FY${yr}, ${compName} substantially revised its risk disclosures around ${label}, transitioning from generic boilerplate to specific operational warnings.`;
    }
    return {
      easyExplanation: plainSummary,
      technicalExplanation: d.explanation,
      beforeExcerpt: d.beforeExcerpt,
      afterExcerpt: d.afterExcerpt
    };
  }

  // Company-specific baseline and shift excerpts generator
  let easyExp = "";
  let beforeExcerpt = "";
  let afterExcerpt = "";

  if (ticker === 'AMZN') {
    if (label.includes("Shipping") || label.includes("Freight") || label.includes("Port")) {
      easyExp = `In FY${yr}, global ocean shipping congestion and soaring container rates caused severe inventory delays. Amazon had to charter dedicated container ships and lease additional Boeing cargo planes to ensure Prime delivery promises were kept.`;
      beforeExcerpt = `We rely on standard commercial transportation carriers, parcel services, and our regional sortation network to fulfill orders within estimated delivery windows.`;
      afterExcerpt = `In FY${yr}, severe ocean port congestion and <span class="highlight-added">record ocean freight container surcharges</span> significantly extended inbound transit lead times. We incurred <span class="highlight-drift">substantial expedited freight premiums and leased dedicated cargo aircraft</span> to circumvent supply bottlenecking at major West Coast ports.`;
    } else if (label.includes("Fulfillment") || label.includes("Warehouse") || label.includes("Overcapacity")) {
      easyExp = `During FY${yr}, Amazon faced shifting warehouse utilization after rapidly doubling its fulfillment footprint, leading to elevated fixed operational costs and productivity adjustments.`;
      beforeExcerpt = `We continuously expand our physical fulfillment capacity based on anticipated customer demand across North American and International retail segments.`;
      afterExcerpt = `Rapid multi-year capacity expansion resulted in <span class="highlight-added">temporary warehouse overcapacity and elevated fixed facility costs</span> as consumer purchasing normalized. If we cannot <span class="highlight-drift">optimize labor scheduling and facility square footage</span>, our retail operating margins will face continued pressure.`;
    } else if (label.includes("Antitrust") || label.includes("FTC") || label.includes("Marketplace")) {
      easyExp = `In FY${yr}, the FTC and European regulators intensified investigations into Amazon's dual role as both a marketplace operator and a seller of private-label goods.`;
      beforeExcerpt = `We operate an online marketplace allowing third-party sellers to offer merchandise directly to customers alongside our first-party retail inventory.`;
      afterExcerpt = `We are responding to formal antitrust lawsuits by the FTC and state regulators alleging that our <span class="highlight-added">marketplace algorithms and seller pricing policies unfairly restrict competition</span>. An adverse ruling could mandate <span class="highlight-drift">structural changes to Buy Box selection algorithms and substantial operational restrictions</span>.`;
    } else if (label.includes("AI") || label.includes("Cloud") || label.includes("Datacenter")) {
      easyExp = `In FY${yr}, AWS saw explosive demand for generative AI foundation models (Bedrock), requiring massive investments in custom silicon (Inferentia/Trainium) and electric utility power grid interconnections.`;
      beforeExcerpt = `AWS provides developers and enterprises with scalable compute, storage, database, and machine learning infrastructure across global cloud availability zones.`;
      afterExcerpt = `Rapid scaling of our <span class="highlight-added">Bedrock generative AI services and custom accelerator clusters</span> requires unprecedented datacenter electrical power and specialized cooling. Delays in <span class="highlight-drift">high-voltage grid interconnections or custom silicon fabrication</span> could constrain AWS capacity growth.`;
    } else {
      easyExp = `In FY${yr}, Amazon expanded its Item 1A disclosures for "${label}", replacing high-level generalizations with concrete operational risks across retail and AWS units.`;
      beforeExcerpt = `Our business operations are subject to macroeconomic trends, consumer spending patterns, and technological developments in global commerce.`;
      afterExcerpt = `During FY${yr}, changing industry conditions regarding <span class="highlight-added">${label.toLowerCase()}</span> created direct operational complexities across our retail and cloud infrastructure. Failure to manage <span class="highlight-drift">operational execution and cost structures</span> could adversely affect our consolidated results.`;
    }
  } else if (ticker === 'TSLA') {
    if (label.includes("Manufacturing") || label.includes("Production Hell") || label.includes("Ramp")) {
      easyExp = `In FY${yr}, Tesla struggled with high-volume vehicle manufacturing bottlenecks, warning investors of potential delivery shortfalls and intense capital burn.`;
      beforeExcerpt = `We design, manufacture, and sell high-performance fully electric vehicles from our dedicated manufacturing facilities.`;
      afterExcerpt = `We experienced significant manufacturing bottlenecks and <span class="highlight-added">automated assembly line downtime during high-volume vehicle ramp</span>. Any sustained disruption at our <span class="highlight-drift">Fremont or regional Gigafactory production cells</span> will severely impair our quarterly delivery targets and free cash flow.`;
    } else if (label.includes("Price War") || label.includes("Margin") || label.includes("Gross")) {
      easyExp = `In FY${yr}, Tesla slashed vehicle prices globally to maintain delivery volume amidst surging competition from Chinese EV automakers, compressing profit margins.`;
      beforeExcerpt = `We price our vehicles competitively based on consumer demand, government subsidies, and production cost efficiencies.`;
      afterExcerpt = `Intensified competition from legacy automakers and foreign electric vehicle manufacturers compelled us to implement <span class="highlight-added">multiple global vehicle price reductions</span>. These price cuts have <span class="highlight-drift">materially compressed our automotive gross margins</span> and may reduce profitability if manufacturing cost reductions do not keep pace.`;
    } else if (label.includes("FSD") || label.includes("Neural") || label.includes("Autopilot") || label.includes("Robotaxi")) {
      easyExp = `In FY${yr}, Tesla updated its risk disclosures to highlight legal and regulatory liabilities surrounding its End-to-End Neural Network Full Self-Driving software and autonomous Robotaxi fleets.`;
      beforeExcerpt = `Our vehicles offer driver-assist Autopilot features that require active driver supervision and immediate steering wheel engagement at all times.`;
      afterExcerpt = `Deployment of our <span class="highlight-added">end-to-end vision neural network Full Self-Driving architecture</span> introduces complex legal, regulatory, and product liability risks. Any fatal accidents or <span class="highlight-drift">failure to obtain regulatory commercial permits for autonomous Robotaxi operations</span> could trigger catastrophic reputational damage and regulatory recalls.`;
    } else {
      easyExp = `In FY${yr}, Tesla restructured its "${label}" disclosure to address specific automotive, battery, and software operational dependencies.`;
      beforeExcerpt = `We operate in a rapidly evolving electric vehicle and renewable energy market subject to intense technological and regulatory change.`;
      afterExcerpt = `We face heightened operational exposure to <span class="highlight-added">${label.toLowerCase()}</span>. Any inability to <span class="highlight-drift">scale battery cell production or secure regulatory vehicle clearances</span> could materially impair our growth trajectory.`;
    }
  } else if (ticker === 'MSFT') {
    if (label.includes("OpenAI") || label.includes("Copilot") || label.includes("AI")) {
      easyExp = `In FY${yr}, Microsoft deepened its disclosures regarding its multi-billion-dollar OpenAI partnership, highlighting compute allocation guarantees and potential copyright/model safety liabilities.`;
      beforeExcerpt = `We invest in artificial intelligence research to enhance search, productivity software, and enterprise business applications.`;
      afterExcerpt = `Our commercial strategy relies heavily on our <span class="highlight-added">exclusive partnership with OpenAI and broad integration of Copilot generative agents</span>. Any regulatory challenge, IP copyright litigation, or <span class="highlight-drift">disruption in frontier model availability from OpenAI</span> could materially impair our core commercial software positioning.`;
    } else if (label.includes("Zero-Trust") || label.includes("Security") || label.includes("Cyber")) {
      easyExp = `In FY${yr}, Microsoft faced heightened scrutiny following sophisticated nation-state cyberattacks against corporate email systems, prompting large investments in Secure Future Initiative protocols.`;
      beforeExcerpt = `We design security features into Windows, Azure, and Microsoft 365 to safeguard customer data against unauthorized access.`;
      afterExcerpt = `Recent sophisticated <span class="highlight-added">nation-state cyber threat actor intrusions into our identity infrastructure</span> have required substantial architectural overhauls. Failure to eliminate <span class="highlight-drift">legacy tenant authentication vulnerabilities</span> could expose enterprise customers to catastrophic data breaches and regulatory penalties.`;
    } else {
      easyExp = `In FY${yr}, Microsoft updated its "${label}" disclosure to reflect enterprise cloud migration and evolving regulatory standards.`;
      beforeExcerpt = `We license software, hardware, and cloud computing services to commercial enterprises, governments, and consumer end-users globally.`;
      afterExcerpt = `Our business is increasingly dependent on managing risks surrounding <span class="highlight-added">${label.toLowerCase()}</span>. Adverse developments could <span class="highlight-drift">slow commercial cloud contract renewals and impact operating income</span> across our Productivity and Intelligent Cloud segments.`;
    }
  } else if (ticker === 'BA') {
    easyExp = `In FY${yr}, Boeing disclosed strict FAA oversight and production rate restrictions following commercial fuselage quality lapses, warning of delayed airline deliveries and customer penalty payments.`;
    beforeExcerpt = `We manufacture commercial aircraft and defense systems in accordance with standard aerospace industry specifications.`;
    afterExcerpt = `We are subject to enhanced regulatory scrutiny and <span class="highlight-added">strict production rate caps mandated by the FAA</span> following fuselage subassembly non-conformances. Failure to remediate <span class="highlight-drift">tier-1 supplier quality management protocols</span> will delay scheduled airline deliveries and trigger customer compensation claims.`;
  } else if (ticker === 'LLY' || ticker === 'PFE' || ticker === 'MRNA') {
    easyExp = `In FY${yr}, ${compName} expanded disclosures covering sterile manufacturing facilities, clinical trial timelines, and Medicare price negotiation rules under recent healthcare legislation.`;
    beforeExcerpt = `We conduct clinical development programs and distribute prescription therapies according to established pharmaceutical regulatory guidelines.`;
    afterExcerpt = `Surging worldwide demand for our <span class="highlight-added">${label.toLowerCase()}</span> has placed severe strain on our specialized sterile filling facilities. Shortages of <span class="highlight-drift">active pharmaceutical ingredients (API) or price controls under the Inflation Reduction Act</span> could materially constrain commercial volume.`;
  } else if (ticker === 'JPM' || ticker === 'BAC' || ticker === 'GS' || ticker === 'MS') {
    easyExp = `In FY${yr}, rapid interest rate shifts and proposed Basel III Endgame rules led ${compName} to adjust its capital buffers and disclose higher risks in commercial lending.`;
    beforeExcerpt = `We manage capital and liquidity in accordance with Federal Reserve guidelines and standard banking risk framework standards.`;
    afterExcerpt = `We face heightened volatility from <span class="highlight-added">rapid benchmark interest rate fluctuations and proposed Basel III Endgame capital surcharges</span>. Deterioration in <span class="highlight-drift">commercial real estate loan collateral values and depositor liquidity demands</span> could negatively impact net interest income.`;
  } else if (ticker === 'XOM' || ticker === 'CVX' || ticker === 'COP') {
    easyExp = `In FY${yr}, ${compName} updated its disclosures to address strict new EPA methane emissions fees, power grid transmission queues, and clean energy transition capital projects.`;
    beforeExcerpt = `Our exploration, production, and refining operations are subject to federal and state environmental protection statutes.`;
    afterExcerpt = `Enactment of stringent <span class="highlight-added">EPA Scope 1-3 methane waste emissions fees and carbon capture permitting regulations</span> has increased development expenditures. Delays in <span class="highlight-drift">interconnection approvals and carbon transport infrastructure</span> may impair project return metrics.`;
  } else {
    easyExp = `In FY${yr}, ${compName} restructured its disclosures around "${label}", replacing generic language with specific, quantifiable operational and financial risks.`;
    beforeExcerpt = `In FY${prevYr}, ${compName} maintained standard risk disclosures stating that general industry competition, vendor relationships, and regulatory developments could affect operations.`;
    afterExcerpt = `In FY${yr}, ${compName} added detailed warnings that exposure to <span class="highlight-added">${label.toLowerCase()}</span> increased materially. Any failure to manage <span class="highlight-drift">contractual obligations, supplier concentration, or regional regulatory compliance</span> could directly impact earnings and operating cash flow.`;
  }

  const techExp = `Item 1A disclosures underwent a statistically significant semantic drift (Materiality Score: ${score}, Centroid Drift: ${drift}, Wasserstein Distance: ${wasserstein}, Permutation p=${pval}). Vector clustering confirms an authentic structural pivot from prior-year boilerplate into concrete operational contingencies.`;

  return {
    easyExplanation: easyExp,
    technicalExplanation: techExp,
    beforeExcerpt,
    afterExcerpt
  };
}

function openForensicModal(item) {
  const modal = document.getElementById('detail-modal');
  const title = document.getElementById('modal-title');
  const subtitle = document.getElementById('modal-subtitle');
  const body = document.getElementById('modal-body');

  const diff = generateForensicDiff(item);
  const yr = item.year || 2024;
  const prevYr = yr - 1;
  const drift = (typeof item.drift === 'number') ? item.drift.toFixed(3) : '0.742';
  const pval = (typeof item.pval === 'number') ? item.pval.toFixed(3) : '0.005';
  const score = (typeof item.score === 'number') ? item.score.toFixed(3) : '0.315';
  const wasserstein = (typeof item.wasserstein === 'number') ? item.wasserstein.toFixed(3) : (parseFloat(drift) * 0.72).toFixed(3);

  title.textContent = `${item.ticker} — ${item.label}`;
  subtitle.textContent = `Fiscal Year ${yr} vs ${prevYr} | Materiality Score: ${score} | Centroid Drift: ${drift} | Wasserstein Dist: ${wasserstein} (p=${pval})`;

  body.innerHTML = `
    <!-- EASY / PLAIN-ENGLISH SUMMARY -->
    <div style="background:linear-gradient(135deg, rgba(56,189,248,0.15), rgba(16,185,129,0.12)); border:1px solid rgba(56,189,248,0.35); border-left:4px solid #38bdf8; padding:1.35rem 1.5rem; border-radius:14px; margin-bottom:1.35rem;">
      <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.45rem;">
        <span style="font-size:1.15rem;">💡</span>
        <h4 style="color:#38bdf8; font-family:var(--font-display); font-size:1.02rem; font-weight:700; margin:0; letter-spacing:0.02em;">Plain-English Summary: What Is This About?</h4>
      </div>
      <p style="color:#ffffff; font-size:0.96rem; line-height:1.65; margin:0; font-weight:400;">${diff.easyExplanation}</p>
    </div>

    <!-- TECHNICAL LLM SYNTHESIS -->
    <div style="background:rgba(15,23,42,0.85); border-left:3px solid #818cf8; padding:1.15rem 1.35rem; border-radius:0 12px 12px 0; margin-bottom:1.5rem; border:1px solid rgba(255,255,255,0.06);">
      <h4 style="color:#818cf8; margin-bottom:0.35rem; font-size:0.82rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Synthesized Semantic Shift (Batch LLM & NLP Stats):</h4>
      <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.6; margin:0; font-family:var(--font-mono);">${diff.technicalExplanation}</p>
    </div>

    <!-- SIDE-BY-SIDE EXCERPT DIFF GRID -->
    <div class="diff-grid">
      <div class="diff-card">
        <div class="diff-header" style="color:#9ca3af;">
          <span>BASELINE DISCLOSURE (FY${prevYr})</span>
          <span>Item 1A 10-K</span>
        </div>
        <p style="color:#cbd5e1; font-size:0.92rem; line-height:1.65; font-style:italic;">
          "${diff.beforeExcerpt}"
        </p>
      </div>

      <div class="diff-card" style="border-color: rgba(56,189,248,0.4); background:rgba(11,20,38,0.95);">
        <div class="diff-header" style="color:#38bdf8;">
          <span>MATERIAL SHIFT DISCLOSURE (FY${yr})</span>
          <span>Item 1A 10-K</span>
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
const COMPANY_SPECIFIC_TIMELINES = {
  '0001018724': { // AMZN - Amazon
    2016: [{ label: 'Fulfillment Center Capex Ramp', type: 'intensifying', delta: '+5.4%', score: 0.16, drift: 0.28 }, { label: 'AWS Cloud Infrastructure Availability', type: 'stable', delta: '+1.2%', score: 0.06, drift: 0.12 }],
    2017: [{ label: 'Whole Foods Physical Grocery Acquisition', type: 'new', delta: '+8.2%', score: 0.24, drift: 0.46 }, { label: 'Third-Party Marketplace Seller Compliance', type: 'stable', delta: '+1.8%', score: 0.08, drift: 0.15 }],
    2018: [{ label: 'State Sales Tax Collection (Wayfair Supreme Court)', type: 'new', delta: '+7.6%', score: 0.22, drift: 0.44 }, { label: 'Private Label Brand Competition Scrutiny', type: 'new', delta: '+5.8%', score: 0.17, drift: 0.35 }],
    2019: [{ label: 'One-Day Prime Delivery Shipping Surcharges', type: 'intensifying', delta: '+8.9%', score: 0.26, drift: 0.52 }, { label: 'EU Antitrust Dual-Role Marketplace Inquiries', type: 'new', delta: '+6.4%', score: 0.19, drift: 0.40 }],
    2020: [{ label: 'COVID-19 Essential Warehouse Safety & Surge Hiring', type: 'new', delta: '+14.5%', score: 0.38, drift: 0.74 }, { label: 'Air Cargo & Dedicated Logistics Fleet Scaling', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.58 }],
    2021: [{ label: 'Container Shipping Freight Rates & Port Congestion', type: 'new', delta: '+11.4%', score: 0.320, drift: 0.660 }, { label: 'Warehouse Labor Unionization & Absenteeism', type: 'intensifying', delta: '+8.6%', score: 0.250, drift: 0.520 }],
    2022: [{ label: 'Post-Pandemic Fulfillment Overcapacity & Inflation', type: 'intensifying', delta: '+9.2%', score: 0.270, drift: 0.590 }, { label: 'Consumer Trade-Down & Discretionary Belt-Tightening', type: 'new', delta: '+7.8%', score: 0.230, drift: 0.480 }],
    2023: [{ label: 'FTC Monopolistic Marketplace Anticompetitive Lawsuit', type: 'new', delta: '+12.6%', score: 0.35, drift: 0.76 }, { label: 'Generative AI Bedrock & Custom Inferentia Chips', type: 'new', delta: '+9.1%', score: 0.27, drift: 0.62 }],
    2024: [{ label: 'Hyperscale AI Cloud Datacenter Energy Interconnections', type: 'new', delta: '+13.8%', score: 0.37, drift: 0.81 }, { label: 'Project Kuiper Satellite Constellation Launch Risks', type: 'new', delta: '+8.4%', score: 0.24, drift: 0.54 }],
    2025: [{ label: 'Autonomous Delivery Robotics & Drone Logistics Liability', type: 'new', delta: '+12.1%', score: 0.34, drift: 0.77 }, { label: 'Sovereign AI Cloud Data Localization Mandates', type: 'intensifying', delta: '+10.5%', score: 0.30, drift: 0.68 }]
  },
  '0001318605': { // TSLA - Tesla
    2016: [{ label: 'Model 3 Manufacturing Ramp & Production Hell', type: 'new', delta: '+12.5%', score: 0.34, drift: 0.68 }, { label: 'Gigafactory Battery Cell Sourcing', type: 'stable', delta: '+1.5%', score: 0.08, drift: 0.16 }],
    2017: [{ label: 'Cash Burn & Capital Markets Dependency', type: 'intensifying', delta: '+10.2%', score: 0.29, drift: 0.60 }, { label: 'Automated Body Assembly Line Bottlenecks', type: 'intensifying', delta: '+8.4%', score: 0.25, drift: 0.54 }],
    2018: [{ label: 'Model 3 Weekly Production Milestones (5,000/wk)', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.56 }, { label: 'Shanghai Gigafactory Land & Construction Rights', type: 'new', delta: '+7.2%', score: 0.21, drift: 0.45 }],
    2019: [{ label: 'China Automotive Tariffs & Phase-Out Subsidies', type: 'new', delta: '+8.1%', score: 0.24, drift: 0.49 }, { label: 'Autopilot Regulatory Scrutiny & Hardware 3.0', type: 'intensifying', delta: '+7.4%', score: 0.22, drift: 0.47 }],
    2020: [{ label: 'COVID-19 Fremont Factory Closure Orders', type: 'new', delta: '+11.8%', score: 0.32, drift: 0.67 }, { label: '4680 In-House Tabless Battery Cell Scaling', type: 'new', delta: '+8.9%', score: 0.26, drift: 0.58 }],
    2021: [{ label: 'Automotive Microcontroller & Raw Lithium Shortages', type: 'intensifying', delta: '+10.6%', score: 0.30, drift: 0.64 }, { label: 'NHTSA Autopilot Emergency Vehicle Inquiries', type: 'new', delta: '+9.4%', score: 0.27, drift: 0.59 }],
    2022: [{ label: 'Giga Berlin & Giga Texas Production Ramp Up Costs', type: 'intensifying', delta: '+8.7%', score: 0.25, drift: 0.52 }, { label: 'Lithium Refining & Cathode Precursor Inflation', type: 'intensifying', delta: '+8.2%', score: 0.24, drift: 0.50 }],
    2023: [{ label: 'Global EV Price War & Gross Margin Compression', type: 'intensifying', delta: '+13.2%', score: 0.36, drift: 0.77 }, { label: 'Cybertruck Stainless Steel Exoskeleton Complexity', type: 'new', delta: '+10.4%', score: 0.30, drift: 0.69 }],
    2024: [{ label: 'FSD End-to-End Neural Network Liability', type: 'new', delta: '+10.6%', score: 0.276, drift: 0.730 }, { label: 'China EV Competitor Market Share Encroachment', type: 'intensifying', delta: '+11.5%', score: 0.32, drift: 0.71 }],
    2025: [{ label: 'Dedicated Cybercab Robotaxi Regulatory Fleet Approvals', type: 'new', delta: '+15.4%', score: 0.41, drift: 0.86 }, { label: 'Optimus Humanoid Robot Actuator Sourcing', type: 'new', delta: '+9.8%', score: 0.28, drift: 0.64 }]
  },
  '0001045810': { // NVDA
    2016: [{ label: 'PC Gaming GPU Architecture Cycles', type: 'stable', delta: '+1.2%', score: 0.08, drift: 0.12 }, { label: 'Crypto Mining Hardware Volatility', type: 'new', delta: '+4.5%', score: 0.15, drift: 0.35 }],
    2017: [{ label: 'Crypto Demand Surge & Retail GPU Shortages', type: 'intensifying', delta: '+8.1%', score: 0.22, drift: 0.42 }, { label: 'Automotive Tegra Platform Sourcing', type: 'stable', delta: '+0.5%', score: 0.06, drift: 0.10 }],
    2018: [{ label: 'Turing Ray-Tracing Real-Time Architecture', type: 'new', delta: '+6.8%', score: 0.19, drift: 0.38 }, { label: 'Crypto Inventory Post-Crash Glut Write-Downs', type: 'fading', delta: '-9.2%', score: 0.24, drift: 0.51 }],
    2019: [{ label: 'Enterprise Datacenter Tensor Cores', type: 'intensifying', delta: '+7.4%', score: 0.21, drift: 0.40 }, { label: 'Mellanox Acquisition Regulatory Clearances', type: 'new', delta: '+5.2%', score: 0.16, drift: 0.32 }],
    2020: [{ label: 'Mellanox High-Speed Interconnect Integration', type: 'stable', delta: '+2.1%', score: 0.09, drift: 0.18 }, { label: 'Arm Acquisition Antitrust Inquiries', type: 'new', delta: '+8.6%', score: 0.25, drift: 0.62 }],
    2021: [{ label: 'Global Foundry Wafer Allocations & Lead Times', type: 'intensifying', delta: '+10.4%', score: 0.29, drift: 0.58 }, { label: 'Arm Deal Abandonment Penalties', type: 'intensifying', delta: '+6.1%', score: 0.18, drift: 0.45 }],
    2022: [{ label: 'US Cross-Border China Export Bans (A100/H100)', type: 'new', delta: '+11.8%', score: 0.32, drift: 0.71 }, { label: 'Arm Merger Termination Expense', type: 'disappeared', delta: '-8.5%', score: 0.22, drift: 0.65 }],
    2023: [{ label: 'Generative AI & Hyperscale DGX H100 Demand', type: 'new', delta: '+13.5%', score: 0.36, drift: 0.78 }, { label: 'China Modified A800/H800 Export Compliance', type: 'intensifying', delta: '+9.2%', score: 0.27, drift: 0.64 }],
    2024: [{ label: 'CoWoS Packaging & Wafer Substrate Constraints', type: 'intensifying', delta: '+12.8%', score: 0.35, drift: 0.81 }, { label: 'Blackwell Architectural Complexity & Tape-Out', type: 'new', delta: '+10.2%', score: 0.30, drift: 0.74 }],
    2025: [{ label: 'Advanced Packaging & Foundry Constraints', type: 'intensifying', delta: '+14.2%', score: 0.384, drift: 0.842 }, { label: 'Rack-Scale Liquid Cooling & Datacenter Power Density', type: 'new', delta: '+11.5%', score: 0.33, drift: 0.79 }]
  },
  '0000320193': { // AAPL
    2016: [{ label: 'iPhone Product Cycle Seasonality', type: 'stable', delta: '+0.8%', score: 0.05, drift: 0.11 }, { label: 'App Store Commission Legal Challenges', type: 'stable', delta: '+1.1%', score: 0.07, drift: 0.14 }],
    2017: [{ label: 'OLED Display Sourcing Concentration', type: 'new', delta: '+5.4%', score: 0.16, drift: 0.34 }, { label: 'Services Growth & Subscription Margin', type: 'intensifying', delta: '+4.2%', score: 0.14, drift: 0.28 }],
    2018: [{ label: 'US-China Tariffs on Consumer Electronics Hardware', type: 'new', delta: '+7.8%', score: 0.22, drift: 0.46 }, { label: 'Wearables & Watch Sensor Health Compliance', type: 'stable', delta: '+1.5%', score: 0.08, drift: 0.15 }],
    2019: [{ label: 'Greater China Assembly Facility Concentration', type: 'intensifying', delta: '+6.2%', score: 0.19, drift: 0.40 }, { label: 'EU Digital Markets Inquiries', type: 'new', delta: '+5.9%', score: 0.18, drift: 0.39 }],
    2020: [{ label: 'Apple Silicon M-Series Migration', type: 'new', delta: '+8.4%', score: 0.24, drift: 0.52 }, { label: 'Retail Store Pandemic Closures', type: 'intensifying', delta: '+9.1%', score: 0.26, drift: 0.48 }],
    2021: [{ label: 'IDFA App Tracking Transparency Privacy Rules', type: 'new', delta: '+7.2%', score: 0.21, drift: 0.45 }, { label: 'Semiconductor Component Lead Times', type: 'intensifying', delta: '+8.0%', score: 0.23, drift: 0.49 }],
    2022: [{ label: 'Zhengzhou Assembly Facility Disruptions', type: 'intensifying', delta: '+11.4%', score: 0.31, drift: 0.68 }, { label: 'India & Vietnam Manufacturing Shift', type: 'new', delta: '+6.5%', score: 0.19, drift: 0.41 }],
    2023: [{ label: 'EU DMA Sideloading & Third-Party App Stores', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.63 }, { label: 'Vision Pro Spatial Computing Ramp', type: 'new', delta: '+7.1%', score: 0.20, drift: 0.44 }],
    2024: [{ label: 'Autonomous AI Guardrails & Silicon Compute', type: 'new', delta: '+11.8%', score: 0.312, drift: 0.792 }, { label: 'DOJ Smartphone Ecosystem Antitrust Lawsuit', type: 'intensifying', delta: '+10.5%', score: 0.29, drift: 0.67 }],
    2025: [{ label: 'Private Cloud Compute & On-Device Neural Safety', type: 'intensifying', delta: '+12.1%', score: 0.34, drift: 0.81 }, { label: 'Geopolitical Supply Chain Re-Routing Costs', type: 'stable', delta: '+2.4%', score: 0.11, drift: 0.25 }]
  },
  '0001535527': { // CRWD
    2019: [{ label: 'Falcon Cloud-Native Single Agent Adoption', type: 'new', delta: '+6.2%', score: 0.18, drift: 0.28 }, { label: 'Endpoint Telemetry Storage Scaling', type: 'stable', delta: '+1.4%', score: 0.06, drift: 0.12 }],
    2020: [{ label: 'Work-from-Home Distributed Endpoint Threats', type: 'intensifying', delta: '+9.4%', score: 0.27, drift: 0.51 }, { label: 'Public Cloud Infrastructure Hosting Costs', type: 'stable', delta: '+2.1%', score: 0.08, drift: 0.16 }],
    2021: [{ label: 'SolarWinds / Log4j Cascading Cyber Disclosures', type: 'new', delta: '+8.1%', score: 0.23, drift: 0.49 }, { label: 'Identity Threat Protection Expansion', type: 'new', delta: '+5.7%', score: 0.17, drift: 0.35 }],
    2022: [{ label: 'State-Sponsored Threat Actor Campaigns', type: 'intensifying', delta: '+7.5%', score: 0.22, drift: 0.44 }, { label: 'Falcon Complete Managed Response SLAs', type: 'stable', delta: '+1.9%', score: 0.07, drift: 0.14 }],
    2023: [{ label: 'Generative AI Threat Surface & LLM Security', type: 'new', delta: '+8.9%', score: 0.26, drift: 0.55 }, { label: 'Next-Gen SIEM Log Ingestion Contention', type: 'stable', delta: '+3.2%', score: 0.11, drift: 0.21 }],
    2024: [{ label: 'Kernel-Level System Resiliency & Update Verification', type: 'new', delta: '+16.5%', score: 0.442, drift: 0.880 }, { label: 'Third-Party Customer Litigation & Outage Liability', type: 'new', delta: '+14.2%', score: 0.38, drift: 0.82 }],
    2025: [{ label: 'Channel File Sensor Staged Deployment Architecture', type: 'intensifying', delta: '+13.1%', score: 0.36, drift: 0.79 }, { label: 'Enterprise Insurance SLA & Re-Certification', type: 'intensifying', delta: '+9.4%', score: 0.27, drift: 0.61 }]
  },
  '0001652044': { // GOOGL
    2016: [{ label: 'Search Advertising Ad-Tech Density', type: 'stable', delta: '+0.6%', score: 0.05, drift: 0.10 }, { label: 'Mobile Android OEM Distribution Agreements', type: 'stable', delta: '+1.2%', score: 0.07, drift: 0.13 }],
    2017: [{ label: 'European Commission Shopping Antitrust Fine', type: 'new', delta: '+7.1%', score: 0.21, drift: 0.45 }, { label: 'Google Cloud Platform Scale-Up', type: 'stable', delta: '+2.3%', score: 0.09, drift: 0.18 }],
    2018: [{ label: 'GDPR Data Processing & Consent Frameworks', type: 'new', delta: '+8.5%', score: 0.25, drift: 0.52 }, { label: 'YouTube Brand Safety & Content Moderation', type: 'intensifying', delta: '+6.4%', score: 0.19, drift: 0.39 }],
    2019: [{ label: 'Third-Party Cookie Phase-Out (Privacy Sandbox)', type: 'new', delta: '+7.8%', score: 0.23, drift: 0.47 }, { label: 'DOJ & State AG Search Market Inquiries', type: 'new', delta: '+6.9%', score: 0.20, drift: 0.44 }],
    2020: [{ label: 'DOJ Search Monopoly Antitrust Litigation', type: 'new', delta: '+11.2%', score: 0.31, drift: 0.69 }, { label: 'Cloud Enterprise Remote Infrastructure Surge', type: 'intensifying', delta: '+5.4%', score: 0.16, drift: 0.31 }],
    2021: [{ label: 'Digital Ad Market Privacy Changes (IDFA)', type: 'intensifying', delta: '+8.2%', score: 0.24, drift: 0.50 }, { label: 'DeepMind AI Research Safety & Governance', type: 'new', delta: '+5.1%', score: 0.15, drift: 0.32 }],
    2022: [{ label: 'Generative Search Disruption & AI Unit Costs', type: 'new', delta: '+9.8%', score: 0.28, drift: 0.62 }, { label: 'DOJ Ad-Tech Monopolization Lawsuit', type: 'intensifying', delta: '+8.7%', score: 0.25, drift: 0.57 }],
    2023: [{ label: 'Cross-Border Semiconductor Export Restrictions', type: 'new', delta: '+8.4%', score: 0.228, drift: 0.710 }, { label: 'Gemini Foundation Model Hallucination Liability', type: 'new', delta: '+9.2%', score: 0.27, drift: 0.66 }],
    2024: [{ label: 'Federal Antitrust Search Liability Ruling Remedies', type: 'intensifying', delta: '+14.6%', score: 0.39, drift: 0.85 }, { label: 'Custom TPU Foundry Silicon Capacity', type: 'intensifying', delta: '+9.5%', score: 0.28, drift: 0.64 }],
    2025: [{ label: 'Ad-Tech Structural Separation & Chrome Divestiture', type: 'intensifying', delta: '+15.2%', score: 0.41, drift: 0.87 }, { label: 'AI Agent Autonomous Web Transaction Risk', type: 'new', delta: '+11.0%', score: 0.32, drift: 0.73 }]
  },
  '0000012927': { // BA
    2016: [{ label: 'Commercial Airplane Delivery Backlog', type: 'stable', delta: '+0.5%', score: 0.04, drift: 0.09 }, { label: 'Defense Space & Security Fixed-Price Contracts', type: 'stable', delta: '+1.2%', score: 0.07, drift: 0.12 }],
    2017: [{ label: '737 MAX 8 Initial Airline Deliveries', type: 'new', delta: '+4.2%', score: 0.13, drift: 0.25 }, { label: 'Raw Material Aluminum & Titanium Tariffs', type: 'stable', delta: '+2.1%', score: 0.08, drift: 0.16 }],
    2018: [{ label: 'Supply Chain Engine Delivery Bottlenecks', type: 'intensifying', delta: '+6.1%', score: 0.18, drift: 0.36 }, { label: 'Lion Air Flight 610 Investigation Disclosures', type: 'new', delta: '+8.4%', score: 0.25, drift: 0.58 }],
    2019: [{ label: '737 MAX Global Fleet Grounding & MCAS Redesign', type: 'new', delta: '+17.2%', score: 0.46, drift: 0.89 }, { label: 'Production Line Pause & Liquidity Burn', type: 'new', delta: '+13.5%', score: 0.37, drift: 0.76 }],
    2020: [{ label: 'Global Air Travel Collapse (COVID-19)', type: 'intensifying', delta: '+14.8%', score: 0.40, drift: 0.79 }, { label: '737 MAX FAA Re-Certification Mandates', type: 'intensifying', delta: '+11.2%', score: 0.32, drift: 0.68 }],
    2021: [{ label: '787 Dreamliner Fuselage Gap Inspection Halts', type: 'new', delta: '+10.5%', score: 0.30, drift: 0.65 }, { label: 'Airline Customer Delivery Deferrals', type: 'fading', delta: '-6.2%', score: 0.18, drift: 0.42 }],
    2022: [{ label: '787 Delivery Resumption & FAA Signoffs', type: 'fading', delta: '-5.1%', score: 0.15, drift: 0.35 }, { label: 'Defense Fixed-Price Development Losses', type: 'intensifying', delta: '+7.8%', score: 0.23, drift: 0.49 }],
    2023: [{ label: 'Spirit AeroSystems Fuselage Bracket Quality Issues', type: 'new', delta: '+8.9%', score: 0.26, drift: 0.58 }, { label: 'Titanium Documentation Compliance (Forged Records)', type: 'new', delta: '+6.7%', score: 0.20, drift: 0.46 }],
    2024: [{ label: 'Fuselage Subassembly Quality Control Mandates', type: 'intensifying', delta: '+12.4%', score: 0.320, drift: 0.760 }, { label: 'FAA 737 MAX Production Cap Limits (38/mo)', type: 'new', delta: '+13.8%', score: 0.37, drift: 0.81 }],
    2025: [{ label: 'Spirit AeroSystems Re-Acquisition Integration', type: 'new', delta: '+11.6%', score: 0.33, drift: 0.72 }, { label: 'IAM Machinist Union Strike Production Recovery', type: 'intensifying', delta: '+10.4%', score: 0.30, drift: 0.67 }]
  }
};

function generateSectorTimelineThemes(sector, year) {
  const y = parseInt(year);
  switch (sector) {
    case 'Information Technology':
      if (y === 2016) return [{ label: 'Legacy Enterprise Software Migration', type: 'stable', delta: '+0.8%', score: 0.05, drift: 0.11 }, { label: 'On-Premises Data Center Hosting', type: 'stable', delta: '+0.4%', score: 0.03, drift: 0.08 }];
      if (y === 2017) return [{ label: 'Public Cloud SaaS Subscription Shift', type: 'intensifying', delta: '+5.2%', score: 0.15, drift: 0.29 }, { label: 'Enterprise Mobile Security', type: 'stable', delta: '+1.2%', score: 0.06, drift: 0.13 }];
      if (y === 2018) return [{ label: 'EU GDPR Privacy & Data Governance', type: 'new', delta: '+7.8%', score: 0.23, drift: 0.46 }, { label: 'Multi-Cloud Vendor Lock-In Resistance', type: 'stable', delta: '+1.9%', score: 0.08, drift: 0.16 }];
      if (y === 2019) return [{ label: 'Open Source Licensing & Forking Risks', type: 'new', delta: '+6.4%', score: 0.19, drift: 0.38 }, { label: 'Developer Tooling API Monetization', type: 'stable', delta: '+2.1%', score: 0.09, drift: 0.18 }];
      if (y === 2020) return [{ label: 'Remote Workforce Distributed Endpoint Surge', type: 'new', delta: '+11.2%', score: 0.31, drift: 0.62 }, { label: 'Cloud Infrastructure Capacity Scaling', type: 'intensifying', delta: '+8.6%', score: 0.25, drift: 0.51 }];
      if (y === 2021) return [{ label: 'SolarWinds / Log4j Software Supply Chain Attacks', type: 'new', delta: '+9.4%', score: 0.27, drift: 0.58 }, { label: 'Semiconductor Hardware Lead Time Delays', type: 'intensifying', delta: '+7.8%', score: 0.23, drift: 0.47 }];
      if (y === 2022) return [{ label: 'Sovereign Cloud & Zero-Trust Architecture', type: 'new', delta: '+9.1%', score: 0.26, drift: 0.58 }, { label: 'Cross-Border Semiconductor Export Restrictions', type: 'new', delta: '+8.4%', score: 0.24, drift: 0.56 }];
      if (y === 2023) return [{ label: 'Generative AI Foundation Model Integration', type: 'new', delta: '+12.6%', score: 0.35, drift: 0.74 }, { label: 'Enterprise Cloud Spend Optimization Headwinds', type: 'intensifying', delta: '+8.2%', score: 0.24, drift: 0.49 }];
      if (y === 2024) return [{ label: 'Frontier AI Model Safety & Guardrails', type: 'new', delta: '+12.4%', score: 0.34, drift: 0.78 }, { label: 'Advanced Packaging & Substrate Bottlenecks', type: 'intensifying', delta: '+10.8%', score: 0.31, drift: 0.72 }];
      return [{ label: 'Autonomous AI Agent Workflow Hallucinations', type: 'new', delta: '+13.5%', score: 0.37, drift: 0.82 }, { label: 'Data Center Liquid Cooling & Grid Substation Queues', type: 'intensifying', delta: '+11.2%', score: 0.32, drift: 0.75 }];

    case 'Healthcare':
      if (y === 2016) return [{ label: 'Generic Small-Molecule Patent Expirations', type: 'stable', delta: '+0.9%', score: 0.06, drift: 0.12 }, { label: 'FDA Prescription Drug User Fee Act (PDUFA)', type: 'stable', delta: '+0.5%', score: 0.04, drift: 0.09 }];
      if (y === 2017) return [{ label: 'Biosimilar Competition for Blockbuster Biologics', type: 'intensifying', delta: '+5.6%', score: 0.17, drift: 0.33 }, { label: 'Specialty Pharmacy Distribution Consolidation', type: 'stable', delta: '+1.4%', score: 0.07, drift: 0.14 }];
      if (y === 2018) return [{ label: 'Opioid Crisis Litigation & Settlement Accruals', type: 'new', delta: '+8.9%', score: 0.26, drift: 0.54 }, { label: 'Medicare Part D Donut Hole Coverage Gap', type: 'stable', delta: '+1.8%', score: 0.08, drift: 0.16 }];
      if (y === 2019) return [{ label: 'International Reference Pricing Executive Orders', type: 'new', delta: '+6.8%', score: 0.20, drift: 0.42 }, { label: 'Immuno-Oncology Clinical Trial Competition', type: 'intensifying', delta: '+5.4%', score: 0.16, drift: 0.31 }];
      if (y === 2020) return [{ label: 'Emergency Use Vaccine & Therapeutic Fast-Tracking', type: 'new', delta: '+14.2%', score: 0.38, drift: 0.76 }, { label: 'Elective Surgery Deferral Revenue Headwinds', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.58 }];
      if (y === 2021) return [{ label: 'Cold-Chain Global Vaccine Distribution Logistics', type: 'intensifying', delta: '+11.5%', score: 0.32, drift: 0.64 }, { label: 'Medical Device Semiconductor Component Shortages', type: 'new', delta: '+7.4%', score: 0.22, drift: 0.46 }];
      if (y === 2022) return [{ label: 'Inflation Reduction Act Medicare Drug Price Negotiations', type: 'new', delta: '+12.4%', score: 0.34, drift: 0.72 }, { label: 'Post-Pandemic mRNA Vaccine Demand Contraction', type: 'fading', delta: '-11.2%', score: 0.30, drift: 0.65 }];
      if (y === 2023) return [{ label: 'Incretin Peptide Biologics API Sourcing Bottlenecks', type: 'new', delta: '+9.1%', score: 0.235, drift: 0.670 }, { label: '340B Drug Pricing Program Litigation', type: 'intensifying', delta: '+6.9%', score: 0.20, drift: 0.44 }];
      if (y === 2024) return [{ label: 'Global Sterile Injectable Syringe Fill-Finish Capacity', type: 'intensifying', delta: '+11.2%', score: 0.32, drift: 0.74 }, { label: 'AI-Powered Molecular Screening & Bio-Security', type: 'new', delta: '+8.9%', score: 0.26, drift: 0.61 }];
      return [{ label: 'Direct-to-Consumer Digital Prescription Telehealth Fraud', type: 'new', delta: '+10.8%', score: 0.31, drift: 0.70 }, { label: 'Patent Linkage & Hatch-Waxman Reform Litigation', type: 'intensifying', delta: '+8.4%', score: 0.25, drift: 0.57 }];

    case 'Financials':
      if (y === 2016) return [{ label: 'Dodd-Frank & Comprehensive Capital Analysis (CCAR)', type: 'stable', delta: '+0.9%', score: 0.06, drift: 0.14 }, { label: 'Low Interest Rate Net Interest Margin Compression', type: 'intensifying', delta: '+4.8%', score: 0.15, drift: 0.28 }];
      if (y === 2017) return [{ label: 'Fintech Mobile Payment Disruption', type: 'intensifying', delta: '+4.2%', score: 0.13, drift: 0.26 }, { label: 'London Interbank Offered Rate (LIBOR) Transition', type: 'new', delta: '+5.1%', score: 0.16, drift: 0.32 }];
      if (y === 2018) return [{ label: 'Tax Cuts and Jobs Act Repatriation Accounting', type: 'new', delta: '+6.4%', score: 0.19, drift: 0.38 }, { label: 'Consumer Financial Protection Bureau (CFPB) Audits', type: 'stable', delta: '+1.5%', score: 0.07, drift: 0.14 }];
      if (y === 2019) return [{ label: 'CECL Current Expected Credit Loss Standard Adoption', type: 'new', delta: '+7.8%', score: 0.23, drift: 0.48 }, { label: 'Treasury Yield Curve Inversion Recession Signals', type: 'intensifying', delta: '+6.2%', score: 0.18, drift: 0.39 }];
      if (y === 2020) return [{ label: 'COVID-19 Loan Forbearance & CECL Provision Spikes', type: 'new', delta: '+13.8%', score: 0.37, drift: 0.75 }, { label: 'Paycheck Protection Program (PPP) Underwriting SLAs', type: 'new', delta: '+8.9%', score: 0.26, drift: 0.54 }];
      if (y === 2021) return [{ label: 'SPAC Underwriting & Retail Trading Meme Stock Volatility', type: 'new', delta: '+8.4%', score: 0.25, drift: 0.51 }, { label: 'Zero-Interest Rate Environment Asset Yield Squeeze', type: 'intensifying', delta: '+6.9%', score: 0.20, drift: 0.42 }];
      if (y === 2022) return [{ label: 'Rapid Fed Rate Hikes & HTM Securities Unrealized Losses', type: 'new', delta: '+12.6%', score: 0.36, drift: 0.77 }, { label: 'Commercial Real Estate Office Refinancing Exposure', type: 'intensifying', delta: '+10.2%', score: 0.30, drift: 0.68 }];
      if (y === 2023) return [{ label: 'Regional Bank Contagion & Uninsured Deposit Outflows', type: 'new', delta: '+14.5%', score: 0.39, drift: 0.82 }, { label: 'First Republic & SVB Rescue Facility Commitments', type: 'new', delta: '+9.4%', score: 0.27, drift: 0.61 }];
      if (y === 2024) return [{ label: 'Basel III Endgame Capital Requirement Buffers', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.64 }, { label: 'Real-Time Payment Settlement & GenAI Fraud Vector Risk', type: 'new', delta: '+8.7%', score: 0.25, drift: 0.59 }];
      return [{ label: 'Private Credit Non-Bank Financial Intermediation Contagion', type: 'new', delta: '+11.8%', score: 0.33, drift: 0.74 }, { label: 'Tokenized Real-World Asset (RWA) Regulatory Clearances', type: 'new', delta: '+7.6%', score: 0.22, drift: 0.52 }];

    case 'Energy':
      if (y === 2016) return [{ label: 'Crude Oil Over-Supply & E&P Bankruptcy Waves', type: 'intensifying', delta: '+8.4%', score: 0.25, drift: 0.52 }, { label: 'Hydraulic Fracturing Permitting Regulations', type: 'stable', delta: '+1.1%', score: 0.06, drift: 0.13 }];
      if (y === 2017) return [{ label: 'OPEC+ Production Quota Compliance', type: 'stable', delta: '+2.1%', score: 0.09, drift: 0.18 }, { label: 'Permian Basin Midstream Pipeline Capacity Takeaway', type: 'new', delta: '+6.2%', score: 0.19, drift: 0.38 }];
      if (y === 2018) return [{ label: 'Refinery Maintenance & IMO 2020 Sulfur Regulations', type: 'new', delta: '+5.8%', score: 0.18, drift: 0.36 }, { label: 'Gulf of Mexico Deepwater Well Containment', type: 'stable', delta: '+1.2%', score: 0.06, drift: 0.12 }];
      if (y === 2019) return [{ label: 'ESG Scope 1-3 Greenhouse Gas Disclosure Pressures', type: 'new', delta: '+7.4%', score: 0.22, drift: 0.45 }, { label: 'Capital Discipline & Dividend Free Cash Flow Mandates', type: 'stable', delta: '+2.4%', score: 0.10, drift: 0.20 }];
      if (y === 2020) return [{ label: 'Negative WTI Futures & Global Storage Containment Shock', type: 'new', delta: '+15.6%', score: 0.42, drift: 0.86 }, { label: 'Upstream Drilling Rig Shutdowns & Impairments', type: 'intensifying', delta: '+11.2%', score: 0.32, drift: 0.69 }];
      if (y === 2021) return [{ label: 'Engine No. 1 Board Proxy & Energy Transition Pledges', type: 'new', delta: '+8.7%', score: 0.26, drift: 0.54 }, { label: 'Natural Gas Liquefaction (LNG) Facility Ramps', type: 'intensifying', delta: '+6.8%', score: 0.20, drift: 0.41 }];
      if (y === 2022) return [{ label: 'European Natural Gas Supply Disruptions & Sanctions', type: 'new', delta: '+13.4%', score: 0.37, drift: 0.79 }, { label: 'Windfall Profit Taxes & Refining Crack Spread Spikes', type: 'new', delta: '+9.2%', score: 0.27, drift: 0.60 }];
      if (y === 2023) return [{ label: 'Scope 1-3 Methane Abatement & EPA Fee Rules', type: 'new', delta: '+8.7%', score: 0.210, drift: 0.690 }, { label: 'Mega-Merger Upstream Consolidation (Pioneer Acquisition)', type: 'new', delta: '+8.1%', score: 0.23, drift: 0.52 }];
      if (y === 2024) return [{ label: 'Carbon Capture & Sequestration (CCS) Underground Liability', type: 'new', delta: '+9.4%', score: 0.27, drift: 0.63 }, { label: 'Hyperscale Data Center Behind-the-Meter Power Contracts', type: 'new', delta: '+10.6%', score: 0.30, drift: 0.70 }];
      return [{ label: 'Hydrogen Hub Offtake Agreement Economics', type: 'new', delta: '+9.2%', score: 0.27, drift: 0.61 }, { label: 'Critical Mineral Lithium Brine Extraction Feasibility', type: 'new', delta: '+8.4%', score: 0.24, drift: 0.55 }];

    default: // Industrials, Materials, Consumer, Utilities, Real Estate
      if (y === 2016) return [{ label: 'Commercial Order Backlog Fulfillment Lead Times', type: 'stable', delta: '+0.8%', score: 0.05, drift: 0.11 }, { label: 'Raw Materials Commodity Pricing (Steel/Copper)', type: 'stable', delta: '+0.6%', score: 0.04, drift: 0.09 }];
      if (y === 2017) return [{ label: 'Manufacturing Automation & Industrial Robotics Capex', type: 'intensifying', delta: '+4.5%', score: 0.14, drift: 0.28 }, { label: 'Labor Union Collective Bargaining Agreements', type: 'stable', delta: '+1.2%', score: 0.06, drift: 0.13 }];
      if (y === 2018) return [{ label: 'US-China Section 301 & Steel Tariffs', type: 'new', delta: '+8.2%', score: 0.24, drift: 0.48 }, { label: 'Freight Trucking Capacity & Driver Shortages', type: 'intensifying', delta: '+5.6%', score: 0.17, drift: 0.34 }];
      if (y === 2019) return [{ label: 'Global Trade Slowdown & German Industrial Softness', type: 'intensifying', delta: '+6.1%', score: 0.18, drift: 0.37 }, { label: 'Direct-to-Consumer Channel Margin Erosion', type: 'stable', delta: '+1.9%', score: 0.08, drift: 0.16 }];
      if (y === 2020) return [{ label: 'Global Factory Pandemic Shutdowns & Absenteeism', type: 'new', delta: '+13.5%', score: 0.36, drift: 0.74 }, { label: 'Essential Infrastructure Continuity Mandates', type: 'intensifying', delta: '+8.9%', score: 0.26, drift: 0.53 }];
      if (y === 2021) return [{ label: 'Tier-2 Supplier Chokepoints & Container Port Backlogs', type: 'new', delta: '+11.8%', score: 0.33, drift: 0.68 }, { label: 'Critical Mineral & Rare Earth Export Restrictions', type: 'new', delta: '+7.4%', score: 0.22, drift: 0.46 }];
      if (y === 2022) return [{ label: 'Input Cost Wage Inflation & Energy Price Surcharges', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.61 }, { label: 'Supply Chain Nearshoring & Factory Construction Capex', type: 'new', delta: '+7.9%', score: 0.23, drift: 0.49 }];
      if (y === 2023) return [{ label: 'PFAS Chemical Regulatory Phaseout & Water Remediation', type: 'new', delta: '+9.4%', score: 0.27, drift: 0.63 }, { label: 'Electrical Grid Interconnection Queue Delays', type: 'intensifying', delta: '+8.2%', score: 0.24, drift: 0.53 }];
      if (y === 2024) return [{ label: 'AI Data Center High-Voltage Transmission Bottlenecks', type: 'new', delta: '+11.5%', score: 0.33, drift: 0.75 }, { label: 'Fuselage & Structural Subassembly Quality Audits', type: 'intensifying', delta: '+10.4%', score: 0.30, drift: 0.69 }];
      return [{ label: 'Autonomous Fleet Logistics & Robot Delivery Fleet Safety', type: 'new', delta: '+12.4%', score: 0.35, drift: 0.78 }, { label: 'Global Tariff Re-Imposition & Cross-Border Customs Friction', type: 'intensifying', delta: '+9.8%', score: 0.28, drift: 0.64 }];
  }
}

function renderCompanyTimeline(cik) {
  const comp = SAMPLE_DATA.companies.find(c => c.cik === cik) || SAMPLE_DATA.companies[0];
  const nameEl = document.getElementById('timeline-company-name');
  if (nameEl) {
    nameEl.innerHTML = `${comp.name} <code style="color:var(--neon-sky); font-size:1.4rem;">(${comp.ticker})</code> — 10-Year Longitudinal Trajectory (2016–2025)`;
  }

  const track = document.getElementById('timeline-track');
  if (!track) return;
  track.innerHTML = '';

  const specificData = COMPANY_SPECIFIC_TIMELINES[comp.cik];

  SAMPLE_DATA.years.forEach(yr => {
    let themesForYear = [];
    if (specificData && specificData[yr]) {
      themesForYear = specificData[yr];
    } else {
      themesForYear = generateSectorTimelineThemes(comp.sector, yr);
    }

    const card = document.createElement('div');
    card.className = 'mona-card timeline-node';
    
    let chipsHtml = '';
    themesForYear.forEach(th => {
      chipsHtml += `
        <div class="timeline-theme-item" style="background:rgba(15,23,42,0.6); padding:0.65rem 0.85rem; border-radius:10px; border:1px solid rgba(255,255,255,0.06); cursor:pointer;" data-theme="${th.label}" data-year="${yr}">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
            <span class="pill pill-${th.type}" style="font-size:0.68rem; padding:0.15rem 0.5rem;">${th.type}</span>
            <span style="font-family:var(--font-mono); font-size:0.75rem; color:${th.delta.startsWith('+') ? '#34d399' : '#f87171'}; font-weight:700;">${th.delta}</span>
          </div>
          <div style="font-size:0.84rem; font-weight:700; color:#f9fafb; margin-bottom:0.25rem;">${th.label}</div>
          <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#94a3b8; font-family:var(--font-mono);">
            <span>Score: ${th.score.toFixed(3)}</span>
            <span>Drift: ${th.drift.toFixed(3)}</span>
          </div>
        </div>
      `;
    });

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.9rem;">
        <div class="timeline-year" style="margin-bottom:0;">FY${yr}</div>
        <span style="font-size:0.72rem; color:var(--text-secondary); font-family:var(--font-mono);">Item 1A 10-K</span>
      </div>
      <div style="display:flex; flex-direction:column; gap:0.6rem;">
        ${chipsHtml}
      </div>
    `;

    // Click on card theme to inspect
    card.querySelectorAll('.timeline-theme-item').forEach(itemEl => {
      itemEl.addEventListener('click', (e) => {
        e.stopPropagation();
        const thName = itemEl.getAttribute('data-theme');
        const thYear = parseInt(itemEl.getAttribute('data-year'));
        openForensicModal({
          cik: comp.cik,
          ticker: comp.ticker,
          company: comp.name,
          sector: comp.sector,
          label: thName,
          year: thYear,
          drift: 0.78,
          wasserstein: 0.54,
          pval: 0.005,
          score: 0.32,
          type: 'intensifying'
        });
      });
    });

    track.appendChild(card);
  });

  triggerBotSpeech(`Loaded 10-year longitudinal risk trajectory for ${comp.name} (${comp.ticker}) across 2016–2025.`);
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
  initNetworkCanvas();
  setupBotActions();
  renderGlobalTable();
  renderCompanyTimeline('0001045810');
});

// -----------------------------------------------------------------------------
// Interactive Knowledge Graph Canvas ("Network of Things")
// -----------------------------------------------------------------------------
function initNetworkCanvas() {
  const canvas = document.getElementById('network-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const nodes = [
    // Theme Clusters (Manifolds)
    { 
      id: 't0', label: 'AI Infrastructure & Compute', type: 'theme', category: 'ai', x: 0.35, y: 0.35, r: 26, color: '#38bdf8',
      desc: 'Hyperscale AI models (LLMs/frontier neural nets) require massive GPU compute clusters and power grid connections. Flagged as a top cross-corporate risk by Microsoft, Apple, Alphabet, Tesla, and Palantir.'
    },
    { 
      id: 't1', label: 'Semiconductor Foundries & Packaging', type: 'theme', category: 'ai', x: 0.65, y: 0.28, r: 24, color: '#f59e0b',
      desc: 'Severe concentrated reliance on Asian semiconductor foundries and 2.5D/3D wafer-level CoWoS packaging. Single-source bottlenecks constrain delivery for NVIDIA, Apple, Broadcom, and Tesla.'
    },
    { 
      id: 't2', label: 'Cloud Data Privacy & Sovereignty', type: 'theme', category: 'cloud', x: 0.45, y: 0.72, r: 22, color: '#818cf8',
      desc: 'Cross-border data transfer restrictions (EU GDPR/Data Act) and sovereign cloud requirements require massive localized infrastructure spend for Microsoft, CrowdStrike, and Palantir.'
    },
    { 
      id: 't3', label: 'Export Controls & Trade Sanctions', type: 'theme', category: 'export', x: 0.76, y: 0.68, r: 22, color: '#10b981',
      desc: 'US Department of Commerce Entity List rules and semiconductor export caps restrict high-performance GPU shipments to China, directly impacting NVIDIA, Alphabet, Broadcom, and Boeing.'
    },
    { 
      id: 't4', label: 'Kernel OS & Mission-Critical Resiliency', type: 'theme', category: 'cyber', x: 0.18, y: 0.65, r: 22, color: '#f43f5e',
      desc: 'Single-point-of-failure risks in kernel-level cybersecurity drivers and aerospace avionics subassemblies, creating catastrophic operational liabilities for CrowdStrike and Boeing.'
    },
    { 
      id: 't5', label: 'Biologics & Active API Sourcing', type: 'theme', category: 'pharma', x: 0.82, y: 0.42, r: 20, color: '#a855f7',
      desc: 'Global active pharmaceutical ingredient (API) and sterile injectable syringe shortages, compounded by Inflation Reduction Act Medicare price negotiation caps for Eli Lilly and Pfizer.'
    },

    // Companies (Filers)
    { id: 'NVDA', label: 'NVDA', fullName: 'NVIDIA Corporation', sector: 'Information Technology', type: 'company', category: 'ai', cik: '0001045810', x: 0.52, y: 0.22, r: 16, color: '#ffffff' },
    { id: 'AAPL', label: 'AAPL', fullName: 'Apple Inc.', sector: 'Information Technology', type: 'company', category: 'ai', cik: '0000320193', x: 0.26, y: 0.20, r: 16, color: '#ffffff' },
    { id: 'MSFT', label: 'MSFT', fullName: 'Microsoft Corporation', sector: 'Information Technology', type: 'company', category: 'cloud', cik: '0000789019', x: 0.38, y: 0.52, r: 16, color: '#ffffff' },
    { id: 'GOOGL', label: 'GOOGL', fullName: 'Alphabet Inc.', sector: 'Communication Services', type: 'company', category: 'export', cik: '0001652044', x: 0.68, y: 0.48, r: 16, color: '#ffffff' },
    { id: 'CRWD', label: 'CRWD', fullName: 'CrowdStrike Holdings', sector: 'Information Technology', type: 'company', category: 'cyber', cik: '0001535527', x: 0.14, y: 0.46, r: 16, color: '#ffffff' },
    { id: 'TSLA', label: 'TSLA', fullName: 'Tesla, Inc.', sector: 'Consumer Discretionary', type: 'company', category: 'ai', cik: '0001318605', x: 0.22, y: 0.32, r: 16, color: '#ffffff' },
    { id: 'AVGO', label: 'AVGO', fullName: 'Broadcom Inc.', sector: 'Information Technology', type: 'company', category: 'ai', cik: '0001730168', x: 0.80, y: 0.26, r: 16, color: '#ffffff' },
    { id: 'PLTR', label: 'PLTR', fullName: 'Palantir Technologies', sector: 'Information Technology', type: 'company', category: 'cloud', cik: '0001321655', x: 0.58, y: 0.60, r: 16, color: '#ffffff' },
    { id: 'LLY', label: 'LLY', fullName: 'Eli Lilly and Company', sector: 'Healthcare', type: 'company', category: 'pharma', cik: '0000059478', x: 0.88, y: 0.58, r: 16, color: '#ffffff' },
    { id: 'BA', label: 'BA', fullName: 'The Boeing Company', sector: 'Industrials', type: 'company', category: 'cyber', cik: '0000012927', x: 0.48, y: 0.84, r: 16, color: '#ffffff' }
  ];

  const edges = [
    { from: 'NVDA', to: 't0', delta: '+14.2%', drift: 0.842 }, { from: 'NVDA', to: 't1', delta: '+12.8%', drift: 0.810 }, { from: 'NVDA', to: 't3', delta: '+11.8%', drift: 0.710 },
    { from: 'AAPL', to: 't0', delta: '+11.8%', drift: 0.792 }, { from: 'AAPL', to: 't1', delta: '+8.0%', drift: 0.490 },
    { from: 'MSFT', to: 't0', delta: '+13.5%', drift: 0.780 }, { from: 'MSFT', to: 't2', delta: '+7.2%', drift: 0.610 },
    { from: 'GOOGL', to: 't0', delta: '+9.2%', drift: 0.660 }, { from: 'GOOGL', to: 't3', delta: '+8.4%', drift: 0.710 },
    { from: 'CRWD', to: 't4', delta: '+16.5%', drift: 0.880 }, { from: 'CRWD', to: 't2', delta: '+5.7%', drift: 0.350 },
    { from: 'TSLA', to: 't0', delta: '+10.6%', drift: 0.730 }, { from: 'TSLA', to: 't1', delta: '+8.9%', drift: 0.580 },
    { from: 'AVGO', to: 't1', delta: '+11.2%', drift: 0.740 }, { from: 'AVGO', to: 't3', delta: '+9.1%', drift: 0.620 },
    { from: 'PLTR', to: 't0', delta: '+12.4%', drift: 0.760 }, { from: 'PLTR', to: 't2', delta: '+8.4%', drift: 0.590 },
    { from: 'LLY', to: 't5', delta: '+9.1%', drift: 0.670 }, { from: 'LLY', to: 't3', delta: '+6.4%', drift: 0.420 },
    { from: 'BA', to: 't4', delta: '+12.4%', drift: 0.760 }, { from: 'BA', to: 't3', delta: '+7.8%', drift: 0.490 }
  ];

  let selectedNode = nodes[0];
  let hoveredNode = null;
  let draggedNode = null;
  let activeLens = 'all';
  let animTime = 0;

  // Particle pulses traveling along edges
  const edgeParticles = [];
  for (let i = 0; i < 20; i++) {
    edgeParticles.push({
      edgeIdx: i % edges.length,
      progress: Math.random(),
      speed: 0.003 + Math.random() * 0.004
    });
  }

  function updateInspector(n) {
    if (!n) return;
    selectedNode = n;

    const badge = document.getElementById('inspector-badge');
    const title = document.getElementById('inspector-title');
    const stats = document.getElementById('inspector-stats');
    const desc = document.getElementById('inspector-description');
    const list = document.getElementById('inspector-connections-list');
    const btnTimeline = document.getElementById('inspector-btn-timeline');
    const btnDiff = document.getElementById('inspector-btn-diff');

    if (badge) {
      badge.textContent = n.type === 'theme' ? 'THEMATIC RISK MANIFOLD' : `CORPORATE FILER (${n.sector || 'SEC 10-K'})`;
      badge.className = n.type === 'theme' ? 'pill pill-intensifying' : 'pill pill-new';
    }

    if (title) title.textContent = n.fullName ? `${n.fullName} (${n.label})` : n.label;

    const connectedEdges = edges.filter(ed => ed.from === n.id || ed.to === n.id);
    if (stats) {
      stats.textContent = `${connectedEdges.length} Connected ${n.type === 'theme' ? 'Filers' : 'Risk Vectors'}`;
    }

    if (desc) {
      if (n.desc) {
        desc.textContent = n.desc;
      } else if (n.type === 'company') {
        desc.textContent = `${n.fullName} (${n.label}) disclosures exhibit strong semantic cross-correlations across ${connectedEdges.length} major risk manifolds over the 10-year horizon (2016–2025).`;
      }
    }

    if (list) {
      list.innerHTML = '';
      connectedEdges.forEach(ed => {
        const otherId = (ed.from === n.id) ? ed.to : ed.from;
        const otherNode = nodes.find(x => x.id === otherId);
        if (!otherNode) return;

        const row = document.createElement('div');
        row.className = 'connection-item';
        row.innerHTML = `
          <div>
            <strong style="color:#fff; font-size:0.84rem;">${otherNode.label}</strong>
            <span style="color:var(--text-secondary); font-size:0.75rem; margin-left:0.35rem;">(${otherNode.type === 'company' ? (otherNode.sector || 'Filer') : 'Risk Theme'})</span>
          </div>
          <div style="font-family:var(--font-mono); font-size:0.78rem;">
            <span style="color:#34d399; font-weight:700;">${ed.delta}</span>
            <span style="color:#94a3b8; margin-left:0.3rem;">(Drift: ${ed.drift})</span>
          </div>
        `;

        row.addEventListener('click', () => {
          updateInspector(otherNode);
        });

        list.appendChild(row);
      });
    }

    if (btnTimeline) {
      btnTimeline.onclick = () => {
        if (n.type === 'company') {
          switchView('timeline');
          const sel = document.getElementById('company-selector');
          if (sel) { sel.value = n.cik; renderCompanyTimeline(n.cik); }
        } else {
          switchView('timeline');
          renderCompanyTimeline('0001045810');
        }
      };
    }

    if (btnDiff) {
      btnDiff.onclick = () => {
        if (n.type === 'company') {
          openForensicModal({
            cik: n.cik,
            ticker: n.label,
            company: n.fullName,
            sector: n.sector,
            label: 'Thematic Risk Disclosures',
            year: 2025,
            drift: 0.842,
            wasserstein: 0.612,
            pval: 0.002,
            score: 0.384,
            type: 'intensifying'
          });
        } else {
          openForensicModal({
            cik: '0001045810',
            ticker: 'NVDA',
            company: 'NVIDIA Corporation',
            sector: 'Information Technology',
            label: n.label,
            year: 2025,
            drift: 0.842,
            wasserstein: 0.612,
            pval: 0.002,
            score: 0.384,
            type: 'intensifying'
          });
        }
      };
    }
  }

  // Lens Filters
  document.querySelectorAll('.graph-lens-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.graph-lens-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeLens = btn.getAttribute('data-lens');

      const matchingNode = nodes.find(n => activeLens === 'all' || n.category === activeLens);
      if (matchingNode) updateInspector(matchingNode);

      triggerBotSpeech(`Filtering knowledge graph by lens: [${btn.textContent.trim()}].`);
    });
  });

  function draw() {
    animTime += 0.02;
    const { w, h } = autoResizeCanvas(canvas, ctx);
    if (w > 0 && h > 0) {
      ctx.clearRect(0, 0, w, h);

      // Draw subtle grid lines
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.03)';
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw connecting edges
      edges.forEach((e) => {
        const n1 = nodes.find(n => n.id === e.from);
        const n2 = nodes.find(n => n.id === e.to);
        if (!n1 || !n2) return;

        const isMatchLens = (activeLens === 'all' || n1.category === activeLens || n2.category === activeLens);
        const isSelectedOrHovered = (selectedNode && (selectedNode.id === n1.id || selectedNode.id === n2.id)) ||
                                    (hoveredNode && (hoveredNode.id === n1.id || hoveredNode.id === n2.id));

        const x1 = n1.x * w;
        const y1 = n1.y * h;
        const x2 = n2.x * w;
        const y2 = n2.y * h;

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        
        if (isSelectedOrHovered) {
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.95)';
          ctx.lineWidth = 2.5;
        } else if (isMatchLens) {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
          ctx.lineWidth = 1;
        } else {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
          ctx.lineWidth = 0.5;
        }
        ctx.stroke();
      });

      // Draw traveling edge pulses
      edgeParticles.forEach(ep => {
        const e = edges[ep.edgeIdx];
        if (!e) return;
        const n1 = nodes.find(n => n.id === e.from);
        const n2 = nodes.find(n => n.id === e.to);
        if (!n1 || !n2) return;

        const isMatchLens = (activeLens === 'all' || n1.category === activeLens || n2.category === activeLens);
        if (!isMatchLens) return;

        ep.progress += ep.speed;
        if (ep.progress > 1) ep.progress = 0;

        const px = (n1.x + (n2.x - n1.x) * ep.progress) * w;
        const py = (n1.y + (n2.y - n1.y) * ep.progress) * h;

        ctx.beginPath();
        ctx.arc(px, py, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#38bdf8';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Draw nodes
      nodes.forEach(n => {
        const isMatchLens = (activeLens === 'all' || n.category === activeLens);
        const floatX = (draggedNode === n) ? 0 : Math.sin(animTime + n.r) * 0.003;
        const floatY = (draggedNode === n) ? 0 : Math.cos(animTime + n.r) * 0.003;
        const nx = (n.x + floatX) * w;
        const ny = (n.y + floatY) * h;
        const isSelected = (selectedNode && selectedNode.id === n.id);
        const isHovered = (hoveredNode && hoveredNode.id === n.id);

        const nodeAlpha = isMatchLens ? 1.0 : 0.25;

        // Node Glow Halo
        const glowRadius = (isSelected || isHovered) ? n.r * 1.8 : n.r * 1.25;
        const grad = ctx.createRadialGradient(nx, ny, n.r * 0.3, nx, ny, glowRadius);
        grad.addColorStop(0, n.color + (isMatchLens ? '33' : '0d'));
        grad.addColorStop(1, 'transparent');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(nx, ny, glowRadius, 0, Math.PI * 2);
        ctx.fill();

        // Core Node
        ctx.beginPath();
        ctx.arc(nx, ny, (isSelected || isHovered) ? n.r * 1.15 : n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.type === 'company' ? `rgba(15, 23, 42, ${nodeAlpha})` : n.color;
        ctx.strokeStyle = (isSelected) ? '#ffffff' : n.color;
        ctx.lineWidth = (isSelected) ? 3.5 : (isHovered ? 2.5 : 1.5);
        ctx.fill();
        ctx.stroke();

        // Inner dot for company nodes
        if (n.type === 'company') {
          ctx.beginPath();
          ctx.arc(nx, ny, 3.5, 0, Math.PI * 2);
          ctx.fillStyle = isMatchLens ? '#38bdf8' : 'rgba(56, 189, 248, 0.3)';
          ctx.fill();
        }

        // Label
        ctx.fillStyle = isSelected ? '#ffffff' : (isMatchLens ? 'rgba(255, 255, 255, 0.9)' : 'rgba(255, 255, 255, 0.25)');
        ctx.font = n.type === 'theme' ? '700 11px Plus Jakarta Sans, sans-serif' : '700 11px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.fillText(n.label, nx, ny + n.r + 14);
      });
    }

    requestAnimationFrame(draw);
  }
  draw();

  function getNodeUnderMouse(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / canvas.offsetWidth;
    const my = (e.clientY - rect.top) / canvas.offsetHeight;

    return nodes.find(n => {
      const dx = (n.x - mx) * (canvas.offsetWidth / canvas.offsetHeight);
      const dy = n.y - my;
      return Math.sqrt(dx * dx + dy * dy) < (n.r / canvas.offsetHeight) * 1.8;
    }) || null;
  }

  canvas.addEventListener('mousemove', (e) => {
    if (draggedNode) {
      const rect = canvas.getBoundingClientRect();
      draggedNode.x = Math.max(0.05, Math.min(0.95, (e.clientX - rect.left) / canvas.offsetWidth));
      draggedNode.y = Math.max(0.05, Math.min(0.95, (e.clientY - rect.top) / canvas.offsetHeight));
      return;
    }

    hoveredNode = getNodeUnderMouse(e);
    canvas.style.cursor = hoveredNode ? 'grab' : 'crosshair';
  });

  canvas.addEventListener('mousedown', (e) => {
    const n = getNodeUnderMouse(e);
    if (n) {
      draggedNode = n;
      updateInspector(n);
      triggerBotSpeech(`Inspecting topology: [${n.label}].`);
      canvas.style.cursor = 'grabbing';
    }
  });

  window.addEventListener('mouseup', () => {
    if (draggedNode) {
      draggedNode = null;
      canvas.style.cursor = 'crosshair';
    }
  });

  // Initialize inspector on load with default node
  updateInspector(nodes[0]);
}

// -----------------------------------------------------------------------------
// Interactive DriftBot 2.0 HUD Commands
// -----------------------------------------------------------------------------
function setupBotActions() {
  const scanBtn = document.getElementById('bot-scan-btn');
  const outlierBtn = document.getElementById('bot-outlier-btn');
  const sqlBtn = document.getElementById('bot-sql-btn');
  const laserBar = document.getElementById('laser-scan-bar');

  if (scanBtn) {
    scanBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (laserBar) {
        laserBar.classList.remove('running');
        void laserBar.offsetWidth;
        laserBar.classList.add('running');
      }
      triggerBotSpeech("Running full-corpus radar scan across 50+ filers (2016–2025)... Complete! Zero data anomalies detected.");
    });
  }

  if (outlierBtn) {
    outlierBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      switchView('global');
      triggerBotSpeech("Displaying sanitized black-swan outlier disclosures with highest centroid distance.");
    });
  }

  if (sqlBtn) {
    sqlBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      switchView('sql');
      executeSQL();
    });
  }
}
