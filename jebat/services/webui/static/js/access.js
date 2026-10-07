/* Server access: explicit validation, tab-only credential storage, no automatic mutation replay. */
(() => {
  const dialog = document.getElementById('access-dialog');
  const form = document.getElementById('access-form');
  const keyInput = document.getElementById('access-key');
  const submit = document.getElementById('access-submit');
  const label = document.getElementById('access-submit-label');
  const error = document.getElementById('access-error');
  const trigger = document.getElementById('access-open');
  let busy = false;
  let prompted = false;
  let returnFocus = null;
  let activeRequest = null;

  function openAccess() {
    if (dialog.open) return;
    returnFocus = document.activeElement;
    error.hidden = true;
    error.textContent = '';
    keyInput.value = '';
    keyInput.removeAttribute('aria-invalid');
    submit.disabled = true;
    dialog.showModal();
    keyInput.focus();
  }
  function closeAccess() {
    activeRequest?.abort();
    dialog.close();
  }
  dialog.addEventListener('close', () => {
    activeRequest?.abort();
    keyInput.value = '';
    if (returnFocus?.isConnected && returnFocus !== document.body) returnFocus.focus();
    else trigger.focus();
  });
  dialog.addEventListener('cancel', () => activeRequest?.abort());
  trigger.addEventListener('click', openAccess);
  document.getElementById('access-cancel').addEventListener('click', closeAccess);
  keyInput.addEventListener('input', () => {
    submit.disabled = busy || !keyInput.value.trim();
    keyInput.removeAttribute('aria-invalid');
    error.hidden = true;
  });
  document.getElementById('access-forget').addEventListener('click', () => {
    activeRequest?.abort();
    API.setKey('');
    window.clearPageTimers?.();
    document.getElementById('app-shell').replaceChildren();
    document.getElementById('status-text').textContent = 'Authentication required';
    keyInput.value = '';
    submit.disabled = true;
    error.hidden = false;
    error.textContent = 'Key removed from this tab. Enter a server key to reconnect.';
    keyInput.focus();
  });
  window.addEventListener('jebat-auth-required', () => {
    if (busy || prompted) return;
    prompted = true;
    openAccess();
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const key = keyInput.value.trim();
    if (busy || !key) return;
    busy = true;
    submit.disabled = true;
    submit.setAttribute('aria-busy', 'true');
    label.textContent = 'Checking key';
    error.hidden = true;
    const controller = new AbortController();
    activeRequest = controller;
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      // Validate with a read-only request before storing; never log or echo the key.
      const response = await fetch('/webui/api/status', {
        headers: { 'X-API-Key': key }, cache: 'no-store', redirect: 'error', signal: controller.signal
      });
      if (!response.ok) throw Object.assign(new Error('Authentication rejected'), { status: response.status });
      const payload = await response.json();
      if (!payload || typeof payload !== 'object' || !payload.status) throw new Error('Unexpected server response');
      if (controller.signal.aborted || !dialog.open) return;
      API.setKey(key);
      keyInput.value = '';
      prompted = false;
      dialog.close();
      // Reload only the current page's reads. Never replay the failed operation.
      window.navigate?.(location.hash.slice(1) || 'dashboard');
      updateConnectionStatus();
    } catch (failure) {
      if (!dialog.open) return;
      error.hidden = false;
      error.textContent = failure.status === 401 || failure.status === 403
        ? 'The server rejected this key. Check the server API key and try again.'
        : failure.name === 'AbortError'
          ? 'The connection timed out. Check connectivity and try again.'
          : 'Could not verify the key. Check connectivity and try again.';
      keyInput.setAttribute('aria-invalid', 'true');
      keyInput.focus();
    } finally {
      clearTimeout(timeout);
      activeRequest = null;
      busy = false;
      submit.removeAttribute('aria-busy');
      label.textContent = 'Connect this tab';
      submit.disabled = !keyInput.value.trim();
    }
  });
})();
