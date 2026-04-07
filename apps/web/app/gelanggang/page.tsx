"use client";

import { useState, useRef, useEffect } from "react";
import { AgentShimmer } from "../../components/agent-shimmer";

// Agent definitions for the demo
const DEMO_AGENTS = [
  { id: "tukang-001", name: "Tukang", role: "Development", provider: "OpenAI", model: "gpt-4o", emoji: "🔧", color: "#3B82F6" },
  { id: "hulubalang-001", name: "Hulubalang", role: "Security", provider: "Anthropic", model: "claude-sonnet-4", emoji: "🛡️", color: "#EF4444" },
  { id: "pawang-001", name: "Pawang", role: "Research", provider: "Gemini", model: "gemini-2.5-pro", emoji: "🔍", color: "#10B981" },
  { id: "syahbandar-001", name: "Syahbandar", role: "Operations", provider: "Ollama", model: "qwen2.5-coder:7b", emoji: "⚙️", color: "#F59E0B" },
  { id: "penyemak-001", name: "Penyemak", role: "QA", provider: "ZAI", model: "glm-5", emoji: "✅", color: "#8B5CF6" },
  { id: "panglima-001", name: "Panglima", role: "Orchestration", provider: "Anthropic", model: "claude-opus-4", emoji: "⚔️", color: "#00E5FF" },
];

const COLLAB_PATTERNS = [
  { id: "sequential", name: "Sequential", description: "Each agent works in order, building on previous results" },
  { id: "parallel", name: "Parallel", description: "All agents work simultaneously" },
  { id: "consensus", name: "Consensus", description: "All agents propose and vote" },
  { id: "adversarial", name: "Adversarial", description: "Two debate, third judges" },
];

const DEMO_SCENARIOS = [
  {
    id: "code_review",
    title: "Multi-Agent Code Review",
    description: "Tukang writes code → Hulubalang audits security → Penyemak validates tests → Panglima synthesizes",
    agents: ["tukang-001", "hulubalang-001", "penyemak-001", "panglima-001"],
    pattern: "sequential",
    task: "Build a secure user authentication API with JWT tokens and rate limiting",
  },
  {
    id: "security_design",
    title: "Security Architecture Design",
    description: "Hulubalang proposes → Pawang researches → Penyemak validates → Panglima decides",
    agents: ["hulubalang-001", "pawang-001", "penyemak-001", "panglima-001"],
    pattern: "consensus",
    task: "Design a zero-trust architecture for a microservices deployment",
  },
  {
    id: "debate",
    title: "Adversarial Architecture Debate",
    description: "Tukang proposes monolith → Syahbandar proposes microservices → Panglima judges",
    agents: ["tukang-001", "syahbandar-001", "panglima-001"],
    pattern: "adversarial",
    task: "Should we use monolith or microservices for our new platform?",
  },
];

// Simulated LLM-to-LLM conversation messages
const SIMULATED_RESPONSES: Record<string, Record<string, string>> = {
  tukang: {
    "code_review": `I'll build a secure auth API with JWT and rate limiting.

\`\`\`python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt
import time

app = FastAPI()
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET")

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    user = await verify_user(credentials)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    token = jwt.encode({
        "sub": user.id,
        "exp": time.time() + 3600,
        "iat": time.time(),
    }, SECRET_KEY, algorithm="HS256")
    
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        return await get_user(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
\`\`\`

I've included proper JWT validation and error handling. Hulubalang should review the security aspects.`,
  },
  hulubalang: {
    "code_review": `🔴 **CRITICAL SECURITY ISSUES FOUND**

| Issue | Severity | Line |
|-------|----------|------|
| Hardcoded secret fallback | CRITICAL | 7 |
| No rate limiting | HIGH | — |
| No password hashing mentioned | HIGH | — |
| Missing CSRF protection | MEDIUM | — |

**Fixes:**
1. Use environment variables ONLY — no fallback
2. Add rate limiting with Redis-backed sliding window
3. Use bcrypt for password hashing
4. Add refresh token rotation
5. Implement token blacklisting for logout

\`\`\`python
# Rate limiting middleware
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    # Implementation with rate limiting
    pass
\`\`\`

Penyemak should validate the test coverage for these security controls.`,
  },
  penyemak: {
    "code_review": `✅ **QA Validation Report**

**Test Coverage Analysis:**
- Auth flow: 85% coverage ✅
- Error handling: 70% coverage ⚠️
- Rate limiting: 60% coverage ⚠️
- Token validation: 90% ✅

**Missing Test Cases:**
1. Expired token handling
2. Invalid signature detection
3. Rate limit exhaustion
4. Concurrent login from different IPs
5. Token replay attack prevention

**Recommendation:** Add integration tests for all 5 missing cases before deployment. Estimated effort: 2-3 hours.

**Overall Assessment:** Code is 75% production-ready. Fix the 3 HIGH security issues and add the 5 missing test cases.`,
  },
  panglima: {
    "code_review": `⚔️ **Orchestrator Synthesis**

**Final Verdict: PROCEED WITH MODIFICATIONS**

**Summary of Multi-Agent Review:**
- 🔧 Tukang: Built solid JWT auth foundation
- 🛡️ Hulubalang: Found 4 security issues (2 CRITICAL, 2 HIGH)
- ✅ Penyemak: 75% production-ready, 5 test gaps

**Action Items (Priority Order):**
1. **[CRITICAL]** Fix hardcoded secret — use env vars only
2. **[CRITICAL]** Add rate limiting (Redis-backed)
3. **[HIGH]** Implement bcrypt password hashing
4. **[HIGH]** Add refresh token rotation
5. **[MEDIUM]** Add 5 missing integration tests

**Estimated Time:** 4-6 hours
**Confidence:** HIGH — All agents agree on critical issues
**Next Step:** Assign to Tukang for fixes, re-review by Hulubalang`,
  },
};

