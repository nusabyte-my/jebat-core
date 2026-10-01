/* JEBAT WebUI service worker — v8.2.1-agentix
 * Strategy:
 *   - HTML shell (/webui/): network-first, cache fallback (offline shell)
 *   - Static assets (/webui/static/): stale-while-revalidate
 *   - API + WS + health: network-only (never cache auth'd/dynamic responses)
 * Version-bumped CACHE_NAME triggers clean activation of old caches.
 */
const CACHE_NAME = 'jebat-v8.2.1-agentix';
const SHELL_CACHE = 'jebat-shell-v8.2.1-agentix';
const PRECACHE = [
  '/webui/static/css/stealth.css',
  '/webui/static/favicon-32.png',
  '/webui/static/favicon.png',
  '/webui/static/jebat-app-icon.png',
  '/webui/static/manifest.json',
  '/webui/static/offline.html',
  '/favicon.svg'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(c => Promise.allSettled(PRECACHE.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== SHELL_CACHE)
            .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  const path = url.pathname;

  // Never intercept: API, WS upgrade, health, cross-origin
  if (
    url.origin !== self.location.origin ||
    path.includes('/api/') ||
    path.startsWith('/webui/ws') ||
    path === '/health' ||
    path === '/ready'
  ) return;

  // HTML shell: network-first with offline shell fallback
  if (path === '/webui/' || path === '/webui/index.html') {
    event.respondWith(
      fetch(event.request)
        .then(resp => {
          const copy = resp.clone();
          caches.open(SHELL_CACHE).then(c => c.put(event.request, copy));
          return resp;
        })
        .catch(() => caches.match(event.request)
          .then(c => c || caches.match('/webui/'))
          .then(c => c || caches.match('/webui/static/offline.html')))
    );
    return;
  }

  // Static assets: stale-while-revalidate
  if (path.startsWith('/webui/static/') || path === '/favicon.svg') {
    event.respondWith(
      caches.match(event.request).then(cached => {
        const network = fetch(event.request).then(resp => {
          if (resp.ok) {
            const copy = resp.clone();
            caches.open(CACHE_NAME).then(c => c.put(event.request, copy));
          }
          return resp;
        }).catch(() => cached);
        return cached || network;
      })
    );
  }
  // everything else: passthrough (no respondWith)
});
