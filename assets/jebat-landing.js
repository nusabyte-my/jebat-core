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
    details.open = compactTechnical.matches ? false : details.open;
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

// Recorded run evidence: deterministic local playback, never a live agent.
const orchestration = document.querySelector('.orchestration');
const replayButton = document.getElementById('replay-run');
const inspectButton = document.getElementById('inspect-run');
const evidencePanel = document.getElementById('run-evidence');
let runEvidence;
async function loadRunEvidence() {
  if (runEvidence) return runEvidence;
  const response = await fetch('assets/parallel-run.json');
  if (!response.ok) throw new Error('Recorded run unavailable');
  runEvidence = await response.json();
  return runEvidence;
}
replayButton?.addEventListener('click', async () => {
  replayButton.disabled = true;
  try {
    await loadRunEvidence();
    orchestration.classList.remove('is-replaying');
    void orchestration.offsetWidth;
    orchestration.classList.add('is-replaying');
    replayButton.textContent = 'Replay recorded run';
  } catch {
    replayButton.textContent = 'Recording unavailable — retry';
  } finally {
    replayButton.disabled = false;
  }
});
inspectButton?.addEventListener('click', async () => {
  inspectButton.disabled = true;
  try {
    const data = await loadRunEvidence();
    const wasHidden = evidencePanel.hidden;
    evidencePanel.textContent = JSON.stringify(data, null, 2);
    evidencePanel.hidden = !wasHidden;
    inspectButton.setAttribute('aria-expanded', String(wasHidden));
    inspectButton.textContent = wasHidden ? 'Hide evidence' : 'Inspect evidence';
  } catch {
    evidencePanel.hidden = false;
    evidencePanel.textContent = 'Recorded evidence could not be loaded. Retry Inspect evidence.';
  } finally {
    inspectButton.disabled = false;
  }
});

// Current specialist catalog, generated from Agentix manifests.
const catalog = document.getElementById('specialist-catalog');
const specialistDetail = document.getElementById('specialist-detail');
fetch('assets/agentix-specialists.json').then(response => {
  if (!response.ok) throw new Error('Catalog unavailable');
  return response.json();
}).then(data => {
  catalog.replaceChildren();
  data.specialists.forEach((specialist, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'jchip' + (index === 0 ? ' on' : '');
    button.textContent = specialist.name;
    button.setAttribute('aria-pressed', String(index === 0));
    button.addEventListener('click', () => {
      catalog.querySelectorAll('button').forEach(item => { item.classList.remove('on'); item.setAttribute('aria-pressed', 'false'); });
      button.classList.add('on');
      button.setAttribute('aria-pressed', 'true');
      specialistDetail.replaceChildren();
      const name = document.createElement('strong'); name.textContent = specialist.name;
      const description = document.createElement('span'); description.textContent = specialist.description;
      specialistDetail.append(name, description);
    });
    catalog.appendChild(button);
  });
}).catch(() => { catalog.textContent = 'Specialist catalog unavailable. Use jebat agentix templates.'; });

// Guided experience: preserve all content, reveal one task-focused view at a time.
const experienceViews = {
  command: ['command'],
  proof: ['proof', 'project-audit'],
  capabilities: ['creative', 'platform', 'memory', 'learning', 'workbench', 'specialists', 'mcp', 'updates'],
  setup: ['mcp-deploy', 'deploy', 'faq']
};
const experienceTabs = [...document.querySelectorAll('[data-experience]')];
function selectExperience(name, focus = false) {
  if (!experienceViews[name]) return;
  document.body.classList.add('experience-active');
  document.querySelectorAll('main > header, main > section').forEach(section => {
    const visible = experienceViews[name].includes(section.id);
    section.dataset.experienceView = visible ? name : '';
  });
  experienceTabs.forEach(tab => {
    const selected = tab.dataset.experience === name;
    tab.classList.toggle('on', selected);
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && focus) tab.focus();
  });
  scrollTo({top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
}
experienceTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectExperience(tab.dataset.experience));
  tab.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const next = experienceTabs[(index + (event.key === 'ArrowRight' ? 1 : experienceTabs.length - 1)) % experienceTabs.length];
    selectExperience(next.dataset.experience, true);
  });
});
document.querySelector('.experience-exit')?.addEventListener('click', () => {
  document.body.classList.remove('experience-active');
  document.querySelectorAll('[data-experience-view]').forEach(section => delete section.dataset.experienceView);
});
const experienceRoutes = {
  command: 'command',
  proof: 'proof',
  'project-audit': 'proof',
  creative: 'capabilities',
  platform: 'capabilities',
  memory: 'capabilities',
  learning: 'capabilities',
  workbench: 'capabilities',
  specialists: 'capabilities',
  mcp: 'capabilities',
  updates: 'capabilities',
  'mcp-deploy': 'setup',
  deploy: 'setup',
  faq: 'setup'
};
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', () => {
    const route = experienceRoutes[link.hash.slice(1)];
    if (route) selectExperience(route);
  });
});
selectExperience('command');

