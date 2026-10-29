'use strict';
const $ = id => document.getElementById(id);
let selectedRun = null;
let filter = 'all';
let pollTimer;
let eventSource;
const api = {
  headers: () => ({ 'Content-Type': 'application/json', ...(window.JEBAT_API_KEY ? { 'X-API-Key': window.JEBAT_API_KEY } : {}) }),
  async get(path) { const response = await fetch(`/webui/api${path}`, { headers: this.headers() }); if (!response.ok) throw new Error(`Request failed: ${response.status}`); return response.json(); },
  async post(path, body) { const response = await fetch(`/webui/api${path}`, { method: 'POST', headers: this.headers(), body: JSON.stringify(body) }); if (!response.ok) throw new Error(`Request failed: ${response.status}`); return response.json(); }
};
function message(text, role) { const item = document.createElement('article'); item.className = `message ${role}`; const label = document.createElement('span'); label.textContent = role === 'user' ? 'You' : 'HangNadim'; const content = document.createElement('p'); content.textContent = text; item.append(label, content); $('conversation').appendChild(item); $('conversation').scrollTop = $('conversation').scrollHeight; return item; }
function renderRun(run) {
  selectedRun = run.run_id;
  $('view-status').textContent = run.status;
  $('cancel-run').hidden = !['running', 'starting'].includes(run.status);
  $('show-artifacts').hidden = !run.result;
  if (eventSource) eventSource.close();
  if (['running', 'starting'].includes(run.status)) {
    eventSource = new EventSource(`/webui/api/hermes/runs/${encodeURIComponent(run.run_id)}/events`);
    eventSource.onmessage = event => renderRun(JSON.parse(event.data));
    eventSource.onerror = () => eventSource.close();
  }
  $('workers').replaceChildren();
  run.workers.forEach(worker => {
    const card = document.createElement('article'); card.className = 'worker'; card.dataset.status = worker.status;
    const top = document.createElement('div'); top.className = 'worker-top';
    const name = document.createElement('strong'); name.textContent = `Subagent ${worker.worker}`;
    const state = document.createElement('span'); state.textContent = worker.status;
    const task = document.createElement('small'); task.textContent = worker.task;
    top.append(name, state); card.append(top, task); $('workers').appendChild(card);
  });
  if (run.result) { $('evidence').hidden = false; $('evidence').textContent = JSON.stringify(run.result, null, 2); } else $('evidence').hidden = true;
}
async function openRun(id) { renderRun(await api.get(`/hermes/runs/${encodeURIComponent(id)}`)); }
async function loadRuns() {
  const data = await api.get('/hermes/runs');
  $('run-list').replaceChildren();
  data.runs.filter(run => filter === 'all' || run.status === filter).forEach(run => {
    const button = document.createElement('button'); button.className = 'run-link' + (run.run_id === selectedRun ? ' active' : ''); button.textContent = `${run.solution || 'workstream'} · ${run.status}`;
    button.addEventListener('click', () => openRun(run.run_id)); $('run-list').appendChild(button);
  });
  if (selectedRun && !eventSource) await openRun(selectedRun);
}
$('goal-form').addEventListener('submit', async event => {
  event.preventDefault();
  const objective = $('goal').value.trim(); if (!objective) return;
  $('start').disabled = true; message(objective, 'user'); const pending = message('Decomposing the goal and starting subagents…', 'assistant');
  try {
    const run = await api.post('/hermes/runs', { objective, solution: $('solution').value, agents: Number($('agents').value) });
    selectedRun = run.run_id; pending.querySelector('p').textContent = `Workstream ${run.run_id} is running.`;
    await loadRuns();
  } catch (error) { pending.querySelector('p').textContent = `Unable to start: ${error.message}`; }
  finally { $('start').disabled = false; }
});
$('refresh').addEventListener('click', loadRuns);
$('cancel-run').addEventListener('click', async () => {
  if (!selectedRun) return;
  $('cancel-run').disabled = true;
  try {
    await api.post(`/hermes/runs/${encodeURIComponent(selectedRun)}/cancel`, {});
    if (eventSource) eventSource.close();
    await openRun(selectedRun);
  } finally { $('cancel-run').disabled = false; }
});
$('show-artifacts').addEventListener('click', async () => {
  if (!selectedRun) return;
  const data = await api.get(`/hermes/runs/${encodeURIComponent(selectedRun)}/artifacts`);
  const panel = $('artifacts');
  panel.replaceChildren();
  data.artifacts.forEach(artifact => {
    const details = document.createElement('details');
    const summary = document.createElement('summary'); summary.textContent = artifact.name;
    const content = document.createElement('pre'); content.textContent = artifact.content;
    details.append(summary, content); panel.appendChild(details);
  });
  panel.hidden = !panel.hidden;
});
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => { filter = button.dataset.filter; document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('active', item === button)); loadRuns(); }));
loadRuns().catch(error => { $('run-list').textContent = error.message; });
