"""Run JEBAT autoMimpi dream consolidation + selflearn analysis.

Consolidates ~/.jebat/memory/traces.json (strengthen/prune), builds a
learning profile, and emits suggestions. Safe to run any time.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jebat.features.memory import EnhancedMemorySystem  # noqa: E402
from jebat.features.memory.automimpi import create_automimpi, create_selflearn  # noqa: E402


async def main():
    mem = EnhancedMemorySystem()
    mem._load()
    print(f"[autoMimpi] loaded {len(mem.traces)} traces from {mem.traces_file}")

    automimpi = create_automimpi(mem)
    report = await automimpi.dream(force=True)

    print("\n=== DREAM REPORT ===")
    print(f"memories_processed:      {report.memories_processed}")
    print(f"patterns_extracted:      {report.patterns_extracted}")
    print(f"generalizations_created: {report.generalizations_created}")
    print(f"memories_pruned:         {report.memories_pruned}")
    print(f"dream_count:             {report.dream_count if hasattr(report,'dream_count') else 'n/a'}")
    print(f"quote: {report.laksamana_quote}")

    if report.suggestions:
        print("\n=== SUGGESTIONS ===")
        for s in report.suggestions:
            print(f"- [{s.urgency}] {s.title}: {s.reason} {f'-> {s.action}' if s.action else ''}")

    # Persist consolidated traces
    mem._save()
    print("\n[autoMimpi] consolidated traces saved.")

    # SelfLearn analysis snapshot
    selflearn = create_selflearn(mem)
    analysis = selflearn.analyze()
    print("\n=== SELFLEARN ANALYSIS ===")
    print(json.dumps({
        k: analysis.get(k) for k in ["skill_levels", "knowledge_map", "velocity", "retention", "recommendations"]
    } if isinstance(analysis, dict) else analysis, indent=2, default=str)[:3000])


if __name__ == "__main__":
    asyncio.run(main())
