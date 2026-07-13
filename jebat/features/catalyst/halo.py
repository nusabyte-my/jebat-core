"""Catalyst O11y — HALO Analysis Engine."""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .models import CatalystTrace, SpanKind, SpanStatus


@dataclass
class HaloConfig:
    """HALO analysis configuration."""
    regression_threshold_pct: float = 10.0
    anomaly_zscore: float = 3.0
    min_spans_for_analysis: int = 5
    critical_path_weight: float = 1.0


@dataclass
class SpanStats:
    """Statistical summary of a span type."""
    count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    mean_duration_ms: float = 0.0
    median_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    std_dev_ms: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0


@dataclass
class TraceComparison:
    """Comparison between two traces."""
    trace_a: CatalystTrace
    trace_b: CatalystTrace
    span_diff: int = 0
    duration_diff_ms: float = 0.0
    duration_change_pct: float = 0.0
    span_stats_a: dict[str, SpanStats] = field(default_factory=dict)
    span_stats_b: dict[str, SpanStats] = field(default_factory=dict)
    regressions: list[dict[str, Any]] = field(default_factory=list)
    improvements: list[dict[str, Any]] = field(default_factory=list)
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class HALOAnalyzer:
    """Hierarchical Analysis of Latent Operations."""

    def __init__(self, config: Optional[HaloConfig] = None):
        self.config = config or HaloConfig()

    def analyze_traces(
        self,
        trace_a: CatalystTrace,
        trace_b: CatalystTrace,
        analysis_type: str = "full",
    ) -> TraceComparison:
        """Compare two traces (baseline vs current)."""
        comparison = TraceComparison(
            trace_a=trace_a,
            trace_b=trace_b,
        )

        # Basic comparison
        comparison.span_diff = len(trace_b.spans) - len(trace_a.spans)
        comparison.duration_diff_ms = trace_b.duration_ms - trace_a.duration_ms
        comparison.duration_change_pct = (
            (comparison.duration_diff_ms / trace_a.duration_ms * 100)
            if trace_a.duration_ms > 0 else 0
        )

        # Compute span statistics
        comparison.span_stats_a = self._compute_span_stats(trace_a)
        comparison.span_stats_b = self._compute_span_stats(trace_b)

        if analysis_type in ("full", "performance"):
            comparison.regressions = self._detect_regressions(comparison)
            comparison.improvements = self._detect_improvements(comparison)

        if analysis_type in ("full", "anomaly"):
            comparison.anomalies = self._detect_anomalies(trace_b)

        comparison.recommendations = self._generate_recommendations(comparison)

        return comparison

    def _compute_span_stats(self, trace: CatalystTrace) -> dict[str, SpanStats]:
        """Compute statistics per span name."""
        stats: dict[str, SpanStats] = defaultdict(SpanStats)

        for span in trace.spans:
            s = stats[span.name]
            s.count += 1
            s.total_duration_ms += span.duration_ms
            s.min_duration_ms = min(s.min_duration_ms, span.duration_ms)
            s.max_duration_ms = max(s.max_duration_ms, span.duration_ms)
            if span.status == SpanStatus.ERROR:
                s.error_count += 1

        # Calculate derived stats
        for name, s in stats.items():
            if s.count > 0:
                s.mean_duration_ms = s.total_duration_ms / s.count
                s.error_rate = s.error_count / s.count

                # Get all durations for percentiles
                durations = [sp.duration_ms for sp in trace.spans if sp.name == name]
                durations.sort()
                n = len(durations)
                s.median_duration_ms = durations[n // 2]
                s.p50_duration_ms = durations[n // 2]
                s.p95_duration_ms = durations[int(n * 0.95)] if n > 0 else 0
                s.p99_duration_ms = durations[int(n * 0.99)] if n > 0 else 0

                if n > 1:
                    s.std_dev_ms = statistics.stdev(durations)

        return dict(stats)

    def _detect_regressions(self, comp: TraceComparison) -> list[dict[str, Any]]:
        """Detect performance regressions."""
        regressions = []
        threshold = self.config.regression_threshold_pct

        for name, stats_b in comp.span_stats_b.items():
            stats_a = comp.span_stats_a.get(name)
            if not stats_a or stats_a.count < self.config.min_spans_for_analysis:
                continue

            # Compare mean durations
            if stats_a.mean_duration_ms > 0:
                change_pct = ((stats_b.mean_duration_ms - stats_a.mean_duration_ms)
                              / stats_a.mean_duration_ms * 100)
                if change_pct > threshold:
                    regressions.append({
                        "span": name,
                        "metric": "mean_duration_ms",
                        "baseline": stats_a.mean_duration_ms,
                        "current": stats_b.mean_duration_ms,
                        "change_pct": round(change_pct, 2),
                        "severity": "high" if change_pct > threshold * 2 else "medium",
                    })

            # Compare error rates
            if stats_b.error_rate > stats_a.error_rate + 0.05:  # 5% increase
                regressions.append({
                    "span": name,
                    "metric": "error_rate",
                    "baseline": stats_a.error_rate,
                    "current": stats_b.error_rate,
                    "change_pct": round((stats_b.error_rate - stats_a.error_rate) * 100, 2),
                    "severity": "high",
                })

            # Compare P99
            if stats_a.p99_duration_ms > 0:
                p99_change = ((stats_b.p99_duration_ms - stats_a.p99_duration_ms)
                              / stats_a.p99_duration_ms * 100)
                if p99_change > threshold:
                    regressions.append({
                        "span": name,
                        "metric": "p99_duration_ms",
                        "baseline": stats_a.p99_duration_ms,
                        "current": stats_b.p99_duration_ms,
                        "change_pct": round(p99_change, 2),
                        "severity": "medium",
                    })

        return regressions

    def _detect_improvements(self, comp: TraceComparison) -> list[dict[str, Any]]:
        """Detect performance improvements."""
        improvements = []
        threshold = self.config.regression_threshold_pct

        for name, stats_a in comp.span_stats_a.items():
            stats_b = comp.span_stats_b.get(name)
            if not stats_b or stats_b.count < self.config.min_spans_for_analysis:
                continue

            if stats_a.mean_duration_ms > 0:
                change_pct = ((stats_b.mean_duration_ms - stats_a.mean_duration_ms)
                              / stats_a.mean_duration_ms * 100)
                if change_pct < -threshold:
                    improvements.append({
                        "span": name,
                        "metric": "mean_duration_ms",
                        "baseline": stats_a.mean_duration_ms,
                        "current": stats_b.mean_duration_ms,
                        "change_pct": round(change_pct, 2),
                    })

        return improvements

    def _detect_anomalies(self, trace: CatalystTrace) -> list[dict[str, Any]]:
        """Detect anomalous spans using z-score."""
        anomalies = []

        # Group by span name
        spans_by_name: dict[str, list[float]] = defaultdict(list)
        for span in trace.spans:
            spans_by_name[span.name].append(span.duration_ms)

        for name, durations in spans_by_name.items():
            if len(durations) < 3:
                continue

            mean = statistics.mean(durations)
            stdev = statistics.stdev(durations) if len(durations) > 1 else 0

            if stdev == 0:
                continue

            zscore_threshold = self.config.anomaly_zscore

            for span in trace.spans:
                if span.name == name:
                    zscore = abs(span.duration_ms - mean) / stdev
                    if zscore > zscore_threshold:
                        anomalies.append({
                            "span_id": span.id,
                            "span_name": name,
                            "duration_ms": span.duration_ms,
                            "mean_ms": mean,
                            "stdev_ms": stdev,
                            "zscore": round(zscore, 2),
                            "attributes": span.attributes,
                        })

        return anomalies

    def _generate_recommendations(self, comp: TraceComparison) -> list[str]:
        """Generate optimization recommendations."""
        recs = []

        # Overall regression
        if comp.duration_change_pct > self.config.regression_threshold_pct:
            recs.append(
                f"Overall trace duration increased by {comp.duration_change_pct:.1f}%. "
                f"Investigate top regressions."
            )

        # Span count increase
        if comp.span_diff > comp.trace_a.spans * 0.2:
            recs.append(
                f"Span count increased by {comp.span_diff} ({comp.span_diff/len(comp.trace_a.spans)*100:.1f}%). "
                f"Check for redundant instrumentation or loops."
            )

        # LLM-specific
        llm_spans_a = [s for s in comp.trace_a.spans if s.kind == SpanKind.LLM]
        llm_spans_b = [s for s in comp.trace_b.spans if s.kind == SpanKind.LLM]

        if llm_spans_b:
            avg_llm_a = statistics.mean([s.duration_ms for s in llm_spans_a]) if llm_spans_a else 0
            avg_llm_b = statistics.mean([s.duration_ms for s in llm_spans_b])

            if avg_llm_b > 5000:
                recs.append(f"High LLM latency: avg {avg_llm_b:.0f}ms. Consider prompt compression or caching.")

            if len(llm_spans_b) > len(llm_spans_a) * 1.5:
                recs.append(f"LLM call count increased significantly. Check for missing cache or repeated calls.")

        # Tool-specific
        tool_spans_b = [s for s in comp.trace_b.spans if s.kind == SpanKind.TOOL]
        if tool_spans_b:
            tool_errors = [s for s in tool_spans_b if s.status == SpanStatus.ERROR]
            if len(tool_errors) / len(tool_spans_b) > 0.05:
                recs.append(f"Tool error rate >5%. Check tool implementations and error handling.")

        # Memory/agent
        agent_spans_b = [s for s in comp.trace_b.spans if s.kind == SpanKind.AGENT]
        if len(agent_spans_b) > 20:
            recs.append(f"High agent span count ({len(agent_spans_b)}). Consider agent consolidation.")

        if not recs:
            recs.append("No significant issues detected.")

        return recs


def run_halo_analysis(
    trace_a: CatalystTrace,
    trace_b: CatalystTrace,
    analysis_type: str = "full",
    config: Optional[HaloConfig] = None,
) -> TraceComparison:
    """Convenience function for HALO analysis."""
    analyzer = HALOAnalyzer(config)
    return analyzer.analyze_traces(trace_a, trace_b, analysis_type)