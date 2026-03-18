"""
GuruFocus Stock Universe Module — All GF stocks by region, mapped to eToro instruments.

Source: gurufocus.com/data API (Enterprise)
Cadence: Monthly (universe rarely changes)
Granularity: Global
Tags: US Equities, EU Equities, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query
from modules_v2.gurufocus_client import get_stocks_by_region

logger = logging.getLogger("quantclaw.gurufocus.universe")

REGIONS = {
    "U": "US",
    "B": "UK",
    "E": "Europe",
    "A": "Asia",
    "O": "Australia",
}


class GurufocusStockUniverse(BaseModule):
    name = "gurufocus_stock_universe"
    display_name = "GuruFocus — Stock Universe"
    cadence = "monthly"
    granularity = "global"
    tags = ["US Equities"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        errors = 0
        total_stocks = 0

        for region_code, region_name in REGIONS.items():
            try:
                data = get_stocks_by_region(region_code)
                if not data:
                    continue

                stocks = data if isinstance(data, list) else data.get("data", data.get("stocks", []))
                if isinstance(stocks, dict):
                    for key in ["data", "stocks", "results"]:
                        if key in stocks:
                            stocks = stocks[key]
                            break
                if not isinstance(stocks, list):
                    continue

                for stock in stocks:
                    sym = stock.get("symbol", "")
                    company = stock.get("company", "")
                    exchange = stock.get("exchange", "")
                    stockid = stock.get("stockid", "")

                    if sym:
                        execute_query(
                            """INSERT INTO gf_symbol_map (etoro_symbol, gf_symbol, exchange)
                               VALUES (%s, %s, %s)
                               ON CONFLICT (etoro_symbol) DO UPDATE SET
                                gf_symbol = EXCLUDED.gf_symbol,
                                exchange = EXCLUDED.exchange""",
                            (sym.split(":")[-1] if ":" in sym else sym, sym, exchange),
                        )

                    total_stocks += 1

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=None,
                    cadence="monthly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "region": region_name,
                        "region_code": region_code,
                        "stock_count": len(stocks) if isinstance(stocks, list) else 0,
                    },
                ))

            except Exception as e:
                errors += 1
                logger.warning(f"Universe fetch failed for region {region_code}: {e}")

        logger.info(f"Universe fetched: {total_stocks} total stocks across {len(REGIONS)} regions, {errors} errors")
        return points


if __name__ == "__main__":
    mod = GurufocusStockUniverse()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
