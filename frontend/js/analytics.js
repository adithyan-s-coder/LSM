async function initAnalyticsPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = loadingHtml("Crunching fleet analytics...");
  try {
    const a = await Api.analytics();
    el.innerHTML = `
      <div class="grid grid-4 mb-16">
        <div class="card"><div class="sc-label">Total Anomalies</div><div class="sc-value">${a.anomaly_count}</div></div>
        <div class="card"><div class="sc-label">Maintenance Cost</div><div class="sc-value" style="font-size:20px">${fmtMoney(a.maintenance_cost_total)}</div></div>
        <div class="card"><div class="sc-label">Downtime</div><div class="sc-value">${Math.round(a.downtime_total_hours)}h</div></div>
        <div class="card"><div class="sc-label">Failure Events</div><div class="sc-value">${a.failure_count}</div></div>
      </div>
      <div class="grid grid-2 mb-16">
        <div class="card"><div class="card-title">Risk Distribution</div><div class="chart-box"><canvas id="ch-risk"></canvas></div></div>
        <div class="card"><div class="card-title">Machine Health (Latest)</div><div class="chart-box"><canvas id="ch-health"></canvas></div></div>
      </div>
      <div class="card">
        <div class="card-title">Machine Health Over Time</div>
        <div class="chart-box" style="height:280px"><canvas id="ch-health-time"></canvas></div>
      </div>
    `;
    renderRiskChart(a.risk_distribution);
    renderHealthBarChart(a.health_distribution);
    renderHealthOverTime(a.health_over_time);
  } catch (err) {
    el.innerHTML = emptyHtml("Couldn't load analytics", err.message);
  }
}

function renderRiskChart(dist){
  new Chart(document.getElementById("ch-risk"), {
    type: "doughnut",
    data: {
      labels: Object.keys(dist),
      datasets: [{ data: Object.values(dist), backgroundColor: ["#22c55e","#f59e0b","#ef4444","#7f1d1d"] }]
    },
    options: { plugins:{ legend:{ position:"bottom", labels:{ color:"#a7b3c8" } } } }
  });
}

function renderHealthBarChart(dist){
  new Chart(document.getElementById("ch-health"), {
    type: "bar",
    data: {
      labels: dist.map(d => d.machine_id),
      datasets: [{ label: "Health %", data: dist.map(d => d.health_score), backgroundColor: "#3b82f6" }]
    },
    options: {
      plugins:{ legend:{ display:false } },
      scales:{ x:{ ticks:{ color:"#6b7890" }, grid:{ display:false } }, y:{ min:0, max:100, ticks:{ color:"#6b7890" }, grid:{ color:"#1b2537" } } }
    }
  });
}

function renderHealthOverTime(byMachine){
  const colors = ["#3b82f6","#22c55e","#f59e0b","#ef4444","#8b5cf6"];
  const datasets = Object.entries(byMachine).map(([machineId, points], i) => ({
    label: machineId,
    data: points.map(p => p.health_score),
    borderColor: colors[i % colors.length],
    backgroundColor: "transparent",
    tension: 0.3,
    pointRadius: 0,
    borderWidth: 2,
  }));
  const maxLen = Math.max(0, ...Object.values(byMachine).map(p => p.length));
  new Chart(document.getElementById("ch-health-time"), {
    type: "line",
    data: { labels: Array.from({length:maxLen}, (_,i)=>`#${i+1}`), datasets },
    options: {
      plugins:{ legend:{ position:"bottom", labels:{ color:"#a7b3c8" } } },
      scales:{ x:{ ticks:{ color:"#6b7890" }, grid:{ color:"#1b2537" } }, y:{ ticks:{ color:"#6b7890" }, grid:{ color:"#1b2537" } } }
    }
  });
}
