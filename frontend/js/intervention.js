async function initInterventionPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Calculating intervention windows...");
  try {
    const windows = await Api.interventionWindows();
    if (!windows.length){ el.innerHTML = emptyHtml("No intervention windows found", "All monitored machines are currently within acceptable operating conditions."); return; }
    el.innerHTML = `
      <div class="section-title">Last-Safe-Moment Analysis</div>
      <div class="section-sub">Machines sorted by urgency — soonest intervention window first.</div>
      <div class="grid grid-2">
        ${windows.map(w => renderWindowCard(w)).join("")}
      </div>
    `;
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load intervention windows", err.message);
  }
}

function renderWindowCard(w){
  // Infer a rough risk label from recommendation urgency for the pill color
  const urgent = w.window_start_hours != null && w.window_start_hours < 48;
  const riskGuess = urgent ? (w.window_start_hours < 12 ? "CRITICAL" : "HIGH") : "MEDIUM";
  return `
    <div class="card">
      <div class="flex-between mb-16">
        <div>
          <div style="font-weight:800;font-size:16px">${w.name}</div>
          <div style="font-size:11.5px;color:var(--text-muted)">${w.machine_id}</div>
        </div>
        <span class="pill pill-${riskClass(riskGuess)}">${riskGuess}</span>
      </div>
      <div style="font-size:26px;font-weight:800;margin-bottom:4px">
        ${fmtHours(w.window_start_hours)} – ${fmtHours(w.window_end_hours)}
      </div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px">Last safe window · Confidence ${Math.round(w.confidence)}%</div>

      <div class="timeline">
        <div class="timeline-seg past"></div>
        <div class="timeline-seg active"></div>
        <div class="timeline-seg"></div>
      </div>
      <div class="timeline-labels"><span>SAFE</span><span>INTERVENTION WINDOW</span><span>CRITICAL</span><span>FAILURE</span></div>

      <div class="hero-action mt-16"><b>Action:</b> ${w.recommendation || 'Continue monitoring'}</div>
      <div class="mt-16" style="font-size:12px;color:var(--text-secondary)">${(w.reason || "").split(";").filter(Boolean).map(r=>`<div style="padding:3px 0">• ${r.trim()}</div>`).join("")}</div>
    </div>
  `;
}
