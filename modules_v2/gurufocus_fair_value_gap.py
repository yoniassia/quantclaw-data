"""
GuruFocus Fair Value Gap — Current price vs GF fair value → opportunity score.

Composite module: reads from gf_valuations table.
Ranks stocks by largest gap between price and fair value.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

logger = logging.getLogger("quantclaw.gurufocus.fair_value_gap")


class GurufocusFairValueGap(BaseModule):
    name = "gurufocus_fair_value_gap"
    display_name = "GuruFocus — Fair Value Gap"
    cadence = "daily"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """SELECT DISTINCT ON (symbol)
                    symbol, gf_symbol, gf_value, dcf_value, graham_number,
                    current_price, price_to_gf_value
                 FROM gf_valuations
                 WHERE gf_value IS NOT NULL AND gf_value > 0
                   AND current_price IS NOT NULL AND current_price > 0
                 ORDER BY symbol, fetched_at DESC""",
                fetch=True,
            )

            for row in (rows or []):
                price = float(row.get("current_price") or 0)
                gf_val = float(row.get("gf_value") or 0)
                dcf = float(row.get("dcf_value") or 0)
                graham = float(row.get("graham_number") or 0)

                if gf_val <= 0:
                    continue

                gap_pct = round((gf_val - price) / gf_val * 100, 1)

                models_below = 0
                if dcf > 0 and price < dcf:
                    models_below += 1
                if graham > 0 and price < graham:
                    models_below += 1
                if price < gf_val:
                    models_below += 1

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="daily",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "fair_value_gap",
                        "gf_symbol": row.get("gf_symbol"),
                        "current_price": price,
                        "gf_value": gf_val,
                        "dcf_value": dcf,
                        "graham_number": graham,
                        "gap_pct": gap_pct,
                        "models_below_price": models_below,
                        "signal": "undervalued" if gap_pct > 20 else "overvalued" if gap_pct < -20 else "fair",
                    },
                ))

        except Exception as e:
            logger.warning(f"Fair value gap failed: {e}")

        logger.info(f"Fair value gap: {len(points)} stocks analyzed")
        return points


if __name__ == "__main__":
    mod = GurufocusFairValueGap()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
