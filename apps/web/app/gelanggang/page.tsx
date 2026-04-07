"use client";

import { useState, useRef, useEffect } from "react";
import { AgentIcon, AGENT_ICONS } from "../../components/icons";

// ─── Agent Definitions ────────────────────────────────────────────────────────

const DEMO_AGENTS = [
  { id: "tukang-001", name: "Tukang", role: "Development", provider: "OpenAI", model: "gpt-4o", icon: "tukang", color: "#3B82F6" },
  { id: "hulubalang-001", name: "Hulubalang", role: "Security", provider: "Anthropic", model: "claude-sonnet-4", icon: "hulubalang", color: "#EF4444" },
  { id: "pawang-001", name: "Pawang", role: "Research", provider: "Gemini", model: "gemini-2.5-pro", icon: "pawang", color: "#10B981" },
  { id: "syahbandar-001", name: "Syahbandar", role: "Operations", provider: "Ollama", model: "qwen2.5-coder:7b", icon: "syahbandar", color: "#F59E0B" },
  { id: "penyemak-001", name: "Penyemak", role: "QA", provider: "ZAI", model: "glm-5", icon: "penyemak", color: "#8B5CF6" },
  { id: "panglima-001", name: "Panglima", role: "Orchestration", provider: "Anthropic", model: "claude-opus-4", icon: "panglima", color: "#00E5FF" },
];

// ─── Orchestration Scenarios ─────────────────────────────────────────────────

const SCENARIOS = [
  {
    id: "secure_api",
    title: "Secure API Design",
    subtitle: "Build & audit a production authentication API",
    description: "Watch Tukang build a JWT auth system → Hulubalang find vulnerabilities → Penyemak validate tests → Panglima synthesize the verdict.",
    pattern: "Sequential",
    patternIcon: "➡️",
    agents: ["tukang-001", "hulubalang-001", "penyemak-001", "panglima-001"],
    estimatedTime: "~45 seconds",
  },
  {
    id: "incident_response",
    title: "Incident Response",
    subtitle: "Detect, investigate, and remediate a security breach",
    description: "Pawang investigates the breach → Hulubalang traces the attack vector → Syahbandar deploys containment → Panglima coordinates the response.",
    pattern: "Parallel",
    patternIcon: "⚡",
    agents: ["pawang-001", "hulubalang-001", "syahbandar-001", "panglima-001"],
    estimatedTime: "~50 seconds",
  },
  {
    id: "architecture_debate",
    title: "Architecture Debate",
    subtitle: "Monolith vs Microservices — adversarial resolution",
    description: "Tukang argues for monolith simplicity → Syahbandar advocates microservices scalability → Panglima judges based on trade-offs.",
    pattern: "Adversarial",
    patternIcon: "⚔️",
    agents: ["tukang-001", "syahbandar-001", "panglima-001"],
    estimatedTime: "~35 seconds",
  },
];

// ─── Randomized Response Pool ─────────────────────────────────────────────────

