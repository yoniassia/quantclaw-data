"""
GuruFocus Guru Rebalance Alert — Detect when gurus add/trim positions.

Composite module: reads from gf_guru_holdings table.
Flags significant position changes (new buys, >50% increases, full exits).
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

logger = logging.getLogger("quantclaw.gurufocus.guru_rebalance")


class GurufocusGuruRebalanceAlert(BaseModule):
    name = "gurufocus_guru_rebalance_alert"
    display_name = "GuruFocus — Guru Rebalance Alerts"
    cadence = "weekly"
    granularity = "global"
    tags = ["Insider", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """SELECT h.guru_id, g.name as guru_name, g.firm,
                    h.symbol, h.gf_symbol, h.change_type, h.change_pct,
                    h.shares, h.portfolio_weight, h.current_price, h.market_value,
                    h.portfolio_date
                 FROM gf_guru_holdings h
                 JOIN gf_gurus g ON g.guru_id = h.guru_id
                 WHERE h.change_type IS NOT NULL
                   AND h.change_type NOT IN ('', 'no_change')
                 ORDER BY h.fetched_at DESC
                 LIMIT 500""",
                fetch=True,
            )

            for row in (rows or []):
                change_type = str(row.get("change_type", "")).lower()
                change_pct = float(row.get("change_pct") or 0)

                is_significant = (
                    "new" in change_type or
                    "add" in change_type or
                    "sold" in change_type or
                    "exit" in change_type or
                    abs(change_pct) > 50
                )

                if not is_significant:
                    continue

                alert_level = "high" if ("new" in change_type or "exit" in change_type or abs(change_pct) > 100) else "medium"

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="weekly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "guru_rebalance",
                        "guru_name": row.get("guru_name"),
                        "firm": row.get("firm"),
                        "change_type": change_type,
                        "change_pct": change_pct,
                        "shares": float(row.get("shares") or 0),
                        "portfolio_weight": float(row.get("portfolio_weight") or 0),
                        "market_value": float(row.get("market_value") or 0),
                        "alert_level": alert_level,
                    },
                ))

        except Exception as e:
            logger.warning(f"Guru rebalance alert failed: {e}")

        logger.info(f"Guru rebalance alerts: {len(points)} significant changes")
        return points


if __name__ == "__main__":
    mod = GurufocusGuruRebalanceAlert()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
