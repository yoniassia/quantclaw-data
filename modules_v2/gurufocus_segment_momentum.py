"""
GuruFocus Segment Momentum — Track business segment revenue growth trends.

Composite module: reads from gf_segments table.
Identifies accelerating/decelerating business lines.
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

logger = logging.getLogger("quantclaw.gurufocus.segment_momentum")


class GurufocusSegmentMomentum(BaseModule):
    name = "gurufocus_segment_momentum"
    display_name = "GuruFocus — Segment Momentum"
    cadence = "weekly"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """SELECT symbol, gf_symbol, segment_name,
                    revenue, profit, period_end,
                    LAG(revenue) OVER (PARTITION BY symbol, segment_name ORDER BY period_end) as prev_revenue,
                    LAG(profit) OVER (PARTITION BY symbol, segment_name ORDER BY period_end) as prev_profit
                 FROM gf_segments
                 WHERE revenue IS NOT NULL AND revenue > 0
                 ORDER BY symbol, segment_name, period_end DESC""",
                fetch=True,
            )

            for row in (rows or []):
                rev = float(row.get("revenue") or 0)
                prev_rev = float(row.get("prev_revenue") or 0)
                if prev_rev <= 0 or rev <= 0:
                    continue

                growth_pct = round((rev - prev_rev) / prev_rev * 100, 1)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="weekly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "segment_momentum",
                        "gf_symbol": row.get("gf_symbol"),
                        "segment_name": row.get("segment_name"),
                        "revenue": rev,
                        "prev_revenue": prev_rev,
                        "growth_pct": growth_pct,
                        "trend": "accelerating" if growth_pct > 10 else "decelerating" if growth_pct < -10 else "stable",
                    },
                ))

        except Exception as e:
            logger.warning(f"Segment momentum failed: {e}")

        logger.info(f"Segment momentum: {len(points)} segments analyzed")
        return points


if __name__ == "__main__":
    mod = GurufocusSegmentMomentum()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
