#!/usr/bin/env python3
"""
GuruFocus Pipeline Runner — Execute all GF modules in correct order.

Usage:
  python3 scripts/run_gurufocus.py                    # Run all modules
  python3 scripts/run_gurufocus.py --tier 1           # Run Tier 1 only (rankings, valuations, fundamentals, insider, profile, guru_tracker)
  python3 scripts/run_gurufocus.py --tier 2           # Run Tier 2 only (segments, ETF, fund_letters, universe, guru_portfolio)
  python3 scripts/run_gurufocus.py --module rankings  # Run single module
  python3 scripts/run_gurufocus.py --symbols AAPL,MSFT,GOOGL  # Specific symbols

Requires GURUFOCUS_DATA_API_KEY env var (vault, never git).
"""
import os
import sys
import json
import time
import argparse
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("gurufocus.runner")

TIER_1 = [
    "gurufocus_rankings",
    "gurufocus_valuations",
    "gurufocus_fundamentals",
    "gurufocus_insider_trading",
    "gurufocus_profile",
    "gurufocus_guru_tracker",
]

TIER_2 = [
    "gurufocus_segments",
    "gurufocus_etf_holdings",
    "gurufocus_fund_letters",
    "gurufocus_stock_universe",
    "gurufocus_guru_portfolio",
]

TIER_3 = [
    "gurufocus_news",
    "gurufocus_bulk_downloader",
]

TIER_4_COMPOSITE = [
    "gurufocus_value_screener",
    "gurufocus_insider_sentiment",
    "gurufocus_fair_value_gap",
    "gurufocus_guru_rebalance_alert",
    "gurufocus_quality_factor",
    "gurufocus_segment_momentum",
    "gurufocus_etf_flow_tracker",
]

MODULE_MAP = {
    "rankings": "modules_v2.gurufocus_rankings:GurufocusRankings",
    "valuations": "modules_v2.gurufocus_valuations:GurufocusValuations",
    "fundamentals": "modules_v2.gurufocus_fundamentals:GurufocusFundamentals",
    "insider": "modules_v2.gurufocus_insider:GurufocusInsider",
    "profile": "modules_v2.gurufocus_profile:GurufocusProfile",
    "guru_tracker": "modules_v2.gurufocus_guru_tracker:GurufocusGuruTracker",
    "segments": "modules_v2.gurufocus_segments:GurufocusSegments",
    "etf": "modules_v2.gurufocus_etf:GurufocusETF",
    "fund_letters": "modules_v2.gurufocus_fund_letters:GurufocusFundLetters",
    "universe": "modules_v2.gurufocus_stock_universe:GurufocusStockUniverse",
    "guru_portfolio": "modules_v2.gurufocus_guru_portfolio:GurufocusGuruPortfolio",
    "news": "modules_v2.gurufocus_news:GurufocusNews",
    "bulk": "modules_v2.gurufocus_bulk_downloader:GurufocusBulkDownloader",
    "screener": "modules_v2.gurufocus_value_screener:GurufocusValueScreener",
    "insider_sentiment": "modules_v2.gurufocus_insider_sentiment:GurufocusInsiderSentiment",
    "fair_value_gap": "modules_v2.gurufocus_fair_value_gap:GurufocusFairValueGap",
    "guru_alerts": "modules_v2.gurufocus_guru_rebalance_alert:GurufocusGuruRebalanceAlert",
    "quality_factor": "modules_v2.gurufocus_quality_factor:GurufocusQualityFactor",
    "segment_momentum": "modules_v2.gurufocus_segment_momentum:GurufocusSegmentMomentum",
    "etf_flow": "modules_v2.gurufocus_etf_flow_tracker:GurufocusETFFlowTracker",
}


def load_module(module_path: str):
    mod_name, cls_name = module_path.rsplit(":", 1)
    mod = __import__(mod_name, fromlist=[cls_name])
    return getattr(mod, cls_name)()


def run_modules(module_names: list, symbols: list = None):
    results = []
    for name in module_names:
        if name not in MODULE_MAP:
            logger.warning(f"Unknown module: {name}")
            continue

        logger.info(f"{'='*60}")
        logger.info(f"Running: {name}")
        start = time.time()

        try:
            mod = load_module(MODULE_MAP[name])
            result = mod.run(symbols=symbols)
            elapsed = round(time.time() - start, 1)
            result["elapsed_seconds"] = elapsed
            results.append({"module": name, **result})
            logger.info(f"Completed: {name} — {result.get('status')} in {elapsed}s, "
                        f"{result.get('rows_out', 0)} rows")
        except Exception as e:
            elapsed = round(time.time() - start, 1)
            logger.error(f"Failed: {name} — {e}")
            results.append({"module": name, "status": "error", "error": str(e), "elapsed_seconds": elapsed})

    return results


def main():
    parser = argparse.ArgumentParser(description="GuruFocus Pipeline Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run specific tier")
    parser.add_argument("--module", type=str, help="Run single module by short name")
    parser.add_argument("--symbols", type=str, help="Comma-separated symbols (e.g. AAPL,MSFT)")
    parser.add_argument("--all", action="store_true", help="Run all tiers")
    args = parser.parse_args()

    if not os.environ.get("GURUFOCUS_DATA_API_KEY"):
        logger.error("GURUFOCUS_DATA_API_KEY not set. Vault it: export GURUFOCUS_DATA_API_KEY=your_key")
        sys.exit(1)

    symbols = args.symbols.split(",") if args.symbols else None

    if args.module:
        modules = [args.module]
    elif args.tier == 1:
        modules = list(MODULE_MAP.keys())[:6]
    elif args.tier == 2:
        modules = list(MODULE_MAP.keys())[6:11]
    elif args.tier == 3:
        modules = list(MODULE_MAP.keys())[11:13]
    elif args.tier == 4:
        modules = list(MODULE_MAP.keys())[13:]
    else:
        modules = list(MODULE_MAP.keys())

    logger.info(f"Running {len(modules)} GuruFocus modules")
    if symbols:
        logger.info(f"Symbols filter: {symbols}")

    results = run_modules(modules, symbols)

    print("\n" + "=" * 60)
    print("GURUFOCUS PIPELINE SUMMARY")
    print("=" * 60)
    success = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") in ("failed", "error"))
    total_rows = sum(r.get("rows_out", 0) for r in results)
    total_time = sum(r.get("elapsed_seconds", 0) for r in results)

    print(f"Modules: {success} success, {failed} failed, {len(results)} total")
    print(f"Total rows: {total_rows}")
    print(f"Total time: {total_time:.1f}s")

    for r in results:
        status = "✓" if r.get("status") == "success" else "✗"
        print(f"  {status} {r['module']}: {r.get('rows_out', 0)} rows in {r.get('elapsed_seconds', 0)}s")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
