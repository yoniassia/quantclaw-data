"""
GuruFocus Segments Module — Business line revenue/profit decomposition.

Source: gurufocus.com/data API (Enterprise)
Cadence: Weekly
Granularity: Symbol-level
Tags: US Equities, Fundamentals, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query
from modules_v2.gurufocus_client import get_segment
from modules_v2.gurufocus_symbol_map import get_all_mappings

logger = logging.getLogger("quantclaw.gurufocus.segments")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class GurufocusSegments(BaseModule):
    name = "gurufocus_segments"
    display_name = "GuruFocus — Business Segments"
    cadence = "weekly"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        mappings = get_all_mappings()
        if symbols:
            mappings = {k: v for k, v in mappings.items() if k in symbols}

        points = []
        errors = 0
        for etoro_sym, gf_sym in mappings.items():
            try:
                data = get_segment(gf_sym)
                if not data or isinstance(data, str):
                    errors += 1
                    continue

                segments = data if isinstance(data, list) else data.get("data", data.get("segments", []))
                if not isinstance(segments, list):
                    segments = [data] if isinstance(data, dict) else []

                for seg in segments:
                    seg_name = seg.get("name", seg.get("segment_name", "Unknown"))
                    seg_type = seg.get("type", seg.get("segment_type", "business"))
                    revenue = _safe_float(seg.get("revenue"))
                    profit = _safe_float(seg.get("profit", seg.get("operating_income")))
                    period = seg.get("period_end", seg.get("date"))
                    period_date = None
                    if period:
                        try:
                            period_date = datetime.strptime(str(period)[:10], "%Y-%m-%d").date()
                        except ValueError:
                            pass

                    execute_query(
                        """INSERT INTO gf_segments (symbol, gf_symbol, segment_name, segment_type,
                            revenue, profit, period_end, payload)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (etoro_sym, gf_sym, seg_name, seg_type, revenue, profit, period_date,
                         json.dumps(seg, default=str)[:5000]),
                    )

                    points.append(DataPoint(
                        ts=datetime.now(timezone.utc),
                        symbol=etoro_sym,
                        cadence="weekly",
                        tier="bronze",
                        payload={
                            "source": "gurufocus",
                            "gf_symbol": gf_sym,
                            "segment_name": seg_name,
                            "segment_type": seg_type,
                            "revenue": revenue,
                            "profit": profit,
                        },
                    ))
            except Exception as e:
                errors += 1
                logger.warning(f"Segments failed for {gf_sym}: {e}")

        logger.info(f"Segments fetched: {len(points)} segments from {len(mappings)} symbols, {errors} errors")
        return points


if __name__ == "__main__":
    mod = GurufocusSegments()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
