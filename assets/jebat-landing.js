/* Recorded product evidence and local UI controls; no agent execution. */
'use strict';

const INSTALL_CMDS = {
  cli: document.getElementById('install-cmd').textContent,
  ide: '# Print the templates, then copy the section for your IDE\njebat mcp ide-config\n\n# Start a local stdio server through the IDE configuration\n# command: jebat\n# args: ["mcp", "serve", "--transport", "stdio"]',
  docker: '# From a configured checkout: review external networks, volumes, and env_file first\ndocker compose -f infra/vps/vps/docker-compose.mcp.yml config\n\n# Start only after providing the required environment and credentials\ndocker compose -f infra/vps/vps/docker-compose.mcp.yml up -d\n\n# Inspect the actual health result; no success is assumed\ndocker inspect --format \'{{.State.Health.Status}}\' jebat-mcp',
  npx: '# Requires Node.js and Python 3.11+ already installed\nnpx @nusabyte/jebat mcp serve --transport stdio\n\n# The launcher may download dependencies on first use.\n# Review the package and configuration before granting tool access.',
  remote: '# Choose your IDE in the configuration panel.\n# Replace the example URL with your running HTTPS MCP endpoint.\n# Supply the existing server key using the header your gateway requires.\n# Generating a new key alone does not grant access to an existing server.\n\n# Confirm authenticated tool discovery before running agents.\n# Require TLS and restricted network access.'
};
const LOCAL_SERVER = { command: 'jebat', args: ['mcp', 'serve', '--transport', 'stdio'] };
const IDE_CLIENTS = ['cursor', 'vscode', 'windsurf'];
let selectedInstall = 'cli';
let selectedIde = 'cursor';

function renderIdeConfig() {
  let server = LOCAL_SERVER;
  let transport = 'Local stdio';
  if (selectedInstall === 'npx') {
    server = { command: 'npx', args: ['@nusabyte/jebat', 'mcp', 'serve', '--transport', 'stdio'] };
    transport = 'npm launcher · stdio';
  } else if (selectedInstall === 'docker' || selectedInstall === 'remote') {
    server = {
      type: 'http',
      url: selectedInstall === 'docker' ? 'http://127.0.0.1:8100/mcp' : 'https://your-jebat-host.example/mcp',
      headers: { 'X-API-Key': 'YOUR_API_KEY' }
    };
    transport = selectedInstall === 'docker' ? 'Container · loopback HTTP' : 'Server · HTTPS';
  }
  const config = selectedIde === 'vscode'
    ? { servers: { jebat: { type: 'stdio', ...server } } }
    : { mcpServers: { jebat: server } };
  document.getElementById('ide-json').textContent = JSON.stringify(config, null, 2);
  const client = { cursor: 'Cursor', vscode: 'VS Code', windsurf: 'Windsurf' }[selectedIde];
  document.getElementById('ide-config-note').textContent = client + ' · ' + transport
    + '. Paste into your IDE’s MCP configuration. For HTTP, replace the endpoint and key and use your gateway’s required authentication header. Printed JSON does not prove a connection.';
}

function selectButton(button, group, attribute) {
  group.querySelectorAll('button').forEach(item => {
    const selected = item === button;
    item.classList.toggle('on', selected);
    item.setAttribute(attribute, String(selected));
    if (attribute === 'aria-selected') item.tabIndex = selected ? 0 : -1;
  });
}

function switchInstall(method, button) {
  if (!Object.hasOwn(INSTALL_CMDS, method)) return;
  selectedInstall = method;
  selectButton(button, button.parentElement, 'aria-selected');
  const panel = document.getElementById('install-cmd');
  panel.textContent = INSTALL_CMDS[method];
  panel.setAttribute('aria-labelledby', button.id);
  document.querySelectorAll('#install-tradeoffs .topt').forEach(item => {
    item.hidden = item.dataset.for !== method;
    item.style.removeProperty('display');
  });
  renderIdeConfig();
  const http = method === 'docker' || method === 'remote';
  document.getElementById('verify-command-wrap').hidden = http;
  document.getElementById('verify-local-note').hidden = http;
  document.getElementById('verify-http-note').hidden = !http;
  const command = method === 'npx' ? 'npx @nusabyte/jebat ' : 'jebat ';
  document.getElementById('verify-command').textContent = command + 'doctor\n' + command + 'mcp ide-config';
}

function switchIde(ide, button) {
  if (!IDE_CLIENTS.includes(ide)) return;
  selectedIde = ide;
  selectButton(button, button.parentElement, 'aria-pressed');
  renderIdeConfig();
}

const copyResetTimers = new WeakMap();
async function copyCommand(text, button) {
  if (button.disabled) return;
  const status = document.getElementById('copy-status');
  const label = button.querySelector('.copy-label');
  const feedback = document.getElementById(button.dataset.feedback);
  window.clearTimeout(copyResetTimers.get(button));
  copyResetTimers.delete(button);
  if (feedback) feedback.textContent = '';
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  button.dataset.state = 'loading';
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(text);
    button.dataset.state = 'success';
    status.textContent = 'Copied to clipboard.';
    label.textContent = 'Copied';
    copyResetTimers.set(button, window.setTimeout(() => {
      label.textContent = 'Copy';
      delete button.dataset.state;
      copyResetTimers.delete(button);
    }, 2200));
  } catch {
    button.dataset.state = 'error';
    const message = 'Copy was blocked. Select the command text and copy it manually, or retry.';
    status.textContent = message;
    if (feedback) feedback.textContent = message;
    label.textContent = 'Retry';
  } finally {
    button.disabled = false;
    button.removeAttribute('aria-busy');
  }
}

