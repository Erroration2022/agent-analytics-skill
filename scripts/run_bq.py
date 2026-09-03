#!/usr/bin/env python3
"""Lightweight BigQuery executor for agent analytics queries.

Usage:
    python scripts/run_bq.py "SELECT ..."
    python scripts/run_bq.py --dry-run "SELECT ..."
    python scripts/run_bq.py --max-gb 5 "SELECT ..."
    python scripts/run_bq.py --days 7 @queries/hitl_bottlenecks.sql

Features:
- Auto-injects {PROJECT}, {DATASET}, {TABLE} from environment variables
  so the LLM never needs to know the user's specific project/dataset/table.
- Binds @start / @end (default: last N days) and @trace_id when present.
- --dry-run mode estimates bytes scanned WITHOUT executing the query.
- --max-gb sets the billing safety limit (default 1 GB).
"""
import sys
import json
import os
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.cloud import bigquery


def inject_placeholders(sql: str, project: str, dataset: str, table: str) -> str:
    """Replace {PROJECT}, {DATASET}, {TABLE} placeholders with env values."""
    return (
        sql.replace("{PROJECT}", project)
        .replace("{DATASET}", dataset)
        .replace("{TABLE}", table)
    )


def format_bytes(n: int) -> str:
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def load_sql(query_arg: str) -> str:
    """Read SQL from a file path or return inline query text."""
    if query_arg.startswith("@") and Path(query_arg[1:]).is_file():
        return Path(query_arg[1:]).read_text()
    path = Path(query_arg)
    if path.is_file():
        return path.read_text()
    return query_arg


def build_query_parameters(
    sql: str,
    start: datetime,
    end: datetime,
    trace_id: str | None,
) -> list[bigquery.ScalarQueryParameter]:
    """Bind named parameters referenced in the SQL string."""
    params: list[bigquery.ScalarQueryParameter] = []
    if "@start" in sql:
        params.append(
            bigquery.ScalarQueryParameter("start", "TIMESTAMP", start)
        )
    if "@end" in sql:
        params.append(
            bigquery.ScalarQueryParameter("end", "TIMESTAMP", end)
        )
    if "@trace_id" in sql and trace_id:
        params.append(
            bigquery.ScalarQueryParameter("trace_id", "STRING", trace_id)
        )
    if "@problematic_trace_id" in sql and trace_id:
        params.append(
            bigquery.ScalarQueryParameter(
                "problematic_trace_id", "STRING", trace_id
            )
        )
    return params


def main():
    parser = argparse.ArgumentParser(description="Run a BigQuery query with safety limits")
    parser.add_argument(
        "query",
        help="SQL query string, file path, or @path/to/query.sql",
    )
    parser.add_argument(
        "--project",
        default=os.environ.get("GCP_PROJECT_ID", ""),
        help="GCP project ID",
    )
    parser.add_argument(
        "--dataset",
        default=os.environ.get("BQ_DATASET", ""),
        help="BigQuery dataset",
    )
    parser.add_argument(
        "--table",
        default=os.environ.get("BQ_TABLE", "agent_events"),
        help="Table name (default: agent_events)",
    )
    parser.add_argument(
        "--max-gb",
        type=int,
        default=1,
        help="Max bytes billed in GB (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Estimate bytes scanned without executing",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Default lookback for @start when not using --start (default: 7)",
    )
    parser.add_argument(
        "--start",
        help="Start timestamp for @start (ISO-8601)",
    )
    parser.add_argument(
        "--end",
        help="End timestamp for @end (ISO-8601, default: now)",
    )
    parser.add_argument(
        "--trace-id",
        help="Value for @trace_id / @problematic_trace_id when present",
    )
    args = parser.parse_args()

    if not args.project:
        print("ERROR: Set GCP_PROJECT_ID env var or pass --project", file=sys.stderr)
        sys.exit(1)
    if not args.dataset:
        print("ERROR: Set BQ_DATASET env var or pass --dataset", file=sys.stderr)
        sys.exit(1)

    end = (
        datetime.fromisoformat(args.end)
        if args.end
        else datetime.now(timezone.utc)
    )
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    if args.start:
        start = datetime.fromisoformat(args.start)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
    else:
        start = end - timedelta(days=args.days)

    raw_sql = load_sql(args.query)
    sql = inject_placeholders(
        raw_sql, args.project, args.dataset, args.table
    )
    query_params = build_query_parameters(
        sql, start, end, args.trace_id
    )

    if "@trace_id" in sql and not args.trace_id:
        print(
            "ERROR: Query uses @trace_id; pass --trace-id",
            file=sys.stderr,
        )
        sys.exit(1)
    if "@problematic_trace_id" in sql and not args.trace_id:
        print(
            "ERROR: Query uses @problematic_trace_id; pass --trace-id",
            file=sys.stderr,
        )
        sys.exit(1)

    client = bigquery.Client(project=args.project)

    if args.dry_run:
        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            use_legacy_sql=False,
            query_parameters=query_params,
        )
        try:
            job = client.query(sql, job_config=job_config)
            bytes_processed = job.total_bytes_processed
            print(json.dumps({
                "dry_run": True,
                "total_bytes_processed": bytes_processed,
                "human_readable": format_bytes(bytes_processed),
                "exceeds_limit": bytes_processed > args.max_gb * (1 << 30),
                "limit_gb": args.max_gb,
            }))
        except Exception as e:
            print(f"ERROR (dry-run): {e}", file=sys.stderr)
            sys.exit(1)
    else:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=args.max_gb * (1 << 30),
            use_legacy_sql=False,
            query_parameters=query_params,
        )
        try:
            result = client.query(sql, job_config=job_config).result()
            for row in result:
                print(json.dumps(dict(row), default=str))
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
