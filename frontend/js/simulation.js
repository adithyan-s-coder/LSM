const SCENARIOS = ["Healthy Machine", "Temporary Anomaly", "Gradual Deterioration", "Rapid Deterioration", "Near Failure"];

async function initSimulationPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Loading machines...");
  try {
    const assets = await Api.assets();
    el.innerHTML = `
      <div class="card mb-16">
        <div class="card-title">Run a Simulation</div>
        <div class="grid grid-4">
          <div class="form-group">
            <label>Machine</label>
            <select class="form-control" id="sim-machine">${assets.map(a => `<option value="${a.machine_id}">${a.name}</option>`).join("")}</select>
          </div>
          <div class="form-group">
            <label>Scenario</label>
            <select class="form-control" id="sim-scenario">${SCENARIOS.map(s => `<option>${s}</option>`).join("")}</select>
          </div>
          <div class="form-group">
            <label>Duration (hours)</label>
            <input class="form-control" type="number" id="sim-duration" value="48" min="6" max="200">
          </div>
          <div class="form-group">
            <label>Severity</label>
            <select class="form-control" id="sim-severity"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select>
          </div>
        </div>
        <button class="btn btn-primary" id="run-sim-btn"><i class="fa-solid fa-flask"></i> Run Simulation</button>
      </div>
      <div id="sim-results"></div>
    `;
    document.getElementById("run-sim-btn").addEventListener("click", runSim);
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load simulation page", err.message);
  }
}

async function runSim(){
  const btn = document.getElementById("run-sim-btn");
  const resultsEl = document.getElementById("sim-results");
  const payload = {
    machine_id: document.getElementById("sim-machine").value,
    scenario: document.getElementById("sim-scenario").value,
    duration_hours: parseInt(document.getElementById("sim-duration").value, 10) || 48,
    severity: document.getElementById("sim-severity").value,
  };
  btn.disabled = true; btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running simulation...`;
  resultsEl.innerHTML = loadingHtml("Running simulation and recalculating predictions...");
  try {
    const result = await Api.runSimulation(payload);
    resultsEl.innerHTML = renderSimResults(result);
    const labels = result.generated_readings.map((_, i) => `+${i+1}h`);
    mkLine("sim-chart-temp", labels, result.generated_readings.map(r=>r.temperature), "#f59e0b");
    mkLine("sim-chart-vib", labels, result.generated_readings.map(r=>r.vibration), "#ef4444");
  } catch (err) {
    resultsEl.innerHTML = emptyHtml("Simulation failed", err.message);
  } finally {
    btn.disabled = false; btn.innerHTML = `<i class="fa-solid fa-flask"></i> Run Simulation`;
  }
}

function renderSimResults(result){
  const b = result.before, a = result.after;
  if (a.error) return emptyHtml("No result", a.error);
  return `
    <div class="grid grid-2 mb-16">
      <div class="card">
        <div class="card-title">Before Simulation</div>
        ${simSnapshot(b)}
      </div>
      <div class="card">
        <div class="card-title">After ${result.scenario} (${result.severity} severity, ${result.duration_hours}h)</div>
        ${simSnapshot(a)}
      </div>
    </div>
    <div class="grid grid-2 mb-16">
      <div class="card"><div class="card-title">Simulated Temperature</div><div class="chart-box"><canvas id="sim-chart-temp"></canvas></div></div>
      <div class="card"><div class="card-title">Simulated Vibration</div><div class="chart-box"><canvas id="sim-chart-vib"></canvas></div></div>
    </div>
    <div class="card">
      <div class="card-title">Updated Recommendation</div>
      <div class="hero-action">${a.recommendation.headline}</div>
    </div>
  `;
}

function simSnapshot(x){
  if (x.error) return emptyHtml("No data", x.error);
  return `
    <div class="grid grid-3">
      <div><div class="sc-label">Health</div><div class="sc-value" style="font-size:20px">${Math.round(x.health.health_score)}%</div></div>
      <div><div class="sc-label">Risk</div><div class="sc-value" style="font-size:20px"><span class="pill pill-${riskClass(x.risk.risk_level)}">${x.risk.risk_level}</span></div></div>
      <div><div class="sc-label">Intervention</div><div class="sc-value" style="font-size:16px">${x.last_safe_moment.intervention_start != null ? fmtHours(x.last_safe_moment.intervention_start)+' – '+fmtHours(x.last_safe_moment.intervention_end) : 'None'}</div></div>
    </div>
  `;
}
