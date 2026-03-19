#!/usr/bin/env python3
"""
GuruFocus Gold Transformer — reads pre-fetched JSON files, transforms through
Bronze→Silver→Gold, stores in PostgreSQL (domain tables + data_points hypertable).

Source: /home/quant/apps/cursor-bridge/gurufocus-data/ (179 tickers × 4 categories)
Target tables: gf_rankings, gf_valuations, gf_fundamentals, gf_profiles, data_points

Usage:
  python3 gf_gold_transformer.py [--category rankings|valuations|fundamentals|profiles|all]
                                  [--test N] [--dry-run] [--verbose]
"""
import os
import sys
import json
import math
import logging
import argparse
import hashlib
import time
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import psycopg2
from psycopg2 import extras

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gf_gold")

DATA_DIR = "/home/quant/apps/cursor-bridge/gurufocus-data"
DB_CONFIG = dict(
    host="localhost", port=5432,
    database="quantclaw_data",
    user="quantclaw_user",
    password="quantclaw_2026_prod",
)

try:
    from qcd_platform.pipeline.kafka_producer import publish_event
    from qcd_platform.pipeline.redis_cache import cache_latest
    HAS_INFRA = True
except ImportError:
    HAS_INFRA = False
    def publish_event(topic, data): pass
    def cache_latest(module, symbol, data): pass


@dataclass
class QualityReport:
    category: str
    total_files: int = 0
    loaded: int = 0
    bronze: int = 0
    silver: int = 0
    gold: int = 0
    errors: int = 0
    completeness: float = 0.0
    accuracy: float = 0.0
    issues: List[str] = field(default_factory=list)

    @property
    def passed_gold(self) -> bool:
        return self.completeness >= 80 and self.accuracy >= 80

    @property
    def overall_score(self) -> int:
        scores = [self.completeness, self.accuracy]
        return int(sum(scores) / len(scores)) if scores else 0


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def load_json_files(category: str) -> List[Tuple[str, dict]]:
    """Load all JSON files for a category. Returns [(symbol, data), ...]."""
    cat_dir = os.path.join(DATA_DIR, category)
    if not os.path.isdir(cat_dir):
        logger.error(f"Directory not found: {cat_dir}")
        return []

    results = []
    for fname in sorted(os.listdir(cat_dir)):
        if not fname.endswith(".json"):
            continue
        symbol = fname.replace(".json", "")
        fpath = os.path.join(cat_dir, fname)
        try:
            with open(fpath) as f:
                data = json.load(f)
            if data:
                results.append((symbol, data))
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load {fpath}: {e}")
    return results


def ensure_module_registered(conn, name: str, display_name: str, cadence: str) -> int:
    with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute("SELECT id FROM modules WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute(
            """INSERT INTO modules (name, display_name, source_file, cadence, granularity, current_tier, is_active)
               VALUES (%s, %s, %s, %s, 'symbol', 'bronze', true) RETURNING id""",
            (name, display_name, "modules_v2/gf_gold_transformer.py", cadence),
        )
        conn.commit()
        return cur.fetchone()["id"]


