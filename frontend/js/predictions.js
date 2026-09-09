async function initPredictionsPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Loading predictions...");
  try {
    const preds = await Api.predictions();
    if (!preds.length){ el.innerHTML = emptyHtml("No predictions yet", "Upload data or run a simulation to generate predictions."); return; }
    el.innerHTML = `
      <div class="card">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Machine</th><th>Health</th><th>Risk</th><th>Critical Time</th><th>Intervention Window</th><th>Confidence</th><th>Updated</th></tr></thead>
            <tbody>
              ${preds.map(p => `
                <tr class="link-row" onclick="window.location.href='assets.html'">
                  <td data-label="Machine"><b>${p.name}</b><div style="font-size:11px;color:var(--text-muted)">${p.machine_id}</div></td>
                  <td data-label="Health">${Math.round(p.health_score)}%</td>
                  <td data-label="Risk"><span class="pill pill-${riskClass(p.risk_level)}">${p.risk_level}</span></td>
                  <td data-label="Critical Time">${fmtHours(p.critical_time_hours)}</td>
                  <td data-label="Intervention">${p.intervention_start != null ? fmtHours(p.intervention_start)+' – '+fmtHours(p.intervention_end) : '—'}</td>
                  <td data-label="Confidence">${p.confidence}%</td>
                  <td data-label="Updated">${fmtDate(p.updated_at)}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load predictions", err.message);
  }
}
