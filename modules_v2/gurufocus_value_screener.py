"""
GuruFocus Value Screener — Screen stocks by GF valuation metrics.

Composite module: reads from gf_valuations + gf_rankings tables.
Produces opportunity scores based on fair value gaps.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

logger = logging.getLogger("quantclaw.gurufocus.value_screener")


class GurufocusValueScreener(BaseModule):
    name = "gurufocus_value_screener"
    display_name = "GuruFocus — Value Screener"
    cadence = "daily"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """SELECT DISTINCT ON (v.symbol)
                    v.symbol, v.gf_symbol, v.gf_value, v.dcf_value, v.graham_number,
                    v.peter_lynch_value, v.current_price, v.price_to_gf_value,
                    r.gf_score, r.financial_strength, r.profitability_rank, r.growth_rank
                 FROM gf_valuations v
                 LEFT JOIN LATERAL (
                    SELECT gf_score, financial_strength, profitability_rank, growth_rank
                    FROM gf_rankings WHERE symbol = v.symbol ORDER BY fetched_at DESC LIMIT 1
                 ) r ON true
                 WHERE v.price_to_gf_value IS NOT NULL AND v.price_to_gf_value < 1.0
                 ORDER BY v.symbol, v.fetched_at DESC""",
                fetch=True,
            )

            for row in (rows or []):
                ratio = float(row.get("price_to_gf_value") or 999)
                gf_score = float(row.get("gf_score") or 0)
                discount_pct = round((1 - ratio) * 100, 1) if ratio < 1 else 0
                opportunity_score = round(discount_pct * 0.4 + gf_score * 0.6, 1)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="daily",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "value_screen",
                        "gf_symbol": row.get("gf_symbol"),
                        "current_price": float(row.get("current_price") or 0),
                        "gf_value": float(row.get("gf_value") or 0),
                        "price_to_gf_value": ratio,
                        "discount_pct": discount_pct,
                        "gf_score": gf_score,
                        "financial_strength": float(row.get("financial_strength") or 0),
                        "opportunity_score": opportunity_score,
                    },
                ))

        except Exception as e:
            logger.warning(f"Value screener failed: {e}")

        logger.info(f"Value screener: {len(points)} undervalued stocks found")
        return points


if __name__ == "__main__":
    mod = GurufocusValueScreener()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
