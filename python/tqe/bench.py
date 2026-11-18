"""Benchmark: unpartitioned tables vs. partition pruning + predicate pushdown.

Each query in ``queries/`` runs against two setups:

* **baseline**  - ``*_flat`` tables (no partitions, unsorted), dynamic filtering off
* **optimized** - month-partitioned, sorted tables, dynamic filtering on

Every query is run ``runs`` times per setup after one warm-up, and the median
wall-clock latency and bytes scanned are reported.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .client import TrinoClient
from .config import Settings
from .report import Summary, median, to_markdown

BASELINE_SESSION = {"enable_dynamic_filtering": "false"}
OPTIMIZED_SESSION = {"enable_dynamic_filtering": "true"}

PARTITIONED_TABLES = ("lineitem", "orders")
SHARED_TABLES = ("customer", "nation")


def queries_dir() -> Path:
    env = os.getenv("QUERIES_DIR")
    candidates = [Path(env)] if env else []
    here = Path(__file__).resolve()
    candidates += [here.parents[2] / "queries", here.parents[1] / "queries"]
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError("queries/ directory not found; set QUERIES_DIR")


def table_names(settings: Settings, flat: bool) -> dict[str, str]:
    names = {t: settings.table(f"{t}_flat" if flat else t) for t in PARTITIONED_TABLES}
    names.update({t: settings.table(t) for t in SHARED_TABLES})
    return names


def render(template: str, settings: Settings, flat: bool) -> str:
    return template.format(**table_names(settings, flat)).strip().rstrip(";")


def _measure(client: TrinoClient, sql: str, runs: int) -> tuple[float, int]:
    client.run(sql)  # warm-up (metadata + file listing caches)
    results = [client.run(sql) for _ in range(runs)]
    latency = median([r.elapsed_ms for r in results])
    scanned = int(median([r.processed_bytes for r in results]))
    return latency, scanned


def bench(settings: Settings, runs: int = 5, results_dir: str = "results") -> list[Summary]:
    baseline = TrinoClient(settings, BASELINE_SESSION)
    optimized = TrinoClient(settings, OPTIMIZED_SESSION)
    workers = optimized.run("SELECT count(*) FROM system.runtime.nodes WHERE coordinator = false").rows[0][0]

    summaries: list[Summary] = []
    try:
        for path in sorted(queries_dir().glob("*.sql")):
            template = path.read_text()
            b_ms, b_bytes = _measure(baseline, render(template, settings, flat=True), runs)
            o_ms, o_bytes = _measure(optimized, render(template, settings, flat=False), runs)
            s = Summary(path.stem, b_ms, o_ms, b_bytes, o_bytes)
            summaries.append(s)
            print(
                f"{s.query:<28} baseline {b_ms:>8.0f} ms | optimized {o_ms:>8.0f} ms "
                f"| latency -{s.latency_reduction_pct:.1f}% | scanned -{s.bytes_reduction_pct:.1f}%"
            )
    finally:
        baseline.close()
        optimized.close()

    meta = {
        "Dataset": f"TPC-H {settings.scale} as Iceberg/Parquet",
        "Workers": str(workers),
        "Runs per query": f"{runs} (median, after 1 warm-up)",
    }
    out = Path(results_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark.md").write_text(to_markdown(summaries, meta))
    (out / "benchmark.json").write_text(
        json.dumps({"meta": meta, "queries": [s.__dict__ for s in summaries]}, indent=2)
    )
    print(f"\nWrote {out / 'benchmark.md'}")
    return summaries
