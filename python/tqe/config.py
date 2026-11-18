"""Runtime settings, read from environment variables with sensible local defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = "localhost"
    port: int = 8080
    user: str = "tqe"
    catalog: str = "iceberg"
    schema: str = "tpch_lake"
    scale: str = "sf1"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            host=os.getenv("TRINO_HOST", cls.host),
            port=int(os.getenv("TRINO_PORT", cls.port)),
            user=os.getenv("TRINO_USER", cls.user),
            catalog=os.getenv("TRINO_CATALOG", cls.catalog),
            schema=os.getenv("TRINO_SCHEMA", cls.schema),
            scale=os.getenv("TPCH_SCALE", cls.scale),
        )

    def table(self, name: str) -> str:
        """Fully qualified table name, e.g. iceberg.tpch_lake.lineitem."""
        return f"{self.catalog}.{self.schema}.{name}"
