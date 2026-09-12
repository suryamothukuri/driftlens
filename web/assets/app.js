
// DriftLens Frontend Logic
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
  themes: [
    { cluster_id: 0, label: 'AI Infrastructure & Model Safety', n_companies_ever: 8 },
    { cluster_id: 1, label: 'Advanced Semiconductor Foundries', n_companies_ever: 6 },
    { cluster_id: 2, label: 'Cloud Data Privacy & Sovereignty', n_companies_ever: 7 },
    { cluster_id: 3, label: 'Cross-Border Export Controls', n_companies_ever: 5 },
    { cluster_id: 4, label: 'Supply Chain Component Fragility', n_companies_ever: 8 },
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
  selectedCompany: '0000320193'
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
      <td>${item.label}</td>
      <td>${item.year}</td>
      <td><span class="chip chip-${item.type}">${item.type}</span></td>
      <td style="color:${item.delta.startsWith('+') ? '#34d399' : '#f87171'}">${item.delta}</td>
      <td><code>${item.drift.toFixed(3)}</code></td>
      <td><strong>${item.score.toFixed(3)}</strong></td>
    `;
    tr.addEventListener('click', () => {
      openModal(item);
    });
    tbody.appendChild(tr);
  });
}

function renderCompanyTimeline(cik) {
  const comp = SAMPLE_DATA.companies.find(c => c.cik === cik) || SAMPLE_DATA.companies[0];
  const nameEl = document.getElementById('timeline-company-name');
  if (nameEl) nameEl.textContent = `${comp.name} (${comp.ticker}) — Temporal Risk Drift`;

  const track = document.getElementById('timeline-track');
  if (!track) return;
  track.innerHTML = '';

  const years = [2020, 2021, 2022, 2023];
  years.forEach(yr => {
    const card = document.createElement('div');
    card.className = 'glass-panel timeline-card';
    card.innerHTML = `
      <div class="timeline-year">FY${yr}</div>
      <div style="display:flex; flex-direction:column; gap:0.5rem;">
        <span class="chip chip-new">AI Infrastructure (New)</span>
        <span class="chip chip-intensifying">Supply Chains (+4.2%)</span>
        <span class="chip chip-stable">Data Security</span>
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
    <div style="margin-bottom:1rem;">
      <span class="chip chip-${item.type}">${item.type}</span>
      <span style="margin-left:0.5rem; color:#94a3b8;">Materiality Score: <strong>${item.score}</strong> | Centroid Drift: <strong>${item.drift}</strong></span>
    </div>
    <div style="background:rgba(59,130,246,0.1); border-left:3px solid #3b82f6; padding:1rem; border-radius:0 8px 8px 0; margin-bottom:1.5rem;">
      <h4 style="color:#60a5fa; margin-bottom:0.25rem;">Synthesized Semantic Shift (Batch LLM):</h4>
      <p style="color:#f8fafc; font-size:0.95rem;">${exp.text}</p>
    </div>
    <div>
      <h4 style="color:#94a3b8; font-size:0.85rem; text-transform:uppercase; margin-bottom:0.5rem;">Primary Source Excerpt (Item 1A):</h4>
      <p style="font-style:italic; color:#cbd5e1; background:rgba(0,0,0,0.4); padding:1rem; border-radius:8px;">
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

async function executeSQL() {
  const txt = document.getElementById('sql-input');
  const resBox = document.getElementById('sql-results');
  const query = txt.value.trim();

  resBox.innerHTML = '<div style="color:#38bdf8;">Running client-side query in DuckDB-Wasm...</div>';

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
    console.warn("Wasm query error:", err);
  }

  // Fallback demo result
  setTimeout(() => {
    resBox.innerHTML = `
      <table class="custom-table">
        <thead>
          <tr><th>theme</th><th>fiscal_year</th><th>companies_affected</th><th>avg_materiality</th></tr>
        </thead>
        <tbody>
          <tr><td>AI Infrastructure & Model Safety</td><td>2023</td><td>8</td><td>0.245</td></tr>
          <tr><td>Advanced Semiconductor Foundries</td><td>2022</td><td>6</td><td>0.218</td></tr>
          <tr><td>Cross-Border Export Controls</td><td>2023</td><td>5</td><td>0.174</td></tr>
        </tbody>
      </table>
    `;
  }, 300);
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
      opt.textContent = `${c.ticker} - ${c.name}`;
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
});
