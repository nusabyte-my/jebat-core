function runHeroCLI(type) {
  playClickSound();
  const box = document.getElementById('hero-cli-output');
  if (type === 'status') {
    box.innerHTML = `> $ jebat status<br/>
<span style="color: var(--hermes-pucuk)">✓ JEBAT Core v8.2.1 Operational — Security Hardened</span><br/>
> Model Route: llama.cpp (local runtime) [LATENCY: RUNTIME-MEASURED]<br/>
> Ghost DB Vector Store: Connected | WebUI + MCP API: Key-Gated<br/>
> MCP Protocol Bus: tool registry available · jebat://metrics/tools live`;
  } else if (type === 'agentix') {
    box.innerHTML = `> $ jebat agentix status<br/>
<span style="color: var(--hermes-amber)">[Agentix Solution Registry]</span><br/>
> deploy-usher   v0.1.0  atomic   sha:85c718ae → deployed<br/>
> research-hive  v0.1.0  hermes   sha:d87e474c → built<br/>
<span style="color: var(--hermes-pucuk)">✓ create → build → deploy → run. Templates: hermes · openclaw · atomic.</span>`;
  } else if (type === 'pentest') {
    box.innerHTML = `> $ jebat agent "Pentest localhost"<br/>
<span style="color: var(--hermes-amber)">[Hulubalang Security Agent Dispatched]</span><br/>
> Port scan: 80, 443, 8081 open.<br/>
> Vulnerability check: 0 critical, 0 high.<br/>
<span style="color: var(--hermes-pucuk)">✓ Security Audit Passed. Airgap boundaries active.</span>`;
  } else if (type === 'mcp') {
    box.innerHTML = `> $ jebat mcp list<br/>
<span style="color: var(--hermes-amber)">[MCP Protocol Bus · Streamable-HTTP :8100]</span><br/>
> Discovered: <strong>118 Registered Tools</strong><br/>
> Ghost DB: 14 tools (ghost.sql, ghost.create, ghost.checkpoint)<br/>
> Design & Copy: design_preflight, ui_critique, copy_audit<br/>
<span style="color: var(--hermes-pucuk)">✓ Streamable HTTP & stdio transports operational.</span>`;
  } else if (type === 'audit') {
    box.innerHTML = `> $ jebat agi audit --all<br/>
<span style="color: var(--hermes-amber)">[Autonomous Reflexion Gates Active]</span><br/>
> Build Gate: AST parse validated (0 syntax errors)<br/>
> Hallmark Design Gate: 6-axis critique — philosophy · hierarchy · execution · specificity · restraint · variety<br/>
> Pawang Jualan Copy Gate: [Action Verb] + [What They Get] enforced<br/>
<span style="color: var(--hermes-pucuk)">✓ Multi-domain quality sign-off confirmed.</span>`;
  } else if (type === 'dream') {
    box.innerHTML = `> $ jebat autoMimpi dream<br/>
<span style="color: var(--hermes-amber)">[Nightly Memory Sleep Consolidation · 04:00 MYT]</span><br/>
> Consolidation pass complete — traces scored, decayed and pruned<br/>
> Patterns extracted | Embeddings synced to Ghost DB (HNSW, cosine)<br/>
<span style="color: var(--hermes-pucuk)">✓ "Errors are the Grid's way of showing where the wall is."</span>`;
  } else if (type === 'memory') {
    box.innerHTML = `> $ jebat memory search "NusaByte"<br/>
<span style="color: var(--hermes-amber)">[Ghost DB Hybrid Retrieval · BM25 + vector, cosine]</span><br/>
> Query embedded → matched against the memory collection<br/>
> Ranked hits returned with a per-result confidence score<br/>
<span style="color: var(--hermes-pucuk)">✓ Context retrieved from the persistent store.</span>`;
  }
}
