"""Seed Jentayu (ThreadBot) arc traces — 2026-08-22 sessions 11-16 — then dream + selflearn.

Covers: competitor teardown, PWA-vs-native verdict, Postgres cutover, engine build,
two live-smoke bugs, a11y fix, content cluster. Idempotent via marker dedupe.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jebat.features.memory import EnhancedMemorySystem, MemoryType  # noqa: E402
from jebat.features.memory.automimpi import create_automimpi, create_selflearn  # noqa: E402

SESSION_TRACES = [
    {
        "content": "[Jentayu][competitive-intel] Threads scheduler landscape (scraped 2026-08-22): Typefully = no mobile app at all (Mac only) yet 10k customers; Buffer = $26.1M ARR open books, native apps both stores but mobile is companion-only; Postiz = OSS AGPL 34.5k stars, NO mobile UI + responsive issues #740/#1008 open since Oct 2025 (community built postiz-mobile), self-host free vs hosted $29+; Publer = price floor $4-8/mo; Metricool = Ionic-wrapped web app to both stores, own docs say planning stays on web. ALL FIVE shipped agentic surfaces in 2026 (MCP/CLI). Nobody owns Threads-specific autopilot or advertises anti-double-post guarantees. Profiles in ThreadBot/competitor-profiles/.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Jentayu", "category:competitive-intel", "project"},
        "importance": 0.85,
    },
    {
        "content": "[Jentayu][decision] Mobile strategy verdict: PWA-first dashboard + Bubblewrap TWA for Play presence ($25 one-time) + defer native Kotlin behind triggers (Lane B revenue / widgets / offline queue). Rationale: scheduler MUST be server-side anyway (Doze/OEM killers kill background cron), client is control-panel-only, zero hardware needs, Typefully proves mobile optional while Postiz proves skipping it creates visible pain. Metricool precedent ships wrapped web app to both stores.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Jentayu", "category:decision", "feature:pwa", "project"},
        "importance": 0.85,
    },
    {
        "content": "[Jentayu][decision] DB = PostgreSQL via postgres.js on Bun. Decisive reason: VPS .65 ALREADY runs PG (Stalwart mail), Lane B stack is Supabase = Postgres so migration never happens, JSONB fits payload, partial indexes identical to SQLite plan. Rejected MariaDB (no edge) and node-embedded (no real constraints -> cannot guarantee idempotency). Schema: migrations table versioned, CHECK enums on status/media_type, UNIQUE idempotency_key on posts, partial indexes idx_posts_queue/idx_posts_retry, rate_events rolling window.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Jentayu", "category:decision", "feature:database", "project"},
        "importance": 0.8,
    },
    {
        "content": "[Jentayu][gotcha] First live-smoke found two bugs: (1) decryptToken ran BEFORE the dry-run branch in scheduler.ts - placeholder token rows crashed GCM decrypt even in dry-run. Fix: move decrypt inside the else (real-publish) branch. Lesson: dry-run paths must not require real secrets. (2) UPDATE referenced phantom column jitter_note that never existed in migration 1 - caught by psql last_error check. Lesson: grep schema DDL before writing new columns into UPDATE statements.",
        "memory_type": MemoryType.EPISODIC,
        "tags": {"project:Jentayu", "category:gotcha", "feature:scheduler", "project"},
        "importance": 0.8,
    },
    {
        "content": "[Jentayu][command] Engine verification = `bun run smoke` (scripts/smoke.ts, dev-safe env defaults): 8 checks - db+migrations, settings seed, account present, queue->publish round-trip under dry-run, published count increment, DUPLICATE idempotency_key INSERT rejected by PG (the guarantee proven as failing-insert test), MCP initialize handshake over real stdio spawn, tools/list returns 5 tools (utus_status/queue/pause/resume/run_once). Green = drum beats true. MCP wire format: line-delimited JSON-RPC, content-before-url gotcha does NOT apply here.",
        "memory_type": MemoryType.PROCEDURAL,
        "tags": {"project:Jentayu", "category:command", "feature:smoke", "project"},
        "importance": 0.8,
    },
    {
        "content": "[Jentayu][convention] Design system locked in DESIGN.md: Linear App v2.3.0 base via needmcp (slug linear-app, the ONLY style available there) + Jentayu Warmth pastel chip extension + Gestalt layout section (proximity-first, whitespace-over-dividers). All 12 pastel pairs MEASURED pass AA (light 4.71-5.70, dark 7.74-10.61). Radius tokens in @theme generate custom utilities (rounded-btn works in TW4). A11y blocker fixed: Switch needs ariaLabel prop when visible label empty (schedule rows were unnamed switches, WCAG 4.1.2). Landing page follows authentic-product-representation: real smoke-run transcript verbatim incl dry- prefix post id.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Jentayu", "category:convention", "feature:design-system", "project"},
        "importance": 0.75,
    },
]


async def main():
    mem = EnhancedMemorySystem()
    mem._load()
    before = len(mem.traces)
    print(f"[seed] store loaded: {before} traces from {mem.traces_file}")

    # Dedupe on FULL stored content against unique per-trace markers.
    # (Prefix-based markers collided across sessions - "gotcha"/"command" are generic.)
    existing = set()
    for t in mem.traces.values():
        existing.add(t.content)

    MARKERS = [
        "Threads scheduler landscape (scraped 2026-08-22)",   # competitive-intel
        "Mobile strategy verdict",                             # decision: PWA/TWA/native
        "DB = PostgreSQL via postgres.js",                     # decision: database
        "First live-smoke found two bugs",                     # gotcha: decrypt+jitter_note
        "Engine verification = `bun run smoke`",               # command: smoke suite
        "Design system locked in DESIGN.md",                   # convention: Linear Pastel
    ]
    assert len(MARKERS) == len(SESSION_TRACES)

    added = 0
    for tr, marker in zip(SESSION_TRACES, MARKERS):
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

    # Mirror dream state to workspace copy (same discipline as run_mimpi_dream.py)
    try:
        ws_state = Path(__file__).resolve().parent / "memory" / ".dream-state.json"
        ws_state.write_text(json.dumps({
            "lastDreamAt": automimpi.last_dream_at.isoformat() if automimpi.last_dream_at else None,
            "lastScanAt": automimpi.last_dream_at.isoformat() if automimpi.last_dream_at else None,
            "sessionsSinceDream": 0,
            "totalDreams": automimpi.dream_count,
        }, indent=2), encoding="utf-8")
        print("[autoMimpi] workspace dream-state mirrored.")
    except Exception as e:
        print(f"[autoMimpi] WARNING: workspace mirror failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