const RESPONSE_POOL: Record<string, Record<string, string[]>> = {
  tukang: {
    secure_api: [
      `I'll build a secure auth API with JWT, bcrypt, and rate limiting.

\`\`\`python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
import jwt, bcrypt, os, time

app = FastAPI()
security = HTTPBearer()
SECRET_KEY = os.environ["JWT_SECRET"]  # No fallbacks

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    user = await db.get_user(credentials.email)
    if not user or not bcrypt.checkpw(credentials.password.encode(), user.hashed_pw):
        raise HTTPException(401, "Invalid credentials")
    
    token = jwt.encode({"sub": user.id, "exp": time.time() + 3600, "iat": time.time()}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}
\`\`\`

Key security decisions:
- Environment-only secrets (no defaults)
- bcrypt for password hashing (cost factor 12)
- Rate limiting at 5 req/min per IP
- JWT expiry at 1 hour with rotation

Hulubalang should review for edge cases.`,

      `Building a production-grade auth API. Here's my approach:

\`\`\`python
from fastapi import FastAPI, Depends, HTTPException
from passlib.context import CryptContext
import jwt, os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ["JWT_SECRET"]

class AuthService:
    async def authenticate(self, email: str, password: str) -> str:
        user = await self._get_user(email)
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(401, "Authentication failed")
        
        return jwt.encode(
            {"sub": str(user.id), "role": user.role, "exp": int(time.time()) + 3600},
            SECRET_KEY, algorithm="HS256"
        )
    
    async def verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")
\`\`\`

Security layers implemented:
1. bcrypt with automatic salt generation
2. JWT with HS256 and 1-hour expiry
3. Token blacklisting support for logout
4. Refresh token rotation (not shown)
5. Input validation on all endpoints

Ready for Hulubalang's security review.`,

      `Here's the auth system I've designed:

\`\`\`python
# Core authentication flow
async def login(email: str, password: str) -> TokenResponse:
    # 1. Validate input format
    validate_email(email)
    validate_password_strength(password)
    
    # 2. Lookup user (constant-time to prevent enumeration)
    user = await users.get_by_email(email)
    
    # 3. Verify password (bcrypt, constant-time compare)
    if not user or not verify_password(password, user.hashed_pw):
        # Same error message to prevent email enumeration
        raise AuthError("Invalid credentials")
    
    # 4. Check account status
    if user.locked_until and user.locked_until > now():
        raise AuthError("Account temporarily locked")
    
    # 5. Issue tokens
    access_token = create_jwt(user.id, expiry=3600)
    refresh_token = create_refresh_token(user.id)
    
    # 6. Log the authentication
    await audit_log.log("login_success", user_id=user.id, ip=request.ip)
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
\`\`\`

Defensive measures:
- Constant-time email lookup (prevents enumeration)
- Account lockout after 5 failed attempts (15 min cooldown)
- Structured audit logging for every auth event
- Refresh token rotation with family detection

Hulubalang, please review the cryptographic choices.`,
    ],
    incident_response: [
      `I'm investigating the breach. Initial findings:

**Timeline of events:**
- 02:14:47 — Unusual API traffic spike from IP 203.0.113.42
- 02:15:02 — Multiple failed login attempts across 12 accounts
- 02:15:33 — Successful login from compromised service account
- 02:16:01 — Data exfiltration attempt on /api/users/export

**Attack vector analysis:**
The attacker appears to have used a credential stuffing attack against our API. The compromised service account had overly broad permissions — it could access the user export endpoint.

**Immediate actions taken:**
1. Blocked IP 203.0.113.42 at WAF level
2. Revoked the compromised service account's tokens
3. Enabled enhanced logging on all export endpoints

I'm passing this to Hulubalang for deeper forensic analysis.`,

      `Breach investigation update:

**What happened:**
At 02:14 UTC, we detected anomalous behavior — 847 login attempts in 90 seconds from a single IP range. This triggered our rate limiter, but the attacker rotated through 47 different IPs.

**Compromised assets:**
- 1 service account (svc-backup-02) — token was stolen
- 3 user accounts — credential stuffing successful
- User database was queried (not exported — our rate limiting on exports held)

**Containment status:**
- 🔴 Active threat: BLOCKED
- 🟡 Investigation: ONGOING
- 🟢 User data: NOT EXFILTRATED

Handing off to Hulubalang for attack vector deep-dive.`,
    ],
    architecture_debate: [
      `I strongly recommend starting with a well-structured monolith. Here's why:

**For our current team size (5 engineers):**
- A monolith means ONE codebase to manage, ONE deployment pipeline, ONE monitoring system
- We can still use modular architecture internally — separate packages for auth, users, billing
- When we hit 50+ engineers OR need independent scaling, we can extract services

**The microservices trap:**
- 5 services = 5x deployment complexity, 5x monitoring, 5x CI/CD pipelines
- Distributed tracing, service mesh, API gateways — all infrastructure we don't need yet
- Network latency between services adds 50-200ms to every request

**My recommendation:**
Build a modular monolith with clear boundaries. When a module outgrows its bounds, extract it. This is what Stripe, Shopify, and GitHub all did.

Syahbandar wants microservices now — but I say we earn that complexity.`,

      `Monolith-first is the right call for Q1-Q2. But let me add context:

**Where I agree with Tukang:**
- Team size < 10 → monolith is correct
- Modular boundaries are key — don't build a big ball of mud
- Extract when you feel pain, not before

**Where I disagree:**
We should DESIGN for microservices from day one. Not build them, but DESIGN:
- Clear API contracts between modules
- Database-per-module pattern (even in monolith)
- Event-driven communication between modules

Why? Because refactoring a monolith into microservices later is 10x harder than extracting well-bounded modules.

Let me show the hybrid approach I'm proposing...`,
    ],
  },
  hulubalang: {
    secure_api: [
      `🔴 **CRITICAL SECURITY FINDINGS**

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | JWT secret not rotated | HIGH | Token forgery if leaked |
| 2 | No CSRF protection | MEDIUM | Cross-site request forgery |
| 3 | Missing X-Content-Type-Options | LOW | MIME-type sniffing |

**Detailed analysis:**

**Issue #1 — JWT Secret Rotation:**
The secret key is static. If compromised, ALL tokens are compromised until manual rotation.
\`\`\`
Recommendation: Implement key rotation with key ID (kid) in JWT header
\`\`\`

**Issue #2 — CSRF:**
The login endpoint accepts POST without CSRF token validation.
\`\`\`python
# Fix: Add CSRF middleware
app.add_middleware(CSRFMiddleware, secret=os.environ["CSRF_SECRET"])
\`\`\`

**Positive findings:**
✅ bcrypt with cost factor 12 — good
✅ Rate limiting implemented — good
✅ No SQL injection (parameterized queries) — good

Overall: 7/10 security score. Fix the 3 issues before production.`,

      `🛡️ **Security Audit Report — Auth API**

**Score: 7/10** — Good foundation, needs hardening

**CRITICAL findings:**
1. **No token blacklisting** — Users can't truly log out. JWTs remain valid until expiry.
   - Fix: Add Redis-backed token blacklist or use short-lived tokens with refresh rotation

2. **Missing input sanitization** — Email field not sanitized before DB query
   - Fix: Add pydantic EmailStr validation + HTML/entity encoding

**HIGH findings:**
3. **No account lockout** — Brute force is rate-limited but not locked
   - Fix: Lock account for 15 min after 5 failed attempts

4. **Missing security headers** — No Content-Security-Policy, no X-Frame-Options
   - Fix: Add SecurityHeaders middleware

**What's done well:**
✅ bcrypt password hashing
✅ Rate limiting
✅ No hardcoded secrets
✅ Structured error messages (no stack traces)

**Recommendation:** Fix CRITICAL items 1-2 before deploying to staging.`,
    ],
    incident_response: [
      `🔴 **Forensic Analysis — Attack Vector Deep Dive**

**Attack chain reconstruction:**

1. **Reconnaissance (02:10-02:14):** Attacker scanned our API for login endpoints using automated tooling
2. **Credential Stuffing (02:14-02:15):** Used 12,000 leaked credentials against /api/auth/login
3. **Token Theft (02:15):** Obtained valid JWT for svc-backup-02 (likely from compromised CI/CD logs)
4. **Lateral Movement (02:16):** Used service account to query /api/users/export
5. **Exfiltration BLOCKED (02:16):** Rate limiting on export endpoint prevented data theft

**Root cause:**
The service account token was accidentally committed to a public CI/CD log 3 weeks ago. Our secret scanning didn't catch it because it was base64-encoded.

**Remediation:**
1. Rotate ALL service account tokens immediately
2. Add base64-encoded secret detection to our scanning pipeline
3. Implement short-lived service tokens (max 1 hour)
4. Add anomaly detection on service account usage patterns

Syahbandar, I need you to rotate the tokens and patch the CI/CD pipeline.`,

      `🔍 **Attack Forensics Update**

**Threat actor profile:**
- Automated tooling (python-requests with randomized user agents)
- Credential list matches HaveIBeenPwned breach from 2024
- Targeted our specific API endpoints (not random scanning)
- This appears to be a targeted attack, not opportunistic

**IOCs (Indicators of Compromise):**
- IPs: 203.0.113.42, 198.51.100.15, 192.0.2.88
- User-Agent pattern: "Mozilla/5.0 (compatible; Bot/1.0)"
- Request pattern: POST /api/auth/login with 0.1s intervals

**What was NOT compromised:**
- User database (export rate limiting held)
- Admin accounts (MFA prevented credential stuffing)
- Payment data (separate service, not accessed)

Passing to Syahbandar for containment deployment.`,
    ],
    architecture_debate: [
      `I disagree with Tukang's monolith recommendation for THIS specific use case.

**Why microservices make sense here:**

1. **Different security requirements:** Auth service needs PCI-DSS compliance. The analytics service doesn't. Putting them in the same codebase means the ENTIRE monolith needs PCI-DSS compliance.

2. **Independent scaling:** During peak hours, our auth endpoints get 10x traffic while admin endpoints get 1x. With a monolith, you scale EVERYTHING. With microservices, you scale only what's under load.

3. **Team autonomy:** When Team A breaks Team B's code in a monolith, you get deployment freezes. With service boundaries, teams deploy independently.

**My proposed architecture:**
- auth-service (Go — high performance, small binary)
- api-gateway (Nginx + Lua)
- user-service (Python/FastAPI — rapid development)
- analytics-service (Node.js — streaming support)

**Yes, it's more complex.** But the complexity buys us: security isolation, independent scaling, team autonomy, and technology diversity.

Panglima, I'd like you to judge this based on our team's operational maturity.`,
    ],
  },
  pawang: {
    incident_response: [
      `📊 **Threat Intelligence Report**

**Attribution analysis:**
The IP addresses (203.0.113.42, 198.51.100.15, 192.0.2.88) belong to a known threat actor group tracked as APT-47 "ShadowNet". This group has been active since 2023, targeting SaaS companies in Southeast Asia.

**TTPs (Tactics, Techniques, Procedures):**
- Initial access: Credential stuffing (MITRE ATT&CK T1110)
- Persistence: Service account token reuse (T1078)
- Collection: API data export (T1530)
- This matches their standard playbook from the March 2025 TechCorp breach

**Recommended additional actions:**
1. Check all CI/CD logs from the past 90 days for other leaked tokens
2. Search threat intelligence feeds for our domain in APT-47 target lists
3. Review all service accounts for overly broad permissions
4. Implement mandatory token rotation every 24 hours

**Confidence level: HIGH** — The attack pattern matches 3 previous incidents attributed to this group.`,

      `📋 **Research Summary — Threat Landscape**

**What we know:**
- This is NOT a random automated attack. The targeting was specific to our API.
- The credential list used matches the "DataBreach2024" leak (8.2M records).
- Our domain appears in 2 dark web forum posts discussing "Southeast Asian SaaS targets."

**Industry context:**
Similar attacks on 3 other companies in our sector this quarter:
- Company A: Full breach (no rate limiting) → $2.4M in damages
- Company B: Partial breach (rate limiting but no MFA) → $800K in damages
- Company C: No breach (rate limiting + MFA + token rotation) → $0 in damages

**Key takeaway:** Our rate limiting saved us. But the compromised service account shows we need mandatory token rotation.

Recommendation: Implement the 4-point remediation plan Hulubalang outlined.`,
    ],
  },
  syahbandar: {
    incident_response: [
      `⚙️ **Containment Deployment — In Progress**

**Actions completed:**
1. ✅ Rotated ALL 23 service account tokens (took 12 minutes)
2. ✅ Patched CI/CD pipeline — added base64 secret detection (commit a3f7b2c)
3. ✅ Implemented 1-hour token expiry for all service accounts
4. ✅ Deployed anomaly detection rules on service account usage

**Infrastructure changes deployed:**
\`\`\`yaml
# New CI/CD secret scanning rule
- name: detect-base64-secrets
  pattern: "(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"
  action: block_and_alert
\`\`\`

**Monitoring status:**
- All export endpoints now have enhanced logging (5 min retention → 90 day retention)
- Real-time alerts configured for service account anomalies
- Dashboard updated with breach timeline

Estimated time to full remediation: 45 minutes. All critical actions complete.`,
    ],
    architecture_debate: [
      `Both of you make valid points. Let me add the operational perspective:

**Infrastructure cost comparison (estimated monthly):**

| Architecture | Compute | Monitoring | CI/CD | Total |
|-------------|---------|-----------|-------|-------|
| Monolith | $200 | $50 | $30 | **$280** |
| Microservices (5 services) | $800 | $200 | $150 | **$1,150** |

**The hidden cost nobody talks about:**
- Developer cognitive load: monolith = 1 context, microservices = 5 contexts
- On-call rotation: monolith = 1 page, microservices = 5 possible pages
- Debugging: monolith = grep logs, microservices = distributed tracing setup

**My operational recommendation:**
Start with monolith BUT build the operational tooling for microservices NOW:
- Containerize each module as if it were a service
- Set up the CI/CD pipeline for independent deployment
- Monitor each module's resource usage independently

When we're ready to split, it's a config change, not a rewrite.`,
    ],
  },
  penyemak: {
    secure_api: [
      `✅ **QA Validation Report**

**Test Coverage Analysis:**
- Auth flow: 85% coverage ✅
- Error handling: 72% coverage ⚠️
- Rate limiting: 65% coverage ⚠️
- Token validation: 90% ✅

**Missing test cases (critical):**
1. Expired token handling — not tested
2. Invalid signature detection — not tested
3. Rate limit exhaustion — not tested
4. Concurrent login from different IPs — not tested
5. Token replay attack prevention — not tested

**Recommendation:** Add integration tests for all 5 missing cases before deployment. Estimated effort: 2-3 hours.

**Overall Assessment:** Code is 75% production-ready. Fix the 3 HIGH security issues from Hulubalang and add the 5 missing test cases.`,

      `📊 **Test Results Summary**

**Passed:** 23/32 tests (72%)
**Failed:** 5/32 tests (missing implementations)
**Skipped:** 4/32 tests (need mock infrastructure)

**Blocking issues:**
- test_expired_token_rejection — FAIL (token doesn't actually expire)
- test_rate_limit_enforcement — FAIL (limiter not connected to Redis)
- test_concurrent_logins — FAIL (no lock mechanism)

**Non-blocking:**
- test_password_complexity — PASS ✅
- test_jwt_signature_validation — PASS ✅
- test_error_message_safety — PASS ✅ (no stack traces leaked)

**Verdict:** NOT READY for production. Fix 3 blocking issues first. Estimated time: 4 hours.`,
    ],
  },
  panglima: {
    secure_api: [
      `⚔️ **Orchestrator Synthesis**

**Final Verdict: PROCEED WITH MODIFICATIONS**

**Summary of Multi-Agent Review:**
- 🔧 Tukang: Built solid JWT auth foundation with bcrypt + rate limiting
- 🛡️ Hulubalang: Found 3 security issues (2 CRITICAL, 1 HIGH)
- ✅ Penyemak: 75% production-ready, 5 test gaps identified

**Action Items (Priority Order):**
1. **[CRITICAL]** Add token blacklisting for true logout capability
2. **[CRITICAL]** Implement CSRF protection middleware
3. **[HIGH]** Add account lockout after 5 failed attempts
4. **[HIGH]** Add 5 missing integration tests
5. **[MEDIUM]** Add security headers (CSP, X-Frame-Options)

**Estimated Time:** 4-6 hours
**Confidence:** HIGH — All agents agree on critical issues
**Next Step:** Assign to Tukang for fixes, re-review by Hulubalang`,

      `⚔️ **Final Verdict — Auth API Review**

**Decision: CONDITIONAL APPROVAL**

The code is solid but needs 3 critical fixes before it touches production.

**What went well:**
- Tukang's architectural decisions were sound (bcrypt, rate limiting, no hardcoded secrets)
- Hulubalang's security review was thorough and actionable
- Penyemak's test coverage analysis identified real gaps

**What needs work:**
- Token lifecycle management (no blacklisting, no rotation)
- CSRF protection missing on state-changing endpoints
- Test coverage below the 80% threshold

**Go/No-Go: NO-GO** until critical items 1-2 are resolved.

I'm assigning this back to Tukang with a 6-hour deadline. Hulubalang will re-review within 1 hour of fix submission.`,
    ],
    incident_response: [
      `⚔️ **Incident Response — Commander's Summary**

**Status: CONTAINED**

**Timeline:**
- 02:14 — Attack detected (automated alert triggered)
- 02:16 — Attack blocked (rate limiting held)
- 02:30 — Root cause identified (leaked service token)
- 02:45 — Full containment deployed (tokens rotated, pipeline patched)

**Impact Assessment:**
- User data: NOT compromised ✅
- Financial data: NOT compromised ✅
- Service disruption: 31 minutes ⚠️
- Reputation risk: LOW (internal detection, no public exposure)

**Lessons Learned:**
1. Rate limiting SAVED us — validate this investment quarterly
2. Base64-encoded secrets slip through scanners — fix immediately
3. Service accounts need mandatory rotation — implement within 48 hours

**Confidence:** HIGH
**Escalation:** No executive notification needed — contained before impact.`,
    ],
    architecture_debate: [
      `⚔️ **Architectural Verdict — Panglima's Decision**

After reviewing both positions, here is my ruling:

**VERDICT: MODULAR MONOLITH with microservices-ready infrastructure**

**Rationale:**

Tukang is RIGHT about:
- Team size (5 engineers) doesn't justify microservices overhead
- Deployment complexity is a real cost
- "Earn your complexity" is the correct philosophy

Syahbandar is RIGHT about:
- Security isolation requirements (PCI-DSS)
- Independent scaling needs for auth endpoints
- Operational tooling should be built early

**My decision:**
1. Build a monolith for Q1-Q2
2. BUT containerize each module independently from day one
3. Set up the full microservices CI/CD pipeline now
4. Monitor each module's resource usage independently
5. Extract to microservices when we hit: 10+ engineers OR 100K+ daily active users

**This gives us:** Tukang's simplicity NOW + Syahbandar's scalability LATER.

Both agents presented strong cases. The compromise honors both perspectives.`,
    ],
  },
};

