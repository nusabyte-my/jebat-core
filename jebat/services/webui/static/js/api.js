/* ── JEBAT API Client ──
 * Shared fetch wrapper. Every page loads this.
 */
const API = {
  base: '/webui/api',
  timeout: 15000,

  async fetch(path, opts = {}) {
    const url = `${this.base}${path}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeout);
    const headers = { ...opts.headers };
    if (opts.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';

    try {
      const res = await fetch(url, { ...opts, headers, signal: controller.signal });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        const error = new Error(payload.detail || payload.error || `Request failed (${res.status})`);
        error.status = res.status;
        throw error;
      }
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
  } catch (_) {
    dot.className = 'topbar-status-dot error';
    text.textContent = 'Reconnecting';
  }
}

updateConnectionStatus();
setInterval(updateConnectionStatus, 15000);

// ── Dark mode toggle (optional) ──
(function() {
  const saved = localStorage.getItem('jebat-theme');
  if (saved === 'dark') document.documentElement.classList.add('dark');
})();
