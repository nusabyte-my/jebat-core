// Cloudflare Pages Function — serve the JEBAT installer as a real shell
// script at https://jebat.online/install.sh instead of the SPA fallback
// (which would return landing.html for unknown routes).
//
// Pages Functions take precedence over the static/SPA layer, so this
// intercepts /install.sh and streams the canonical bootstrap script.

const INSTALL_SCRIPT =
  'https://raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh';

export async function onRequest() {
  try {
    const upstream = await fetch(INSTALL_SCRIPT, {
      headers: { 'User-Agent': 'cloudflare-pages-function' },
    });
    const body = await upstream.text();
    return new Response(body, {
      status: 200,
      headers: {
        'Content-Type': 'text/x-shellscript; charset=utf-8',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'X-Content-Type-Options': 'nosniff',
      },
    });
  } catch (err) {
    return new Response(`# JEBAT installer temporarily unavailable: ${err.message}\n`, {
      status: 502,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}
