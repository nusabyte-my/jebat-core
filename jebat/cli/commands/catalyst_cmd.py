"""
Catalyst command — Inference.net Catalyst integration for tracing, gateway, signals, evals, training.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any


def catalyst_command(args: Any) -> int:
    """Inference.net Catalyst integration commands."""
    subcommand = getattr(args, "catalyst_command", None)

    if subcommand == "init":
        return _init_catalyst(args)
    elif subcommand == "status":
        return _catalyst_status(args)
    elif subcommand == "instrument":
        return _instrument_jebat(args)
    elif subcommand == "trace":
        return _create_trace(args)
    elif subcommand == "eval":
        return _eval(args)
    elif subcommand == "train":
        return _train(args)
    elif subcommand == "halo":
        return _halo(args)
    else:
        print("Usage: jebat catalyst {init|status|instrument|trace|eval|train|halo}")
        print()
        print("Commands:")
        print("  init        Initialize Catalyst with API key")
        print("  status      Check Catalyst integration status")
        print("  instrument  Auto-instrument JEBAT agent loop")
        print("  trace       Create a trace span")
        print("  eval        Run evaluation")
        print("  train       Train custom model")
        print("  halo        Run HALO analysis on traces")
        return 1


def _init_catalyst(args: Any) -> int:
    """Initialize Catalyst integration."""
    from jebat.features.catalyst import initialize_catalyst, CatalystConfig

    config = CatalystConfig(
        api_key=args.api_key or "",
        project_id=args.project_id or "",
        enable_gateway=args.gateway,
        sample_rate=args.sample_rate,
    )

    async def run():
        try:
            await initialize_catalyst(config)
            print("Catalyst initialized successfully!")
            print(f"  Tracing: enabled")
            print(f"  Gateway: {config.enable_gateway}")
            print(f"  Signals: {len(config.signals)}")
            print(f"  Sample rate: {config.sample_rate}")
        except Exception as e:
            print(f"Error initializing Catalyst: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _catalyst_status(args: Any) -> int:
    """Check Catalyst integration status."""
    from jebat.features.catalyst import is_catalyst_available, get_catalyst

    available = is_catalyst_available()
    catalyst = get_catalyst()

    print(f"Catalyst SDK available: {available}")
    if catalyst:
        print(f"Initialized: {catalyst._initialized}")
        print(f"Tracing: {catalyst.config.enable_tracing}")
        print(f"Gateway: {catalyst.config.enable_gateway}")
        print(f"Signals: {len(catalyst.config.signals)}")
    return 0


def _instrument_jebat(args: Any) -> int:
    """Auto-instrument JEBAT agent loop."""
    from jebat.features.catalyst import get_catalyst

    catalyst = get_catalyst()
    result = catalyst.instrument_jebat()

    print("JEBAT auto-instrumented with Catalyst")
    print("Hooks: agent_loop, tool_dispatch, llm_generate, session")
    return 0


def _create_trace(args: Any) -> int:
    """Create a trace span."""
    import json
    from jebat.features.catalyst import get_catalyst

    catalyst = get_catalyst()
    attrs = json.loads(args.attrs) if args.attrs else {}
    span = catalyst.trace(args.name, attrs)

    print(f"Trace created: {args.name}")
    print("Usage: with context manager or call span.set_attribute() / span.end()")
    return 0


def _eval(args: Any) -> int:
    """Run evaluation."""
    import json
    from jebat.features.catalyst import get_catalyst

    catalyst = get_catalyst()
    rubric = {"criteria": {"quality": "rate 1-5", "accuracy": "rate 1-5"}}

    async def run():
        eval_id = await catalyst.create_eval(
            name="jebat-eval",
            dataset_id=args.dataset,
            rubric=rubric,
            model_ids=args.models or [],
        )
        print(f"Evaluation created: {eval_id}")

        if args.models:
            for model_id in args.models:
                result = await catalyst.run_eval(eval_id, model_id)
                print(f"  {model_id}: {json.dumps(result, indent=2)}")

    asyncio.run(run())
    return 0


def _train(args: Any) -> int:
    """Train custom model."""
    import json
    from jebat.features.catalyst import get_catalyst

    catalyst = get_catalyst()
    config = json.loads(args.config) if hasattr(args, 'config') else {}

    async def run():
        job_id = await catalyst.create_training_job(
            name=args.name,
            dataset_id=args.dataset,
            base_model=args.base_model,
            config=config,
        )
        print(f"Training job created: {job_id}")

    asyncio.run(run())
    return 0


def _halo(args: Any) -> int:
    """Run HALO analysis on traces."""
    from jebat.features.catalyst import get_catalyst

    catalyst = get_catalyst()

    async def run():
        result = await catalyst.analyze_with_halo(args.traces, args.type)
        print(f"HALO Analysis Complete ({len(args.traces)} traces)")
        print(f"Type: {args.type}")
        if result.get("report"):
            print(f"\nReport:\n{result['report']}")
        if result.get("improvements"):
            print(f"\nImprovements:")
            for imp in result["improvements"]:
                print(f"  - {imp}")

    asyncio.run(run())
    return 0


__all__ = ["catalyst_command"]