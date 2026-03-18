"""
GuruFocus Fund Letters Module — Quarterly hedge fund letters.

Source: gurufocus.com/data API (Enterprise)
Cadence: Quarterly
Granularity: Global (not per-symbol)
Tags: Fundamentals, Insider, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from modules_v2.gurufocus_client import get_fund_letters

logger = logging.getLogger("quantclaw.gurufocus.fund_letters")

RECENT_QUARTERS = ["2025Q4", "2025Q3", "2025Q2", "2025Q1", "2024Q4", "2024Q3", "2024Q2", "2024Q1"]


class GurufocusFundLetters(BaseModule):
    name = "gurufocus_fund_letters"
    display_name = "GuruFocus — Fund Letters"
    cadence = "quarterly"
    granularity = "global"
    tags = ["Fundamentals", "Insider"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        errors = 0

        for quarter in RECENT_QUARTERS:
            try:
                data = get_fund_letters(quarter)
                if not data:
                    continue

                letters = data if isinstance(data, list) else data.get("data", data.get("letters", []))
                if not isinstance(letters, list):
                    continue

                for letter in letters:
                    fund_name = letter.get("fund_name", letter.get("name", "Unknown"))
                    points.append(DataPoint(
                        ts=datetime.now(timezone.utc),
                        symbol=None,
                        cadence="quarterly",
                        tier="bronze",
                        payload={
                            "source": "gurufocus",
                            "quarter": quarter,
                            "fund_name": fund_name,
                            "title": letter.get("title", ""),
                            "url": letter.get("url", letter.get("link", "")),
                            "date": letter.get("date", ""),
                        },
                    ))

            except Exception as e:
                errors += 1
                logger.warning(f"Fund letters failed for {quarter}: {e}")

        logger.info(f"Fund letters fetched: {len(points)} letters, {errors} errors")
        return points


if __name__ == "__main__":
    mod = GurufocusFundLetters()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
