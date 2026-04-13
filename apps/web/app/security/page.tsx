"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const pillars = [
  {
    title: "JEBAT CLI",
    body: "Run `python jebat-pentest-cli/main.py engage ...` or `jebat security` for the terminal-first operator flow.",
  },
  {
    title: "Security API",
    body: "Use `/api/v1/security/*` to create targets, sessions, runs, findings, and copilot conversations.",
  },
  {
    title: "Ollama Local-First",
    body: "JEBAT and Serangan share the same local security runtime, with Ollama-backed reasoning and SQLite session persistence.",
  },
];

type Summary = {
  target_count: number;
  session_count: number;
  finding_count: number;
  run_count: number;
  tools: string[];
};

type Session = { id: string; target_id: string; status: string; model: string };

type Finding = {
  id: string;
  title: string;
  severity: string;
  source_tool: string;
  asset?: string;
  metadata?: Record<string, string | number | string[] | null | undefined>;
};

function summarizeMetadata(
  metadata?: Record<string, string | number | string[] | null | undefined>,
): string[] {
  if (!metadata) {
    return [];
  }
  const entries: string[] = [];
  if (metadata.status_code !== undefined) {
    entries.push(`status ${metadata.status_code}`);
  }
  if (metadata.port !== undefined) {
    entries.push(`port ${metadata.port}`);
  }
  if (metadata.template_id) {
    entries.push(`template ${metadata.template_id}`);
  }
  if (Array.isArray(metadata.technologies) && metadata.technologies.length > 0) {
    entries.push(`tech ${metadata.technologies.slice(0, 2).join(", ")}`);
  }
  if (metadata.service) {
    entries.push(`svc ${metadata.service}`);
  }
  return entries.slice(0, 3);
}

