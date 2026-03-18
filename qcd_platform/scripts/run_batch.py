#!/usr/bin/env python3
"""
Batch Runner — Runs modules through the pipeline using V1 adapters.

Usage:
  python3 run_batch.py                          # Run all due modules
  python3 run_batch.py --tag "Sentiment"        # Run modules with specific tag
  python3 run_batch.py --cadence daily          # Run daily modules
  python3 run_batch.py --modules mod1,mod2      # Run specific modules
  python3 run_batch.py --limit 50               # Run first N due modules
  python3 run_batch.py --overnight              # Full overnight batch
  python3 run_batch.py --dry-run                # Show what would run without executing
"""
import argparse
import json
import logging
import os
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qcd_platform.pipeline.db import execute_query, get_db_pool
from qcd_platform.pipeline.v1_adapter import V1ModuleAdapter
from qcd_platform.pipeline.kafka_producer import publish_event
from qcd_platform.pipeline.redis_cache import set_module_health, publish_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("quantclaw.batch")

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "..", "module_manifest.json")


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        entries = json.load(f)
    return {e["name"]: e for e in entries}


def get_due_modules(tag: str = None, cadence: str = None, limit: int = None) -> list:
    """Get modules due for execution from the database."""
    conditions = ["is_active = true", "consecutive_failures < 3"]
    params = []

    if cadence:
        conditions.append("cadence = %s")
        params.append(cadence)

    where = " AND ".join(conditions)
    query = f"""
        SELECT m.id, m.name, m.cadence, m.granularity, m.last_run_at, m.next_run_at
        FROM modules m
        {"JOIN module_tags mt ON m.id = mt.module_id JOIN tag_definitions td ON mt.tag_id = td.id" if tag else ""}
        WHERE {where}
        {"AND td.label = %s" if tag else ""}
        AND (m.next_run_at IS NULL OR m.next_run_at <= NOW())
        ORDER BY m.next_run_at NULLS FIRST
        {"LIMIT %s" if limit else ""}
    """
    if tag:
        params.append(tag)
    if limit:
        params.append(limit)

    return execute_query(query, tuple(params), fetch=True) or []


