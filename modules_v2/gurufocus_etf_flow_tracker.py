"""
GuruFocus ETF Flow Tracker — Track ETF holding changes for flow signals.

Composite module: reads from gf_etf_holdings table.
Detects weight changes between snapshots as proxy for fund flows.
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

logger = logging.getLogger("quantclaw.gurufocus.etf_flow")


class GurufocusETFFlowTracker(BaseModule):
    name = "gurufocus_etf_flow_tracker"
    display_name = "GuruFocus — ETF Flow Tracker"
    cadence = "weekly"
    granularity = "symbol"
    tags = ["ETF", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """WITH ranked AS (
                    SELECT etf_symbol, holding_symbol, holding_name, weight, shares, market_value,
                           fetched_at,
                           LAG(weight) OVER (PARTITION BY etf_symbol, holding_symbol ORDER BY fetched_at) as prev_weight,
                           LAG(shares) OVER (PARTITION BY etf_symbol, holding_symbol ORDER BY fetched_at) as prev_shares,
                           ROW_NUMBER() OVER (PARTITION BY etf_symbol, holding_symbol ORDER BY fetched_at DESC) as rn
                    FROM gf_etf_holdings
                    WHERE holding_symbol IS NOT NULL
                 )
                 SELECT * FROM ranked WHERE rn = 1 AND prev_weight IS NOT NULL
                 ORDER BY ABS(weight - prev_weight) DESC NULLS LAST
                 LIMIT 200""",
                fetch=True,
            )

            for row in (rows or []):
                weight = float(row.get("weight") or 0)
                prev_weight = float(row.get("prev_weight") or 0)
                weight_change = round(weight - prev_weight, 4)

                if abs(weight_change) < 0.01:
                    continue

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row.get("holding_symbol", ""),
                    cadence="weekly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "etf_flow",
                        "etf_symbol": row.get("etf_symbol"),
                        "holding_symbol": row.get("holding_symbol"),
                        "holding_name": row.get("holding_name"),
                        "current_weight": weight,
                        "prev_weight": prev_weight,
                        "weight_change": weight_change,
                        "direction": "inflow" if weight_change > 0 else "outflow",
                    },
                ))

        except Exception as e:
            logger.warning(f"ETF flow tracker failed: {e}")

        logger.info(f"ETF flow tracker: {len(points)} significant weight changes")
        return points


if __name__ == "__main__":
    mod = GurufocusETFFlowTracker()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
