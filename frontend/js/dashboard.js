/* dashboard.js — the most important page: what's wrong, how fast, how much time,
   what happens if we wait, what to do now. */

function trendArrow(slope, thresholdUp=0.02){
  if (slope > thresholdUp) return { cls: "trend-up", icon: "fa-arrow-up", label: "Increasing" };
  if (slope < -thresholdUp) return { cls: "trend-down", icon: "fa-arrow-down", label: "Decreasing" };
  return { cls: "trend-flat", icon: "fa-minus", label: "Stable" };
}

function healthRingSvg(score){
  const r = 46, c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score || 0));
  const offset = c - (pct / 100) * c;
  const color = pct >= 75 ? "var(--green)" : pct >= 50 ? "var(--amber)" : "var(--red)";
  return `
    <div class="health-ring">
      <svg width="110" height="110" viewBox="0 0 110 110">
        <circle cx="55" cy="55" r="${r}" stroke="var(--navy-700)" stroke-width="10" fill="none"/>
        <circle cx="55" cy="55" r="${r}" stroke="${color}" stroke-width="10" fill="none"
          stroke-dasharray="${c}" stroke-dashoffset="${offset}" stroke-linecap="round"/>
      </svg>
      <div class="ring-value"><div class="ring-num">${Math.round(pct)}</div><div class="ring-den">/ 100</div></div>
    </div>`;
}

async function initDashboard(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Loading dashboard...");
  try {
    const data = await Api.dashboard();
    if (!data.assets || data.assets.length === 0){
      el.innerHTML = emptyHtml("No machines yet", "Upload sensor data or add an asset to get started.");
      return;
    }
    const p = data.priority_asset;
    el.innerHTML = renderDashboard(data, p);
    if (p && !p.error) renderDashboardCharts(p);
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load dashboard", err.message);
  }
}

