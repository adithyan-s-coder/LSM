let MAINT_ASSETS = [];

async function initMaintenancePage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Loading maintenance records...");
  try {
    const [records, assets] = await Promise.all([Api.maintenance(), Api.assets()]);
    MAINT_ASSETS = assets;
    el.innerHTML = renderMaintenancePage(records);
    document.getElementById("new-maint-btn").addEventListener("click", () => openMaintForm());
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load maintenance", err.message);
  }
}

function renderMaintenancePage(records){
  const groups = { Recommended: [], Scheduled: [], "In Progress": [], Completed: [], Cancelled: [] };
  records.forEach(r => { (groups[r.status] || (groups[r.status] = [])).push(r); });

  return `
    <div class="flex-between mb-16">
      <div class="section-sub" style="margin-bottom:0">Recommended, scheduled, and completed maintenance across the fleet.</div>
      <button class="btn btn-primary btn-sm" id="new-maint-btn"><i class="fa-solid fa-plus"></i> Schedule Maintenance</button>
    </div>
    <div id="maint-form-slot"></div>
    ${Object.entries(groups).map(([status, rows]) => rows.length ? `
      <div class="card mt-16">
        <div class="card-title">${status} (${rows.length})</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Machine</th><th>Type</th><th>Scheduled</th><th>Cost</th><th>Downtime</th><th>Status</th><th></th></tr></thead>
            <tbody>
              ${rows.map(r => `
                <tr>
                  <td data-label="Machine">${r.machine_name || r.machine_id}</td>
                  <td data-label="Type">${r.maintenance_type}</td>
                  <td data-label="Scheduled">${fmtDate(r.scheduled_at)}</td>
                  <td data-label="Cost">${fmtMoney(r.cost)}</td>
                  <td data-label="Downtime">${r.downtime_hours || 0}h</td>
                  <td data-label="Status"><span class="pill pill-neutral">${r.status}</span></td>
                  <td data-label="">
                    ${r.status !== "Completed" && r.status !== "Cancelled" ? `<button class="btn btn-secondary btn-sm" onclick="advanceStatus(${r.id}, '${r.status}')">Advance</button>` : ""}
                  </td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>` : "").join("")}
  `;
}

function openMaintForm(){
  document.getElementById("maint-form-slot").innerHTML = `
    <div class="card mb-16">
      <div class="card-title">Schedule Maintenance</div>
      <div class="grid grid-2">
        <div class="form-group">
          <label>Machine</label>
          <select class="form-control" id="mf-machine">
            ${MAINT_ASSETS.map(a => `<option value="${a.machine_id}">${a.name}</option>`).join("")}
          </select>
        </div>
        <div class="form-group">
          <label>Maintenance Type</label>
          <input class="form-control" id="mf-type" placeholder="e.g. Bearing inspection">
        </div>
        <div class="form-group">
          <label>Scheduled At</label>
          <input class="form-control" type="datetime-local" id="mf-date">
        </div>
        <div class="form-group">
          <label>Estimated Cost (₹)</label>
          <input class="form-control" type="number" id="mf-cost" value="5000">
        </div>
        <div class="form-group">
          <label>Estimated Downtime (hours)</label>
          <input class="form-control" type="number" id="mf-downtime" value="2">
        </div>
        <div class="form-group">
          <label>Notes</label>
          <input class="form-control" id="mf-notes" placeholder="Optional notes">
        </div>
      </div>
      <button class="btn btn-primary" id="mf-submit">Save</button>
      <button class="btn btn-secondary" onclick="document.getElementById('maint-form-slot').innerHTML=''">Cancel</button>
    </div>
  `;
  document.getElementById("mf-submit").addEventListener("click", submitMaintForm);
}

async function submitMaintForm(){
  const payload = {
    machine_id: document.getElementById("mf-machine").value,
    maintenance_type: document.getElementById("mf-type").value || "General maintenance",
    scheduled_at: document.getElementById("mf-date").value || null,
    cost: parseFloat(document.getElementById("mf-cost").value) || 0,
    downtime_hours: parseFloat(document.getElementById("mf-downtime").value) || 0,
    notes: document.getElementById("mf-notes").value,
    status: "Scheduled",
  };
  try {
    await Api.createMaintenance(payload);
    showToast("Maintenance scheduled");
    initMaintenancePage();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function advanceStatus(id, current){
  const flow = { Recommended: "Scheduled", Scheduled: "In Progress", "In Progress": "Completed" };
  const next = flow[current];
  if (!next) return;
  try {
    await Api.updateMaintenance(id, { status: next, completed_at: next === "Completed" ? new Date().toISOString() : null });
    showToast(`Marked as ${next}`);
    initMaintenancePage();
  } catch (err) {
    showToast(err.message, "error");
  }
}
