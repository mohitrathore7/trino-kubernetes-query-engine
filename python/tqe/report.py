"""Pure functions that summarise benchmark runs (kept separate so they are unit-testable)."""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class Summary:
    query: str
    baseline_ms: float
    optimized_ms: float
    baseline_bytes: int
    optimized_bytes: int

    @property
    def latency_reduction_pct(self) -> float:
        return pct_reduction(self.baseline_ms, self.optimized_ms)

    @property
    def bytes_reduction_pct(self) -> float:
        return pct_reduction(self.baseline_bytes, self.optimized_bytes)


def pct_reduction(before: float, after: float) -> float:
    """Percentage drop from `before` to `after` (negative means it got slower)."""
    if before <= 0:
        return 0.0
    return (before - after) / before * 100


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("no measurements")
    return float(statistics.median(values))


def to_markdown(summaries: list[Summary], meta: dict[str, str]) -> str:
    lines = ["# Benchmark results", ""]
    lines += [f"- **{k}**: {v}" for k, v in meta.items()]
    lines += [
        "",
        "| Query | Baseline (ms) | Optimized (ms) | Latency change "
        "| Baseline scanned | Optimized scanned | Scan change |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        lines.append(
            f"| {s.query} | {s.baseline_ms:,.0f} | {s.optimized_ms:,.0f} | "
            f"{-s.latency_reduction_pct:+.1f}% | {human_bytes(s.baseline_bytes)} | "
            f"{human_bytes(s.optimized_bytes)} | {-s.bytes_reduction_pct:+.1f}% |"
        )

    if summaries:
        total_before = sum(s.baseline_ms for s in summaries)
        total_after = sum(s.optimized_ms for s in summaries)
        lines += [
            "",
            f"**Overall latency reduction (sum of medians): "
            f"{pct_reduction(total_before, total_after):.1f}%**",
        ]
    return "\n".join(lines) + "\n"


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} TB"