function renderDashboard(data, p){
  if (!p || p.error) {
    return emptyHtml("No prediction data yet", "Run a simulation or upload sensor data for a machine to see predictions.");
  }
  const risk = p.risk.risk_level;
  const lsm = p.last_safe_moment;
  const windowLabel = (lsm.intervention_start != null)
    ? `${fmtHours(lsm.intervention_start)} – ${fmtHours(lsm.intervention_end)}`
    : "No action needed";

  return `
    <!-- HERO: LAST SAFE MOMENT -->
    <div class="hero risk-${riskClass(risk).toLowerCase()}">
      <div class="hero-tag"><i class="fa-solid fa-triangle-exclamation"></i> LAST SAFE MOMENT</div>
      <div class="hero-machine">${p.machine_name} (${p.machine_id})</div>
      <div class="hero-window">${windowLabel}</div>
      <div class="hero-window-label">Estimated last-safe intervention window</div>
      <div class="hero-stats">
        <div class="hero-stat"><div class="hs-val">${Math.round(p.health.health_score)}%</div><div class="hs-label">Health</div></div>
        <div class="hero-stat"><div class="hs-val"><span class="pill pill-${riskClass(risk)}">${risk}</span></div><div class="hs-label">Risk</div></div>
        <div class="hero-stat"><div class="hs-val">${lsm.confidence}%</div><div class="hs-label">Confidence</div></div>
        <div class="hero-stat"><div class="hs-val">${fmtHours(p.critical_time.estimated_critical_time_hours)}</div><div class="hs-label">Est. Critical Condition</div></div>
      </div>
      <div class="hero-action"><b>Recommended:</b> ${p.recommendation.headline}</div>
    </div>

    <!-- TIMELINE -->
    <div class="card mt-24">
      <div class="card-title">Machine Timeline</div>
      ${renderTimeline(p)}
    </div>

    <div class="grid grid-2 mt-24">
      <!-- HEALTH SCORE -->
      <div class="card">
        <div class="card-title">Machine Health</div>
        <div class="health-ring-wrap">
          ${healthRingSvg(p.health.health_score)}
          <div>
            <div style="font-size:20px;font-weight:800">${p.health.status}</div>
            <div style="font-size:12.5px;color:var(--text-muted);margin-top:4px">Based on temperature, vibration, current, load and recent trend</div>
          </div>
        </div>
      </div>
      <!-- WHY RECOMMENDATION -->
      <div class="card">
        <div class="card-title">Why are we recommending action now?</div>
        <ul class="reason-list">
          ${p.reasons.map(r => `<li><i class="fa-solid fa-circle-check chk"></i> ${r}</li>`).join("")}
        </ul>
      </div>
    </div>

    <!-- CONDITION CARDS -->
    <div class="grid grid-4 mt-24">
      ${conditionCard("Temperature", p.latest_reading.temperature, "°C", p.deterioration.temperature_slope_per_hour)}
      ${conditionCard("Vibration", p.latest_reading.vibration, "mm/s", p.deterioration.vibration_slope_per_hour)}
      ${conditionCard("Current", p.latest_reading.current, "A", p.deterioration.current_slope_per_hour)}
      ${conditionCard("Load", p.latest_reading.load, "%", p.deterioration.load_slope_per_hour, true)}
    </div>

    <!-- TREND CHARTS -->
    <div class="grid grid-2 mt-24">
      <div class="card"><div class="card-title">Temperature Trend</div><div class="chart-box"><canvas id="chart-temp"></canvas></div></div>
      <div class="card"><div class="card-title">Vibration Trend</div><div class="chart-box"><canvas id="chart-vib"></canvas></div></div>
      <div class="card"><div class="card-title">Current Trend</div><div class="chart-box"><canvas id="chart-cur"></canvas></div></div>
      <div class="card"><div class="card-title">Health Trend</div><div class="chart-box"><canvas id="chart-health"></canvas></div></div>
    </div>

    <!-- COST OF WAITING -->
    <div class="card mt-24">
      <div class="card-title">What Happens If I Wait?</div>
      <div class="cost-cols">
        <div class="cost-col act-now">
          <h4>Act Now</h4>
          <div class="cost-row"><span>Maintenance</span><b>${fmtMoney(p.cost_analysis.act_now.maintenance_cost)}</b></div>
          <div class="cost-row"><span>Downtime</span><b>${p.cost_analysis.act_now.downtime_hours}h</b></div>
          <div class="cost-row"><span>Risk</span><b>${p.cost_analysis.act_now.risk}</b></div>
        </div>
        <div class="cost-col wait">
          <h4>Wait</h4>
          <div class="cost-row"><span>Est. Maintenance</span><b>${fmtMoney(p.cost_analysis.wait.maintenance_cost)}</b></div>
          <div class="cost-row"><span>Downtime</span><b>${p.cost_analysis.wait.downtime_hours}h</b></div>
          <div class="cost-row"><span>Risk</span><b>${p.cost_analysis.wait.risk}</b></div>
        </div>
        <div class="cost-col failure">
          <h4>Failure</h4>
          <div class="cost-row"><span>Potential Repair</span><b>${fmtMoney(p.cost_analysis.failure.repair_cost)}</b></div>
          <div class="cost-row"><span>Production Loss</span><b>${fmtMoney(p.cost_analysis.failure.production_loss)}</b></div>
          <div class="cost-row"><span>Total Impact</span><b>${fmtMoney(p.cost_analysis.failure.total_impact)}+</b></div>
        </div>
      </div>
      <div style="font-size:11.5px;color:var(--text-muted);margin-top:12px">
        Figures are demonstration estimates based on configured cost assumptions, not guaranteed outcomes.
      </div>
    </div>

    <!-- FLEET SUMMARY -->
    <div class="card mt-24">
      <div class="flex-between mb-16">
        <div class="card-title" style="margin-bottom:0">Fleet Overview</div>
        <a href="assets.html" class="btn btn-secondary btn-sm">View all assets</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Machine</th><th>Health</th><th>Risk</th><th>Status</th><th>Intervention</th></tr></thead>
          <tbody>
            ${data.assets.map(a => `
              <tr>
                <td data-label="Machine">${a.name}</td>
                <td data-label="Health">${a.health_score != null ? Math.round(a.health_score)+'%' : '—'}</td>
                <td data-label="Risk">${a.risk_level ? `<span class="pill pill-${riskClass(a.risk_level)}">${a.risk_level}</span>` : '—'}</td>
                <td data-label="Status">${a.status || '—'}</td>
                <td data-label="Intervention">${a.intervention_start != null ? fmtHours(a.intervention_start)+' – '+fmtHours(a.intervention_end) : '—'}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function conditionCard(label, value, unit, slope, isLoad=false){
  const t = isLoad ? trendArrow(0, 999) : trendArrow(slope);
  const label2 = isLoad ? "Normal/High" : t.label;
  return `
    <div class="card sensor-card">
      <div class="sc-label">${label}</div>
      <div class="sc-value">${value != null ? value : '—'}${unit}</div>
      <div class="sc-trend ${t.cls}"><i class="fa-solid ${t.icon}"></i> ${label2}</div>
    </div>`;
}

function renderTimeline(p){
  const stages = ["NORMAL", "WARNING", "INTERVENTION WINDOW", "CRITICAL", "FAILURE"];
  const risk = p.risk.risk_level;
  const stageIdx = { LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3 }[risk] ?? 0;
  return `
    <div class="timeline">
      ${stages.slice(0,-1).map((s,i) => `<div class="timeline-seg ${i < stageIdx ? 'past' : i === stageIdx ? 'active' : ''}"></div>`).join("")}
    </div>
    <div class="timeline-labels">${stages.map(s => `<span>${s}</span>`).join("")}</div>
  `;
}

function renderDashboardCharts(p){
  // We don't have full history embedded in the dashboard payload, so pull
  // asset readings separately for richer trend charts.
  fetch(`${API_BASE}/assets`, { headers: { Authorization: "Bearer " + getToken() } })
    .then(r => r.json())
    .then(async assets => {
      const asset = assets.find(a => a.machine_id === p.machine_id);
      if (!asset) return;
      const readings = await Api.assetReadings(asset.id, 100);
      const labels = readings.map(r => new Date(r.timestamp).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit'}));
      mkLine("chart-temp", labels, readings.map(r=>r.temperature), "#f59e0b");
      mkLine("chart-vib", labels, readings.map(r=>r.vibration), "#ef4444");
      mkLine("chart-cur", labels, readings.map(r=>r.current), "#3b82f6");

      const history = await Api.predictionHistory(p.machine_id);
      const hLabels = history.map(h => new Date(h.created_at).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit'}));
      mkLine("chart-health", hLabels, history.map(h=>h.health_score), "#22c55e");
    })
    .catch(()=>{});
}

function mkLine(canvasId, labels, data, color){
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "line",
    data: { labels, datasets: [{ data, borderColor: color, backgroundColor: color+"22", fill:true, tension:0.35, pointRadius:0, borderWidth:2 }] },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ display:false } },
      scales:{
        x:{ ticks:{ color:"#6b7890", maxTicksLimit:6, font:{size:10} }, grid:{ color:"#1b2537" } },
        y:{ ticks:{ color:"#6b7890", font:{size:10} }, grid:{ color:"#1b2537" } }
      }
    }
  });
}
