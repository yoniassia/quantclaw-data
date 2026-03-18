#!/usr/bin/env python3
"""
GuruFocus Data Importer — fetches rankings + valuations for all stocks in symbol_universe.
Writes to gf_rankings and gf_valuations tables.
Usage:
  python3 gf_import.py [--test N] [--rankings-only] [--valuations-only] [--dry-run]
"""
import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone

import psycopg2
from psycopg2 import extras

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from gurufocus_client import gf_request, get_rankings as gf_get_rankings, get_valuations as gf_get_valuations
from gurufocus_symbol_map import etoro_symbol_to_gf, SKIP_SUFFIXES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("gf_import")

CRYPTO_TICKERS = {"BTC", "ETH", "BNB", "LUNC", "XRP", "SOL", "ADA", "DOGE", "DOT", "AVAX", "MATIC", "LINK", "UNI", "ATOM"}
ETF_TICKERS = {"ARKK", "ARKF", "GLD", "SLV", "GDX", "PALL", "PPLT", "XLE", "XOP", "XLRE", "XBI", "SOXX", "TAN", "ICLN", "LIT", "UNG", "USO", "TQQQ", "JEPQ", "APE"}


def get_db_conn():
    return psycopg2.connect(
        host="localhost", port=5432,
        database="quantclaw_data",
        user="quantclaw_user",
        password="quantclaw_2026_prod",
    )


def get_stock_symbols(conn, limit=None):
    with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute("SELECT symbol, exchange FROM symbol_universe WHERE asset_class='stocks' AND is_active=true ORDER BY symbol")
        rows = cur.fetchall()

    results = []
    skipped = []
    for row in rows:
        sym = row["symbol"]
        exch = row.get("exchange") or None
        ticker_base = sym.split(".")[0] if "." in sym else sym

        if ticker_base in CRYPTO_TICKERS:
            skipped.append((sym, "crypto"))
            continue
        if ticker_base in ETF_TICKERS:
            skipped.append((sym, "etf"))
            continue

        gf_sym = etoro_symbol_to_gf(sym, exch)
        if not gf_sym:
            skipped.append((sym, "no_mapping"))
            continue
        results.append((sym, gf_sym))

    logger.info(f"Mapped {len(results)} stocks to GF symbols, skipped {len(skipped)} ({len([s for s in skipped if s[1]=='crypto'])} crypto, {len([s for s in skipped if s[1]=='etf'])} ETF, {len([s for s in skipped if s[1]=='no_mapping'])} unmapped)")
    if limit:
        results = results[:limit]
    return results, skipped


def _safe_float(val):
    if val is None or val == "" or val == "N/A":
        return None
    try:
        f = float(val)
        import math
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def import_rankings(conn, symbols, dry_run=False):
    logger.info(f"=== RANKINGS IMPORT: {len(symbols)} symbols ===")
    success, errors = 0, 0
    for i, (etoro_sym, gf_sym) in enumerate(symbols):
        try:
            data = gf_get_rankings(gf_sym)
            if not data or isinstance(data, str):
                logger.warning(f"[{i+1}/{len(symbols)}] {gf_sym}: empty response")
                errors += 1
                continue

            rankings = data.get("guru_focus_rankings", data)
            if isinstance(rankings, str):
                logger.warning(f"[{i+1}/{len(symbols)}] {gf_sym}: unexpected string response")
                errors += 1
                continue

            if not dry_run:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO gf_rankings (symbol, gf_symbol, gf_score, financial_strength,
                            profitability_rank, growth_rank, gf_value_rank, momentum_rank,
                            predictability_rank, payload)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        etoro_sym, gf_sym,
                        _safe_float(rankings.get("gf_score")),
                        _safe_float(rankings.get("rank_balancesheet")),
                        _safe_float(rankings.get("rank_profitability")),
                        _safe_float(rankings.get("rank_growth")),
                        _safe_float(rankings.get("rank_gf_value")),
                        _safe_float(rankings.get("rank_momentum")),
                        str(rankings.get("predictability", "")),
                        json.dumps(data, default=str),
                    ))
                conn.commit()

            success += 1
            score = rankings.get("gf_score", "?")
            logger.info(f"[{i+1}/{len(symbols)}] {etoro_sym} ({gf_sym}): GF Score={score} ✓")

        except Exception as e:
            errors += 1
            logger.error(f"[{i+1}/{len(symbols)}] {etoro_sym} ({gf_sym}): {e}")
            conn.rollback()

    logger.info(f"=== RANKINGS DONE: {success} ok, {errors} errors ===")
    return success, errors


