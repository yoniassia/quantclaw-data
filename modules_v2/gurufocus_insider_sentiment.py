"""
GuruFocus Insider Sentiment — Aggregate insider buy/sell ratio as sentiment signal.

Composite module: reads from gf_insider_trades table.
Produces buy/sell ratios and net insider sentiment per symbol.
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

logger = logging.getLogger("quantclaw.gurufocus.insider_sentiment")


class GurufocusInsiderSentiment(BaseModule):
    name = "gurufocus_insider_sentiment"
    display_name = "GuruFocus — Insider Sentiment"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Insider", "Sentiment"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """SELECT
                    symbol,
                    COUNT(*) FILTER (WHERE trade_type ILIKE '%buy%' OR trade_type ILIKE '%purchase%') as buys,
                    COUNT(*) FILTER (WHERE trade_type ILIKE '%sell%' OR trade_type ILIKE '%sale%') as sells,
                    SUM(total_value) FILTER (WHERE trade_type ILIKE '%buy%' OR trade_type ILIKE '%purchase%') as buy_value,
                    SUM(total_value) FILTER (WHERE trade_type ILIKE '%sell%' OR trade_type ILIKE '%sale%') as sell_value,
                    COUNT(DISTINCT insider_name) as unique_insiders
                 FROM gf_insider_trades
                 WHERE trade_date >= CURRENT_DATE - 30
                 AND symbol IS NOT NULL AND symbol != ''
                 GROUP BY symbol
                 HAVING COUNT(*) >= 2
                 ORDER BY COUNT(*) DESC""",
                fetch=True,
            )

            for row in (rows or []):
                buys = int(row.get("buys") or 0)
                sells = int(row.get("sells") or 0)
                total = buys + sells
                buy_ratio = buys / total if total > 0 else 0.5
                sentiment = "bullish" if buy_ratio > 0.6 else "bearish" if buy_ratio < 0.4 else "neutral"

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="daily",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "insider_sentiment",
                        "buys": buys,
                        "sells": sells,
                        "buy_ratio": round(buy_ratio, 3),
                        "buy_value": float(row.get("buy_value") or 0),
                        "sell_value": float(row.get("sell_value") or 0),
                        "unique_insiders": int(row.get("unique_insiders") or 0),
                        "sentiment": sentiment,
                        "period_days": 30,
                    },
                ))

        except Exception as e:
            logger.warning(f"Insider sentiment failed: {e}")

        logger.info(f"Insider sentiment: {len(points)} symbols with 30d activity")
        return points


if __name__ == "__main__":
    mod = GurufocusInsiderSentiment()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
