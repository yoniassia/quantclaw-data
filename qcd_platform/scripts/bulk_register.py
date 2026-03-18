#!/usr/bin/env python3
"""
Bulk Register — Reads the module manifest and registers all modules in PostgreSQL.
Also ensures tag_definitions are populated.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qcd_platform.pipeline.db import execute_query, get_db_pool

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "..", "module_manifest.json")

TAG_DEFINITIONS = {
    "asset_class": [
        "US Equities", "EU Equities", "Crypto", "FX", "Commodities",
        "Fixed Income", "ETF", "Indices",
    ],
    "data_type": [
        "Fundamentals", "Earnings", "Sentiment", "Corporate Actions",
        "Alternative Data", "Risk", "ESG",
    ],
    "region": ["US", "EU", "Asia", "Emerging Markets", "Global"],
    "domain": ["Macro"],
}


def ensure_tags():
    """Create all tag_definitions if not exist."""
    count = 0
    for category, labels in TAG_DEFINITIONS.items():
        for label in labels:
            execute_query(
                """INSERT INTO tag_definitions (category, label)
                   VALUES (%s, %s) ON CONFLICT (category, label) DO NOTHING""",
                (category, label),
            )
            count += 1
    print(f"Ensured {count} tag definitions")


def register_modules():
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    registered = 0
    skipped = 0

    for entry in manifest:
        name = entry["name"]
        if entry.get("parse_error") and not entry.get("main_callable"):
            skipped += 1
            continue

        cadence = entry.get("cadence", "daily")
        granularity = entry.get("granularity", "symbol")
        tags = entry.get("tags", ["US Equities"])
        source_file = entry.get("file", f"modules/{name}.py")
        main_callable = entry.get("main_callable")

        rows = execute_query(
            """INSERT INTO modules (name, display_name, source_file, cadence, granularity)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (name) DO UPDATE SET
                   cadence = EXCLUDED.cadence,
                   granularity = EXCLUDED.granularity,
                   source_file = EXCLUDED.source_file,
                   updated_at = NOW()
               RETURNING id""",
            (name, name.replace("_", " ").title(), source_file, cadence, granularity),
            fetch=True,
        )
        module_id = rows[0]["id"]

        for tag_label in tags:
            execute_query(
                """INSERT INTO module_tags (module_id, tag_id)
                   SELECT %s, id FROM tag_definitions WHERE label = %s
                   ON CONFLICT DO NOTHING""",
                (module_id, tag_label),
            )

        registered += 1

    return registered, skipped


def print_stats():
    rows = execute_query(
        """SELECT
             COUNT(*) as total,
             COUNT(*) FILTER (WHERE is_active) as active
           FROM modules""",
        fetch=True,
    )
    if rows:
        print(f"Total modules in DB: {rows[0]['total']}")
        print(f"Active: {rows[0]['active']}")

    cadence_rows = execute_query(
        """SELECT cadence, COUNT(*) as cnt
           FROM modules GROUP BY cadence ORDER BY cnt DESC""",
        fetch=True,
    )
    if cadence_rows:
        print("\nBy cadence:")
        for r in cadence_rows:
            print(f"  {r['cadence']}: {r['cnt']}")

    tag_rows = execute_query(
        """SELECT td.label, COUNT(*) as cnt
           FROM module_tags mt
           JOIN tag_definitions td ON mt.tag_id = td.id
           GROUP BY td.label ORDER BY cnt DESC""",
        fetch=True,
    )
    if tag_rows:
        print("\nBy tag:")
        for r in tag_rows:
            print(f"  {r['label']}: {r['cnt']}")


def main():
    get_db_pool()
    print("Ensuring tag definitions...")
    ensure_tags()
    print("\nRegistering modules from manifest...")
    registered, skipped = register_modules()
    print(f"\nRegistered: {registered}, Skipped: {skipped}")
    print("\n=== Database Stats ===")
    print_stats()


if __name__ == "__main__":
    main()