// ─── Helper ───────────────────────────────────────────────────────────────────

function getRandomResponse(agentKey: string, scenarioId: string): string {
  const pool = RESPONSE_POOL[agentKey]?.[scenarioId];
  if (!pool || pool.length === 0) return `${agentKey} is processing the task...`;
  return pool[Math.floor(Math.random() * pool.length)];
}

// ─── Page Component ───────────────────────────────────────────────────────────

export default function GelanggangPage() {
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0]);
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
    setMessages([{ role: "system", content: `🏛️ Gelanggang Panglima initialized\nScenario: ${selectedScenario.title}\nPattern: ${selectedScenario.pattern}\nAgents: ${selectedScenario.agents.map(id => DEMO_AGENTS.find(a => a.id === id)?.icon + " " + DEMO_AGENTS.find(a => a.id === id)?.name).join(" → ")}` }]);

    const agentIds = selectedScenario.agents;

    for (let i = 0; i < agentIds.length; i++) {
      const agentId = agentIds[i];
      const agent = DEMO_AGENTS.find(a => a.id === agentId)!;

      setLoadingAgents([agentId]);
      setCurrentStep(i + 1);

      await new Promise(r => setTimeout(r, 800 + Math.random() * 600));

      const agentKey = agent.name.toLowerCase();
      const content = getRandomResponse(agentKey, selectedScenario.id);

      setMessages(prev => [...prev, {
        role: "agent",
        agent: agent,
        content: content,
        timestamp: new Date().toLocaleTimeString(),
      }]);

      setLoadingAgents([]);
      await new Promise(r => setTimeout(r, 400 + Math.random() * 300));
    }

    setFinalResult("✅ Collaboration complete. All agents have contributed.");
    setIsRunning(false);
  };

  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* ─── Nav ──────────────────────────────────────────────────── */}
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
        {/* ─── Hero ───────────────────────────────────────────────── */}
        <section className="text-center space-y-4">
          <h1 className="text-4xl font-bold gradient-text">⚔️ Gelanggang Panglima</h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-400">
            Pick a scenario, watch agents from different LLM providers communicate, debate, and decide — all orchestrated by Panglima.
          </p>
        </section>

        {/* ─── Scenario Selector ──────────────────────────────────── */}
        <section className="grid gap-4 md:grid-cols-3">
          {SCENARIOS.map((scenario) => (
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
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{scenario.patternIcon}</span>
                <span className="text-xs rounded-full border border-white/10 px-2 py-0.5 text-neutral-400">{scenario.pattern}</span>
              </div>
              <h3 className="font-semibold text-white mb-1">{scenario.title}</h3>
              <p className="text-xs text-cyan-300 mb-2">{scenario.subtitle}</p>
              <p className="text-sm text-neutral-400 mb-3">{scenario.description}</p>
              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-1">
                  {scenario.agents.map(id => {
                    const agent = DEMO_AGENTS.find(a => a.id === id);
                    return agent ? (
                      <span key={id} className="text-xs rounded-full border px-1.5 py-0.5" style={{ borderColor: agent.color + "40", color: agent.color }}>
                      <AgentIcon name={agent.icon} size={14} color={agent.color} /> {agent.name}
                      </span>
                    ) : null;
                  })}
                </div>
                <span className="text-xs text-neutral-600">{scenario.estimatedTime}</span>
              </div>
            </button>
          ))}
        </section>

        {/* ─── Run Button ─────────────────────────────────────────── */}
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
            {isRunning ? `⏳ Step ${currentStep}/${selectedScenario.agents.length} — ${DEMO_AGENTS.find(a => a.id === selectedScenario.agents[currentStep - 1])?.icon} ${DEMO_AGENTS.find(a => a.id === selectedScenario.agents[currentStep - 1])?.name} is thinking...` : "🏛️ Start Gelanggang"}
          </button>
          {!isRunning && messages.length > 1 && (
            <button onClick={runDemo} className="ml-3 rounded-xl border border-white/10 px-6 py-4 text-base font-medium text-white transition hover:bg-white/10">
              🔄 Rerun (new responses)
            </button>
          )}
        </div>

        {/* ─── Agent Status Bar ───────────────────────────────────── */}
        <section className="flex flex-wrap justify-center gap-4">
          {DEMO_AGENTS.map((agent) => {
            const isActive = loadingAgents.includes(agent.id);
            const hasSpoken = messages.some(m => m.agent?.id === agent.id);
            const isInvolved = selectedScenario.agents.includes(agent.id);
            return (
              <div
                key={agent.id}
                className={`flex items-center gap-2 rounded-xl border px-4 py-2 transition ${
                  isActive ? "border-cyan-400/50 bg-cyan-400/10" :
                  hasSpoken ? "border-emerald-400/30 bg-emerald-400/5" :
                  isInvolved ? "border-white/10 bg-white/[0.02]" : "border-white/5 bg-white/[0.01] opacity-40"
                }`}
              >
                <AgentIcon name={agent.icon} size={20} color={agent.color} />
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

        {/* ─── Conversation Feed ──────────────────────────────────── */}
        <section className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 min-h-[400px] max-h-[600px] overflow-y-auto">
          {messages.length <= 1 && !isRunning && (
            <div className="flex flex-col items-center justify-center h-64 text-neutral-500">
              <span className="text-4xl mb-4">🏛️</span>
              <p className="text-center">Select a scenario above and click "Start Gelanggang" to watch agents communicate.</p>
              <p className="text-xs text-neutral-600 mt-2">Each run generates randomized responses for variety.</p>
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
                    <AgentIcon name={msg.agent.icon} size={24} color={msg.agent.color} />
                    <div>
                      <span className="font-semibold" style={{ color: msg.agent.color }}>{msg.agent.name}</span>
                      <span className="ml-2 text-xs text-neutral-500">{msg.agent.provider}/{msg.agent.model}</span>
                      <span className="ml-2 text-xs text-neutral-600">{msg.timestamp}</span>
                    </div>
                    <div className="ml-auto">
                      <span className="text-xs rounded-full border px-2 py-0.5 text-neutral-400 border-white/10">
                        LLM-to-LLM #{i}
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
            <div className="rounded-xl border border-white/10 bg-black/20 p-4 flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-sm text-cyan-300">
              <AgentIcon name={DEMO_AGENTS.find(a => a.id === loadingAgents[0])?.icon || "panglima"} size={20} color="#00E5FF" /> {DEMO_AGENTS.find(a => a.id === loadingAgents[0])?.name} is generating response...
              </span>
            </div>
          )}

          {finalResult && (
            <div className="rounded-xl bg-emerald-400/5 border border-emerald-400/20 px-4 py-3 text-center">
              <span className="text-emerald-300 font-medium">{finalResult}</span>
              <p className="text-xs text-neutral-500 mt-1">Click "Rerun" to see different randomized responses.</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </section>

        {/* ─── How It Works ───────────────────────────────────────── */}
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
