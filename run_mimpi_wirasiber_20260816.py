"""Seed WiraSiber VPS incident session traces (2026-08-16), then run autoMimpi dream + selflearn."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jebat.features.memory import EnhancedMemorySystem, MemoryType  # noqa: E402
from jebat.features.memory.automimpi import create_automimpi, create_selflearn  # noqa: E402

SESSION_TRACES = [
    {
        "content": "[WiraSiber][gotcha] VPS 'unreachable' was 3 stacked faults, NOT a network issue. (1) dist/index.html referenced index-Bjj-2d2f.js but the file was MISSING from dist/assets (broken deploy Aug 8) -> browser shell loads, app never boots, console 404. (2) nginx /api proxied to 127.0.0.1:3000 which was sharavenan-lawfirm's next-server; wirasiber server.cjs actually listens on :4000 -> ALL API calls hit wrong service. (3) Cloudflare edge had pinned the 404 (cf-cache-status HIT, browser_cache_ttl=14400 + cache_level=aggressive). Verify origin with Host-header curl (curl -H 'Host: wirasiber.my' https://127.0.0.1/...) to separate origin vs edge failures.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:gotcha", "vps", "cloudflare", "nginx", "project"},
        "importance": 0.85,
    },
    {
        "content": "[WiraSiber][gotcha] VPS deploy worktree gotcha: src/constants.ts was DELETED on the VPS working tree (git status ' D src/constants.ts'). Fix: git checkout -- src/constants.ts BEFORE building, otherwise tsc fails. This is a recurring trap on this VPS.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:gotcha", "vps", "deploy", "project"},
        "importance": 0.7,
    },
    {
        "content": "[WiraSiber][gotcha] Cloudflare purge API denied -> token is READ-ONLY. All write operations fail: POST /zones/{id}/purge_cache (Auth error 10000), PUT cache ruleset entrypoint (Auth error 10000), user/tokens list (9109 Unauthorized). Workaround for stale 404-pinned assets: bump app version (package.json + index.html meta + SW VERSION const + a bundled source constant so the bundle hash rotates) -> rebuild -> new hashed filename bypasses the stale edge entry. To write: need Zone->Cache Purge->Purge, Zone->Cache Rules->Edit, Zone->Zone Settings->Edit scopes on the MCP token.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:gotcha", "cloudflare", "cache", "mcp", "project"},
        "importance": 0.8,
    },
    {
        "content": "[WiraSiber][command] Cloudflare MCP diagnostics that work read-only: GET /zones?per_page=100 (list all), GET /zones/{id}/settings/ssl|min_tls_version|security_header|cache_level|edge_cache_ttl|browser_cache_ttl, GET /zones/{id}/rulesets (phases), GET /zones/{id}/dns_records. Detect stale edge 404 via curl -sI and grep cf-cache-status: HIT. Root 404 causes: cache_level=aggressive + no cache rules + browser_cache_ttl=14400 pins error responses.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:command", "cloudflare", "mcp", "project"},
        "importance": 0.7,
    },
    {
        "content": "[JEBAT][gotcha] jebat-api pm2 crash-loop (45 restarts, errored, empty logs) root causes: (1) .venv was a broken COPY from local Windows machine - uvicorn shebang pointed to '/home/humm1ngb1rd/Desktop/Jebat Online/.venv/bin/python3' (path not found on server) and venv lib was python3.14 while binary was 3.12.3. (2) pm2 script used 'python' which does NOT exist on Ubuntu 24.04 (only python3). (3) uvicorn port 8080 was already taken by stalwart (mail server). Fix: apt install python3.12-venv, rebuild venv with /usr/bin/python3 -m venv + pip install -r requirements.prod.txt, run via pm2 on port 8082 with .venv/bin/python.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:JEBAT", "category:gotcha", "pm2", "venv", "vps", "deploy", "project"},
        "importance": 0.85,
    },
    {
        "content": "[JEBAT][convention] jebat-core production API on VPS runs via pm2 name 'jebat-api', cwd /var/www/jebat-core, command .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8082 --workers 4. Health: GET http://127.0.0.1:8082/ returns {'service':'jebat-api','version':'8.2.1','status':'running'}. LLM: ollama qwen3:8b. Port 8080 belongs to stalwart mail - never reassign it.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:JEBAT", "category:convention", "pm2", "vps", "api", "project"},
        "importance": 0.7,
    },
    {
        "content": "[WiraSiber][command] PowerShell->SSH quoting hell on win32: double-quoted remote commands get mangled (grep patterns with $ and quotes fail, node -e breaks). Robust pattern: write a .sh script locally -> scp to /tmp -> ssh 'bash /tmp/script.sh'. Single-quote the remote command string so $ expands on remote bash only. Backup nginx config (cp sites-available/wirasiber.my .bak) BEFORE sed editing.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:command", "ssh", "powershell", "workflow", "project"},
        "importance": 0.75,
    },
    {
        "content": "[NusaByte][environment] Cloudflare fleet = 5 zones: wirasiber.my, jebat.online, nusabyte.my, prodigylearning.com.my, serambitiffin.my. ALL share identical weak posture: cache_level=aggressive, NO cache rules, min_tls=1.0, HSTS disabled. jebat.online + nusabyte.my use Cloudflare Tunnel CNAMEs (*.cfargotunnel.com). SECURITY FINDING: auth.nusabyte.my -> 72.62.255.206 is NOT proxied (origin IP exposed, no WAF). Cache rule template: /assets/* -> override TTL 86400 immutable; /api/* -> cache:false; / -> cache:false.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:NusaByte", "category:environment", "cloudflare", "security", "dns", "project"},
        "importance": 0.8,
    },
    {
        "content": "[WiraSiber][gotcha] wirasiber.my nginx /api proxy_pass target: the SPA is served by nginx (root /var/www/wirasiber-academy/dist) but /api proxies to server.cjs. server.cjs reads src/server/config.cjs for port (currently 4000). When adding another Node service on the same VPS, its port lands on 3000+ causing wire-crossing. Always verify the listening port of the target app (ss -ltnp | grep pid) BEFORE trusting the nginx proxy target.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:gotcha", "nginx", "proxy", "ports", "project"},
        "importance": 0.75,
    },
    {
        "content": "[WiraSiber][gotcha] Timezone bug: password_reset_expires and email_verification_expires columns are 'timestamp without time zone' but server.cjs wrote JS Date objects (serialized UTC via toISOString). On UTC+8 VPS the expiry lands ~8h in the past -> EVERY reset/verification token instantly 'expired'. Symptom: hash matches but 'Reset token has expired' / 'Verification token has expired'. Fix: compute expiry in SQL - NOW() + ($n * interval '1 millisecond') - so Postgres stores naive-local wall time that matches the column type and the JS comparison (node-postgres parses naive timestamp as local). 3 sites: registration INSERT, resend-verification, forgot-password. Commit 9d392cd.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:gotcha", "timezone", "postgres", "auth", "tokens", "project"},
        "importance": 0.85,
    },
    {
        "content": "[WiraSiber][gotcha] Email service was SILENTLY disabled: .env had zero SMTP_* keys so emailService.initialize() returned false (nodemailer SMTP-backed, NOT Resend API). Every verification/reset email 'sent' as emailSent:false in response but user never receives anything. Fix: wired Resend SMTP - SMTP_HOST=smtp.resend.com, SMTP_PORT=587, SMTP_USER=resend, SMTP_PASS=<resend api key>, SMTP_FROM=\"WiraSiber Academy\" <noreply@wirasiber.my>. Requires Resend domain verification (resend._domainkey TXT + send MX/SPF + _dmarc in the AUTHORITATIVE zone - CF for wirasiber.my). pm2 restart --update-env needed after .env change.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:gotcha", "email", "smtp", "resend", "deploy", "project"},
        "importance": 0.8,
    },
    {
        "content": "[NusaByte][command] Cloudflare API token format: 'cfat_' prefixed tokens do NOT verify via GET /user/tokens/verify (returns code 1000 Invalid API Token) but WORK fine for real API calls (zones, dns_records, purge_cache, rulesets). Verify a cfat_ token by listing zones instead. Also: token permissions are visible per-zone in the zone object's permissions array (#dns_records:edit, #cache_purge:edit, #zone_settings:edit, #ssl:edit). Wrote all 5-zone hardening with a single cfat_ token: cache rules entrypoint (PUT /zones/{id}/rulesets/phases/http_request_cache_settings/entrypoint), min_tls_version 1.2, HSTS security_header, purge_cache, proxied auth.nusabyte.my.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:NusaByte", "category:command", "cloudflare", "api", "token", "project"},
        "importance": 0.75,
    },
    {
        "content": "[WiraSiber][command] Resend DNS verification records for wirasiber.my must go in the AUTHORITATIVE zone = Cloudflare (NS anna/major.ns.cloudflare.com), NOT Hostinger (domain's registrar zone is a dead-end for writes - accepted but never resolves). Hostinger MCP delete tool doesn't expose the required filters param, so dead duplicate records can't be removed via MCP. Record set: resend._domainkey TXT (DKIM public key), send MX priority 10 -> feedback-smtp.ap-northeast-1.amazonses.com, send TXT 'v=spf1 include:amazonses.com ~all', _dmarc TXT 'v=DMARC1; p=none;'.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:WiraSiber", "category:command", "dns", "resend", "cloudflare", "project"},
        "importance": 0.7,
    },
]


async def main():
    mem = EnhancedMemorySystem()
    mem._load()
    before = len(mem.traces)
    print(f"[seed] store loaded: {before} traces from {mem.traces_file}")

    existing = set()
    for t in mem.traces.values():
        existing.add(t.content.split("]")[0] if "]" in t.content else t.content)

    added = 0
    for tr in SESSION_TRACES:
        marker = tr["content"].split("[")[2].split("]")[0] if tr["content"].startswith("[") else tr["content"][:40]
        if any(marker in e for e in existing):
            print(f"[seed] SKIP (already present): {marker}")
            continue
        await mem.remember(
            tr["content"],
            memory_type=tr["memory_type"],
            tags=tr["tags"],
            importance=tr["importance"],
        )
        added += 1
        print(f"[seed] added: {marker}")

    mem._save()
    print(f"[seed] saved. {before} -> {len(mem.traces)} traces (+{added})")

    automimpi = create_automimpi(mem)
    report = await automimpi.dream(force=True)

    print("\n=== DREAM REPORT ===")
    print(f"memories_processed:      {report.memories_processed}")
    print(f"patterns_extracted:      {report.patterns_extracted}")
    print(f"generalizations_created: {report.generalizations_created}")
    print(f"memories_pruned:         {report.memories_pruned}")
    if report.suggestions:
        print("\n=== SUGGESTIONS ===")
        for s in report.suggestions:
            print(f"- [{s.urgency}] {s.title}: {s.reason} {f'-> {s.action}' if s.action else ''}")

    mem._save()
    print("\n[autoMimpi] consolidated traces saved.")

    selflearn = create_selflearn(mem)
    analysis = selflearn.analyze()
    print("\n=== SELFLEARN ANALYSIS ===")
    out = analysis if isinstance(analysis, dict) else analysis
    if isinstance(out, dict):
        for k in ["skill_levels", "knowledge_map", "velocity", "retention", "recommendations"]:
            print(f"{k}: {json.dumps(out.get(k), indent=2, default=str)[:1200]}")
    else:
        print(str(out)[:3000])


if __name__ == "__main__":
    asyncio.run(main())
