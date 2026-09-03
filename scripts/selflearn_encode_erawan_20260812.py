"""selfLearn encode: durable facts from 2026-08-12 Erawan session.

Encodes the Mena stale-active incident learnings into ~/.jebat/memory/traces.json
with project:Erawan-QSys + category tags, then re-runs selflearn analyze.
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
        "Erawan-QSys assignment availability: assignmentConflictWhere() in apps/api/src/common/assignment-availability.ts scopes by businessDate (derived from candidate startsAt MYT via toMYTDateString, or explicit extra.businessDate) since aa0eb92. Stale active/paused assignments from PREVIOUS business days never block today's windows. Same-day stale-endsAt guard (EAK-001773) preserved.",
        "gotcha", 0.9,
    ),
    (
        "Erawan-QSys stale assignment diagnosis: therapist 'free' in live queue but masseur_busy on pin = check Assignment rows with status IN ('active','paused') AND businessDate < today. Close manually: completed when commission credited, else stopped. Live queue (queue.service.ts getLiveQueue) scopes by businessDate; conflict checks now do too.",
        "gotcha", 0.9,
    ),
    (
        "Erawan-QSys StaleAssignmentSweeper (apps/api/src/assignments/stale-assignment.sweeper.ts, commit 98db147): nightly 01:30 MYT cron via @nestjs/schedule + POST /assignments/sweep-stale manual trigger (owner/manager). Closes stale active/paused rows: completed if commission entry exists (session ran+paid), else stopped. PRESERVES planned endsAt — never stamp now onto old rows (would inflate report duration). Writes masseur waiting event, completes booking when all items terminal + any ran, event+audit logs. Idempotent.",
        "stack", 0.85,
    ),
    (
        "Erawan-QSys prod SSH one-shot commands: never 'sudo -E env PATH=$PATH pnpm --filter' in a single ssh arg (env eats --filter). Use: ssh ... \"sudo -H -u root bash -lc 'export NVM_DIR=/usr/local/nvm; . /usr/local/nvm/nvm.sh; cd /opt/erawanQPOS-v2 && pnpm ...'\". pm2 must run via sudo -H -u root (root-owned pm2 home).",
        "command", 0.9,
    ),
    (
        "Erawan-QSys prod DB access: no local psql. Pipe SQL via stdin: compose SQL to temp LF file locally, then 'Get-Content -Raw file | ssh ... \"docker exec -i erawanqpos-postgres-1 psql -U erawan -d erawan_qsys\"'. Never inline SQL through pwsh double-quoted strings (backtick is pwsh escape char). Multi-command remote scripts over SSH pipe truncate output — one command per ssh call or per-step scripts.",
        "command", 0.85,
    ),
    (
        "Erawan-QSys prod topology: Hostinger dual-stack erawanhq, IPv6 2a02:4780:5e:20bd::1 (ssh -6 -i ~/.ssh/id_ed25519-hostinger opsadmin@...), IPv4 72.60.42.163, domain qpos.erawanwellness.com. V2 checkout /opt/erawanQPOS-v2, pm2 erawan-api-v2 (4001) + erawan-web-v2 (5501), nginx 443. DB docker erawanqpos-postgres-1 on 127.0.0.1:5433. Repo+pm2 root-owned (sudo git/pm2). 72.62.254.65 is NOT production.",
        "environment", 0.9,
    ),
    (
        "Erawan-QSys queue ranking is ENFORCED from packages/core/src/index.ts — SERVED_STATUSES, COMMISSION_EXCLUDED_STATUSES, compareQueueCandidates, buildQueueCandidate, rankQueueCandidates. NEVER re-inline status arrays in apps/api; import from @erawan/core. Same workflow wired into queue, bookings, live-matrix, recommendations, ai-ops, dashboard-agent services.",
        "convention", 0.9,
    ),
    (
        "Erawan-QSys POS session-start retry semantics: checkout groups by guestIndex::masseurId; pinned masseur/room dropped ONLY when conflicting, then auto-pick fills. masseur_busy on pin → drop masseur pin, keep room. Errors surface as 'No available therapist/room' after both pins dropped.",
        "stack", 0.75,
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
                tags={"project:Erawan-QSys", f"category:{category}", "project", category},
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
