"""
GuruFocus ETF Module — Full ETF composition, holdings, and weight tracking.

Source: gurufocus.com/data API (Enterprise)
Cadence: Weekly
Granularity: Symbol-level (ETF symbol → holdings)
Tags: ETF, Fundamentals, GuruFocus
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
from modules_v2.gurufocus_client import get_etf_data

logger = logging.getLogger("quantclaw.gurufocus.etf")

MAJOR_ETFS = [
    "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "ARKK", "XLF", "XLK", "XLE",
    "XLV", "XLI", "XLP", "XLU", "XLY", "XLB", "XLRE", "XLC", "VGK", "EFA",
    "EEM", "GLD", "SLV", "TLT", "HYG", "LQD", "IBIT", "ETHA", "SOXX", "SMH",
]


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class GurufocusETF(BaseModule):
    name = "gurufocus_etf_holdings"
    display_name = "GuruFocus — ETF Holdings"
    cadence = "weekly"
    granularity = "symbol"
    tags = ["ETF", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        etf_list = symbols or MAJOR_ETFS
        points = []
        errors = 0

        for etf_sym in etf_list:
            try:
                data = get_etf_data(etf_sym)
                if not data or isinstance(data, str):
                    errors += 1
                    continue

                holdings = data.get("holdings", data.get("data", []))
                if isinstance(holdings, dict):
                    holdings = holdings.get("data", [])
                if not isinstance(holdings, list):
                    holdings = []

                for holding in holdings[:100]:
                    h_sym = holding.get("symbol", holding.get("ticker", ""))
                    h_name = holding.get("name", holding.get("company", ""))
                    weight = _safe_float(holding.get("weight", holding.get("percentage")))
                    shares = _safe_float(holding.get("shares"))
                    mkt_val = _safe_float(holding.get("market_value", holding.get("value")))

                    execute_query(
                        """INSERT INTO gf_etf_holdings (etf_symbol, holding_symbol, holding_name,
                            weight, shares, market_value, payload)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (etf_symbol, holding_symbol, fetched_at) DO UPDATE SET
                            weight = EXCLUDED.weight, payload = EXCLUDED.payload""",
                        (etf_sym, h_sym, h_name, weight, shares, mkt_val,
                         json.dumps(holding, default=str)[:3000]),
                    )

                    points.append(DataPoint(
                        ts=datetime.now(timezone.utc),
                        symbol=etf_sym,
                        cadence="weekly",
                        tier="bronze",
                        payload={
                            "source": "gurufocus",
                            "etf_symbol": etf_sym,
                            "holding_symbol": h_sym,
                            "holding_name": h_name,
                            "weight": weight,
                        },
                    ))

            except Exception as e:
                errors += 1
                logger.warning(f"ETF data failed for {etf_sym}: {e}")

        logger.info(f"ETF holdings fetched: {len(points)} holdings from {len(etf_list)} ETFs, {errors} errors")
        return points


if __name__ == "__main__":
    mod = GurufocusETF()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
