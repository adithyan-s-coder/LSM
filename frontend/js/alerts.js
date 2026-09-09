let ALL_ALERTS = [];

async function initAlertsPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Loading alerts...");
  try {
    ALL_ALERTS = await Api.alerts();
    el.innerHTML = renderAlertsPage();
    document.getElementById("alert-search").addEventListener("input", filterAlerts);
    document.getElementById("alert-sev-filter").addEventListener("change", filterAlerts);
    filterAlerts();
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load alerts", err.message);
  }
}

function renderAlertsPage(){
  return `
    <div class="card">
      <div class="filter-bar">
        <input class="form-control search-input" id="alert-search" placeholder="Search alerts...">
        <select class="form-control" id="alert-sev-filter" style="max-width:160px">
          <option value="">All severities</option>
          <option>Info</option><option>Warning</option><option>High</option><option>Critical</option>
        </select>
      </div>
      <div id="alerts-list"></div>
    </div>
  `;
}

function filterAlerts(){
  const q = (document.getElementById("alert-search").value || "").toLowerCase();
  const sev = document.getElementById("alert-sev-filter").value;
  const filtered = ALL_ALERTS.filter(a =>
    (a.title.toLowerCase().includes(q) || (a.machine_name||"").toLowerCase().includes(q)) &&
    (!sev || a.severity === sev)
  );
  const list = document.getElementById("alerts-list");
  if (!filtered.length){ list.innerHTML = emptyHtml("No alerts found", "Nothing matches your current filters."); return; }
  list.innerHTML = filtered.map(a => `
    <div class="alert-item ${a.is_read ? '' : 'unread'}">
      <div class="alert-sev ${a.severity.toLowerCase()}"></div>
      <div style="flex:1">
        <div class="alert-title">${a.title}</div>
        <div class="alert-msg">${a.message}</div>
        <div class="alert-time">${a.machine_name || ''} · ${fmtDate(a.created_at)}</div>
      </div>
      ${!a.is_read ? `<button class="btn btn-secondary btn-sm" onclick="markRead(${a.id})">Mark read</button>` : ''}
    </div>
  `).join("");
}

async function markRead(id){
  try {
    await Api.markAlertRead(id);
    const a = ALL_ALERTS.find(x => x.id === id);
    if (a) a.is_read = true;
    filterAlerts();
  } catch (err) {
    showToast(err.message, "error");
  }
}
