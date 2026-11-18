"""Load TPC-H data into Iceberg tables stored as Parquet on S3.

Two copies of each fact table are written so the benchmark can compare them:

* ``<table>``       - partitioned by month and sorted on the join key (optimized)
* ``<table>_flat``  - same rows, no partitioning or sorting (baseline)
"""

from __future__ import annotations

from dataclasses import dataclass

from .client import TrinoClient
from .config import Settings


@dataclass(frozen=True)
class TableSpec:
    name: str
    source: str
    partitioning: tuple[str, ...] = ()
    sorted_by: tuple[str, ...] = ()
    flat_copy: bool = True


TABLES: tuple[TableSpec, ...] = (
    TableSpec("lineitem", "lineitem", partitioning=("month(shipdate)",), sorted_by=("orderkey",)),
    TableSpec("orders", "orders", partitioning=("month(orderdate)",), sorted_by=("orderkey",)),
    TableSpec("customer", "customer", flat_copy=False),
    TableSpec("nation", "nation", flat_copy=False),
)


def _array(values: tuple[str, ...]) -> str:
    return "ARRAY[" + ", ".join(f"'{v}'" for v in values) + "]"


def create_table_sql(settings: Settings, spec: TableSpec, flat: bool = False) -> str:
    """Build the CREATE TABLE AS statement for one table."""
    props = ["format = 'PARQUET'"]
    if not flat:
        if spec.partitioning:
            props.append(f"partitioning = {_array(spec.partitioning)}")
        if spec.sorted_by:
            props.append(f"sorted_by = {_array(spec.sorted_by)}")

    target = settings.table(f"{spec.name}_flat" if flat else spec.name)
    return (
        f"CREATE TABLE IF NOT EXISTS {target}\n"
        f"WITH ({', '.join(props)})\n"
        f"AS SELECT * FROM tpch.{settings.scale}.{spec.source}"
    )


def load(settings: Settings) -> None:
    client = TrinoClient(settings)
    try:
        client.run(f"CREATE SCHEMA IF NOT EXISTS {settings.catalog}.{settings.schema}")
        for spec in TABLES:
            variants = [False, True] if spec.flat_copy else [False]
            for flat in variants:
                sql = create_table_sql(settings, spec, flat=flat)
                name = f"{spec.name}_flat" if flat else spec.name
                print(f"-> loading {name} from tpch.{settings.scale}.{spec.source}")
                client.run(sql)

        for spec in TABLES:
            count = client.run(f"SELECT count(*) FROM {settings.table(spec.name)}").rows[0][0]
            print(f"   {spec.name:<10} {count:>12,} rows")
    finally:
        client.close()
