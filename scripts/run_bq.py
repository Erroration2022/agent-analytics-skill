#!/usr/bin/env python3
"""Lightweight BigQuery executor for agent analytics queries.

Usage:
    python run_bq.py "SELECT ..." [--project PROJECT] [--max-gb MAX_GB]

The LLM should always invoke queries through this script rather than
using `bq query` directly. It handles auth, formatting, and byte-scan limits.
"""
import sys
import json
import os
import argparse

from google.cloud import bigquery


def main():
    parser = argparse.ArgumentParser(description="Run a BigQuery query with safety limits")
    parser.add_argument("query", help="SQL query string")
    parser.add_argument("--project", default=os.environ.get("GCP_PROJECT_ID", ""), help="GCP project ID")
    parser.add_argument("--max-gb", type=int, default=1, help="Max bytes billed in GB (default: 1)")
    args = parser.parse_args()

    if not args.project:
        print("ERROR: Set GCP_PROJECT_ID env var or pass --project", file=sys.stderr)
        sys.exit(1)

    client = bigquery.Client(project=args.project)
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=args.max_gb * (1 << 30),
        use_legacy_sql=False,
    )

    try:
        rows = client.query(args.query, job_config=job_config).result()
        for row in rows:
            print(json.dumps(dict(row), default=str))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