def insert_data_point(conn, module_id: int, symbol: str, ts: datetime,
                      cadence: str, tier: str, quality: int, payload: dict):
    source_hash = _payload_hash(payload)
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO data_points (ts, module_id, symbol, cadence, tier, quality_score, payload, source_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT DO NOTHING""",
            (ts, module_id, symbol, cadence, tier, quality, json.dumps(payload, default=str), source_hash),
        )


# =============================================================================
# RANKINGS: GF Score, financial strength, profitability, growth, value, momentum
# =============================================================================
def transform_rankings(conn, files: List[Tuple[str, dict]], dry_run: bool) -> QualityReport:
    report = QualityReport(category="rankings", total_files=len(files))
    now = datetime.now(timezone.utc)
    module_id = ensure_module_registered(conn, "gurufocus_rankings_gold", "GuruFocus Rankings (Gold)", "daily")

    valid_rows = []
    for symbol, data in files:
        report.loaded += 1
        rankings = data.get("guru_focus_rankings", data)
        if not isinstance(rankings, dict):
            report.errors += 1
            report.issues.append(f"{symbol}: no rankings dict")
            continue

        report.bronze += 1

        gf_score = _safe_float(rankings.get("gf_score"))
        gf_value = _safe_float(rankings.get("gf_value"))
        p2gf = _safe_float(rankings.get("p2gf_value"))
        predictability = str(rankings.get("predictability", ""))

        row = dict(
            symbol=symbol,
            gf_symbol=data.get("basic_information", {}).get("symbol", symbol),
            gf_score=gf_score,
            financial_strength=_safe_float(rankings.get("rank_balancesheet")),
            profitability_rank=_safe_float(rankings.get("rank_profitability")),
            growth_rank=_safe_float(rankings.get("rank_growth")),
            gf_value_rank=_safe_float(rankings.get("rank_gf_value")),
            momentum_rank=_safe_float(rankings.get("rank_momentum")),
            predictability_rank=predictability,
            gf_value=gf_value,
            price_to_gf=p2gf,
        )

        has_score = gf_score is not None
        ranks_present = sum(1 for k in ["financial_strength", "profitability_rank", "growth_rank",
                                         "gf_value_rank", "momentum_rank"]
                           if row[k] is not None)

        if has_score and ranks_present >= 3:
            report.silver += 1
            row["_payload"] = rankings
            row["_quality"] = 90 if ranks_present == 5 else 80
            valid_rows.append(row)
        else:
            report.issues.append(f"{symbol}: incomplete (score={has_score}, ranks={ranks_present}/5)")

    report.completeness = (len(valid_rows) / report.loaded * 100) if report.loaded else 0
    report.accuracy = (sum(1 for r in valid_rows if r["_quality"] >= 90) / len(valid_rows) * 100) if valid_rows else 0

    if not dry_run and valid_rows:
        for row in valid_rows:
            payload = row.pop("_payload")
            quality = row.pop("_quality")
            tier = "gold" if report.passed_gold else "silver"

            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO gf_rankings (symbol, gf_symbol, gf_score, financial_strength,
                        profitability_rank, growth_rank, gf_value_rank, momentum_rank,
                        predictability_rank, gf_value, price_to_gf, payload)
                       VALUES (%(symbol)s, %(gf_symbol)s, %(gf_score)s, %(financial_strength)s,
                        %(profitability_rank)s, %(growth_rank)s, %(gf_value_rank)s, %(momentum_rank)s,
                        %(predictability_rank)s, %(gf_value)s, %(price_to_gf)s, %(payload)s)""",
                    {**row, "payload": json.dumps(payload, default=str)},
                )

            dp_payload = {k: v for k, v in row.items() if k != "gf_symbol" and v is not None}
            dp_payload["source"] = "gurufocus"
            insert_data_point(conn, module_id, row["symbol"], now, "daily", tier, quality, dp_payload)
            cache_latest("gurufocus_rankings", row["symbol"], dp_payload)

            if report.passed_gold:
                report.gold += 1

        conn.commit()
        publish_event("quantclaw.pipeline.gold.fundamentals", {
            "module": "gurufocus_rankings_gold",
            "count": len(valid_rows),
            "quality_score": report.overall_score,
            "ts": now.isoformat(),
        })

    return report


