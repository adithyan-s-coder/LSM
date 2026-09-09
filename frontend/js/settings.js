function initSettingsPage(){
  const el = document.getElementById("page-content");
  const user = getUser() || { name: "", email: "" };
  el.innerHTML = `
    <div class="grid grid-2">
      <div class="card">
        <div class="card-title">User Settings</div>
        <div class="form-group"><label>Name</label><input class="form-control" value="${user.name}" disabled></div>
        <div class="form-group"><label>Email</label><input class="form-control" value="${user.email}" disabled></div>
        <div style="font-size:11.5px;color:var(--text-muted)">Profile editing is not wired up in this MVP — this reflects the logged-in demo account.</div>
      </div>

      <div class="card">
        <div class="card-title">Machine Threshold Settings</div>
        <div class="form-group"><label>Temperature limit (°C)</label><input class="form-control" type="number" id="t-limit" value="85"></div>
        <div class="form-group"><label>Vibration limit (mm/s)</label><input class="form-control" type="number" id="v-limit" value="9"></div>
        <div class="form-group"><label>Current limit (A)</label><input class="form-control" type="number" id="c-limit" value="18"></div>
        <div class="form-group"><label>Load limit (%)</label><input class="form-control" type="number" id="l-limit" value="95"></div>
        <div class="form-group"><label>Critical health threshold</label><input class="form-control" type="number" id="h-limit" value="45"></div>
        <button class="btn btn-primary btn-sm" onclick="showToast('Threshold settings saved (demo only — not yet persisted per machine via UI)')">Save Thresholds</button>
      </div>

      <div class="card">
        <div class="card-title">Cost Settings</div>
        <div class="form-group"><label>Hourly downtime cost (₹)</label><input class="form-control" type="number" id="dt-cost" value="2500"></div>
        <div class="form-group"><label>Emergency repair cost (₹)</label><input class="form-control" type="number" id="er-cost" value="280000"></div>
        <div class="form-group"><label>Production loss estimate (₹)</label><input class="form-control" type="number" id="pl-cost" value="520000"></div>
        <button class="btn btn-primary btn-sm" onclick="showToast('Cost settings saved (demo only — not yet persisted per machine via UI)')">Save Costs</button>
      </div>

      <div class="card">
        <div class="card-title">About</div>
        <div style="font-size:13px;color:var(--text-secondary);line-height:1.7">
          <b>Last-Safe-Moment Engine</b><br>
          Don't just predict failure. Find the last safe moment to act.<br><br>
          All predictions and cost/risk figures are estimates derived from available sensor data
          and configured assumptions — never guarantees.
        </div>
      </div>
    </div>
  `;
}
