/* api.js — all backend communication lives here, kept separate from UI logic. */
const API_BASE = "/api";

function getToken(){ return localStorage.getItem("lsm_token"); }
function getUser(){
  try { return JSON.parse(localStorage.getItem("lsm_user") || "null"); }
  catch(e){ return null; }
}
function setSession(token, user){
  localStorage.setItem("lsm_token", token);
  localStorage.setItem("lsm_user", JSON.stringify(user));
}
function clearSession(){
  localStorage.removeItem("lsm_token");
  localStorage.removeItem("lsm_user");
}

async function apiRequest(path, { method = "GET", body = null, isForm = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  if (!isForm && body) headers["Content-Type"] = "application/json";

  let resp;
  try {
    resp = await fetch(API_BASE + path, {
      method,
      headers,
      body: isForm ? body : (body ? JSON.stringify(body) : undefined),
    });
  } catch (networkErr) {
    throw new Error("Network error — could not reach the server. Please check your connection.");
  }

  if (resp.status === 401) {
    clearSession();
    window.location.href = "login.html";
    throw new Error("Session expired. Please log in again.");
  }

  let data = null;
  try { data = await resp.json(); } catch (e) { /* empty body */ }

  if (!resp.ok) {
    const detail = (data && data.detail) ? data.detail : `Request failed (${resp.status})`;
    throw new Error(detail);
  }
  return data;
}

const Api = {
  login: (email, password) => apiRequest("/auth/login", { method: "POST", body: { email, password } }),
  dashboard: () => apiRequest("/dashboard"),
  assets: () => apiRequest("/assets"),
  asset: (id) => apiRequest(`/assets/${id}`),
  assetReadings: (id, limit=200) => apiRequest(`/assets/${id}/readings?limit=${limit}`),
  assetAnalysis: (id) => apiRequest(`/assets/${id}/analysis`),
  createAsset: (payload) => apiRequest("/assets", { method: "POST", body: payload }),
  uploadCsv: (formData) => apiRequest("/data/upload", { method: "POST", body: formData, isForm: true }),
  predictions: () => apiRequest("/predictions"),
  predictionHistory: (machineId) => apiRequest(`/predictions/${machineId}/history`),
  interventionWindows: () => apiRequest("/intervention-windows"),
  maintenance: () => apiRequest("/maintenance"),
  createMaintenance: (payload) => apiRequest("/maintenance", { method: "POST", body: payload }),
  updateMaintenance: (id, payload) => apiRequest(`/maintenance/${id}`, { method: "PUT", body: payload }),
  alerts: () => apiRequest("/alerts"),
  markAlertRead: (id) => apiRequest(`/alerts/${id}/read`, { method: "PUT" }),
  analytics: () => apiRequest("/analytics"),
  runSimulation: (payload) => apiRequest("/simulation/run", { method: "POST", body: payload }),
};
