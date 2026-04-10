"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

type Session = {
  id: string;
  target_id: string;
  status: string;
  model: string;
  provider: string;
  operator: string;
  notes: string;
  started_at: string;
  ended_at?: string | null;
};

type Run = {
  id: string;
  tool: string;
  command: string;
  status: string;
  exit_code: number | null;
  stdout: string;
  stderr: string;
  started_at: string;
};

type Finding = {
  id: string;
  title: string;
  severity: string;
  category: string;
  source_tool: string;
  asset?: string | null;
  evidence_summary: string;
  remediation: string;
  metadata?: Record<string, string | number | string[] | null | undefined>;
};

type Target = {
  id: string;
  name: string;
  type: string;
  scope: string;
};

type SessionStateMessage = {
  type: "session_state";
  session: Session;
  runs: Run[];
  findings: Finding[];
};

type CopilotMessage = {
  role: string;
  content: string;
  provider?: string;
  model?: string;
};

type RunbookPreset = {
  id: string;
  label: string;
  tool: string;
  cwd: string;
  command: string;
  types: string[];
};

function summarizeMetadata(
  metadata?: Record<string, string | number | string[] | null | undefined>,
): string[] {
  if (!metadata) {
    return [];
  }
  const items: string[] = [];
  for (const key of ["status_code", "port", "service", "template_id", "matcher_name", "parser"]) {
    const value = metadata[key];
    if (value !== undefined && value !== null && value !== "") {
      items.push(`${key}: ${Array.isArray(value) ? value.join(", ") : value}`);
    }
  }
  if (Array.isArray(metadata.technologies) && metadata.technologies.length > 0) {
    items.push(`technologies: ${metadata.technologies.join(", ")}`);
  }
  return items.slice(0, 5);
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail || `HTTP ${response.status}`;
  } catch {
    return `HTTP ${response.status}`;
  }
}

function buildRunbookPresets(target: Target | null): RunbookPreset[] {
  const scopeHint = target?.scope || "target.example";
  return [
    {
      id: "scope-banner",
      label: "Scope Banner",
      tool: "shell",
      cwd: ".",
      command: "pwd && ls -la scope 2>/dev/null || true",
      types: ["workspace", "web", "api", "host", "container"],
    },
    {
      id: "httpx-probe",
      label: "HTTP Probe",
      tool: "httpx",
      cwd: ".",
      command: `httpx -json -u ${scopeHint}`,
      types: ["web", "api"],
    },
    {
      id: "nuclei-quick",
      label: "Nuclei Quick",
      tool: "nuclei",
      cwd: ".",
      command: `nuclei -u ${scopeHint} -jsonl -severity critical,high,medium`,
      types: ["web", "api"],
    },
    {
      id: "ffuf-common",
      label: "FFUF Common Paths",
      tool: "ffuf",
      cwd: ".",
      command: `ffuf -u ${scopeHint.replace(/\/$/, "")}/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -of json`,
      types: ["web", "api"],
    },
    {
      id: "nmap-top",
      label: "Nmap Top Ports",
      tool: "nmap",
      cwd: ".",
      command: `nmap -Pn -sV --top-ports 100 ${scopeHint}`,
      types: ["host", "workspace", "container"],
    },
    {
      id: "repo-scan",
      label: "Workspace Scan",
      tool: "serangan",
      cwd: ".",
      command: "python scripts/security-autonomous-scan.py",
      types: ["workspace"],
    },
  ].filter((preset) => preset.types.includes(target?.type || "workspace"));
}