# =============================================================================
# VALUATIONS: PE, PS, PB, EV/EBITDA, DCF, GF Value, historical ratios
# =============================================================================
def transform_valuations(conn, files: List[Tuple[str, dict]], dry_run: bool) -> QualityReport:
    report = QualityReport(category="valuations", total_files=len(files))
    now = datetime.now(timezone.utc)
    module_id = ensure_module_registered(conn, "gurufocus_valuations_gold", "GuruFocus Valuations (Gold)", "daily")

    valid_rows = []
    for symbol, data in files:
        report.loaded += 1

        if not isinstance(data, dict):
            report.errors += 1
            continue

        report.bronze += 1

        annually = data.get("annually", [])
        ttm = data.get("ttm", {})

        latest = annually[-1] if annually else {}
        latest_ratios = latest.get("ratios", {}) if isinstance(latest, dict) else {}
        latest_ps = latest.get("per_share_data", {}) if isinstance(latest, dict) else {}
        ttm_ratios = ttm.get("ratios", {}) if isinstance(ttm, dict) else {}
        ttm_ps = ttm.get("per_share_data", {}) if isinstance(ttm, dict) else {}

        current_price = _safe_float(ttm_ps.get("month_end_stock_price") or latest_ps.get("month_end_stock_price"))
        eps = _safe_float(ttm_ps.get("earning_per_share_diluted") or latest_ps.get("earning_per_share_diluted"))
        bvps = _safe_float(ttm_ps.get("book_value_per_share") or latest_ps.get("book_value_per_share"))
        fcf_ps = _safe_float(ttm_ps.get("free_cash_flow_per_share") or latest_ps.get("free_cash_flow_per_share"))
        rev_ps = _safe_float(ttm_ps.get("revenue_per_share") or latest_ps.get("revenue_per_share"))

        pe = _safe_float(ttm_ratios.get("pe_ratio") or latest_ratios.get("pe_ratio"))
        pb = _safe_float(ttm_ratios.get("pb_ratio") or latest_ratios.get("pb_ratio"))
        ps = _safe_float(ttm_ratios.get("ps_ratio") or latest_ratios.get("ps_ratio"))
        ev_ebitda = _safe_float(ttm_ratios.get("ev_to_ebitda") or latest_ratios.get("ev_to_ebitda"))
        fcf_yield = _safe_float(ttm_ratios.get("fcf_yield") or latest_ratios.get("fcf_yield"))
        div_yield = _safe_float(ttm_ratios.get("dividend_yield") or latest_ratios.get("dividend_yield"))

        bi = data.get("basic_information", {})
        rankings = data.get("guru_focus_rankings", {})
        gf_value = _safe_float(rankings.get("gf_value") if isinstance(rankings, dict) else None)
        dcf_value = _safe_float(bi.get("dcf_value"))
        graham_number = _safe_float(bi.get("graham_number"))
        peter_lynch = _safe_float(bi.get("peter_lynch_value"))
        median_ps_value = _safe_float(bi.get("median_ps_value"))

        price_to_gf = None
        if current_price and gf_value and gf_value > 0:
            price_to_gf = round(current_price / gf_value, 4)

        row = dict(
            symbol=symbol,
            gf_symbol=bi.get("symbol", symbol),
            gf_value=gf_value,
            dcf_value=dcf_value,
            graham_number=graham_number,
            peter_lynch_value=peter_lynch,
            median_ps_value=median_ps_value,
            current_price=current_price,
            price_to_gf_value=price_to_gf,
        )

        dp_payload = dict(
            source="gurufocus",
            current_price=current_price,
            eps=eps,
            bvps=bvps,
            fcf_per_share=fcf_ps,
            revenue_per_share=rev_ps,
            pe_ratio=pe,
            pb_ratio=pb,
            ps_ratio=ps,
            ev_ebitda=ev_ebitda,
            fcf_yield=fcf_yield,
            dividend_yield=div_yield,
            years_data=len(annually),
            latest_period=latest.get("date"),
        )
        dp_payload = {k: v for k, v in dp_payload.items() if v is not None}

        metrics_present = sum(1 for v in [current_price, eps, bvps, fcf_ps, rev_ps] if v is not None)
        ratios_present = sum(1 for v in [pe, pb, ps, ev_ebitda, fcf_yield, div_yield] if v is not None)
        total_quality = metrics_present + ratios_present
        if metrics_present >= 2:
            report.silver += 1
            row["_dp_payload"] = dp_payload
            row["_full_payload"] = data
            row["_quality"] = min(100, 70 + total_quality * 3)
            valid_rows.append(row)
        else:
            report.issues.append(f"{symbol}: only {metrics_present}/5 key metrics")

    report.completeness = (len(valid_rows) / report.loaded * 100) if report.loaded else 0
    report.accuracy = (sum(1 for r in valid_rows if r["_quality"] >= 85) / len(valid_rows) * 100) if valid_rows else 0

    if not dry_run and valid_rows:
        for row in valid_rows:
            dp_payload = row.pop("_dp_payload")
            full_payload = row.pop("_full_payload")
            quality = row.pop("_quality")
            tier = "gold" if report.passed_gold else "silver"

            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO gf_valuations (symbol, gf_symbol, gf_value, dcf_value,
                        graham_number, peter_lynch_value, median_ps_value, current_price,
                        price_to_gf_value, payload)
                       VALUES (%(symbol)s, %(gf_symbol)s, %(gf_value)s, %(dcf_value)s,
                        %(graham_number)s, %(peter_lynch_value)s, %(median_ps_value)s,
                        %(current_price)s, %(price_to_gf_value)s, %(payload)s)""",
                    {**row, "payload": json.dumps(full_payload, default=str)},
                )

            insert_data_point(conn, module_id, row["symbol"], now, "daily", tier, quality, dp_payload)
            cache_latest("gurufocus_valuations", row["symbol"], dp_payload)

            if report.passed_gold:
                report.gold += 1

        conn.commit()
        publish_event("quantclaw.pipeline.gold.fundamentals", {
            "module": "gurufocus_valuations_gold",
            "count": len(valid_rows),
            "quality_score": report.overall_score,
            "ts": now.isoformat(),
        })

    return report


# =============================================================================
# FUNDAMENTALS: Income statement, balance sheet, cash flow — annual + quarterly + TTM
# =============================================================================
def transform_fundamentals(conn, files: List[Tuple[str, dict]], dry_run: bool) -> QualityReport:
    report = QualityReport(category="fundamentals", total_files=len(files))
    now = datetime.now(timezone.utc)
    module_id = ensure_module_registered(conn, "gurufocus_fundamentals_gold", "GuruFocus Fundamentals (Gold)", "weekly")

    rows_inserted = 0
    for symbol, data in files:
        report.loaded += 1

        if not isinstance(data, dict) or "annually" not in data:
            report.errors += 1
            continue

        report.bronze += 1
        bi = data.get("basic_information", {})
        gf_symbol = bi.get("symbol", symbol)

        periods = []

        for entry in data.get("annually", []):
            period = _extract_fundamental_period(entry, "annual")
            if period:
                periods.append(period)

        for entry in data.get("quarterly", []):
            period = _extract_fundamental_period(entry, "quarterly")
            if period:
                periods.append(period)

        ttm = data.get("ttm", {})
        if ttm:
            ttm_period = _extract_fundamental_period(ttm, "ttm")
            if ttm_period:
                periods.append(ttm_period)

        if not periods:
            report.issues.append(f"{symbol}: no extractable periods")
            continue

        has_revenue = sum(1 for p in periods if p["revenue"] is not None)
        completeness_ratio = has_revenue / len(periods) if periods else 0

        if completeness_ratio < 0.5:
            report.issues.append(f"{symbol}: low completeness ({has_revenue}/{len(periods)} have revenue)")
            continue

        report.silver += 1
        quality = min(100, int(60 + completeness_ratio * 40))

        if not dry_run:
            for p in periods:
                period_end = None
                if p["date"]:
                    try:
                        parts = p["date"].split("-")
                        if len(parts) == 2:
                            period_end = date(int(parts[0]), int(parts[1]), 1)
                        elif len(parts) == 3:
                            period_end = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    except (ValueError, IndexError):
                        pass

                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO gf_fundamentals (symbol, gf_symbol, period_type, period_end,
                            revenue, net_income, eps, total_assets, total_liabilities,
                            free_cash_flow, roe, roa, debt_to_equity, payload)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (symbol, period_type, period_end) DO UPDATE SET
                            payload = EXCLUDED.payload, revenue = EXCLUDED.revenue,
                            net_income = EXCLUDED.net_income, eps = EXCLUDED.eps,
                            total_assets = EXCLUDED.total_assets, total_liabilities = EXCLUDED.total_liabilities,
                            free_cash_flow = EXCLUDED.free_cash_flow""",
                        (symbol, gf_symbol, p["period_type"], period_end,
                         p["revenue"], p["net_income"], p["eps"],
                         p["total_assets"], p["total_liabilities"], p["free_cash_flow"],
                         p["roe"], p["roa"], p["debt_to_equity"],
                         json.dumps(p["raw"], default=str)),
                    )
                rows_inserted += 1

            tier = "gold" if quality >= 80 else "silver"
            latest = periods[-1]
            dp_payload = {
                "source": "gurufocus",
                "periods_count": len(periods),
                "annual_count": sum(1 for p in periods if p["period_type"] == "annual"),
                "quarterly_count": sum(1 for p in periods if p["period_type"] == "quarterly"),
                "latest_revenue": latest["revenue"],
                "latest_net_income": latest["net_income"],
                "latest_eps": latest["eps"],
                "latest_period": latest["date"],
            }
            dp_payload = {k: v for k, v in dp_payload.items() if v is not None}
            insert_data_point(conn, module_id, symbol, now, "weekly", tier, quality, dp_payload)
            cache_latest("gurufocus_fundamentals", symbol, dp_payload)

            if quality >= 80:
                report.gold += 1

        conn.commit()

    report.completeness = (report.silver / report.loaded * 100) if report.loaded else 0
    report.accuracy = (report.gold / max(report.silver, 1) * 100) if report.silver else 0

    if not dry_run:
        publish_event("quantclaw.pipeline.gold.fundamentals", {
            "module": "gurufocus_fundamentals_gold",
            "count": rows_inserted,
            "symbols": report.silver,
            "quality_score": report.overall_score,
            "ts": now.isoformat(),
        })

    logger.info(f"Fundamentals: {rows_inserted} period rows inserted across {report.silver} symbols")
    return report


