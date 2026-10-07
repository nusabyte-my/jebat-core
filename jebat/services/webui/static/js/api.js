/* ── JEBAT API Client ──
 * Shared fetch wrapper. Every page loads this.
 */
// One-time migration: keep an existing credential only in this tab's session.
try {
  const legacy = localStorage.getItem('jebat_api_key') || localStorage.getItem('api_key');
  if (legacy && !sessionStorage.getItem('jebat_api_key')) sessionStorage.setItem('jebat_api_key', legacy);
  localStorage.removeItem('jebat_api_key');
  localStorage.removeItem('api_key');
} catch (_) { /* Storage may be disabled; the current tab can still authenticate. */ }

const API = {
  base: '/webui/api',
  timeout: 15000,
  key: '',

  getKey() {
    try { return this.key || sessionStorage.getItem('jebat_api_key') || ''; }
    catch (_) { return this.key; }
  },

  setKey(key) {
    this.key = key || '';
    try {
      if (this.key) sessionStorage.setItem('jebat_api_key', this.key);
      else sessionStorage.removeItem('jebat_api_key');
    } catch (_) { /* In-memory authentication remains available. */ }
  },

  getWsUrl(userId) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const key = this.getKey();
    const query = key ? `?api_key=${encodeURIComponent(key)}` : '';
    return `${proto}//${window.location.host}/webui/ws/${encodeURIComponent(userId || 'default')}${query}`;
  },

  async request(path, opts = {}) {
    const url = new URL(path, window.location.href);
    if (url.origin !== window.location.origin || !(/^\/(?:api|v1)\//.test(url.pathname) || url.pathname.startsWith('/webui/api/'))) {
      throw new Error('API requests must use a same-origin JEBAT API route.');
    }
    const headers = new Headers(opts.headers);
    const key = this.getKey();
    if (key && !headers.has('X-API-Key') && !headers.has('Authorization')) headers.set('X-API-Key', key);
    const response = await fetch(url.href, { ...opts, headers, redirect: 'error' });
    if (!response.ok) {
      const payload = await response.clone().json().catch(() => ({}));
      const error = new Error(payload.detail || payload.message || payload.error || `Request failed (${response.status})`);
      error.status = response.status;
      if (response.status === 401 || (response.status === 403 && payload.error === 'forbidden')) {
        window.dispatchEvent(new CustomEvent('jebat-auth-required', { detail: { status: response.status } }));
      }
      throw error;
    }
    return response;
  },

  async fetch(path, opts = {}) {
    const url = `${this.base}${path}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeout);
    const headers = { ...opts.headers };
    if (opts.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
    // request() owns same-origin credential injection and authentication errors.

    try {
      const res = await this.request(url, { ...opts, headers, signal: controller.signal });
      const payload = await res.json().catch(() => ({}));
      return payload;
    } catch (error) {
      if (error.name === 'AbortError') {
        const timeoutError = new Error('Request timed out. Check the JEBAT connection and try again.');
        timeoutError.status = 408;
        throw timeoutError;
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  },

  get(path) { return this.fetch(path); },
  post(path, body) { return this.fetch(path, { method: 'POST', body: JSON.stringify(body) }); },

  // Convenience methods
  status()     { return this.get('/status'); },
  runtime()    { return this.get('/runtime'); },
  setRuntime(data) { return this.post('/runtime', data); },
  chat(data) { return this.post('/chat', data); },
  channels()   { return this.get('/channels/connect'); },
  connectChannel(data) { return this.post('/channels/connect', data); },
  workstations() { return this.get('/workstations/connect'); },
  connectStation(data) { return this.post('/workstations/connect', data); },
  checkStation(data) { return this.post('/workstations/check', data); },
  providerAuth(data) { return this.post('/provider-auth', data); },
  providerAuthGoogleStart(clientId, clientSecret) {
    return this.post('/provider-auth/google/oauth/start', { client_id: clientId || null, client_secret: clientSecret || null });
  },
  providerAuthGooglePoll(deviceCode) { return this.post('/provider-auth/google/oauth/poll', { device_code: deviceCode }); },
  providerAuthGoogleDisconnect() { return this.post('/provider-auth/google/oauth/disconnect', {}); },
  memoryStats(layer) { return this.get(`/memory/stats?layer=${layer || 'all'}`); },
  consoleMeta() { return this.get('/console-meta'); }
};

async function updateConnectionStatus() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  if (!dot || !text) return;
  try {
    const data = await API.status();
    const componentCount = Object.keys(data.components || {}).length;
    dot.className = 'topbar-status-dot';
    text.textContent = `${componentCount} systems ready`;
  } catch (error) {
    dot.className = 'topbar-status-dot error';
    text.textContent = error.status === 401 || error.status === 403 ? 'Authentication required' : 'Connection unavailable';
  }
}

updateConnectionStatus();
setInterval(updateConnectionStatus, 15000);

// ── Host CPU steal indicator ──
// Shows a chip in the topbar when the hypervisor steals CPU from this VM
// (visible cause of slow local inference). Hidden below the warn threshold.
async function updateStealChip() {
  const chip = document.getElementById('steal-chip');
  if (!chip) return;
  try {
    const res = await API.request('/api/system/metrics', { cache: 'no-store' });
    const m = await res.json();
    const steal = Number(m.cpu_steal_percent || 0);
    if (steal >= 12) {
      chip.hidden = false;
      chip.textContent = `steal ${steal.toFixed ? steal.toFixed(0) : steal}%`;
      chip.classList.toggle('hot', steal >= 25);
      chip.title = `Host CPU steal: ${steal}% — the hypervisor is taking CPU cycles from this VM. This directly slows local model inference.`;
    } else {
      chip.hidden = true;
    }
  } catch (_) { /* metrics unavailable — keep chip hidden */ }
}
updateStealChip();
setInterval(updateStealChip, 60000);

// ── Dark mode toggle (optional) ──
(function() {
  const saved = localStorage.getItem('jebat-theme');
  if (saved === 'dark') document.documentElement.classList.add('dark');
})();
