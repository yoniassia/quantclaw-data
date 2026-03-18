"""
GuruFocus Quality Factor — Quality-minus-junk factor using GF financial strength.

Composite module: reads from gf_rankings + gf_fundamentals.
Computes a composite quality score for factor-based investing.
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

logger = logging.getLogger("quantclaw.gurufocus.quality_factor")


class GurufocusQualityFactor(BaseModule):
    name = "gurufocus_quality_factor"
    display_name = "GuruFocus — Quality Factor (QMJ)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        try:
            rows = execute_query(
                """SELECT DISTINCT ON (r.symbol)
                    r.symbol, r.gf_symbol,
                    r.gf_score, r.financial_strength, r.profitability_rank, r.growth_rank,
                    f.roe, f.roa, f.debt_to_equity, f.free_cash_flow, f.revenue
                 FROM gf_rankings r
                 LEFT JOIN LATERAL (
                    SELECT roe, roa, debt_to_equity, free_cash_flow, revenue
                    FROM gf_fundamentals WHERE symbol = r.symbol ORDER BY fetched_at DESC LIMIT 1
                 ) f ON true
                 WHERE r.gf_score IS NOT NULL
                 ORDER BY r.symbol, r.fetched_at DESC""",
                fetch=True,
            )

            for row in (rows or []):
                fs = float(row.get("financial_strength") or 0)
                prof = float(row.get("profitability_rank") or 0)
                growth = float(row.get("growth_rank") or 0)
                roe = float(row.get("roe") or 0)
                de = float(row.get("debt_to_equity") or 0)

                # Composite quality score (0-100)
                quality = (fs * 0.3 + prof * 0.3 + growth * 0.2) / 10  # normalize to 0-100 range
                if roe > 0.15:
                    quality += 10
                if de < 0.5 and de > 0:
                    quality += 5
                quality = min(100, max(0, quality))

                tier = "premium" if quality >= 70 else "standard" if quality >= 40 else "junk"

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=row["symbol"],
                    cadence="daily",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "quality_factor",
                        "gf_symbol": row.get("gf_symbol"),
                        "quality_score": round(quality, 1),
                        "quality_tier": tier,
                        "financial_strength": fs,
                        "profitability": prof,
                        "growth": growth,
                        "roe": roe,
                        "debt_to_equity": de,
                    },
                ))

        except Exception as e:
            logger.warning(f"Quality factor failed: {e}")

        logger.info(f"Quality factor: {len(points)} stocks scored")
        return points


if __name__ == "__main__":
    mod = GurufocusQualityFactor()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