export default function SecuritySessionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [session, setSession] = useState<Session | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [error, setError] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("");
  const [tool, setTool] = useState("shell");
  const [command, setCommand] = useState("");
  const [cwd, setCwd] = useState(".");
  const [findingTitle, setFindingTitle] = useState("");
  const [findingSeverity, setFindingSeverity] = useState("medium");
  const [findingEvidence, setFindingEvidence] = useState("");
  const [copilotPrompt, setCopilotPrompt] = useState("");
  const [copilotMessages, setCopilotMessages] = useState<CopilotMessage[]>([]);
  const [actionState, setActionState] = useState<string>("");

  useEffect(() => {
    let active = true;
    params
      .then(({ id }) => {
        if (!active) {
          return;
        }
        setSessionId(id);
        return Promise.all([
          fetchJson<Session>(`http://127.0.0.1:8080/api/v1/security/sessions/${id}`),
          fetchJson<Run[]>(`http://127.0.0.1:8080/api/v1/security/sessions/${id}/runs`),
          fetchJson<Finding[]>(`http://127.0.0.1:8080/api/v1/security/sessions/${id}/findings`),
          fetchJson<Target[]>("http://127.0.0.1:8080/api/v1/security/targets"),
        ]);
      })
      .then((data) => {
        if (!active || !data) {
          return;
        }
        const [sessionData, runData, findingData, targetData] = data;
        setSession(sessionData);
        setRuns(runData);
        setFindings(findingData);
        setTargets(targetData);
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message);
        }
      });
    return () => {
      active = false;
    };
  }, [params]);

  useEffect(() => {
    if (!sessionId) {
      return;
    }
    const socket = new WebSocket(`ws://127.0.0.1:8080/api/v1/security/sessions/${sessionId}/ws`);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as SessionStateMessage | { type: "pong" };
        if (payload.type !== "session_state") {
          return;
        }
        setSession(payload.session);
        setRuns(payload.runs);
        setFindings(payload.findings);
      } catch {
        // Ignore malformed payloads from local dev state.
      }
    };
    const interval = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send("ping");
      }
    }, 15000);
    return () => {
      window.clearInterval(interval);
      socket.close();
    };
  }, [sessionId]);

  const target = useMemo(
    () => targets.find((item) => item.id === session?.target_id) ?? null,
    [session?.target_id, targets],
  );
  const presets = useMemo(() => buildRunbookPresets(target), [target]);

  function applyPreset(preset: RunbookPreset) {
    setTool(preset.tool);
    setCwd(preset.cwd);
    setCommand(preset.command);
    setActionState(`Loaded preset: ${preset.label}`);
  }

  async function runCommand() {
    if (!sessionId || !command.trim()) {
      return;
    }
    setActionState("Running command...");
    const response = await fetch(`http://127.0.0.1:8080/api/v1/security/sessions/${sessionId}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool,
        command,
        cwd,
      }),
    });
    if (!response.ok) {
      setActionState(`Command failed: ${await readErrorDetail(response)}`);
      return;
    }
    setCommand("");
    setActionState("Command submitted.");
  }

  async function addFinding() {
    if (!sessionId || !findingTitle.trim()) {
      return;
    }
    setActionState("Creating finding...");
    const response = await fetch(`http://127.0.0.1:8080/api/v1/security/sessions/${sessionId}/findings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: findingTitle,
        severity: findingSeverity,
        evidence_summary: findingEvidence,
        source_tool: "web-console",
      }),
    });
    if (!response.ok) {
      setActionState(`Finding failed: ${await readErrorDetail(response)}`);
      return;
    }
    setFindingTitle("");
    setFindingEvidence("");
    setActionState("Finding created.");
  }

  async function askCopilot() {
    if (!sessionId || !copilotPrompt.trim()) {
      return;
    }
    const prompt = copilotPrompt;
    setActionState("Asking copilot...");
    setCopilotMessages((current) => [...current, { role: "user", content: prompt }]);
    setCopilotPrompt("");
    const response = await fetch(`http://127.0.0.1:8080/api/v1/security/sessions/${sessionId}/copilot/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: prompt,
        mode: "suggest_next_step",
      }),
    });
    if (!response.ok) {
      setActionState(`Copilot failed: ${await readErrorDetail(response)}`);
      return;
    }
    const data = (await response.json()) as {
      provider: string;
      model: string;
      response: string;
    };
    setCopilotMessages((current) => [
      ...current,
      {
        role: "assistant",
        content: data.response,
        provider: data.provider,
        model: data.model,
      },
    ]);
    setActionState("Copilot responded.");
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top right, rgba(59,130,246,0.18), transparent 28%), linear-gradient(180deg, #08111f 0%, #111827 100%)",
        color: "#f8fafc",
        padding: "40px 24px 72px",
      }}
    >
      <div style={{ maxWidth: 1240, margin: "0 auto", display: "grid", gap: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 12, color: "#93c5fd", letterSpacing: "0.2em", textTransform: "uppercase" }}>
              Security Session
            </div>
            <h1 style={{ margin: "10px 0 0", fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
              {session ? session.id : sessionId || "Loading session"}
            </h1>
          </div>
          <Link
            href="/security"
            style={{
              borderRadius: 999,
              padding: "10px 16px",
              border: "1px solid rgba(148,163,184,0.28)",
              color: "#e2e8f0",
              textDecoration: "none",
              background: "rgba(15,23,42,0.58)",
            }}
          >
            Back to Security
          </Link>
        </div>

        {error ? (
          <section
            style={{
              borderRadius: 20,
              padding: 20,
              background: "rgba(127,29,29,0.3)",
              border: "1px solid rgba(248,113,113,0.3)",
            }}
          >
            API unavailable: {error}
          </section>
        ) : null}

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 16,
          }}
        >
          {[
            { label: "Status", value: session?.status ?? "loading" },
            { label: "Target", value: target ? `${target.name} (${target.type})` : session?.target_id ?? "loading" },
            { label: "Provider", value: session ? `${session.provider} / ${session.model}` : "loading" },
            { label: "Operator", value: session?.operator ?? "loading" },
          ].map((item) => (
            <article
              key={item.label}
              style={{
                borderRadius: 20,
                padding: 20,
                background: "rgba(15,23,42,0.72)",
                border: "1px solid rgba(148,163,184,0.12)",
              }}
            >
              <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.16em", color: "#93c5fd" }}>
                {item.label}
              </div>
              <div style={{ marginTop: 8, fontSize: 18 }}>{item.value}</div>
            </article>
          ))}
        </section>

        <section
          style={{
            borderRadius: 24,
            padding: 24,
            background: "rgba(15,23,42,0.72)",
            border: "1px solid rgba(148,163,184,0.12)",
          }}
        >
          <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.16em", color: "#93c5fd" }}>
            Scope
          </div>
          <p style={{ margin: "10px 0 0", color: "#cbd5e1", lineHeight: 1.7 }}>{target?.scope ?? "No target scope loaded."}</p>
          {session?.notes ? <p style={{ margin: "10px 0 0", color: "#94a3b8" }}>{session.notes}</p> : null}
        </section>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "0.9fr 1.1fr 1fr",
            gap: 20,
          }}
        >
          <article
            style={{
              borderRadius: 24,
              padding: 24,
              background: "rgba(15,23,42,0.72)",
              border: "1px solid rgba(148,163,184,0.12)",
            }}
          >
            <h2 style={{ margin: 0, fontSize: 24 }}>Actions</h2>
            <div style={{ marginTop: 16, display: "grid", gap: 18 }}>
              <section>
                <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.16em", color: "#93c5fd" }}>
                  Run Command
                </div>
                <p style={{ margin: "8px 0 0", color: "#94a3b8", fontSize: 13, lineHeight: 1.6 }}>
                  Guardrails apply here: blocked destructive commands, target tool allowlists, and scope checks for
                  network/web commands.
                </p>
                <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {presets.map((preset) => (
                    <button
                      key={preset.id}
                      onClick={() => applyPreset(preset)}
                      style={presetButtonStyle}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
                <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                  <input value={tool} onChange={(e) => setTool(e.target.value)} placeholder="tool" style={inputStyle} />
                  <input value={cwd} onChange={(e) => setCwd(e.target.value)} placeholder="cwd" style={inputStyle} />
                  <textarea
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="command"
                    style={{ ...inputStyle, minHeight: 90, resize: "vertical" }}
                  />
                  <button onClick={runCommand} style={buttonStyle}>
                    Execute
                  </button>
                </div>
              </section>

              <section>
                <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.16em", color: "#93c5fd" }}>
                  Add Finding
                </div>
                <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                  <input
                    value={findingTitle}
                    onChange={(e) => setFindingTitle(e.target.value)}
                    placeholder="finding title"
                    style={inputStyle}
                  />
                  <select value={findingSeverity} onChange={(e) => setFindingSeverity(e.target.value)} style={inputStyle}>
                    <option value="critical">critical</option>
                    <option value="high">high</option>
                    <option value="medium">medium</option>
                    <option value="low">low</option>
                    <option value="info">info</option>
                  </select>
                  <textarea
                    value={findingEvidence}
                    onChange={(e) => setFindingEvidence(e.target.value)}
                    placeholder="evidence summary"
                    style={{ ...inputStyle, minHeight: 80, resize: "vertical" }}
                  />
                  <button onClick={addFinding} style={buttonStyle}>
                    Save Finding
                  </button>
                </div>
              </section>

              <section>
                <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.16em", color: "#93c5fd" }}>
                  Ask Copilot
                </div>
                <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                  <textarea
                    value={copilotPrompt}
                    onChange={(e) => setCopilotPrompt(e.target.value)}
                    placeholder="Ask for next steps, triage, or remediation"
                    style={{ ...inputStyle, minHeight: 100, resize: "vertical" }}
                  />
                  <button onClick={askCopilot} style={buttonStyle}>
                    Send
                  </button>
                </div>
                <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                  {copilotMessages.slice(-4).map((message, index) => (
                    <div
                      key={`${message.role}-${index}`}
                      style={{
                        borderRadius: 14,
                        padding: 12,
                        background: message.role === "assistant" ? "rgba(30,41,59,0.9)" : "rgba(15,23,42,0.9)",
                        border: "1px solid rgba(148,163,184,0.12)",
                      }}
                    >
                      <div style={{ fontSize: 12, color: "#93c5fd", textTransform: "uppercase", letterSpacing: "0.16em" }}>
                        {message.role}
                        {message.provider ? ` · ${message.provider}` : ""}
                        {message.model ? ` / ${message.model}` : ""}
                      </div>
                      <div style={{ marginTop: 8, color: "#e2e8f0", whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                        {message.content}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {actionState ? <div style={{ color: "#93c5fd", fontSize: 14 }}>{actionState}</div> : null}
            </div>
          </article>

          <article
            style={{
              borderRadius: 24,
              padding: 24,
              background: "rgba(15,23,42,0.72)",
              border: "1px solid rgba(148,163,184,0.12)",
            }}
          >
            <h2 style={{ margin: 0, fontSize: 24 }}>Command Runs</h2>
            <div style={{ marginTop: 16, display: "grid", gap: 14 }}>
              {runs.map((run) => (
                <div
                  key={run.id}
                  style={{
                    borderRadius: 18,
                    padding: 16,
                    background: "rgba(2,6,23,0.55)",
                    border: "1px solid rgba(148,163,184,0.08)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ fontWeight: 600 }}>{run.tool}</div>
                    <div style={{ color: "#93c5fd", fontSize: 14 }}>
                      {run.status}
                      {run.exit_code !== null ? ` · exit ${run.exit_code}` : ""}
                    </div>
                  </div>
                  <pre
                    style={{
                      margin: "10px 0 0",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      color: "#cbd5e1",
                      fontFamily: "var(--font-geist-mono), monospace",
                      fontSize: 13,
                    }}
                  >
                    {run.command}
                  </pre>
                  {run.stdout ? (
                    <details style={{ marginTop: 10 }}>
                      <summary style={{ cursor: "pointer", color: "#93c5fd" }}>stdout</summary>
                      <pre style={{ marginTop: 8, whiteSpace: "pre-wrap", color: "#cbd5e1", fontSize: 12 }}>
                        {run.stdout.slice(0, 2000)}
                      </pre>
                    </details>
                  ) : null}
                  {run.stderr ? (
                    <details style={{ marginTop: 10 }}>
                      <summary style={{ cursor: "pointer", color: "#fca5a5" }}>stderr</summary>
                      <pre style={{ marginTop: 8, whiteSpace: "pre-wrap", color: "#fecaca", fontSize: 12 }}>
                        {run.stderr.slice(0, 2000)}
                      </pre>
                    </details>
                  ) : null}
                </div>
              ))}
              {runs.length === 0 ? <div style={{ color: "#94a3b8" }}>No command runs recorded.</div> : null}
            </div>
          </article>

          <article
            style={{
              borderRadius: 24,
              padding: 24,
              background: "rgba(15,23,42,0.72)",
              border: "1px solid rgba(148,163,184,0.12)",
            }}
          >
            <h2 style={{ margin: 0, fontSize: 24 }}>Findings</h2>
            <div style={{ marginTop: 16, display: "grid", gap: 14 }}>
              {findings.map((finding) => (
                <div
                  key={finding.id}
                  style={{
                    borderRadius: 18,
                    padding: 16,
                    background: "rgba(2,6,23,0.55)",
                    border: "1px solid rgba(148,163,184,0.08)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ fontWeight: 600 }}>{finding.title}</div>
                    <div style={{ color: "#fca5a5", fontSize: 14 }}>{finding.severity}</div>
                  </div>
                  <div style={{ marginTop: 6, color: "#94a3b8", fontSize: 14 }}>
                    {finding.source_tool} · {finding.category}
                    {finding.asset ? ` · ${finding.asset}` : ""}
                  </div>
                  <p style={{ margin: "10px 0 0", color: "#cbd5e1", lineHeight: 1.6 }}>{finding.evidence_summary}</p>
                  {summarizeMetadata(finding.metadata).length > 0 ? (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
                      {summarizeMetadata(finding.metadata).map((chip) => (
                        <span
                          key={chip}
                          style={{
                            fontSize: 12,
                            padding: "4px 8px",
                            borderRadius: 999,
                            color: "#cbd5e1",
                            background: "rgba(148,163,184,0.12)",
                            border: "1px solid rgba(148,163,184,0.2)",
                          }}
                        >
                          {chip}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  {finding.remediation ? (
                    <p style={{ margin: "10px 0 0", color: "#86efac", lineHeight: 1.6 }}>
                      Remediation: {finding.remediation}
                    </p>
                  ) : null}
                </div>
              ))}
              {findings.length === 0 ? <div style={{ color: "#94a3b8" }}>No findings recorded.</div> : null}
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}

const inputStyle: CSSProperties = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid rgba(148,163,184,0.18)",
  background: "rgba(2,6,23,0.72)",
  color: "#f8fafc",
  padding: "12px 14px",
  outline: "none",
};

const buttonStyle: CSSProperties = {
  borderRadius: 999,
  border: "1px solid rgba(96,165,250,0.3)",
  background: "rgba(59,130,246,0.18)",
  color: "#e0f2fe",
  padding: "10px 14px",
  cursor: "pointer",
};

const presetButtonStyle: CSSProperties = {
  borderRadius: 999,
  border: "1px solid rgba(148,163,184,0.22)",
  background: "rgba(30,41,59,0.72)",
  color: "#cbd5e1",
  padding: "8px 12px",
  cursor: "pointer",
  fontSize: 12,
};