def import_valuations(conn, symbols, dry_run=False):
    logger.info(f"=== VALUATIONS IMPORT: {len(symbols)} symbols ===")
    success, errors = 0, 0
    for i, (etoro_sym, gf_sym) in enumerate(symbols):
        try:
            data = gf_get_valuations(gf_sym)
            if not data or isinstance(data, str):
                logger.warning(f"[{i+1}/{len(symbols)}] {gf_sym}: empty response")
                errors += 1
                continue

            latest = data
            if "annually" in data and isinstance(data["annually"], list) and data["annually"]:
                latest_annual = data["annually"][-1]
            else:
                latest_annual = {}

            ratios = latest_annual.get("ratios", {}) if isinstance(latest_annual, dict) else {}
            per_share = latest_annual.get("per_share_data", {}) if isinstance(latest_annual, dict) else {}

            gf_value = None
            dcf_value = None
            graham_number = None
            current_price = _safe_float(per_share.get("month_end_stock_price"))

            if "valuation_and_quality" in data:
                vq = data["valuation_and_quality"]
                gf_value = _safe_float(vq.get("gf_value"))
                dcf_value = _safe_float(vq.get("dcf_value"))
                graham_number = _safe_float(vq.get("graham_number"))
            elif isinstance(data.get("guru_focus_rankings"), dict):
                gfr = data["guru_focus_rankings"]
                gf_value = _safe_float(gfr.get("gf_value"))

            price_to_gf = None
            if current_price and gf_value and gf_value > 0:
                price_to_gf = round(current_price / gf_value, 4)

            if not dry_run:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO gf_valuations (symbol, gf_symbol, gf_value, dcf_value,
                            graham_number, peter_lynch_value, median_ps_value, current_price,
                            price_to_gf_value, payload)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        etoro_sym, gf_sym, gf_value, dcf_value, graham_number,
                        None, None, current_price, price_to_gf,
                        json.dumps(data, default=str),
                    ))
                conn.commit()

            success += 1
            years = len(data.get("annually", []))
            logger.info(f"[{i+1}/{len(symbols)}] {etoro_sym} ({gf_sym}): {years} years data ✓")

        except Exception as e:
            errors += 1
            logger.error(f"[{i+1}/{len(symbols)}] {etoro_sym} ({gf_sym}): {e}")
            conn.rollback()

    logger.info(f"=== VALUATIONS DONE: {success} ok, {errors} errors ===")
    return success, errors


def main():
    parser = argparse.ArgumentParser(description="GuruFocus Data Import")
    parser.add_argument("--test", type=int, help="Test with N symbols only")
    parser.add_argument("--rankings-only", action="store_true")
    parser.add_argument("--valuations-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = get_db_conn()
    symbols, skipped = get_stock_symbols(conn, limit=args.test)

    if skipped:
        logger.info(f"Skipped symbols: {', '.join(f'{s[0]}({s[1]})' for s in skipped[:20])}{'...' if len(skipped) > 20 else ''}")

    results = {}
    if not args.valuations_only:
        results["rankings"] = import_rankings(conn, symbols, dry_run=args.dry_run)
    if not args.rankings_only:
        results["valuations"] = import_valuations(conn, symbols, dry_run=args.dry_run)

    print(f"\n{'='*50}")
    print(f"IMPORT COMPLETE — {datetime.now(timezone.utc).isoformat()}")
    for name, (ok, err) in results.items():
        print(f"  {name}: {ok} success, {err} errors")
    print(f"{'='*50}")

    conn.close()


if __name__ == "__main__":
    main()
