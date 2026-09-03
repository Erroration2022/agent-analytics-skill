"""Tests for scripts/run_bq.py query parameter binding."""

from datetime import datetime, timezone

from scripts.run_bq import build_query_parameters


def test_binds_start_end_when_present():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 8, tzinfo=timezone.utc)
    sql = "SELECT 1 WHERE timestamp BETWEEN @start AND @end"
    params = build_query_parameters(sql, start, end, None)
    names = {p.name for p in params}
    assert names == {"start", "end"}


def test_binds_trace_id_when_present():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 8, tzinfo=timezone.utc)
    sql = "SELECT 1 WHERE trace_id = @trace_id"
    params = build_query_parameters(sql, start, end, "trace-abc")
    assert len(params) == 1
    assert params[0].name == "trace_id"
    assert params[0].value == "trace-abc"


def test_skips_unused_parameters():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 8, tzinfo=timezone.utc)
    sql = "SELECT COUNT(*) FROM t"
    params = build_query_parameters(sql, start, end, "trace-abc")
    assert params == []
