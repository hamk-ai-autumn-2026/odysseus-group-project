#!/usr/bin/env python3
"""
CLI SQLite Database Viewer for DocuMind AI.
Allows viewing tables, schemas, row counts, and executing read-only SQL queries from terminal.
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import (
    get_database_stats,
    get_table_names,
    get_table_schema,
    get_table_data,
    execute_readonly_query,
)


def main():
    parser = argparse.ArgumentParser(description="DocuMind AI SQLite Database Viewer CLI")
    parser.add_argument("--db-path", type=str, help="Path to SQLite database file")
    parser.add_argument("--tables", action="store_true", help="List database tables and row counts")
    parser.add_argument("--schema", type=str, help="Show schema column metadata for a table")
    parser.add_argument("--data", type=str, help="Display row records from a specific table")
    parser.add_argument("--limit", type=int, default=20, help="Limit number of rows returned (default: 20)")
    parser.add_argument("--search", type=str, help="Filter rows matching search term")
    parser.add_argument("--query", type=str, help="Execute a read-only SQL query (SELECT / EXPLAIN / PRAGMA)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    stats = get_database_stats(args.db_path)

    if args.tables or (not args.schema and not args.data and not args.query):
        print("==========================================")
        print("  🗄️ DocuMind AI SQLite Database Summary")
        print("==========================================")
        print(f" Database Path  : {stats['db_path']}")
        print(f" File Size      : {stats['file_size_formatted']}")
        print(f" Journal Mode   : {stats['journal_mode']}")
        print(f" Total Rows     : {stats['total_rows']:,}")
        print("------------------------------------------")
        print(" Tables & Record Counts:")
        for tbl, count in stats["table_counts"].items():
            print(f"  • {tbl:<20} : {count} row(s)")
        print("==========================================\n")

    if args.schema:
        schema = get_table_schema(args.schema, args.db_path)
        if args.json:
            print(json.dumps(schema, indent=2))
        else:
            print(f"--- Schema for table '{args.schema}' ---")
            print(f"{'CID':<5} {'Column Name':<25} {'Type':<15} {'NotNull':<10} {'PrimaryKey':<10}")
            print("-" * 65)
            for col in schema:
                print(f"{col['cid']:<5} {col['name']:<25} {col['type']:<15} {str(col['notnull']):<10} {str(col['pk']):<10}")

    if args.data:
        cols, rows, total = get_table_data(
            table_name=args.data,
            limit=args.limit,
            offset=0,
            search_query=args.search,
            db_path=args.db_path,
        )
        if args.json:
            print(json.dumps({"table": args.data, "total": total, "rows": rows}, indent=2, ensure_ascii=False))
        else:
            print(f"--- Table '{args.data}' Data (showing {len(rows)} of {total}) ---")
            for idx, r in enumerate(rows, 1):
                print(f"[{idx}] {json.dumps(r, ensure_ascii=False)}")

    if args.query:
        try:
            cols, rows = execute_readonly_query(args.query, limit=args.limit, db_path=args.db_path)
            if args.json:
                print(json.dumps({"columns": cols, "rows": rows}, indent=2, ensure_ascii=False))
            else:
                print(f"--- SQL Query Results ({len(rows)} row(s)) ---")
                for idx, r in enumerate(rows, 1):
                    print(f"[{idx}] {json.dumps(r, ensure_ascii=False)}")
        except Exception as err:
            print(f"❌ Error executing SQL query: {err}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
