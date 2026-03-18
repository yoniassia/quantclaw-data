"""
GuruFocus Guru Portfolio Module — Full guru portfolio snapshots with conviction scoring.

Source: gurufocus.com/data API (Enterprise)
Cadence: Weekly
Granularity: Guru-level
Tags: Insider, Fundamentals, GuruFocus

Computes conviction scores: stocks held by multiple top gurus get higher scores.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

logger = logging.getLogger("quantclaw.gurufocus.guru_portfolio")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class GurufocusGuruPortfolio(BaseModule):
    name = "gurufocus_guru_portfolio"
    display_name = "GuruFocus — Guru Portfolio & Consensus"
    cadence = "weekly"
    granularity = "global"
    tags = ["Insider", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        """
        Reads from gf_guru_holdings (populated by guru_tracker module)
        and computes consensus/conviction metrics.
        """
        points = []

        try:
            consensus = execute_query(
                """SELECT
                    h.symbol,
                    COUNT(DISTINCT h.guru_id) as guru_count,
                    AVG(h.portfolio_weight) as avg_weight,
                    MAX(h.portfolio_weight) as max_weight,
                    SUM(h.market_value) as total_guru_value,
                    ARRAY_AGG(DISTINCT g.name ORDER BY g.name) as guru_names
                 FROM gf_guru_holdings h
                 JOIN gf_gurus g ON g.guru_id = h.guru_id
                 WHERE h.symbol IS NOT NULL AND h.symbol != ''
                 GROUP BY h.symbol
                 HAVING COUNT(DISTINCT h.guru_id) >= 2
                 ORDER BY COUNT(DISTINCT h.guru_id) DESC, AVG(h.portfolio_weight) DESC
                 LIMIT 200""",
                fetch=True,
            )

            for row in (consensus or []):
                guru_count = int(row.get("guru_count", 0))
                avg_weight = _safe_float(row.get("avg_weight"))
                conviction_score = min(100, guru_count * 10 + (avg_weight or 0) * 20)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="weekly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "guru_consensus",
                        "guru_count": guru_count,
                        "avg_portfolio_weight": avg_weight,
                        "max_portfolio_weight": _safe_float(row.get("max_weight")),
                        "total_guru_value": _safe_float(row.get("total_guru_value")),
                        "conviction_score": round(conviction_score, 1),
                        "guru_names": row.get("guru_names", []),
                    },
                ))

        except Exception as e:
            logger.warning(f"Guru portfolio consensus computation failed: {e}")

        logger.info(f"Guru portfolio: {len(points)} consensus entries computed")
        return points


if __name__ == "__main__":
    mod = GurufocusGuruPortfolio()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
