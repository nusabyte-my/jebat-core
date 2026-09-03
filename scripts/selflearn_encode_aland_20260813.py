"""selfLearn encode: durable facts from 2026-08-13 ALAND highrise session.

Encodes the ALAND highrise feasibility calculator session learnings into
~/.jebat/memory/traces.json with project:ALAND + category tags, then
re-runs selflearn analyze.
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jebat.features.memory import EnhancedMemorySystem  # noqa: E402
from jebat.features.memory.automimpi import create_selflearn  # noqa: E402

FACTS = [
    # (content, category, importance)
    (
        "ALAND prod topology: Hostinger VPS 187.127.204.89 (domain alandfeasi.tech). IPv4:22 is fail2ban-DROPped from dev box -> ALL deploys use IPv6 root@2a02:4780:5e:a100::1 with key ~/.ssh/id_ed25519-hostinger. Webroot /var/www/ALAND/packages/frontend/dist (nginx static), backend /var/www/ALAND/packages/backend/dist pm2 aland-backend :3001. DB PostgreSQL 16 native :5432. nginx needs BOTH listen 80/443 and listen [::]:80/443 (IPv6 listen added 2026-08-13, backup /root/alandfeasi.nginx.bak-20260813; keep backup OUT of sites-enabled or nginx -t fails).",
        "environment", 0.9,
    ),
    (
        "ALAND deploy flow (Windows/pwsh, IPv6): pnpm build -> scp packages/frontend/dist/* to /tmp/aland-deploy/fe/ then cp -r to /var/www/ALAND/packages/frontend/dist/ -> scp backend dist -> cp -> pm2 restart aland-backend -> verify curl -sI https://alandfeasi.tech (200) + https://alandfeasi.tech/api/health (200). Never use the .sh deploy script on Windows (pwsh mis-executes bash; WSL can't run pnpm shim). .ps1 sleeps between sessions to dodge fail2ban burst-block (~45s on 3+ rapid connections).",
        "command", 0.85,
    ),
    (
        "ALAND service-worker cache trap: after each frontend deploy, bump SW version (alandfeasi-v5 on 2026-08-13) in packages/frontend/public/sw.js so clients purge the stale cached shell. Users must hard-refresh / incognito once to see updates; otherwise they see the old bundle even though the server is serving the new one.",
        "gotcha", 0.9,
    ),
    (
        "ALAND HR engine lock numbers (FS- High Rise v2 workbook, cell-for-cell): GDC 193,146,807 / profit 31,895,393.38 (14.17%) / CFA 622,327 / NFA 309,900 / cost/GFA 310.36 / cost/NFA 623.26. Landed v2: GDC 406,279,824.92 / profit -41,812,074.92. Engine is hard-locked to the cent by packages/frontend/src/lib/engine-lock.test.ts (both modes).",
        "stack", 0.9,
    ),
    (
        "ALAND workbook-parity testing pattern: workbooks (FS- High Rise v2 / Landed v2 xlsx) are gitignored -> tests reading them skip on clean CI (describeIf fileExists). Parity tests use vi.mock of CalcContext + renderToStaticMarkup on the rendered DOM, asserting exact formatted cells. Display-vs-engine lesson: rendered DOM can disagree with engine totals even when engine tests pass (B2/B5/B9 display bugs in GDC table were only caught by DOM parity tests, not engine locks).",
        "convention", 0.85,
    ),
    (
        "ALAND GDC table display bugs fixed 2026-08-13 (commit 591dc8d): B2 service_residence water rows must render (279,000/183,600/108,800), retail water floors=1 (16,800/18,900/21,000), electricity rows SR-first; B5 tower/retail GFA sourced from building-area (315,625/71,750) with podium sf 234,952 from engine; B9 town planner must NOT be clamped (shows -10.14 ac / -RM 20,280 negative). All GDC buckets B1-B11 + SUMMARY + Results have rendered-DOM parity tests (gdc-parity.test.tsx, summary-table-parity, results-section-parity).",
        "gotcha", 0.85,
    ),
    (
        "ALAND editable-input UX rule: any source input must have VISIBLE border (border-slate-200) + white bg, or users can't tell it's editable (transparent borders looked read-only to the owner). Apply to every editable cell/table: HighRiseMixTable, podium tables, density/plot-ratio/building-area estimates, GDV table, retail divisors. Each table has an integration test asserting editability + parity.",
        "convention", 0.8,
    ),
    (
        "ALAND architecture (pnpm monorepo): packages/frontend (React+Vite+Tailwind), packages/backend (Express+tRPC+Drizzle, port 3001), packages/shared (feasibility engine + types). Dev: pnpm dev -> frontend :5175 / backend :3001. Commands: pnpm check / lint / build / test / db:push. Trunk-based git: branch off main, conventional commits, PR into main (protected, CI verify job + 1 review). Canonical remote github.com/nusabyte-my/ALAND-Production.git. Git push occasionally fails transient DNS (Could not resolve host) - retry once after DNS recovers.",
        "stack", 0.85,
    ),
    (
        "ALAND registration auth fix (commit fc8ae26): upsertUser in packages/backend/server/db.ts must write passwordHash/googleId/emailVerified from a whitelist (not bare destructure) - previously dropped passwordHash so registered users could not log in. Live-verified register->login with a temp user (deleted after).",
        "gotcha", 0.8,
    ),
]


async def main():
    mem = EnhancedMemorySystem()
    mem._load()
    print(f"[selfLearn] loaded {len(mem.traces)} traces before encode")

    for content, category, importance in FACTS:
        try:
            trace = await mem.remember(
                content,
                memory_type="semantic",
                tags={"project:ALAND", f"category:{category}", "project", category},
                importance=importance,
            )
            print(f"[+] encoded {trace.trace_id[:8]} ({category}, imp={importance})")
        except Exception as e:
            print(f"[-] FAILED: {e}")

    mem._save()
    print(f"[selfLearn] saved {len(mem.traces)} traces total")

    selflearn = create_selflearn(mem)
    analysis = selflearn.analyze()
    print("\n=== SELFLEARN ANALYSIS ===")
    print(json.dumps({
        "total_memories": analysis.get("knowledge_map", {}).get("total_memories") if isinstance(analysis, dict) else None,
        "coverage": analysis.get("knowledge_map", {}).get("coverage") if isinstance(analysis, dict) else None,
        "recommendations": analysis.get("recommendations") if isinstance(analysis, dict) else None,
    }, indent=2, default=str)[:2500])


if __name__ == "__main__":
    asyncio.run(main())
