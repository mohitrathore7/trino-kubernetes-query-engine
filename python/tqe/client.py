"""Thin wrapper around the Trino DB-API client that also returns query statistics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import trino

from .config import Settings


@dataclass
class QueryResult:
    rows: list[tuple[Any, ...]]
    elapsed_ms: float
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def processed_bytes(self) -> int:
        return int(self.stats.get("processedBytes", 0))

    @property
    def processed_rows(self) -> int:
        return int(self.stats.get("processedRows", 0))

    @property
    def completed_splits(self) -> int:
        return int(self.stats.get("completedSplits", 0))


class TrinoClient:
    def __init__(self, settings: Settings, session_properties: dict[str, str] | None = None):
        self.settings = settings
        self._conn = trino.dbapi.connect(
            host=settings.host,
            port=settings.port,
            user=settings.user,
            catalog=settings.catalog,
            schema=settings.schema,
            session_properties=session_properties or {},
        )

    def run(self, sql: str) -> QueryResult:
        cur = self._conn.cursor()
        start = time.perf_counter()
        cur.execute(sql)
        rows = cur.fetchall()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return QueryResult(rows=rows, elapsed_ms=elapsed_ms, stats=dict(cur.stats or {}))

    def wait_for_workers(self, expected: int, timeout_s: int = 300) -> int:
        """Block until `expected` active workers have joined the cluster."""
        deadline = time.time() + timeout_s
        sql = "SELECT count(*) FROM system.runtime.nodes WHERE coordinator = false AND state = 'active'"
        while True:
            try:
                active = self.run(sql).rows[0][0]
            except Exception:  # coordinator still starting
                active = 0
            if active >= expected:
                return active
            if time.time() > deadline:
                raise TimeoutError(f"only {active}/{expected} workers active after {timeout_s}s")
            time.sleep(5)

    def close(self) -> None:
        self._conn.close()