function copySnippet(id, button) {
  const source = document.getElementById(id);
  if (source) return copyCommand(source.textContent.trim(), button);
}

let captures;
let loadingCapture = false;
async function showCapture(button) {
  if (loadingCapture) return;
  const output = document.getElementById('hero-cli-output');
  const controls = [...document.querySelectorAll('[data-capture]')];
  loadingCapture = true;
  controls.forEach(control => { control.disabled = true; });
  button.setAttribute('aria-busy', 'true');
  output.setAttribute('aria-busy', 'true');
  controls.forEach(control => { delete control.dataset.state; });
  try {
    if (!captures) {
      const response = await fetch('assets/jebat-cli-captures.json?v=0fd02c7c');
      if (!response.ok) throw new Error('Capture unavailable');
      const payload = await response.json();
      if (!payload.commands || typeof payload.commands !== 'object') throw new Error('Invalid capture');
      captures = payload.commands;
    }
    const capture = captures[button.dataset.capture];
    if (!capture || typeof capture.command !== 'string' || typeof capture.output !== 'string') throw new Error('Missing capture');
    output.textContent = '$ ' + capture.command + '\n' + capture.output;
    selectButton(button, button.parentElement, 'aria-pressed');
    button.dataset.state = 'success';
  } catch {
    output.textContent = 'Recorded output could not be loaded. Select a command again to retry. No command was executed.';
    button.dataset.state = 'error';
    captures = undefined;
  } finally {
    controls.forEach(control => { control.disabled = false; });
    button.removeAttribute('aria-busy');
    output.removeAttribute('aria-busy');
    loadingCapture = false;
  }
}

document.querySelectorAll('[data-capture]').forEach(button => button.addEventListener('click', () => showCapture(button)));
const installTabs = [...document.querySelectorAll('[role="tab"]')];
const installPanel = document.getElementById('install-cmd');
installPanel.setAttribute('role', 'tabpanel');
installPanel.tabIndex = 0;
installTabs.forEach((button, index) => {
  button.setAttribute('aria-controls', 'install-cmd');
  button.tabIndex = index === 0 ? 0 : -1;
  button.addEventListener('keydown', event => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % installTabs.length;
    if (event.key === 'ArrowLeft') next = (index + installTabs.length - 1) % installTabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = installTabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    installTabs[next].focus();
    installTabs[next].click();
  });
});
installPanel.setAttribute('aria-labelledby', installTabs[0].id);
function selectInstallRoute(hash) {
  const button = installTabs.find(tab => '#' + tab.id === hash);
  if (!button) return;
  switchInstall(button.dataset.installMethod, button);
  button.focus({ preventScroll: true });
}
document.querySelectorAll('a[href^="#install-tab-"]').forEach(link => {
  link.addEventListener('click', () => selectInstallRoute(link.hash));
});
window.addEventListener('hashchange', () => selectInstallRoute(location.hash));
renderIdeConfig();
selectInstallRoute(location.hash);
document.querySelectorAll('button[onclick^="switchIde"]').forEach(button => button.setAttribute('aria-pressed', String(button.classList.contains('on'))));

const navigation = document.querySelector('.nav');
const burger = document.querySelector('.burger');
const mobileNavigation = document.getElementById('mnav');
function setNavigation(open) {
  mobileNavigation.classList.toggle('open', open);
  burger.setAttribute('aria-expanded', String(open));
  burger.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
}
burger.addEventListener('click', () => setNavigation(burger.getAttribute('aria-expanded') !== 'true'));
mobileNavigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setNavigation(false)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') { setNavigation(false); burger.focus(); }
});
const desktop = matchMedia('(min-width:901px)');
desktop.addEventListener('change', event => { if (event.matches) setNavigation(false); });
addEventListener('scroll', () => navigation.classList.toggle('scrolled', scrollY > 8), { passive: true });
const technicalDetails = [...document.querySelectorAll('details.technical-details')];
const compactTechnical = matchMedia('(max-width:640px)');
function openTechnicalHash() {
  const target = document.getElementById(location.hash.slice(1));
  if (!target) return;
  const details = target.closest('details.technical-details')
    || target.querySelector('details.technical-details');
  if (details) details.open = true;
}
function setTechnicalDefaults() {
  technicalDetails.forEach(details => {
    if (compactTechnical.matches && details.contains(document.activeElement)) {
      details.querySelector('summary').focus({ preventScroll: true });
    }
    details.open = !compactTechnical.matches;
  });
  openTechnicalHash();
}
setTechnicalDefaults();
compactTechnical.addEventListener('change', setTechnicalDefaults);
window.addEventListener('hashchange', openTechnicalHash);

document.querySelectorAll('svg').forEach(icon => { icon.setAttribute('aria-hidden', 'true'); icon.setAttribute('focusable', 'false'); });
document.querySelectorAll('a[target="_blank"]').forEach(link => {
  link.setAttribute('aria-label', link.textContent.trim() + ' (opens in a new tab)');
});
// FAQ schema comes from the visible native disclosure content, preventing copy drift.
const faqSchema = document.createElement('script');
faqSchema.type = 'application/ld+json';
faqSchema.textContent = JSON.stringify({ '@context': 'https://schema.org', '@type': 'FAQPage', mainEntity:
  [...document.querySelectorAll('.faq details')].map(item => ({ '@type': 'Question', name: item.querySelector('summary').textContent, acceptedAnswer: { '@type': 'Answer', text: item.querySelector('.a').textContent.trim() } }))
});
document.head.appendChild(faqSchema);