def _extract_fundamental_period(entry: dict, period_type: str) -> Optional[dict]:
    if not isinstance(entry, dict):
        return None

    inc = entry.get("income_statement", {})
    bs = entry.get("balance_sheet", {})
    cf = entry.get("cashflow_statement", {})

    revenue = _safe_float(inc.get("revenue") or inc.get("total_revenue"))
    net_income = _safe_float(inc.get("net_income"))
    eps = _safe_float(inc.get("eps_diluated") or inc.get("eps_diluted") or inc.get("eps_basic"))
    total_assets = _safe_float(bs.get("total_assets"))
    total_liabilities = _safe_float(bs.get("total_liabilities"))
    fcf = None
    ocf = _safe_float(cf.get("cash_flow_from_operations"))
    capex = _safe_float(cf.get("cash_flow_capital_expenditure"))
    if ocf is not None and capex is not None:
        fcf = ocf + capex  # capex is typically negative

    roe = _safe_float(inc.get("roe"))
    roa = _safe_float(inc.get("roa"))
    de = _safe_float(bs.get("debt_to_equity"))

    if revenue is None and net_income is None and total_assets is None:
        return None

    return dict(
        date=entry.get("date"),
        period_type=period_type,
        revenue=revenue,
        net_income=net_income,
        eps=eps,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        free_cash_flow=fcf,
        roe=roe,
        roa=roa,
        debt_to_equity=de,
        raw=entry,
    )


