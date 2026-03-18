"""
GuruFocus Valuations Module — DCF, Graham Number, GF Value, Peter Lynch, fair value gap.

Source: gurufocus.com/data API (Enterprise)
Cadence: Daily
Granularity: Symbol-level
Tags: US Equities, Fundamentals, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query
from modules_v2.gurufocus_client import get_valuations
from modules_v2.gurufocus_symbol_map import get_all_mappings

logger = logging.getLogger("quantclaw.gurufocus.valuations")


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


class GurufocusValuations(BaseModule):
    name = "gurufocus_valuations"
    display_name = "GuruFocus — Valuations & Fair Value"
    cadence = "daily"
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
                data = get_valuations(gf_sym)
                if not data or isinstance(data, str):
                    errors += 1
                    continue

                flat = _flatten(data) if isinstance(data, dict) else {}

                gf_value = _safe_float(flat.get("gf_value") or flat.get("GFValue"))
                dcf = _safe_float(flat.get("dcf") or flat.get("DCF_growth_exit_10yr"))
                graham = _safe_float(flat.get("graham_number") or flat.get("GrahamNumber"))
                lynch = _safe_float(flat.get("peter_lynch_value") or flat.get("PeterLynch"))
                median_ps = _safe_float(flat.get("median_ps_value"))
                price = _safe_float(flat.get("price") or flat.get("current_price"))

                price_to_gf = None
                if price and gf_value and gf_value > 0:
                    price_to_gf = round(price / gf_value, 4)

                self._store_valuation(etoro_sym, gf_sym, gf_value, dcf, graham, lynch, median_ps, price, price_to_gf, flat)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=etoro_sym,
                    cadence="daily",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "gf_symbol": gf_sym,
                        "gf_value": gf_value,
                        "dcf_value": dcf,
                        "graham_number": graham,
                        "peter_lynch_value": lynch,
                        "median_ps_value": median_ps,
                        "current_price": price,
                        "price_to_gf_value": price_to_gf,
                    },
                ))
            except Exception as e:
                errors += 1
                logger.warning(f"Valuations failed for {gf_sym}: {e}")

        logger.info(f"Valuations fetched: {len(points)} ok, {errors} errors")
        return points

    def _store_valuation(self, etoro_sym, gf_sym, gf_value, dcf, graham, lynch, median_ps, price, ratio, flat):
        execute_query(
            """INSERT INTO gf_valuations (symbol, gf_symbol, gf_value, dcf_value,
                graham_number, peter_lynch_value, median_ps_value, current_price,
                price_to_gf_value, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (symbol, fetched_at) DO UPDATE SET
                payload = EXCLUDED.payload, gf_value = EXCLUDED.gf_value""",
            (etoro_sym, gf_sym, gf_value, dcf, graham, lynch, median_ps, price, ratio,
             json.dumps(flat, default=str)),
        )


if __name__ == "__main__":
    mod = GurufocusValuations()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
