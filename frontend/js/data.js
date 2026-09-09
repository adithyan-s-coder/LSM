function initDataPage(){
  const el = document.getElementById("page-content");
  el.innerHTML = `
    <div class="grid grid-2">
      <div class="card">
        <div class="card-title">Upload Sensor CSV</div>
        <div class="section-sub">Upload historical or new sensor readings for processing. Required columns:</div>
        <div class="card" style="background:var(--navy-800);font-family:monospace;font-size:12px;margin-bottom:16px;overflow-x:auto;white-space:nowrap">
          timestamp, machine_id, temperature, vibration, current, load, operating_hours
        </div>
        <div class="form-group">
          <label for="csv-file">CSV File</label>
          <input type="file" id="csv-file" accept=".csv" class="form-control">
        </div>
        <button class="btn btn-primary" id="upload-btn"><i class="fa-solid fa-upload"></i> Upload &amp; Process</button>
        <div id="upload-status" class="mt-16"></div>
      </div>
      <div class="card">
        <div class="card-title">What Happens On Upload</div>
        <ul class="reason-list">
          <li><i class="fa-solid fa-circle-check chk"></i> Columns and values are validated</li>
          <li><i class="fa-solid fa-circle-check chk"></i> Readings are stored per machine</li>
          <li><i class="fa-solid fa-circle-check chk"></i> Anomaly detection is re-run (Isolation Forest)</li>
          <li><i class="fa-solid fa-circle-check chk"></i> Health score and deterioration are recalculated</li>
          <li><i class="fa-solid fa-circle-check chk"></i> Predictions and the intervention window are updated</li>
        </ul>
        <div class="mt-16" style="font-size:12px;color:var(--text-muted)">
          Rows referencing an unknown machine_id are skipped and reported, not silently dropped.
        </div>
      </div>
    </div>
  `;
  document.getElementById("upload-btn").addEventListener("click", handleUpload);
}

async function handleUpload(){
  const fileInput = document.getElementById("csv-file");
  const statusEl = document.getElementById("upload-status");
  const btn = document.getElementById("upload-btn");
  if (!fileInput.files.length){
    statusEl.innerHTML = `<div class="err-box" style="display:block">Please choose a CSV file first.</div>`;
    return;
  }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  btn.disabled = true; btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing...`;
  statusEl.innerHTML = loadingHtml("Processing sensor data...");
  try {
    const result = await Api.uploadCsv(formData);
    statusEl.innerHTML = `
      <div class="card" style="background:var(--navy-800)">
        <div style="font-weight:700;color:var(--green);margin-bottom:8px"><i class="fa-solid fa-circle-check"></i> Upload processed</div>
        <div style="font-size:13px;color:var(--text-secondary)">
          Rows inserted: <b>${result.rows_inserted}</b> · Rows skipped: <b>${result.rows_skipped}</b> · Machines updated: <b>${result.assets_updated}</b>
        </div>
        ${result.errors.length ? `<div style="margin-top:10px;font-size:12px;color:var(--amber)">${result.errors.join("<br>")}</div>` : ""}
      </div>`;
    showToast("CSV processed and predictions updated");
  } catch (err) {
    statusEl.innerHTML = `<div class="err-box" style="display:block">${err.message}</div>`;
  } finally {
    btn.disabled = false; btn.innerHTML = `<i class="fa-solid fa-upload"></i> Upload &amp; Process`;
  }
}
