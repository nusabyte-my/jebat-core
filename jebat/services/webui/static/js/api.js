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

/* ── SPA Router ──
 * Client-side navigation via hash fragments.
 * Pages are partials loaded into <main id="app-shell">.
 * URL pattern: /webui/#dashboard, /webui/#chat, etc.
 */
const Router = {
  current: null,
  pages: {},

  register(name, initFn) { this.pages[name] = initFn; },

  navigate(nameOrPath) {
    const name = nameOrPath.replace('#', '');
    if (!this.pages[name]) { console.warn('No page:', name); return; }
    const main = document.getElementById('app-shell');
    if (!main) return;
    main.innerHTML = '';
    this.current = name;
    this.pages[name](main);
    // Update nav active
    document.querySelectorAll('.nav-link').forEach(lnk => {
      lnk.classList.toggle('active', lnk.dataset.page === name);
    });
    // Update hash
    window.location.hash = name;
  },

  init(defaultPage) {
    window.addEventListener('hashchange', () => {
      this.navigate(window.location.hash || defaultPage);
    });
    // Load initial
    const hash = window.location.hash || defaultPage;
    if (hash) this.navigate(hash);
  },

  // Override nav link clicks
  bindNav() {
    document.addEventListener('click', e => {
      const link = e.target.closest('[data-page]');
      if (!link) return;
      e.preventDefault();
      this.navigate(link.dataset.page);
    });
  }
};

/* ── Shell layout ──
 * app-shell.html is the persistent chrome: nav + <main id="app-shell">
 * Every page partial is injected into <main id="app-shell">.
 */
/* ── Status strip updater ── */
async function updateStatusStrip() {
  try {
    const data = await API.status();
    const strip = document.getElementById('status-strip');
    if (!strip) return;
    const comps = data.components || {};
    strip.innerHTML = Object.entries(comps).map(([k, v]) =>
      `<span class="status-item"><span class="status-dot ok"></span>${k}</span>`
    ).join('');
  } catch (_) {}
}

// Poll status every 5s
setInterval(updateStatusStrip, 5000);

// ── Dark mode toggle (optional) ──
(function() {
  const saved = localStorage.getItem('jebat-theme');
  if (saved === 'dark') document.documentElement.classList.add('dark');
})();
