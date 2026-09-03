"""Seed today's missed-key session traces, then run autoMimpi dream + selflearn."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jebat.features.memory import EnhancedMemorySystem, MemoryType  # noqa: E402
from jebat.features.memory.automimpi import create_automimpi, create_selflearn  # noqa: E402

SESSION_TRACES = [
    {
        "content": "[Erawan-QSys][feature] Missed Key Entry (2026-08-10): POST /bookings/missed-key — atomic batch; each entry creates Booking->BookingItem->Assignment->CommissionEntry->Payment in one transaction. Assignment status = completed when window elapsed, active while running; booking status mirrors. Payment computed SERVER-SIDE from package price (net /1.08 + SST + round RM0.05) — FD never types amounts. Skips no-busy/queue checks (retroactive) but keeps duplicate guard. POS header 'Missed Key' amber button + add-row modal. Commits c46901a/3240d9b.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:feature", "feature:missed-key", "project"},
        "importance": 0.8,
    },
    {
        "content": "[Erawan-QSys][gotcha] Retroactive paths need completed-aware helpers: computeNextSubRoom and assignmentConflictWhere only count BUSY statuses (scheduled/recommended/confirmed/active/paused) — built for FUTURE scheduling. Missed-key assignments are COMPLETED (the session already ran), so reusing those helpers made two same-batch A1 entries both land on A1a. Fix: inline sub-room pick + duplicate guard in missedKey with wider status set [scheduled..completed] + true window overlap (startsAt < endsAt && endsAt > startsAt). Same trap hit the duplicate guard (assignmentConflictWhere excludes completed — exactly what gets re-keyed).",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:gotcha", "feature:missed-key", "project"},
        "importance": 0.85,
    },
    {
        "content": "[Erawan-QSys][convention] Missed-key duplicate guard caught a REAL conflict in production: On's claimed Thai 20:34 overlapped his actual HBS EAK-002422 (F2, 19:51-21:05 MYT, unpaid). Owner confirmed the Thai was real -> cancelled the unpaid HBS (kept as audit row, reversible), forfeited its commission (+1800/-1800 = net 0), wrote EventLog 'missed_key_reconcile', then keyed the Thai (EAK-002435). The guard's value: it forced an explicit owner decision instead of silently double-booking a masseur. Keyed 4 sessions total (Lee/Lisa/Chai/On, RM602.50, all completed, cash).",
        "memory_type": MemoryType.EPISODIC,
        "tags": {"project:Erawan-QSys", "category:convention", "feature:missed-key", "project"},
        "importance": 0.75,
    },
    {
        "content": "[Erawan-QSys][command] Nested sudo breaks: `sudo -H -u root bash -lc '... sudo -H -u root env PATH=\\$PATH pm2 restart ...'` fails with 'env: restart: No such file or directory'. One sudo layer per command: build in one bash -lc, pm2 restart as its OWN top-level SSH command. Also: PowerShell eats $VAR in double-quoted SSH strings — use single-quoted outer or compose locally + pipe.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:command", "project"},
        "importance": 0.7,
    },
    {
        "content": "[Erawan-QSys][gotcha] Verify retroactive/backfill writes against REAL existing records before trusting them: Thiam's overlapping Foot45 session (A1a, 11:51-13:05 UTC) was only visible because the prod DB was queried before/after the write. The missed-key sub-room bug (both Lee and Lisa on A1a) was caught the same way — a fresh SELECT after the POST showed the collision. Dry-probe overlaps first; the guard is only as good as the data it sees.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:gotcha", "feature:missed-key", "project"},
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
