let ALL_ASSETS = [];

async function initAssetsPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Loading assets...");
  try {
    ALL_ASSETS = await Api.assets();
    el.innerHTML = renderAssetsPage();
    if (ALL_ASSETS.length){
      document.getElementById("asset-search").addEventListener("input", applyAssetFilters);
      document.getElementById("risk-filter").addEventListener("change", applyAssetFilters);
      document.getElementById("status-filter").addEventListener("change", applyAssetFilters);
      renderAssetRows([...ALL_ASSETS].sort((a,b)=>(a.health_score??100)-(b.health_score??100)));
    }
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load assets", err.message);
  }
}

function renderAssetsPage(){
  if (ALL_ASSETS.length === 0) return emptyHtml("No assets yet", "Add a machine to get started.");
  return `
    <div class="card">
      <div class="filter-bar">
        <input class="form-control search-input" id="asset-search" placeholder="Search machines...">
        <select class="form-control" id="risk-filter" style="max-width:160px">
          <option value="">All risk levels</option>
          <option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option>
        </select>
        <select class="form-control" id="status-filter" style="max-width:180px">
          <option value="">All statuses</option>
          <option>Stable</option><option>Mild deterioration</option><option>Gradual deterioration</option><option>Rapid deterioration</option>
        </select>
      </div>
      <div class="table-wrap">
        <table id="assets-table">
          <thead><tr><th>Machine</th><th>Health</th><th>Risk</th><th>Condition</th><th>Critical Time</th><th>Intervention</th></tr></thead>
          <tbody id="assets-tbody"></tbody>
        </table>
      </div>
    </div>
  `;
}

function applyAssetFilters(){
  const q = (document.getElementById("asset-search").value || "").toLowerCase();
  const riskF = document.getElementById("risk-filter").value;
  const statusF = document.getElementById("status-filter").value;
  const filtered = ALL_ASSETS.filter(a =>
    (a.name.toLowerCase().includes(q) || a.machine_id.toLowerCase().includes(q)) &&
    (!riskF || a.risk_level === riskF) &&
    (!statusF || a.status === statusF)
  ).sort((a,b) => (a.health_score ?? 100) - (b.health_score ?? 100));
  renderAssetRows(filtered);
}

function renderAssetRows(rows){
  document.getElementById("assets-tbody").innerHTML = rows.map(a => `
    <tr class="link-row" onclick="window.location.href='asset-detail.html?id=${a.id}'">
      <td data-label="Machine"><b>${a.name}</b><div style="font-size:11px;color:var(--text-muted)">${a.machine_id}</div></td>
      <td data-label="Health">${a.health_score != null ? Math.round(a.health_score)+'%' : '—'}</td>
      <td data-label="Risk">${a.risk_level ? `<span class="pill pill-${riskClass(a.risk_level)}">${a.risk_level}</span>` : '—'}</td>
      <td data-label="Condition">${a.status || '—'}</td>
      <td data-label="Critical Time">${fmtHours(a.critical_time_hours)}</td>
      <td data-label="Intervention">${a.intervention_start != null ? fmtHours(a.intervention_start)+' – '+fmtHours(a.intervention_end) : '—'}</td>
    </tr>`).join("");
}

