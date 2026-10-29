'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let project = null;
  let currentFile = 'index.html';
  let visualEditing = false;
  const headers = { 'Content-Type': 'application/json' };
  async function request(path, options = {}) {
    const response = await fetch(`/webui/api/builder${path}`, { ...options, headers: { ...headers, ...(options.headers || {}) } });
    if (!response.ok) throw new Error(`Builder request failed: ${response.status}`);
    return response.json();
  }
  function reloadPreview() {
    if (!project) return;
    $('preview').src = `${project.preview}?v=${Date.now()}`;
  }
  async function loadCheckpoints() {
    if (!project) return;
    const data = await request(`/projects/${project.id}/checkpoints`);
    $('checkpoint-list').replaceChildren();
    data.checkpoints.forEach(checkpoint => {
      const row = document.createElement('div'); row.className = 'checkpoint-item';
      const label = document.createElement('span'); label.textContent = checkpoint.label;
      const restore = document.createElement('button'); restore.textContent = 'Restore';
      restore.addEventListener('click', async () => {
        await request(`/projects/${project.id}/checkpoints/${checkpoint.id}/restore`, { method: 'POST' });
        await loadEditor(); reloadPreview();
      });
      row.append(label, restore); $('checkpoint-list').appendChild(row);
    });
  }
  async function loadEditor() {
    const data = await request(`/projects/${project.id}/files/${currentFile}`);
    $('code-editor').value = data.content;
  }
  function renderFileTabs() {
    $('file-tabs').replaceChildren();
    project.files.forEach(file => {
      const button = document.createElement('button'); button.textContent = file; button.classList.toggle('active', file === currentFile);
      button.addEventListener('click', async () => { currentFile = file; renderFileTabs(); await loadEditor(); });
      $('file-tabs').appendChild(button);
    });
  }
  $('builder-form').addEventListener('submit', async event => {
    event.preventDefault();
    const objective = $('build-goal').value.trim(); if (!objective) return;
    $('build-button').disabled = true;
    try {
      project = await request('/projects', { method: 'POST', body: JSON.stringify({ name: objective.split(/[.!?\n]/)[0].slice(0, 80), objective }) });
      $('project-name').textContent = project.name;
      $('builder-workspace').hidden = false;
      $('export-project').href = `/webui/api/builder/projects/${project.id}/export`;
      await loadEditor(); reloadPreview(); await loadCheckpoints(); renderFileTabs();
      const media = await request(`/projects/${project.id}/media`);
      renderMediaArtifacts(media.artifacts);
      $('build-log').textContent = `Plan created: ${project.plan.pages.length} page · ${project.files.length} files · ${project.plan.checks.length} checks`;
    } catch (error) { $('build-button').textContent = error.message; }
    finally { $('build-button').disabled = false; $('build-button').textContent = 'Build project →'; }
  });
  $('save-file').addEventListener('click', async () => {
    if (!project) return;
    $('save-file').disabled = true;
    try {
      await request(`/projects/${project.id}/files/${currentFile}`, { method: 'PUT', body: JSON.stringify({ content: $('code-editor').value }) });
      $('build-log').textContent = `Saved ${currentFile} and created checkpoint.`;
      reloadPreview(); await loadCheckpoints();
    } finally { $('save-file').disabled = false; }
  });
  $('refresh-preview').addEventListener('click', reloadPreview);
  document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('[data-view]').forEach(item => item.classList.toggle('active', item === button));
    $('preview').style.width = ({ desktop: '100%', tablet: '768px', mobile: '375px' })[button.dataset.view];
    $('preview').style.margin = button.dataset.view === 'desktop' ? '0' : '0 auto';
  }));
  document.querySelector('[data-action="checkpoint"]').addEventListener('click', async () => {
    if (!project) return;
    await request(`/projects/${project.id}/files/index.html`, { method: 'PUT', body: JSON.stringify({ content: $('code-editor').value }) });
    await loadCheckpoints();
  });
  document.querySelector('[data-action="test"]').addEventListener('click', async () => {
    if (!project) return;
    $('preview-state').textContent = 'Running checks…';
    const result = await request(`/projects/${project.id}/test`, { method: 'POST' });
    $('preview-state').textContent = result.status === 'passed' ? 'All checks passed' : 'Checks failed';
    $('build-log').textContent = result.checks.map(check => `${check.status === 'passed' ? 'PASS' : 'FAIL'} ${check.name}${check.detail ? ` — ${check.detail}` : ''}`).join('\n');
  });
  $('visual-edit').addEventListener('click', () => {
    if (!project) return;
    visualEditing = !visualEditing;
    $('visual-edit').classList.toggle('active', visualEditing);
    $('preview-state').textContent = visualEditing ? 'Click an element to edit source' : 'Live';
    if (visualEditing) {
      $('preview').addEventListener('load', () => {
        $('preview').contentDocument?.querySelectorAll('[data-component]').forEach(element => {
          element.addEventListener('click', event => {
            if (!visualEditing) return;
            event.preventDefault(); event.stopPropagation();
            currentFile = 'index.html'; renderFileTabs();
            const source = $('code-editor').value;
            const component = element.dataset.component;
            const marker = `data-component="${component}"`;
            const markerIndex = source.indexOf(marker);
            if (markerIndex >= 0) {
              const start = source.lastIndexOf('<', markerIndex);
              const end = source.indexOf('>', markerIndex) + 1;
              $('code-editor').setSelectionRange(start, end);
            }
            $('code-editor').focus();
            $('build-log').textContent = `Selected ${element.dataset.component}. Source is index.html; edit this component only.`;
          });
        });
      }, { once: true });
    }
  });
  $('fork-project').addEventListener('click', async () => {
    if (!project) return;
    project = await request(`/projects/${project.id}/fork`, { method: 'POST' });
    $('project-name').textContent = project.name;
    $('export-project').href = `/webui/api/builder/projects/${project.id}/export`;
    currentFile = 'index.html'; renderFileTabs(); await loadEditor(); reloadPreview(); await loadCheckpoints();
    $('build-log').textContent = 'Forked project. You can iterate independently.';
  });
  $('share-project').addEventListener('click', async () => {
    if (!project) return;
    const url = `${location.origin}${project.preview}`;
    try { await navigator.clipboard.writeText(url); $('build-log').textContent = `Preview link copied: ${url}`; }
    catch { $('build-log').textContent = `Preview link: ${url}`; }
  });
  $('implement-project').addEventListener('click', async () => {
    if (!project) return;
    $('implement-project').disabled = true;
    $('build-log').textContent = 'Requesting implementation from the configured provider…';
    try {
      const result = await request(`/projects/${project.id}/implement`, { method: 'POST', body: JSON.stringify({ model: $('builder-model').value || null }) });
      $('build-log').textContent = result.status === 'implemented' ? `Implemented with ${result.provider}:${result.model}` : result.error;
      if (result.status === 'error' || result.status === 'unavailable') {
        $('preview-state').textContent = 'Implementation unavailable';
      }
      if (result.status === 'implemented') { await loadEditor(); reloadPreview(); await loadCheckpoints(); }
    } finally { $('implement-project').disabled = false; }
  });
  $('deploy-project').addEventListener('click', async () => {
    if (!project) return;
    const result = await request(`/projects/${project.id}/deploy`, { method: 'POST', body: JSON.stringify({ confirm: false }) });
    if (result.status === 'confirmation_required') {
      const confirmed = window.confirm('Deploy this project as a public preview on this host? Run tests and review the files before continuing.');
      if (!confirmed) return;
      const deployed = await request(`/projects/${project.id}/deploy`, { method: 'POST', body: JSON.stringify({ confirm: true }) });
      $('build-log').textContent = `Preview deployed: ${location.origin}${deployed.url}`;
    }
  });
  $('rollback-project').addEventListener('click', async () => {
    if (!project) return;
    const result = await request(`/projects/${project.id}/rollback`, { method: 'POST' });
    $('build-log').textContent = result.status === 'rolled_back' ? 'Preview deployment rolled back.' : result.error;
  });
  function renderMediaArtifacts(artifacts) {
    const panel = $('media-artifacts');
    panel.replaceChildren();
    const media = artifacts.filter(item => /\.(png|jpe?g|webp|glb)$/i.test(item.name));
    if (!media.length) { panel.hidden = true; return; }
    panel.hidden = false;
    media.forEach(item => {
      if (/\.glb$/i.test(item.name)) {
        const pre = document.createElement('pre'); pre.textContent = `GLB artifact: ${item.name}\n${item.content}`;
        panel.appendChild(pre);
      } else {
        const image = document.createElement('img'); image.alt = item.name; image.src = item.url || item.path;
        panel.appendChild(image);
      }
    });
  }
  $('builder-model').value = localStorage.getItem('hangnadim_model') || '';
  $('builder-model').addEventListener('change', () => localStorage.setItem('hangnadim_model', $('builder-model').value));
  $('new-project').addEventListener('click', () => {
    project = null;
    $('builder-workspace').hidden = true;
    $('build-goal').value = '';
    $('build-goal').focus();
  });
})();
