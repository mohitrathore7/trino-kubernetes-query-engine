import re

import pytest

from tqe.bench import queries_dir, render
from tqe.config import Settings
from tqe.load import TABLES, create_table_sql
from tqe.report import Summary, human_bytes, median, pct_reduction, to_markdown

S = Settings(schema="lake", scale="sf1")


def test_partitioned_table_sql_has_partitioning_and_sort():
    sql = create_table_sql(S, TABLES[0])
    assert "iceberg.lake.lineitem\n" in sql
    assert "partitioning = ARRAY['month(shipdate)']" in sql
    assert "sorted_by = ARRAY['orderkey']" in sql
    assert sql.endswith("FROM tpch.sf1.lineitem")


def test_flat_table_sql_has_no_layout_properties():
    sql = create_table_sql(S, TABLES[0], flat=True)
    assert "iceberg.lake.lineitem_flat" in sql
    assert "partitioning" not in sql and "sorted_by" not in sql


@pytest.mark.parametrize("flat", [True, False])
def test_every_query_renders_without_leftover_placeholders(flat):
    files = sorted(queries_dir().glob("*.sql"))
    assert len(files) >= 5
    for f in files:
        sql = render(f.read_text(), S, flat=flat)
        assert not re.search(r"\{\w+\}", sql), f.name
        assert ("lineitem_flat" in sql or "orders_flat" in sql) == flat, f.name


def test_pct_reduction():
    assert pct_reduction(100, 70) == pytest.approx(30.0)
    assert pct_reduction(100, 120) == pytest.approx(-20.0)
    assert pct_reduction(0, 5) == 0.0


def test_median_and_bytes():
    assert median([3, 1, 2]) == 2
    with pytest.raises(ValueError):
        median([])
    assert human_bytes(2048) == "2.0 KB"


def test_markdown_report_contains_overall_line():
    md = to_markdown([Summary("q1", 200, 100, 4096, 1024)], {"Workers": "3"})
    assert "| q1 | 200 | 100 | -50.0% |" in md
    assert "Overall latency reduction (sum of medians): 50.0%" in md
