/* auth.js — login page + shared route-guard/shell used by every other page */

function requireAuth(){
  if (!getToken()){
    window.location.href = "login.html";
    return false;
  }
  return true;
}

function initLoginPage(){
  const form = document.getElementById("login-form");
  const errBox = document.getElementById("login-error");
  if (getToken()){ window.location.href = "dashboard.html"; return; }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const btn = document.getElementById("login-btn");
    btn.disabled = true; btn.textContent = "Signing in...";
    try {
      const data = await Api.login(email, password);
      setSession(data.access_token, { name: data.user_name, email: data.user_email });
      window.location.href = "dashboard.html";
    } catch (err) {
      errBox.textContent = err.message || "Invalid email or password.";
      errBox.style.display = "block";
    } finally {
      btn.disabled = false; btn.textContent = "Login";
    }
  });
}

/* ---------------- Shared app shell (sidebar/topbar) ---------------- */
const NAV_ITEMS = [
  { href: "dashboard.html", icon: "fa-gauge-high", label: "Dashboard" },
  { href: "assets.html", icon: "fa-server", label: "Assets" },
  { href: "data.html", icon: "fa-upload", label: "Data Upload" },
  { href: "predictions.html", icon: "fa-chart-line", label: "Predictions" },
  { href: "intervention-windows.html", icon: "fa-triangle-exclamation", label: "Intervention Windows" },
  { href: "maintenance.html", icon: "fa-screwdriver-wrench", label: "Maintenance" },
  { href: "alerts.html", icon: "fa-bell", label: "Alerts" },
  { href: "analytics.html", icon: "fa-chart-pie", label: "Analytics" },
  { href: "simulation.html", icon: "fa-flask", label: "Simulation" },
  { href: "settings.html", icon: "fa-gear", label: "Settings" },
];

function renderShell(activeHref, pageTitle){
  if (!requireAuth()) return;
  const user = getUser() || { name: "User", email: "" };
  const initials = (user.name || "U").split(" ").map(s=>s[0]).slice(0,2).join("").toUpperCase();

  document.getElementById("app-shell").innerHTML = `
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <div class="brand-title">Last-Safe-<span>Moment</span></div>
        <div class="brand-sub">Predictive Maintenance Decision Support</div>
      </div>
      <nav class="nav">
        ${NAV_ITEMS.map(item => `
          <a href="${item.href}" class="${item.href === activeHref ? 'active' : ''}">
            <i class="fa-solid ${item.icon} nav-icon"></i> ${item.label}
          </a>`).join("")}
      </nav>
      <div class="sidebar-footer">
        <div class="user-chip">
          <div class="avatar">${initials}</div>
          <div>
            <div class="u-name">${user.name}</div>
            <div class="u-email">${user.email}</div>
          </div>
        </div>
        <button class="logout-btn" id="logout-btn">Log out</button>
      </div>
    </aside>
    <div class="main">
      <div class="topbar">
        <div style="display:flex;align-items:center;gap:12px">
          <button class="menu-toggle" id="menu-toggle"><i class="fa-solid fa-bars"></i></button>
          <h1>${pageTitle}</h1>
        </div>
        <div class="top-actions">
          <div class="icon-btn" title="Notifications"><i class="fa-solid fa-bell"></i><span class="dot" id="alert-dot" style="display:none"></span></div>
          <div class="icon-btn" title="Account"><i class="fa-solid fa-user"></i></div>
        </div>
      </div>
      <div class="page" id="page-content"></div>
    </div>
  `;

  document.getElementById("logout-btn").addEventListener("click", () => {
    clearSession();
    window.location.href = "login.html";
  });
  const toggle = document.getElementById("menu-toggle");
  if (toggle){
    toggle.addEventListener("click", () => document.getElementById("sidebar").classList.toggle("open"));
  }

  // Light-touch unread-alert indicator on the bell icon
  Api.alerts().then(alerts => {
    const unread = alerts.filter(a => !a.is_read).length;
    if (unread > 0) document.getElementById("alert-dot").style.display = "block";
  }).catch(() => {});
}

function showToast(message, type="success"){
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function loadingHtml(msg){
  return `<div class="loading-state"><div class="spinner"></div>${msg}</div>`;
}
function emptyHtml(title, msg){
  return `<div class="empty-state"><h4>${title}</h4><p>${msg}</p></div>`;
}

/* ---------------- Shared formatting helpers (used across all pages) ---------------- */
function riskClass(risk){
  return { LOW:"low", MEDIUM:"medium", HIGH:"high", CRITICAL:"critical" }[risk] || "neutral";
}
function fmtMoney(n){
  if (n == null) return "—";
  return "₹" + Number(n).toLocaleString("en-IN");
}
function fmtHours(n){
  if (n == null) return "—";
  if (n > 999) return Math.round(n).toLocaleString() + "h";
  return Math.round(n * 10) / 10 + "h";
}
function fmtDate(iso){
  if (!iso) return "—";
  return new Date(iso).toLocaleString([], { month:"short", day:"numeric", hour:"2-digit", minute:"2-digit" });
}
