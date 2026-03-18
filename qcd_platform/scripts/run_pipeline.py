#!/usr/bin/env python3
"""
QuantClaw Data Pipeline — CLI Runner

Usage:
  python run_pipeline.py --module aaii_sentiment         # Run single module
  python run_pipeline.py --batch daily                   # Run all daily modules
  python run_pipeline.py --overnight                     # Full overnight batch
  python run_pipeline.py --register-all                  # Register all modules_v2
  python run_pipeline.py --status                        # Show pipeline status
"""
import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qcd_platform.pipeline.orchestrator import PipelineOrchestrator
from qcd_platform.pipeline import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("quantclaw.cli")


def register_all_modules(modules_dir: str):
    """Scan modules_v2 and register all BaseModule subclasses."""
    import importlib.util
    from qcd_platform.pipeline.base_module import BaseModule

    count = 0
    for fname in sorted(os.listdir(modules_dir)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        filepath = os.path.join(modules_dir, fname)
        module_name = fname[:-3]

        try:
            spec = importlib.util.spec_from_file_location(f"modules_v2.{module_name}", filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseModule) and attr is not BaseModule:
                    instance = attr()
                    mid = instance.register()
                    logger.info(f"Registered: {instance.name} (id={mid}, cadence={instance.cadence}, tags={instance.tags})")
                    count += 1
        except Exception as e:
            logger.error(f"Failed to register {fname}: {e}")

    logger.info(f"Registered {count} modules total")


def show_status():
    """Show pipeline status summary."""
    modules = db.execute_query(
        """SELECT current_tier, COUNT(*) as cnt FROM modules
           WHERE is_active = true GROUP BY current_tier ORDER BY current_tier""",
        fetch=True,
    )
    print("\n=== QuantClaw Data Platform Status ===\n")
    print("Module Tiers:")
    for row in (modules or []):
        print(f"  {row['current_tier'].upper():10s} {row['cnt']}")

    total = db.execute_query("SELECT COUNT(*) as cnt FROM modules WHERE is_active = true", fetch=True)
    print(f"\n  Total active: {total[0]['cnt'] if total else 0}")

    recent = db.execute_query(
        """SELECT m.name, pr.status, pr.duration_ms, pr.rows_out, pr.started_at
           FROM pipeline_runs pr JOIN modules m ON m.id = pr.module_id
           ORDER BY pr.started_at DESC LIMIT 10""",
        fetch=True,
    )
    if recent:
        print("\nRecent Runs:")
        for r in recent:
            print(f"  {r['name']:30s} {r['status']:10s} {r['rows_out'] or 0:5d} rows  {r['duration_ms'] or 0:6d}ms")

    alerts = db.execute_query(
        """SELECT COUNT(*) as cnt FROM alerts WHERE resolved = false""", fetch=True
    )
    unresolved = alerts[0]["cnt"] if alerts else 0
    print(f"\nUnresolved Alerts: {unresolved}")

    symbols = db.execute_query("SELECT COUNT(*) as cnt FROM symbol_universe WHERE is_active = true", fetch=True)
    print(f"Symbol Universe: {symbols[0]['cnt'] if symbols else 0} active symbols")

    dp = db.execute_query(
        "SELECT COUNT(*) as cnt FROM data_points", fetch=True
    )
    print(f"Data Points: {dp[0]['cnt'] if dp else 0}")
    print()


def main():
    parser = argparse.ArgumentParser(description="QuantClaw Data Pipeline Runner")
    parser.add_argument("--module", type=str, help="Run a single module by name")
    parser.add_argument("--batch", type=str, help="Run all modules for a cadence (daily/weekly/etc)")
    parser.add_argument("--overnight", action="store_true", help="Run full overnight batch")
    parser.add_argument("--register-all", action="store_true", help="Register all modules_v2")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--workers", type=int, default=4, help="Max parallel workers")

    args = parser.parse_args()
    modules_dir = os.path.join(os.path.dirname(__file__), "..", "..", "modules_v2")

    if args.register_all:
        register_all_modules(modules_dir)
        return

    if args.status:
        show_status()
        return

    orch = PipelineOrchestrator(modules_dir=modules_dir, max_workers=args.workers)

    if args.module:
        result = orch.run_module_with_retry(args.module)
        print(json.dumps(result, indent=2, default=str))
    elif args.batch:
        results = orch.run_overnight(cadences=[args.batch])
        for r in results:
            status_icon = "✅" if r["status"] == "success" else "❌"
            print(f"  {status_icon} {r['module']:30s} → {r.get('tier_reached', 'none'):6s} ({r.get('rows_out', 0)} rows, {r.get('duration_ms', 0)}ms)")
    elif args.overnight:
        results = orch.run_overnight()
        success = sum(1 for r in results if r["status"] == "success")
        print(f"\nOvernight run complete: {success}/{len(results)} succeeded")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