export default function GelanggangPage() {
  const [selectedScenario, setSelectedScenario] = useState(DEMO_SCENARIOS[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [messages, setMessages] = useState<any[]>([]);
  const [loadingAgents, setLoadingAgents] = useState<string[]>([]);
  const [finalResult, setFinalResult] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(scrollToBottom, [messages, currentStep]);

  const runDemo = async () => {
    setIsRunning(true);
    setCurrentStep(0);
    setMessages([]);
    setFinalResult("");
    setMessages([{ role: "system", content: `🏛️ Gelanggang Panglima initialized\nTask: ${selectedScenario.task}\nPattern: ${selectedScenario.pattern}\nAgents: ${selectedScenario.agents.map(id => DEMO_AGENTS.find(a => a.id === id)?.name).join(" → ")}` }]);

    const agentIds = selectedScenario.agents;

    for (let i = 0; i < agentIds.length; i++) {
      const agentId = agentIds[i];
      const agent = DEMO_AGENTS.find(a => a.id === agentId)!;

      // Show shimmer
      setLoadingAgents([agentId]);
      setCurrentStep(i + 1);

      await new Promise(r => setTimeout(r, 800));

      // Simulate LLM-to-LLM communication
      const agentKey = agent.name.toLowerCase();
      const content = SIMULATED_RESPONSES[agentKey]?.[selectedScenario.id] || `${agent.name} is processing the task with ${agent.provider} (${agent.model})...`;

      setMessages(prev => [...prev, {
        role: "agent",
        agent: agent,
        content: content,
        timestamp: new Date().toLocaleTimeString(),
      }]);

      setLoadingAgents([]);
      await new Promise(r => setTimeout(r, 500));
    }

    setFinalResult("✅ Collaboration complete. All agents have contributed.");
    setIsRunning(false);
  };

  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🏛️</span>
            <div>
              <span className="text-lg font-semibold tracking-tight">Gelanggang Panglima</span>
              <span className="ml-2 text-xs text-neutral-500">LLM-to-LLM Orchestration Arena</span>
            </div>
          </div>
          <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-6 py-8 space-y-8">
        {/* Hero */}
        <section className="text-center space-y-4">
          <h1 className="text-4xl font-bold gradient-text">⚔️ Gelanggang Panglima</h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-400">
            Watch LLM agents from different providers (OpenAI, Anthropic, Gemini, Ollama, ZAI) communicate, collaborate, and debate — all orchestrated by Panglima.
          </p>
        </section>

        {/* Scenario Selector */}
        <section className="grid gap-4 md:grid-cols-3">
          {DEMO_SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => !isRunning && setSelectedScenario(scenario)}
              disabled={isRunning}
              className={`text-left rounded-2xl border p-5 transition card-hover ${
                selectedScenario.id === scenario.id
                  ? "border-cyan-400/30 bg-cyan-400/10"
                  : "border-white/10 bg-white/[0.02] hover:border-white/20"
              } ${isRunning ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              <h3 className="font-semibold text-white mb-2">{scenario.title}</h3>
              <p className="text-sm text-neutral-400 mb-3">{scenario.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {scenario.agents.map(id => {
                  const agent = DEMO_AGENTS.find(a => a.id === id);
                  return agent ? (
                    <span key={id} className="text-xs rounded-full border px-2 py-0.5" style={{ borderColor: agent.color + "40", color: agent.color }}>
                      {agent.emoji} {agent.name}
                    </span>
                  ) : null;
                })}
              </div>
            </button>
          ))}
        </section>

        {/* Run Button */}
        <div className="flex justify-center">
          <button
            onClick={runDemo}
            disabled={isRunning}
            className={`rounded-xl px-8 py-4 text-base font-semibold transition ${
              isRunning
                ? "bg-neutral-700 text-neutral-400 cursor-not-allowed"
                : "bg-cyan-400 text-black hover:bg-cyan-300"
            }`}
          >
            {isRunning ? `⏳ Step ${currentStep}/${selectedScenario.agents.length} — ${DEMO_AGENTS.find(a => a.id === selectedScenario.agents[currentStep - 1])?.name} is thinking...` : "🏛️ Start Gelanggang"}
          </button>
        </div>

        {/* Agent Status Bar */}
        <section className="flex flex-wrap justify-center gap-4">
          {DEMO_AGENTS.map((agent) => {
            const isActive = loadingAgents.includes(agent.id);
            const hasSpoken = messages.some(m => m.agent?.id === agent.id);
            return (
              <div
                key={agent.id}
                className={`flex items-center gap-2 rounded-xl border px-4 py-2 transition ${
                  isActive ? "border-cyan-400/50 bg-cyan-400/10" :
                  hasSpoken ? "border-emerald-400/30 bg-emerald-400/5" :
                  "border-white/10 bg-white/[0.02]"
                }`}
              >
                <span className="text-lg">{agent.emoji}</span>
                <div>
                  <div className="text-sm font-medium">{agent.name}</div>
                  <div className="text-xs text-neutral-500">{agent.provider} · {agent.model}</div>
                </div>
                {isActive && <span className="ml-1 h-2 w-2 rounded-full bg-cyan-400 animate-ping" />}
                {hasSpoken && !isActive && <span className="ml-1 text-emerald-400 text-xs">✓</span>}
              </div>
            );
          })}
        </section>

        {/* Conversation Feed */}
        <section className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 min-h-[400px] max-h-[600px] overflow-y-auto">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-neutral-500">
              <span className="text-4xl mb-4">🏛️</span>
              <p>Select a scenario and click "Start Gelanggang" to watch agents communicate</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className="mb-6">
              {msg.role === "system" ? (
                <div className="rounded-xl bg-cyan-400/5 border border-cyan-400/20 px-4 py-3">
                  <pre className="text-sm text-cyan-300 whitespace-pre-wrap font-mono">{msg.content}</pre>
                </div>
              ) : (
                <div className="rounded-xl border border-white/10 bg-black/20 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">{msg.agent.emoji}</span>
                    <div>
                      <span className="font-semibold" style={{ color: msg.agent.color }}>{msg.agent.name}</span>
                      <span className="ml-2 text-xs text-neutral-500">{msg.agent.provider}/{msg.agent.model}</span>
                      <span className="ml-2 text-xs text-neutral-600">{msg.timestamp}</span>
                    </div>
                    <div className="ml-auto">
                      <span className="text-xs rounded-full border px-2 py-0.5 text-neutral-400 border-white/10">
                        LLM-to-LLM Message #{i}
                      </span>
                    </div>
                  </div>
                  <div className="text-sm text-neutral-300 whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              )}
            </div>
          ))}

          {isRunning && loadingAgents.length > 0 && (
            <div className="rounded-xl border border-white/10 bg-black/20 p-4">
              <AgentShimmer agents={loadingAgents} visible={true} />
            </div>
          )}

          {finalResult && (
            <div className="rounded-xl bg-emerald-400/5 border border-emerald-400/20 px-4 py-3 text-center">
              <span className="text-emerald-300 font-medium">{finalResult}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </section>

        {/* How It Works */}
        <section className="rounded-3xl border border-white/10 bg-white/[0.02] p-8">
          <h2 className="text-2xl font-bold mb-6 text-center">How Gelanggang Panglima Works</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                icon: "🔌",
                title: "1. Provider Bridge",
                desc: "Each agent connects to its LLM provider (OpenAI, Anthropic, Gemini, Ollama, ZAI). Messages are translated to the provider's format automatically.",
              },
              {
                icon: "💬",
                title: "2. Agent Protocol",
                desc: "Agents communicate using a standardized protocol with 15+ message types: request, response, delegate, proposal, vote, consensus, and more.",
              },
              {
                icon: "⚔️",
                title: "3. Panglima Orchestrates",
                desc: "Panglima manages the conversation flow — sequential, parallel, consensus, or adversarial — ensuring each agent contributes optimally.",
              },
            ].map((item) => (
              <div key={item.title} className="text-center">
                <div className="text-4xl mb-3">{item.icon}</div>
                <h3 className="font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-neutral-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
