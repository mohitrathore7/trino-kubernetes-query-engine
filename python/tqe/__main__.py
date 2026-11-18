"""CLI: python -m tqe {load,bench,all} [options]"""

from __future__ import annotations

import argparse
import dataclasses

from .bench import bench
from .client import TrinoClient
from .config import Settings
from .load import load


def main() -> None:
    parser = argparse.ArgumentParser(prog="tqe", description=__doc__)
    parser.add_argument("command", choices=["load", "bench", "all"])
    parser.add_argument("--schema", help="Iceberg schema (Glue database on AWS)")
    parser.add_argument("--scale", help="TPC-H scale, e.g. sf1, sf10, sf100")
    parser.add_argument("--runs", type=int, default=5, help="measured runs per query")
    parser.add_argument("--workers", type=int, default=3, help="workers to wait for")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    settings = Settings.from_env()
    overrides = {k: v for k, v in {"schema": args.schema, "scale": args.scale}.items() if v}
    settings = dataclasses.replace(settings, **overrides)

    client = TrinoClient(settings)
    print(f"Waiting for {args.workers} workers at {settings.host}:{settings.port} ...")
    print(f"{client.wait_for_workers(args.workers)} workers active")
    client.close()

    if args.command in ("load", "all"):
        load(settings)
    if args.command in ("bench", "all"):
        bench(settings, runs=args.runs, results_dir=args.results_dir)


if __name__ == "__main__":
    main()
