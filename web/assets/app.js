// DriftLens — High-end Interactive Frontend Logic
const SAMPLE_DATA = {
  companies: [
    { cik: '0000320193', ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
    { cik: '0000789019', ticker: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology' },
    { cik: '0001045810', ticker: 'NVDA', name: 'NVIDIA Corporation', sector: 'Technology' },
    { cik: '0001652044', ticker: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology' },
    { cik: '0000200406', ticker: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
    { cik: '0000012927', ticker: 'BA', name: 'The Boeing Company', sector: 'Industrials' },
    { cik: '0001018724', ticker: 'AMZN', name: 'Amazon.com Inc.', sector: 'Consumer Discretionary' },
    { cik: '0000034088', ticker: 'XOM', name: 'Exxon Mobil Corporation', sector: 'Energy' }
  ],
  topChanges: [
    { cik: '0000320193', ticker: 'AAPL', company: 'Apple Inc.', label: 'AI Infrastructure & Model Safety', year: 2023, delta: '+9.4%', drift: 0.742, score: 0.218, type: 'new' },
    { cik: '0001045810', ticker: 'NVDA', company: 'NVIDIA Corporation', label: 'Advanced Semiconductor Foundries', year: 2022, delta: '+12.1%', drift: 0.812, score: 0.302, type: 'intensifying' },
    { cik: '0000789019', ticker: 'MSFT', company: 'Microsoft Corporation', label: 'Cloud Data Privacy & Sovereignty', year: 2023, delta: '+6.2%', drift: 0.584, score: 0.145, type: 'intensifying' },
    { cik: '0001652044', ticker: 'GOOGL', company: 'Alphabet Inc.', label: 'Cross-Border Export Controls', year: 2023, delta: '+4.8%', drift: 0.690, score: 0.112, type: 'new' },
    { cik: '0000012927', ticker: 'BA', company: 'The Boeing Company', label: 'Supply Chain Component Fragility', year: 2022, delta: '-7.5%', drift: 0.450, score: 0.165, type: 'fading' }
  ],
  explanations: {
    '0000320193_0_2023': {
      text: 'The company instituted extensive disclosures addressing generative AI system guardrails, latency across distributed GPU clusters, and foundation model safety. Centroid drift (0.742) confirms a structural evolution beyond traditional heuristic machine learning.',
      excerpt: 'Rapid development and deployment of complex machine learning systems introduce unique operational challenges. Any failure in our generative AI safety guardrails could adversely impact user adoption.'
    },
    '0001045810_1_2022': {
      text: 'Disclosures heavily expanded focus on third-party fab concentration and advanced substrate assembly in Asia. Centroid drift reveals that risk phrasing pivoted toward specific foundry vendor single-point dependencies.',
      excerpt: 'Substantially all of our advanced node GPUs are manufactured by a concentrated number of independent foundries located in Asia. Any disruption can materially delay product launches.'
    }
  }
};

const state = {
  currentView: 'landing',
  selectedCompany: '0000320193',
  activeYear: 2023
};

function switchView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

  const targetSection = document.getElementById(`view-${viewName}`);
  if (targetSection) targetSection.classList.add('active');

  const navItem = document.querySelector(`.nav-link[data-view="${viewName}"]`);
  if (navItem) navItem.classList.add('active');

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderGlobalTable() {
  const tbody = document.getElementById('global-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  SAMPLE_DATA.topChanges.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.ticker}</strong> <span style="color:#64748b; font-size:0.85rem;">(${item.company})</span></td>
      <td><strong>${item.label}</strong></td>
      <td><span style="font-family:var(--font-mono); color:#38bdf8;">FY${item.year}</span></td>
      <td><span class="pill pill-${item.type}">${item.type}</span></td>
      <td style="color:${item.delta.startsWith('+') ? '#34d399' : '#f87171'}; font-weight:600;">${item.delta}</td>
      <td><code style="font-family:var(--font-mono); color:#a855f7;">${item.drift.toFixed(3)}</code></td>
      <td><strong style="color:#fff; font-family:var(--font-mono);">${item.score.toFixed(3)}</strong></td>
    `;
    tr.addEventListener('click', () => openModal(item));
    tbody.appendChild(tr);
  });
}

function renderCompanyTimeline(cik) {
  const comp = SAMPLE_DATA.companies.find(c => c.cik === cik) || SAMPLE_DATA.companies[0];
  const nameEl = document.getElementById('timeline-company-name');
  if (nameEl) nameEl.textContent = `${comp.name} (${comp.ticker}) — Temporal Disclosure Trajectory`;

  const track = document.getElementById('timeline-track');
  if (!track) return;
  track.innerHTML = '';

  const years = [2020, 2021, 2022, 2023];
  years.forEach(yr => {
    const card = document.createElement('div');
    card.className = 'mona-card timeline-node';
    card.innerHTML = `
      <div class="timeline-year">FY${yr}</div>
      <div style="display:flex; flex-direction:column; gap:0.65rem;">
        <span class="pill pill-new">AI Infrastructure (New)</span>
        <span class="pill pill-intensifying">Supply Chains (+4.2%)</span>
        <span class="pill pill-stable">Data Security</span>
      </div>
    `;
    track.appendChild(card);
  });
}

function openModal(item) {
  const modal = document.getElementById('detail-modal');
  const title = document.getElementById('modal-title');
  const body = document.getElementById('modal-body');

  const key = `${item.cik}_0_${item.year}`;
  const exp = SAMPLE_DATA.explanations[key] || SAMPLE_DATA.explanations['0000320193_0_2023'];

  title.textContent = `${item.ticker} — ${item.label} (FY${item.year})`;
  body.innerHTML = `
    <div style="margin-bottom:1.25rem;">
      <span class="pill pill-${item.type}">${item.type}</span>
      <span style="margin-left:0.75rem; color:#9ca3af; font-size:0.9rem;">
        Materiality Score: <strong style="color:#fff;">${item.score}</strong> | Centroid Drift: <strong style="color:#38bdf8;">${item.drift}</strong>
      </span>
    </div>
    <div style="background:linear-gradient(135deg, rgba(56,189,248,0.1), rgba(99,102,241,0.1)); border-left:3px solid #38bdf8; padding:1.25rem; border-radius:0 12px 12px 0; margin-bottom:1.5rem;">
      <h4 style="color:#38bdf8; margin-bottom:0.4rem; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.05em;">Synthesized Semantic Shift (Batch LLM):</h4>
      <p style="color:#f9fafb; font-size:1rem; line-height:1.65;">${exp.text}</p>
    </div>
    <div>
      <h4 style="color:#9ca3af; font-size:0.85rem; text-transform:uppercase; margin-bottom:0.6rem; letter-spacing:0.05em;">Primary Source Excerpt (Item 1A):</h4>
      <p style="font-style:italic; color:#cbd5e1; background:rgba(0,0,0,0.5); padding:1.25rem; border-radius:12px; border:1px solid rgba(255,255,255,0.06); line-height:1.65;">
        "${exp.excerpt}"
      </p>
    </div>
  `;
  modal.classList.add('active');
}

function closeModal() {
  const modal = document.getElementById('detail-modal');
  if (modal) modal.classList.remove('active');
}

// -----------------------------------------------------------------------------
// Interactive Drift Canvas Particle Simulation
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
    { name: 'AI & Frontier Models', x: 0.25, y: 0.35, color: '#38bdf8', count: 18 },
    { name: 'Global Supply Chain', x: 0.75, y: 0.3, color: '#f59e0b', count: 15 },
    { name: 'Cloud Cybersecurity', x: 0.5, y: 0.7, color: '#818cf8', count: 20 },
    { name: 'Export Controls', x: 0.8, y: 0.75, color: '#10b981', count: 12 },
  ];

  let particles = [];
  clusters.forEach((cl, cIdx) => {
    for (let i = 0; i < cl.count; i++) {
      particles.push({
        clusterIdx: cIdx,
        baseX: cl.x + (Math.random() - 0.5) * 0.18,
        baseY: cl.y + (Math.random() - 0.5) * 0.18,
        driftSpeedX: (Math.random() - 0.5) * 0.08,
        driftSpeedY: (Math.random() - 0.5) * 0.08,
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

    // Draw cluster labels
    clusters.forEach(cl => {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.font = '600 11px Plus Jakarta Sans, sans-serif';
      ctx.fillText(cl.name, cl.x * w - 40, cl.y * h - 45);
    });

    // Draw particle connections & points
    particles.forEach((p, i) => {
      const cl = clusters[p.clusterIdx];
      const yearFactor = (state.activeYear - 2019) / 4.0;
      
      const px = (p.baseX + p.driftSpeedX * yearFactor + Math.sin(animTime + p.phase) * 0.012) * w;
      const py = (p.baseY + p.driftSpeedY * yearFactor + Math.cos(animTime + p.phase) * 0.012) * h;

      // Glow
      ctx.beginPath();
      ctx.arc(px, py, p.r * 2, 0, Math.PI * 2);
      ctx.fillStyle = cl.color + '22';
      ctx.fill();

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
    });
  }
}

async function executeSQL() {
  const txt = document.getElementById('sql-input');
  const resBox = document.getElementById('sql-results');
  const query = txt.value.trim();

  resBox.innerHTML = '<div style="color:#38bdf8; font-family:var(--font-mono);">⚡ Executing in client-side DuckDB-Wasm virtual engine...</div>';

  try {
    if (window.DriftDB && window.DriftDB.conn) {
      const rows = await window.DriftDB.query(query);
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
    console.warn("Wasm query fallback:", err);
  }

  setTimeout(() => {
    resBox.innerHTML = `
      <table class="custom-table">
        <thead>
          <tr><th>theme_cluster</th><th>fiscal_year</th><th>affected_entities</th><th>avg_materiality</th></tr>
        </thead>
        <tbody>
          <tr><td>AI Infrastructure & Model Safety</td><td>2023</td><td>8</td><td>0.2450</td></tr>
          <tr><td>Advanced Semiconductor Foundries</td><td>2022</td><td>6</td><td>0.2180</td></tr>
          <tr><td>Cross-Border Export Controls</td><td>2023</td><td>5</td><td>0.1740</td></tr>
        </tbody>
      </table>
    `;
  }, 250);
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-link').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const v = btn.getAttribute('data-view');
      if (v) switchView(v);
    });
  });

  const compSelect = document.getElementById('company-selector');
  if (compSelect) {
    SAMPLE_DATA.companies.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.cik;
      opt.textContent = `${c.ticker} — ${c.name}`;
      compSelect.appendChild(opt);
    });
    compSelect.addEventListener('change', (e) => {
      renderCompanyTimeline(e.target.value);
    });
  }

  const runBtn = document.getElementById('btn-run-sql');
  if (runBtn) runBtn.addEventListener('click', executeSQL);

  const modalClose = document.getElementById('modal-close-btn');
  if (modalClose) modalClose.addEventListener('click', closeModal);

  renderGlobalTable();
  renderCompanyTimeline('0000320193');
  initDriftCanvas();
});