export default function SecurityPage() {
  const HomeLink = () => (
    <a href="/" className="inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white transition mb-6">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
      Home
    </a>
  );
  const [summary, setSummary] = useState<Summary | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<string>("");
  const [search, setSearch] = useState("");
  const [sessionStatusFilter, setSessionStatusFilter] = useState("all");
  const [findingSeverityFilter, setFindingSeverityFilter] = useState("all");
  const [toolFilter, setToolFilter] = useState("all");

  useEffect(() => {
    let active = true;
    fetch("http://127.0.0.1:8080/api/v1/security/summary")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data: Summary) => {
        if (active) {
          setSummary(data);
        }
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams();
    if (search.trim()) {
      params.set("query", search.trim());
    }
    if (sessionStatusFilter !== "all") {
      params.set("status", sessionStatusFilter);
    }
    fetch(`http://127.0.0.1:8080/api/v1/security/sessions?${params.toString()}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data: Session[]) => {
        if (active) {
          setSessions(data);
        }
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message);
        }
      });
    return () => {
      active = false;
    };
  }, [search, sessionStatusFilter]);

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams();
    if (search.trim()) {
      params.set("query", search.trim());
    }
    if (findingSeverityFilter !== "all") {
      params.set("severity", findingSeverityFilter);
    }
    if (toolFilter !== "all") {
      params.set("tool", toolFilter);
    }
    fetch(`http://127.0.0.1:8080/api/v1/security/findings?${params.toString()}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data: Finding[]) => {
        if (active) {
          setFindings(data);
        }
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message);
        }
      });
    return () => {
      active = false;
    };
  }, [findingSeverityFilter, search, toolFilter]);

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top left, rgba(239,68,68,0.18), transparent 30%), linear-gradient(180deg, #0a0f1a 0%, #111827 100%)",
        color: "#f8fafc",
        padding: "56px 24px 72px",
      }}
    >
      <div style={{ maxWidth: 1120, margin: "0 auto" }}>
        <div
          style={{
            display: "grid",
            gap: 24,
            gridTemplateColumns: "2fr 1fr",
            alignItems: "start",
          }}
        >
          <section
            style={{
              border: "1px solid rgba(248,250,252,0.12)",
              borderRadius: 24,
              padding: 28,
              background: "rgba(15,23,42,0.78)",
              boxShadow: "0 30px 80px rgba(0,0,0,0.35)",
            }}
          >
            <div style={{ fontSize: 12, letterSpacing: "0.22em", textTransform: "uppercase", color: "#fca5a5" }}>
              j3b4t p3nt3st CLI
            </div>
            <h1 style={{ fontSize: "clamp(2rem, 5vw, 4.5rem)", lineHeight: 1, margin: "16px 0" }}>
              Local pentest workspace and control plane for real operators.
            </h1>
            <p style={{ maxWidth: 780, color: "#cbd5e1", fontSize: 18, lineHeight: 1.6 }}>
              The cloned j3b4t workspace, the Serangan Console API, and this dashboard now share one local session
              model: guarded command execution, normalized findings, Ollama-backed copilot chat, and SQLite-backed
              persistence.
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 24 }}>
              <code
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  background: "rgba(239,68,68,0.14)",
                  border: "1px solid rgba(248,113,113,0.3)",
                }}
              >
                python j3b4t-p3nt3st-cli/main.py engage ...
              </code>
              <code
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  background: "rgba(59,130,246,0.14)",
                  border: "1px solid rgba(96,165,250,0.3)",
                }}
              >
                /api/v1/security/summary
              </code>
            </div>
          </section>

          <section
            style={{
              border: "1px solid rgba(248,250,252,0.12)",
              borderRadius: 24,
              padding: 24,
              background: "rgba(2,6,23,0.7)",
            }}
          >
            <div style={{ fontSize: 13, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.18em" }}>
              Combined Surface
            </div>
            <ul style={{ margin: "18px 0 0", paddingLeft: 18, color: "#e2e8f0", lineHeight: 1.8 }}>
              <li>Targets</li>
              <li>Sessions</li>
              <li>Findings</li>
              <li>Command runs</li>
              <li>Copilot chat</li>
            </ul>
          </section>
        </div>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 18,
            marginTop: 28,
          }}
        >
          {pillars.map((pillar) => (
            <article
              key={pillar.title}
              style={{
                border: "1px solid rgba(248,250,252,0.1)",
                borderRadius: 20,
                padding: 22,
                background: "rgba(15,23,42,0.72)",
              }}
            >
              <h2 style={{ margin: 0, fontSize: 22 }}>{pillar.title}</h2>
              <p style={{ margin: "12px 0 0", color: "#cbd5e1", lineHeight: 1.7 }}>{pillar.body}</p>
            </article>
          ))}
        </section>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "2fr repeat(3, minmax(140px, 1fr))",
            gap: 12,
            marginTop: 28,
            padding: 18,
            borderRadius: 20,
            background: "rgba(15,23,42,0.72)",
            border: "1px solid rgba(148,163,184,0.12)",
          }}
        >
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search sessions, findings, assets, tools"
            style={filterInputStyle}
          />
          <select
            value={sessionStatusFilter}
            onChange={(event) => setSessionStatusFilter(event.target.value)}
            style={filterInputStyle}
          >
            <option value="all">All session states</option>
            <option value="idle">idle</option>
            <option value="active">active</option>
            <option value="complete">complete</option>
            <option value="failed">failed</option>
          </select>
          <select
            value={findingSeverityFilter}
            onChange={(event) => setFindingSeverityFilter(event.target.value)}
            style={filterInputStyle}
          >
            <option value="all">All severities</option>
            <option value="critical">critical</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
            <option value="info">info</option>
          </select>
          <select value={toolFilter} onChange={(event) => setToolFilter(event.target.value)} style={filterInputStyle}>
            <option value="all">All tools</option>
            {(summary?.tools ?? []).map((tool) => (
              <option key={tool} value={tool}>
                {tool}
              </option>
            ))}
          </select>
        </section>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 18,
            marginTop: 28,
          }}
        >
          <article
            style={{
              border: "1px solid rgba(248,250,252,0.1)",
              borderRadius: 20,
              padding: 22,
              background: "rgba(15,23,42,0.72)",
            }}
          >
            <h2 style={{ margin: 0, fontSize: 22 }}>Live Snapshot</h2>
            <p style={{ margin: "10px 0 0", color: "#cbd5e1", lineHeight: 1.7 }}>
              {summary
                ? `${summary.target_count} targets, ${summary.session_count} sessions, ${summary.finding_count} findings, ${summary.run_count} command runs.`
                : error
                  ? `API unavailable: ${error}`
                  : "Waiting for local API summary..."}
            </p>
          </article>
          <article
            style={{
              border: "1px solid rgba(248,250,252,0.1)",
              borderRadius: 20,
              padding: 22,
              background: "rgba(15,23,42,0.72)",
            }}
          >
            <h2 style={{ margin: 0, fontSize: 22 }}>Recent Findings</h2>
            <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
              {findings.slice(0, 6).map((finding) => (
                <div
                  key={finding.id}
                  style={{
                    padding: 12,
                    borderRadius: 14,
                    background: "rgba(2,6,23,0.65)",
                    border: "1px solid rgba(248,250,252,0.08)",
                  }}
                >
                  <div style={{ fontSize: 12, letterSpacing: "0.16em", textTransform: "uppercase", color: "#fca5a5" }}>
                    {finding.severity}
                  </div>
                  <div style={{ marginTop: 4 }}>{finding.title}</div>
                  <div style={{ marginTop: 4, color: "#94a3b8", fontSize: 14 }}>
                    {finding.source_tool}
                    {finding.asset ? ` · ${finding.asset}` : ""}
                  </div>
                  {summarizeMetadata(finding.metadata).length > 0 && (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                      {summarizeMetadata(finding.metadata).map((item) => (
                        <span
                          key={item}
                          style={{
                            fontSize: 12,
                            padding: "4px 8px",
                            borderRadius: 999,
                            color: "#cbd5e1",
                            background: "rgba(148,163,184,0.12)",
                            border: "1px solid rgba(148,163,184,0.2)",
                          }}
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!findings.length && (
                <div style={{ color: "#94a3b8" }}>No findings match the current filters.</div>
              )}
            </div>
          </article>
        </section>

        <section
          style={{
            borderRadius: 24,
            padding: 24,
            background: "rgba(15,23,42,0.72)",
            border: "1px solid rgba(148,163,184,0.12)",
            marginTop: 28,
          }}
        >
          <h2 style={{ margin: 0, fontSize: 24 }}>Sessions</h2>
          <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
            {sessions.slice(0, 12).map((session) => (
              <Link
                key={session.id}
                href={`/security/sessions/${session.id}`}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 12,
                  alignItems: "center",
                  padding: 16,
                  borderRadius: 18,
                  textDecoration: "none",
                  color: "#f8fafc",
                  background: "rgba(2,6,23,0.55)",
                  border: "1px solid rgba(148,163,184,0.08)",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{session.id}</div>
                  <div style={{ marginTop: 4, color: "#94a3b8", fontSize: 14 }}>
                    {session.status} · {session.model}
                  </div>
                </div>
                <div style={{ color: "#93c5fd", fontSize: 14 }}>Open session</div>
              </Link>
            ))}
            {!sessions.length && (
              <div style={{ color: "#94a3b8" }}>No sessions match the current filters.</div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

const filterInputStyle = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid rgba(148,163,184,0.18)",
  background: "rgba(2,6,23,0.72)",
  color: "#f8fafc",
  padding: "12px 14px",
  outline: "none",
};
