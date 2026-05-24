/**
 * js/api.js — Cliente centralizado para la API
 *
 * ¿Por qué centralizar las peticiones?
 *   Si algún día cambias la URL base, lo cambias en UN solo lugar.
 *   El token JWT se agrega automáticamente a todas las peticiones
 *   que lo necesiten, sin repetir código en cada página.
 */

const API_URL = 'https://fine-shoes-production.up.railway.app';

// ── Token helpers ──────────────────────────────────────────────
export function getToken()        { return localStorage.getItem('fs_token'); }
export function setToken(t)       { localStorage.setItem('fs_token', t); }
export function removeToken()     { localStorage.removeItem('fs_token'); }
export function getUser()         { return JSON.parse(localStorage.getItem('fs_user') || 'null'); }
export function setUser(u)        { localStorage.setItem('fs_user', JSON.stringify(u)); }
export function removeUser()      { localStorage.removeItem('fs_user'); }
export function isLoggedIn()      { return !!getToken(); }
export function isAdmin()         { return getUser()?.role === 'admin'; }

// ── Función base de fetch ──────────────────────────────────────
/**
 * Wrapper sobre fetch que:
 *  1. Construye la URL completa
 *  2. Agrega el token JWT si existe
 *  3. Serializa el body como JSON
 *  4. Lanza un error con el mensaje del servidor si falla
 */
async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  // Si la respuesta no es 2xx, lanzar error con el mensaje del servidor
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error de red' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  // 204 No Content — no tiene body
  if (res.status === 204) return null;
  return res.json();
}

// ── Auth ───────────────────────────────────────────────────────
export const auth = {
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login:    (data) => request('/auth/login',    { method: 'POST', body: JSON.stringify(data) }),
  me:       ()     => request('/auth/me'),
  update:   (data) => request('/auth/me',       { method: 'PUT',  body: JSON.stringify(data) }),
};

// ── Productos ──────────────────────────────────────────────────
export const products = {
  list:   (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
    ).toString();
    return request(`/products/${qs ? '?' + qs : ''}`);
  },
  get:    (id)    => request(`/products/${id}`),
  create: (data)  => request('/products/',     { method: 'POST',   body: JSON.stringify(data) }),
  update: (id, d) => request(`/products/${id}`,{ method: 'PUT',    body: JSON.stringify(d) }),
  delete: (id)    => request(`/products/${id}`,{ method: 'DELETE' }),
  updateInventory: (pid, iid, d) =>
    request(`/products/${pid}/inventory/${iid}`, { method: 'PUT', body: JSON.stringify(d) }),
  importApi: () => request('/products/import-api', { method: 'POST' }),
};

// ── Marcas ─────────────────────────────────────────────────────
export const brands = {
  list: () => request('/brands'),
};

// ── Carrito ────────────────────────────────────────────────────
export const cart = {
  get:    ()        => request('/cart/'),
  add:    (data)    => request('/cart/', { method: 'POST',   body: JSON.stringify(data) }),
  update: (id, qty) => request(`/cart/${id}`, { method: 'PUT', body: JSON.stringify({ quantity: qty }) }),
  remove: (id)      => request(`/cart/${id}`, { method: 'DELETE' }),
  clear:  ()        => request('/cart/', { method: 'DELETE' }),
};

// ── Pedidos ────────────────────────────────────────────────────
export const orders = {
  checkout: (data) => request('/orders/checkout', { method: 'POST', body: JSON.stringify(data) }),
  mine:     ()     => request('/orders/my'),
  get:      (id)   => request(`/orders/${id}`),
  all:      (p={}) => {
    const qs = new URLSearchParams(Object.fromEntries(Object.entries(p).filter(([,v])=>v))).toString();
    return request(`/orders/${qs ? '?' + qs : ''}`);
  },
  updateStatus: (id, status) =>
    request(`/orders/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),
};

// ── Reportes ───────────────────────────────────────────────────
export const reports = {
  byProduct: (limit = 10) => request(`/reports/sales-by-product?limit=${limit}`),
  byMonth:   ()           => request('/reports/sales-by-month'),
  lowStock:  (t = 5)      => request(`/reports/low-stock?threshold=${t}`),
  summary:   ()           => request('/reports/summary'),
};

// ── Logout ─────────────────────────────────────────────────────
export function logout() {
  removeToken();
  removeUser();
  window.location.href = '/fine-shoes/login.html';
}

// ── Proteger rutas ─────────────────────────────────────────────
/**
 * Llama esto al inicio de páginas que requieren login.
 * Si no hay token, redirige al login.
 */
export function requireAuth(adminOnly = false) {
  if (!isLoggedIn()) {
    window.location.href = '/fine-shoes/login.html';  // 
    return false;
  }
  if (adminOnly && !isAdmin()) {
    window.location.href = '/fine-shoes/index.html';  // 
    return false;
  }
  return true;
}

// ── Toast notifications ────────────────────────────────────────
export function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── Actualizar badge del carrito en navbar ──────────────────────
export async function refreshCartBadge() {
  if (!isLoggedIn()) return;
  try {
    const data = await cart.get();
    const badge = document.querySelector('.cart-badge');
    if (badge) {
      const total = data.items.reduce((s, i) => s + i.quantity, 0);
      badge.textContent = total;
      badge.style.display = total ? 'flex' : 'none';
    }
  } catch { /* silencioso */ }
}
