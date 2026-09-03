"""Seed today's (2026-08-24) Erawan-QSys session traces, then run autoMimpi dream + selflearn."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jebat.features.memory import EnhancedMemorySystem, MemoryType  # noqa: E402
from jebat.features.memory.automimpi import create_automimpi, create_selflearn  # noqa: E402

SESSION_TRACES = [
    {
        "content": "[Erawan-QSys][feature] Gantt fit-based zoom law (2026-08-24, commit 56f79cb): replaced the fixed PX_PER_MIN=4.5 scalar zoom with one fit-based scale law px/min = (containerW/WORK_MIN) x zoomScale, where 100% IS the whole day fitting the container. ZOOM_STEPS [0.25..8]; SCALE_FOCUS 1.25->3 (old 1.25 of the 4.5 base was ~3.5x fit). Fit mode is just zoomScale===1 with zero pads, so zooming never desyncs fit from the ladder. Ruler/block ladders recalibrated for honest overview rungs.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:feature", "feature:gantt-zoom", "project"},
        "importance": 0.8,
    },
    {
        "content": "[Erawan-QSys][gotcha] Active-session overrun overlap FALSE positive (2026-08-24, commit 7eff1d4, Fon/EAK-003539): an active assignment that overran its scheduled endsAt is drawn with blockEnd=now (live extension); feeding that speculative end into detectOverlaps flagged an overlap against an adjacent future block (DB gap 68s, no true overlap). Fix: SessionBlock.scheduledEndMin (pre-extension scheduled end) threaded through buildBlock only when live-extended; detectOverlaps compares the SCHEDULED window via effEnd() for both overlap + room overbooking, keeping endMin extended for display. Real concurrent conflicts still flag.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:gotcha", "feature:live-matrix", "project"},
        "importance": 0.85,
    },
    {
        "content": "[Erawan-QSys][feature] POS checkout guard + receipt sign/colour (2026-08-24, commit d06db20): PROCEED TO CHECKOUT disabled + click-guarded when selectedPaymentItems.length===0 (not just cart empty) - was opening receipt with everything auto-selected via openPayment fallback. Discount + Receipt Discount rows pass NEGATIVE to formatRMAligned (sign inside the fixed-width field) so they show -RM.. matching print receipt. Payment hero RECEIVED colour-coded (emerald paid, dimmed 0), + REMAINING red row.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:feature", "feature:pos-checkout", "project"},
        "importance": 0.8,
    },
    {
        "content": "[Erawan-QSys][feature] Auto-issue therapist ticket on payment (2026-08-24, commit b5346b3): removed the manual Ticket button from PrintReceiptModal; PaymentModal.process() (single + multi both funnel here) enriches the captured receipt with masseurId/masseurName/masseurCode/roomCode/durationMinutes from cart items then calls openTherapistTicketWindow(receipt) on success. Pressure is CHECKBOX-ONLY - renderTicketHtml(t, null) prints an unchecked [ ] Hard [ ] Medium [ ] Soft strip for the therapist to tick with the clientele; window auto-prints on load + closes after print. NOTE: 'cronjob' implemented event-driven (server @Cron/BullMQ can't reach a browser printer - no ESC-POS relay). Allow popups for the app origin.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:feature", "feature:therapist-ticket", "project"},
        "importance": 0.85,
    },
    {
        "content": "[Erawan-QSys][command] Deploy batch scoping (2026-08-24): a change batch touching ONLY apps/web/* + apps/api/* needs NO @erawan/core build and NO prisma generate/migrate deploy. Confirm which packages changed before running the core/prisma steps - don't over-build. PM2 restart -> brief 502; wait ~10s then verify, do NOT panic-retry. Remote HEAD may already be at your local HEAD even without you building (someone/CI pulled) - always verify builds + SW version, not just git log.",
        "memory_type": MemoryType.SEMANTIC,
        "tags": {"project:Erawan-QSys", "category:command", "feature:deploy", "project"},
        "importance": 0.75,
    },
    {
        "content": "[Erawan-QSys][gotcha] PrintReceiptModal 'Ticket' button was broken before 2026-08-24: it passed the limited onCaptured receipt (only name/detail/qty/price, no masseur/room) to openTherapistTicketWindow, which filtered i.masseurName||i.roomCode -> empty serviceItems -> returned early (printed nothing). The therapist ticket only actually printed from the standalone ReceiptModal (rich receipt). Enriching the process() receipt with cart masseur/room fixed it AND enabled the auto-print. Lesson: verify a print path's receipt actually carries the fields the renderer needs.",
        "memory_type": MemoryType.EPISODIC,
        "tags": {"project:Erawan-QSys", "category:gotcha", "feature:therapist-ticket", "project"},
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
        existing.add(t.content.strip())

    added = 0
    for tr in SESSION_TRACES:
        marker = tr["content"].split("[")[2].split("]")[0] if tr["content"].startswith("[") else tr["content"][:40]
        if tr["content"].strip() in existing:
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