const UPDATE_CONTENT = {
  parallel: {
    tag: 'Agentix', title: 'Split independent work. Keep one model.',
    copy: 'Automatically decompose an objective across up to three concurrent workers with exact provider/model inheritance and isolated tool policies.',
    facts: ['Read-only parallel default', 'Recorded worker runs and consolidated results', 'Explicit failure without model substitution'],
    link: '#workbench', label: 'Explore Agentix'
  },
  comfy: {
    tag: 'Local GPU', title: 'Generate on your GPU. Call from the VPS.',
    copy: 'ComfyUI runs locally with Juggernaut XL Ragnarok FP8 while an authenticated asynchronous bridge lets JEBAT CLI and MCP on the VPS submit jobs and receive image files.',
    facts: ['RTX 3060 low-VRAM execution verified', 'VPS → tunnel → workstation generation in 14.4 seconds', 'No public ComfyUI port or router forwarding'],
    link: 'https://github.com/nusabyte-my/jebat-core/blob/main/docs/COMFYUI_LOCAL_GPU.md', label: 'Read the bridge setup'
  },
  security: {
    tag: 'Security', title: 'Audit the agent layer, not just the app.',
    copy: 'Security-full combines the complete agent-skills security catalog with a workflow for skill provenance, MCP permissions, prompt injection, memory, and multi-agent trust boundaries.',
    facts: ['Full upstream catalog preserved', 'Evidence and verification boundaries required', 'No unreviewed scanner or proof-of-concept execution'],
    link: 'https://github.com/nusabyte-my/jebat-core/tree/main/skills/security-full', label: 'Inspect Security-full'
  },
  creative: {
    tag: 'Creative', title: 'Design for the artifact, then make it real.',
    copy: 'JEBAT Creative supplies domain-specific interface grammar while image-to-3D turns a source image into a reviewed, normalized textured asset for Blender and game workflows.',
    facts: ['Nine product-domain references', 'Anti-template and accessibility gates', 'Scale, origin, materials, and GLB review'],
    link: 'https://github.com/nusabyte-my/jebat-core/tree/main/skills/jebat-creative', label: 'Explore the creative system'
  }
};
const updateButtons = [...document.querySelectorAll('[data-update]')];
function selectUpdate(key, focus = false) {
  const content = UPDATE_CONTENT[key];
  if (!content) return;
  updateButtons.forEach(button => {
    const selected = button.dataset.update === key;
    button.classList.toggle('on', selected);
    button.setAttribute('aria-selected', String(selected));
    button.tabIndex = selected ? 0 : -1;
    if (selected && focus) button.focus();
  });
  document.getElementById('update-detail-tag').textContent = content.tag;
  document.getElementById('update-detail-title').textContent = content.title;
  document.getElementById('update-detail-copy').textContent = content.copy;
  const facts = document.getElementById('update-detail-facts');
  facts.replaceChildren(...content.facts.map(fact => { const li = document.createElement('li'); li.textContent = fact; return li; }));
  const link = document.getElementById('update-detail-link');
  link.href = content.link;
  link.textContent = content.label;
}
updateButtons.forEach((button, index) => {
  button.addEventListener('click', () => selectUpdate(button.dataset.update));
  button.addEventListener('keydown', event => {
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const forward = ['ArrowDown', 'ArrowRight'].includes(event.key);
    const next = updateButtons[(index + (forward ? 1 : updateButtons.length - 1)) % updateButtons.length];
    selectUpdate(next.dataset.update, true);
  });
});
