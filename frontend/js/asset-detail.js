async function initAssetDetailPage(){
  const el = document.getElementById("page-content");
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");
  if (!id){ el.innerHTML = emptyHtml("No machine selected", "Go back to Assets and pick a machine."); return; }
  el.innerHTML = loadingHtml("Loading machine analysis...");
  try {
    const a = await Api.assetAnalysis(id);
    if (a.error){ el.innerHTML = emptyHtml("No data yet", a.error); return; }
    el.innerHTML = renderDetail(a);
    const readings = await Api.assetReadings(id, 150);
    const labels = readings.map(r => new Date(r.timestamp).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit'}));
    mkLine("d-chart-temp", labels, readings.map(r=>r.temperature), "#f59e0b");
    mkLine("d-chart-vib", labels, readings.map(r=>r.vibration), "#ef4444");
    mkLine("d-chart-cur", labels, readings.map(r=>r.current), "#3b82f6");
    mkLine("d-chart-load", labels, readings.map(r=>r.load), "#8b5cf6");
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load machine analysis", err.message);
  }
}

function renderDetail(a){
  const risk = a.risk.risk_level;
  return `
    <div class="flex-between mb-16">
      <div>
        <div class="section-title">${a.asset.name}</div>
        <div class="section-sub">${a.asset.machine_id} · ${a.asset.type} · ${a.asset.location || 'Unspecified location'}</div>
      </div>
      <span class="pill pill-${riskClass(risk)}">${risk} RISK</span>
    </div>

    <div class="grid grid-4 mb-16">
      <div class="card"><div class="sc-label">Operating Hours</div><div class="sc-value" style="font-size:20px">${Math.round(a.asset.operating_hours || 0).toLocaleString()}</div></div>
      <div class="card"><div class="sc-label">Health</div><div class="sc-value" style="font-size:20px">${Math.round(a.health.health_score)}%</div></div>
      <div class="card"><div class="sc-label">Est. Critical Time</div><div class="sc-value" style="font-size:20px">${fmtHours(a.critical_time.estimated_critical_time_hours)}</div></div>
      <div class="card"><div class="sc-label">Confidence</div><div class="sc-value" style="font-size:20px">${a.critical_time.confidence}%</div></div>
    </div>

    <div class="card mb-16">
      <div class="card-title">Last Safe Intervention</div>
      <div style="font-size:22px;font-weight:800">${a.last_safe_moment.intervention_start != null ? fmtHours(a.last_safe_moment.intervention_start) + ' – ' + fmtHours(a.last_safe_moment.intervention_end) : 'No intervention required'}</div>
      <div style="font-size:12.5px;color:var(--text-muted);margin-top:4px">${a.recommendation.headline}</div>
    </div>

    <div class="grid grid-4 mb-16">
      ${conditionCard("Temperature", a.latest_reading.temperature, "°C", a.deterioration.temperature_slope_per_hour)}
      ${conditionCard("Vibration", a.latest_reading.vibration, "mm/s", a.deterioration.vibration_slope_per_hour)}
      ${conditionCard("Current", a.latest_reading.current, "A", a.deterioration.current_slope_per_hour)}
      ${conditionCard("Load", a.latest_reading.load, "%", a.deterioration.load_slope_per_hour, true)}
    </div>

    <div class="grid grid-2 mb-16">
      <div class="card"><div class="card-title">Temperature</div><div class="chart-box"><canvas id="d-chart-temp"></canvas></div></div>
      <div class="card"><div class="card-title">Vibration</div><div class="chart-box"><canvas id="d-chart-vib"></canvas></div></div>
      <div class="card"><div class="card-title">Current</div><div class="chart-box"><canvas id="d-chart-cur"></canvas></div></div>
      <div class="card"><div class="card-title">Load</div><div class="chart-box"><canvas id="d-chart-load"></canvas></div></div>
    </div>

    <div class="grid grid-2 mb-16">
      <div class="card">
        <div class="card-title">Failure History</div>
        ${a.failure_history.length ? a.failure_history.map(f => `
          <div style="padding:10px 0;border-bottom:1px solid var(--border)">
            <div style="font-weight:700;font-size:13px">${fmtDate(f.date)}</div>
            <div style="font-size:12.5px;color:var(--text-secondary)">${f.description}</div>
            <div style="font-size:12px;color:var(--text-muted)">Repair: ${fmtMoney(f.repair_cost)} · Production loss: ${fmtMoney(f.production_loss)}</div>
          </div>`).join("") : emptyHtml("No failures recorded", "This machine has no logged failure history.")}
      </div>
      <div class="card">
        <div class="card-title">Maintenance History</div>
        ${a.maintenance_history.length ? a.maintenance_history.map(m => `
          <div style="padding:10px 0;border-bottom:1px solid var(--border)">
            <div style="font-weight:700;font-size:13px">${m.type} <span class="pill pill-neutral">${m.status}</span></div>
            <div style="font-size:12px;color:var(--text-muted)">Scheduled ${fmtDate(m.scheduled_at)} · Cost ${fmtMoney(m.cost)}</div>
          </div>`).join("") : emptyHtml("No maintenance yet", "No maintenance has been logged for this machine.")}
      </div>
    </div>

    <div class="card">
      <div class="card-title">Prediction Explanation</div>
      <ul class="reason-list">${a.reasons.map(r => `<li><i class="fa-solid fa-circle-check chk"></i> ${r}</li>`).join("")}</ul>
    </div>
  `;
}
