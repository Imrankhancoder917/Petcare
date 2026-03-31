/* ===== PetCare Connect Pro — Shared JavaScript ===== */

const API_BASE = "http://localhost:5000";

// ── Token helpers ──────────────────────────────────────
function getToken()         { return localStorage.getItem("pc_token"); }
function getRole()          { return localStorage.getItem("pc_role"); }
function getUserName()      { return localStorage.getItem("pc_name"); }
function isLoggedIn()       { return !!getToken(); }

function saveAuth(token, role, name) {
  localStorage.setItem("pc_token", token);
  localStorage.setItem("pc_role", role);
  localStorage.setItem("pc_name", name);
}

function clearAuth() {
  localStorage.removeItem("pc_token");
  localStorage.removeItem("pc_role");
  localStorage.removeItem("pc_name");
}

function logout() {
  clearAuth();
  window.location.href = "login.html";
}

// Redirect to login if not authenticated
function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "login.html";
  }
}

// ── Fetch wrapper ──────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) {
    clearAuth();
    window.location.href = "login.html";
    return null;
  }
  return { ok: res.ok, status: res.status, data };
}

// ── Toast notifications ────────────────────────────────
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

// ── Navbar builder ─────────────────────────────────────
function buildNavbar(activePage) {
  const role = getRole();
  const name = getUserName();

  const pages = [
    { href: "index.html",     label: "Home",      always: true },
    { href: "dashboard.html", label: "Dashboard", auth: true },
    { href: "map.html",       label: "Map",       auth: true },
    { href: "admin.html",     label: "Admin",     role: "admin" },
  ];

  const links = pages
    .filter(p => {
      if (p.role) return role === p.role;
      if (p.auth) return isLoggedIn();
      return true;
    })
    .map(p => `<a href="${p.href}" class="${activePage === p.href ? 'active' : ''}">${p.label}</a>`)
    .join("");

  const rightSide = isLoggedIn()
    ? `<span id="nav-user-info">👤 ${name} (${role})</span>
       <button class="btn btn-sm btn-outline" style="color:#fff;border-color:#fff" onclick="logout()">Logout</button>`
    : `<a href="login.html" class="btn btn-sm btn-outline" style="color:#fff;border-color:#fff">Login</a>`;

  return `
    <nav class="navbar">
      <a href="index.html" class="brand">🐾 PetCare <span>Connect Pro</span></a>
      <div class="nav-links">${links}</div>
      <div class="flex">${rightSide}</div>
    </nav>`;
}

// ── Badge helpers ──────────────────────────────────────
function urgencyBadge(u) {
  const cls = u === "HIGH" ? "badge-high" : "badge-low";
  return `<span class="badge ${cls}">${u}</span>`;
}

function statusBadge(s) {
  const cls = "badge-" + s.toLowerCase().replace(/_/g, "-");
  return `<span class="badge ${cls}">${s.replace(/_/g, " ")}</span>`;
}

// ── Format date ────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString();
}
