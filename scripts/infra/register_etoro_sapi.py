#!/usr/bin/env python3
"""
Register eToro SAPI modules, run a small SAPI fetch, verify data_points, optional platinum bridge.

Usage:
  python3 scripts/infra/register_etoro_sapi.py [--full-fetch] [--bridge] [--batch N]

Default: first N instrument IDs (discovery or fallback), fetch, query stats.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qcd_platform.pipeline import db  # noqa: E402


def _ensure_multi_asset_tag():
    db.execute_query(
        """INSERT INTO tag_definitions (category, label)
           VALUES ('asset_class', 'Multi-Asset')
           ON CONFLICT (category, label) DO NOTHING""",
    )


def _discover_sample_ids(limit: int) -> list[str]:
    from modules_v2.etoro_sapi_instruments import EtoroSapiInstrumentsModule, _discover_from_bronze_cache

    mod = EtoroSapiInstrumentsModule()
    ids = _discover_from_bronze_cache()
    if not ids:
        try:
            ids = asyncio.run(mod._discover_ids_standalone())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                ids = loop.run_until_complete(mod._discover_ids_standalone())
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    if not ids:
        ids = list(range(1001, 1100))
    return [str(i) for i in ids[:limit]]


def main():
    parser = argparse.ArgumentParser(description="Register and test eToro SAPI DCC modules")
    parser.add_argument("--batch", type=int, default=50, help="Instrument count for test fetch")
    parser.add_argument("--full-fetch", action="store_true", help="Discover full universe (no ID cap)")
    parser.add_argument("--bridge", action="store_true", help="Run platinum bridge after SAPI run")
    args = parser.parse_args()

    _ensure_multi_asset_tag()

    from modules_v2.etoro_sapi_instruments import EtoroSapiInstrumentsModule
    from modules_v2.etoro_sapi_platinum_bridge import EtoroSapiPlatinumBridgeModule

    sapi_mod = EtoroSapiInstrumentsModule()
    sapi_mod.register()
    print(f"Registered module id={sapi_mod.module_id} name={sapi_mod.name!r}")

    bridge_mod = EtoroSapiPlatinumBridgeModule()
    bridge_mod.register()
    print(f"Registered module id={bridge_mod.module_id} name={bridge_mod.name!r}")

    if args.full_fetch:
        test_symbols = None
        print("Running full SAPI fetch (all discovered IDs)...")
    else:
        test_symbols = _discover_sample_ids(args.batch)
        print(f"Test instrument IDs ({len(test_symbols)}): {test_symbols[:8]}...")

    result = sapi_mod.run(symbols=test_symbols)
    print("SAPI run result:", result)

    rows = db.execute_query(
        """
        SELECT tier, COUNT(*) AS n
        FROM data_points
        WHERE module_id = %s
        GROUP BY tier
        ORDER BY tier
        """,
        (sapi_mod.module_id,),
        fetch=True,
    )
    print("data_points by tier:", rows)

    sample = db.execute_query(
        """
        SELECT symbol, tier, ts,
               payload->>'symbol' AS p_sym,
               payload->>'current_price' AS price,
               payload->>'pe_ratio' AS pe
        FROM data_points
        WHERE module_id = %s AND tier = 'gold'
        ORDER BY ts DESC, symbol
        LIMIT 8
        """,
        (sapi_mod.module_id,),
        fetch=True,
    )
    print("Sample rows:")
    for r in sample or []:
        print(dict(r))

    if args.bridge:
        # Bridge filters by ticker symbol; test batch uses instrument IDs, so resolve gold symbols.
        gsyms = db.execute_query(
            """SELECT DISTINCT symbol FROM data_points
               WHERE module_id = %s AND tier = 'gold' AND symbol IS NOT NULL
               ORDER BY symbol""",
            (sapi_mod.module_id,),
            fetch=True,
        )
        bridge_symbols = [r["symbol"] for r in (gsyms or [])]
        bres = bridge_mod.run(symbols=bridge_symbols if bridge_symbols else None)
        print("Bridge run result:", bres)
        try:
            plat = db.execute_query(
                """
                SELECT symbol, composite_score, rating, price, pe_trailing, generated_at
                FROM platinum_records
                WHERE payload->>'source' = 'etoro_sapi'
                ORDER BY generated_at DESC
                LIMIT 8
                """,
                fetch=True,
            )
            print("Recent platinum_records (eToro):")
            for r in plat or []:
                print(dict(r))
        except Exception as e:
            print("platinum_records sample query skipped:", e)


if __name__ == "__main__":
    main()