# =============================================================================
# PROFILES: Company info, sector, industry, dividends, price, growth, ratios
# =============================================================================
def transform_profiles(conn, files: List[Tuple[str, dict]], dry_run: bool) -> QualityReport:
    report = QualityReport(category="profiles", total_files=len(files))
    now = datetime.now(timezone.utc)
    module_id = ensure_module_registered(conn, "gurufocus_profiles_gold", "GuruFocus Profiles (Gold)", "weekly")

    valid_rows = []
    for symbol, data in files:
        report.loaded += 1

        if not isinstance(data, dict):
            report.errors += 1
            continue

        report.bronze += 1

        bi = data.get("basic_information", {})
        gen = data.get("general", {})
        fund = data.get("fundamental", {})
        price_data = data.get("price", {})
        growth = data.get("growth", {})
        val_ratio = data.get("valuation_ratio", {})
        divs = data.get("dividends", {})
        prof = data.get("profitability", {})

        company_name = bi.get("company") or gen.get("company") or ""
        sector = gen.get("sector") or ""
        industry = gen.get("industry") or ""
        country = gen.get("country") or ""
        market_cap = _safe_float(fund.get("mktcap") or gen.get("mktcap"))
        employees = _safe_int(gen.get("number_of_employee"))
        description = gen.get("business_description", "")

        row = dict(
            symbol=symbol,
            gf_symbol=bi.get("symbol", symbol),
            company_name=company_name[:300] if company_name else None,
            sector=sector[:100] if sector else None,
            industry=industry[:200] if industry else None,
            country=country[:50] if country else None,
            market_cap=market_cap,
            employees=employees,
            description=description[:5000] if description else None,
        )

        dp_payload = dict(
            source="gurufocus",
            company=company_name,
            sector=sector,
            industry=industry,
            country=country,
            market_cap=market_cap,
            beta=_safe_float(price_data.get("beta")),
            current_price=_safe_float(price_data.get("price") or price_data.get("last")),
            sma_50=_safe_float(price_data.get("sma_50")),
            sma_200=_safe_float(price_data.get("sma_200")),
            ema_20=_safe_float(price_data.get("ema_20")),
            ema_50=_safe_float(price_data.get("ema_50")),
            ema_200=_safe_float(price_data.get("ema_200")),
            revenue_growth_1y=_safe_float(growth.get("revenue_growth_1y")),
            revenue_growth_3y=_safe_float(growth.get("revenue_growth_3y")),
            eps_growth_1y=_safe_float(growth.get("epsgrowth_1y")),
            eps_growth_3y=_safe_float(growth.get("epsgrowth_3y")),
            dividend_yield=_safe_float(divs.get("yield")),
            payout_ratio=_safe_float(divs.get("payout")),
            roe=_safe_float(prof.get("roe") if isinstance(prof, dict) else None),
            roa=_safe_float(prof.get("roa") if isinstance(prof, dict) else None),
            gross_margin=_safe_float(prof.get("grossmargin") if isinstance(prof, dict) else None),
            net_margin=_safe_float(prof.get("netmargin") if isinstance(prof, dict) else None),
            pe_ratio=_safe_float(val_ratio.get("PE")),
            pb_ratio=_safe_float(val_ratio.get("PB")),
            ps_ratio=_safe_float(val_ratio.get("PS")),
            ev_ebitda=_safe_float(val_ratio.get("EV2EBITDA")),
            fcf_yield=_safe_float(val_ratio.get("FCFyield")),
        )
        dp_payload = {k: v for k, v in dp_payload.items() if v is not None}

        has_name = bool(company_name)
        has_sector = bool(sector)
        info_score = sum(1 for v in [company_name, sector, industry, country, description] if v)

        if has_name and info_score >= 3:
            report.silver += 1
            row["_dp_payload"] = dp_payload
            row["_full_payload"] = data
            row["_quality"] = min(100, 70 + info_score * 6)
            valid_rows.append(row)
        else:
            report.issues.append(f"{symbol}: incomplete profile (score={info_score}/5)")

    report.completeness = (len(valid_rows) / report.loaded * 100) if report.loaded else 0
    report.accuracy = (sum(1 for r in valid_rows if r["_quality"] >= 85) / len(valid_rows) * 100) if valid_rows else 0

    if not dry_run and valid_rows:
        for row in valid_rows:
            dp_payload = row.pop("_dp_payload")
            full_payload = row.pop("_full_payload")
            quality = row.pop("_quality")
            tier = "gold" if report.passed_gold else "silver"

            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO gf_profiles (symbol, gf_symbol, company_name, sector, industry,
                        country, market_cap, employees, description, payload)
                       VALUES (%(symbol)s, %(gf_symbol)s, %(company_name)s, %(sector)s, %(industry)s,
                        %(country)s, %(market_cap)s, %(employees)s, %(description)s, %(payload)s)
                       ON CONFLICT (symbol) DO UPDATE SET
                        company_name = EXCLUDED.company_name, sector = EXCLUDED.sector,
                        industry = EXCLUDED.industry, market_cap = EXCLUDED.market_cap,
                        employees = EXCLUDED.employees, payload = EXCLUDED.payload,
                        fetched_at = NOW()""",
                    {**row, "payload": json.dumps(full_payload, default=str)},
                )

            insert_data_point(conn, module_id, row["symbol"], now, "weekly", tier, quality, dp_payload)
            cache_latest("gurufocus_profiles", row["symbol"], dp_payload)

            if report.passed_gold:
                report.gold += 1

        conn.commit()
        publish_event("quantclaw.pipeline.gold.fundamentals", {
            "module": "gurufocus_profiles_gold",
            "count": len(valid_rows),
            "quality_score": report.overall_score,
            "ts": now.isoformat(),
        })

    return report


# =============================================================================
# ORCHESTRATOR
# =============================================================================
TRANSFORMERS = {
    "rankings": ("rankings", transform_rankings),
    "valuations": ("valuations", transform_valuations),
    "fundamentals": ("fundamentals", transform_fundamentals),
    "profiles": ("profiles", transform_profiles),
}


def main():
    parser = argparse.ArgumentParser(description="GuruFocus Gold Transformer")
    parser.add_argument("--category", choices=list(TRANSFORMERS.keys()) + ["all"], default="all")
    parser.add_argument("--test", type=int, help="Limit to N files per category")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    categories = list(TRANSFORMERS.keys()) if args.category == "all" else [args.category]

    conn = get_conn()
    t0 = time.time()
    results = {}

    for cat in categories:
        dir_name, transformer = TRANSFORMERS[cat]
        logger.info(f"{'='*60}")
        logger.info(f"TRANSFORMING: {cat.upper()}")
        logger.info(f"{'='*60}")

        files = load_json_files(dir_name)
        if args.test:
            files = files[:args.test]

        logger.info(f"Loaded {len(files)} files from {dir_name}/")

        try:
            report = transformer(conn, files, dry_run=args.dry_run)
            results[cat] = report
            tier_label = "GOLD" if report.passed_gold else "SILVER"
            logger.info(
                f"{cat}: {report.loaded} loaded → {report.bronze} bronze → "
                f"{report.silver} silver → {report.gold} gold | "
                f"Quality: {report.overall_score}% ({tier_label}) | "
                f"Errors: {report.errors}"
            )
        except Exception as e:
            conn.rollback()
            logger.error(f"{cat} FAILED: {e}", exc_info=True)
            results[cat] = QualityReport(category=cat, issues=[str(e)])

    elapsed = time.time() - t0
    conn.close()

    print(f"\n{'='*60}")
    print(f"GURUFOCUS GOLD TRANSFORMATION COMPLETE")
    print(f"Time: {elapsed:.1f}s | Dry run: {args.dry_run}")
    print(f"{'='*60}")

    for cat, report in results.items():
        tier = "GOLD" if report.passed_gold else "SILVER" if report.silver > 0 else "BRONZE"
        print(f"  {cat:15s}: {report.loaded:3d} → B:{report.bronze:3d} → S:{report.silver:3d} → G:{report.gold:3d} "
              f"| Score:{report.overall_score:3d}% [{tier}] | Err:{report.errors}")

    total_gold = sum(r.gold for r in results.values())
    total_loaded = sum(r.loaded for r in results.values())
    print(f"\n  TOTAL: {total_loaded} files processed, {total_gold} reached Gold")

    if any(r.issues for r in results.values()):
        print(f"\n  Issues (first 10 per category):")
        for cat, report in results.items():
            for issue in report.issues[:10]:
                print(f"    [{cat}] {issue}")

    return results


if __name__ == "__main__":
    main()
