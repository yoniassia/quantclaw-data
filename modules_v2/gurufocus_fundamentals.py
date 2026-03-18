"""
GuruFocus Fundamentals Module — Deep financial statements (income, balance sheet, cashflow).

Source: gurufocus.com/data API (Enterprise)
Cadence: Weekly (financials don't change daily)
Granularity: Symbol-level
Tags: US Equities, Fundamentals, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone, date
from typing import List, Optional, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query
from modules_v2.gurufocus_client import get_fundamentals
from modules_v2.gurufocus_symbol_map import get_all_mappings

logger = logging.getLogger("quantclaw.gurufocus.fundamentals")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _flatten(d: Dict, parent_key: str = "", sep: str = "_") -> Dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class GurufocusFundamentals(BaseModule):
    name = "gurufocus_fundamentals"
    display_name = "GuruFocus — Financial Statements"
    cadence = "weekly"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        mappings = get_all_mappings()
        if symbols:
            mappings = {k: v for k, v in mappings.items() if k in symbols}

        points = []
        errors = 0
        for etoro_sym, gf_sym in mappings.items():
            try:
                data = get_fundamentals(gf_sym)
                if not data or isinstance(data, str):
                    errors += 1
                    continue

                flat = _flatten(data) if isinstance(data, dict) else {}

                revenue = _safe_float(flat.get("Revenue") or flat.get("revenue"))
                net_income = _safe_float(flat.get("Net_Income") or flat.get("net_income"))
                eps = _safe_float(flat.get("EPS") or flat.get("eps_diluted") or flat.get("per_share_data_array_EPS_(Diluted)"))
                total_assets = _safe_float(flat.get("Total_Assets") or flat.get("total_assets"))
                total_liabilities = _safe_float(flat.get("Total_Liabilities") or flat.get("total_liabilities"))
                fcf = _safe_float(flat.get("Free_Cash_Flow") or flat.get("free_cash_flow"))
                roe = _safe_float(flat.get("ROE") or flat.get("roe"))
                roa = _safe_float(flat.get("ROA") or flat.get("roa"))
                de = _safe_float(flat.get("Debt-to-Equity") or flat.get("debt_to_equity"))

                self._store_fundamental(etoro_sym, gf_sym, "annual", None,
                    revenue, net_income, eps, total_assets, total_liabilities, fcf, roe, roa, de, flat)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=etoro_sym,
                    cadence="weekly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "gf_symbol": gf_sym,
                        "revenue": revenue,
                        "net_income": net_income,
                        "eps": eps,
                        "total_assets": total_assets,
                        "total_liabilities": total_liabilities,
                        "free_cash_flow": fcf,
                        "roe": roe,
                        "roa": roa,
                        "debt_to_equity": de,
                    },
                ))
            except Exception as e:
                errors += 1
                logger.warning(f"Fundamentals failed for {gf_sym}: {e}")

        logger.info(f"Fundamentals fetched: {len(points)} ok, {errors} errors")
        return points

    def _store_fundamental(self, etoro_sym, gf_sym, period_type, period_end,
                           revenue, net_income, eps, assets, liabilities, fcf, roe, roa, de, flat):
        execute_query(
            """INSERT INTO gf_fundamentals (symbol, gf_symbol, period_type, period_end,
                revenue, net_income, eps, total_assets, total_liabilities,
                free_cash_flow, roe, roa, debt_to_equity, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (symbol, period_type, period_end) DO UPDATE SET
                payload = EXCLUDED.payload, revenue = EXCLUDED.revenue,
                net_income = EXCLUDED.net_income, eps = EXCLUDED.eps""",
            (etoro_sym, gf_sym, period_type, period_end,
             revenue, net_income, eps, assets, liabilities, fcf, roe, roa, de,
             json.dumps(flat, default=str)),
        )


if __name__ == "__main__":
    mod = GurufocusFundamentals()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