def run_single_module(module_name: str, manifest: dict, max_retries: int = 3) -> dict:
    """Run a single module through the pipeline with retry logic."""
    entry = manifest.get(module_name)
    if not entry:
        return {"module": module_name, "status": "not_in_manifest"}

    main_callable = entry.get("main_callable")
    if not main_callable:
        return {"module": module_name, "status": "no_callable"}

    adapter = V1ModuleAdapter(
        module_name=module_name,
        main_callable=main_callable,
        cadence=entry.get("cadence", "daily"),
        granularity=entry.get("granularity", "symbol"),
        tags=entry.get("tags", ["US Equities"]),
    )

    last_result = None
    for attempt in range(1, max_retries + 1):
        try:
            set_module_health(module_name, "running")

            start = time.time()
            result = adapter.run()
            elapsed = time.time() - start

            if elapsed > 60:
                logger.warning(f"[{module_name}] Slow module: {elapsed:.1f}s")

            last_result = result

            if result["status"] in ("success", "empty"):
                set_module_health(module_name, "healthy", {
                    "tier": result.get("tier_reached", "none"),
                    "quality": result.get("quality_score", 0),
                    "duration_ms": result.get("duration_ms", 0),
                })

                execute_query(
                    """UPDATE modules SET
                           last_run_at = NOW(),
                           last_success_at = NOW(),
                           run_count = run_count + 1,
                           consecutive_failures = 0,
                           current_tier = %s,
                           quality_score = %s
                       WHERE name = %s""",
                    (result.get("tier_reached", "bronze"),
                     result.get("quality_score", 0),
                     module_name),
                )
                return result

            logger.warning(f"[{module_name}] Attempt {attempt}/{max_retries}: {result.get('error', 'unknown')[:100]}")

        except Exception as e:
            last_result = {"module": module_name, "status": "error", "error": str(e)[:200]}
            logger.warning(f"[{module_name}] Attempt {attempt}/{max_retries} exception: {str(e)[:100]}")

        if attempt < max_retries:
            time.sleep(min(3 * attempt, 15))

    # All retries exhausted
    set_module_health(module_name, "error")
    execute_query(
        """UPDATE modules SET
               last_run_at = NOW(),
               error_count = error_count + 1,
               consecutive_failures = consecutive_failures + 1
           WHERE name = %s""",
        (module_name,),
    )

    publish_event("quantclaw.pipeline.errors", {
        "module": module_name,
        "error": last_result.get("error", "unknown") if last_result else "all retries failed",
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    return last_result or {"module": module_name, "status": "failed"}


def run_batch(module_names: list, manifest: dict, max_workers: int = 4) -> list:
    """Run modules in parallel with thread pool."""
    results = []
    total = len(module_names)
    completed = 0
    success = 0
    failed = 0

    logger.info(f"Starting batch: {total} modules, {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_module, name, manifest): name
            for name in module_names
        }
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            try:
                result = future.result()
                results.append(result)
                if result.get("status") in ("success", "empty"):
                    success += 1
                else:
                    failed += 1
                tier = result.get("tier_reached", "-")
                duration = result.get("duration_ms", 0)
                logger.info(f"[{completed}/{total}] {name}: {result['status']} "
                            f"(tier={tier}, {duration}ms)")
            except Exception as e:
                failed += 1
                results.append({"module": name, "status": "error", "error": str(e)})
                logger.error(f"[{completed}/{total}] {name}: EXCEPTION {e}")

    logger.info(f"\nBatch complete: {success}/{total} success, {failed} failed")

    publish_update("qcd:updates", {
        "type": "batch_complete",
        "total": total,
        "success": success,
        "failed": failed,
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    return results


def main():
    parser = argparse.ArgumentParser(description="QuantClaw Data Pipeline Batch Runner")
    parser.add_argument("--tag", help="Filter by tag (e.g. 'Sentiment', 'Earnings')")
    parser.add_argument("--cadence", help="Filter by cadence (e.g. daily, weekly)")
    parser.add_argument("--modules", help="Comma-separated module names to run")
    parser.add_argument("--limit", type=int, help="Max modules to run")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    parser.add_argument("--overnight", action="store_true", help="Run full overnight batch")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    args = parser.parse_args()

    get_db_pool()
    manifest = load_manifest()

    if args.modules:
        module_names = [m.strip() for m in args.modules.split(",")]
    elif args.overnight:
        modules = get_due_modules(cadence=None, limit=None)
        module_names = [m["name"] for m in modules]
    else:
        modules = get_due_modules(tag=args.tag, cadence=args.cadence, limit=args.limit)
        module_names = [m["name"] for m in modules]

    # Filter to only those in manifest with a callable
    runnable = [n for n in module_names if n in manifest and manifest[n].get("main_callable")]

    if args.dry_run:
        print(f"\n=== DRY RUN — {len(runnable)} modules would execute ===")
        for name in runnable[:50]:
            entry = manifest[name]
            print(f"  {name} [{entry.get('cadence')}] → {entry.get('main_callable')}")
        if len(runnable) > 50:
            print(f"  ... and {len(runnable) - 50} more")
        return

    if not runnable:
        logger.info("No modules to run")
        return

    start = time.time()
    results = run_batch(runnable, manifest, max_workers=args.workers)
    elapsed = time.time() - start

    # Summary
    success = sum(1 for r in results if r.get("status") in ("success", "empty"))
    gold = sum(1 for r in results if r.get("tier_reached") == "gold")
    silver = sum(1 for r in results if r.get("tier_reached") == "silver")
    failed = sum(1 for r in results if r.get("status") in ("failed", "error"))
    total_rows = sum(r.get("rows_out", 0) for r in results)

    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE — {elapsed:.1f}s")
    print(f"{'='*60}")
    print(f"Total: {len(results)} | Success: {success} | Failed: {failed}")
    print(f"Gold: {gold} | Silver: {silver}")
    print(f"Total rows ingested: {total_rows}")

    if failed:
        print(f"\nFailed modules:")
        for r in results:
            if r.get("status") in ("failed", "error"):
                print(f"  {r['module']}: {r.get('error', 'unknown')[:80]}")


if __name__ == "__main__":
    main()
