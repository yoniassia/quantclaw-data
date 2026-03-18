"""
GuruFocus Rankings Module — GF Score, financial strength, profitability, growth, value, momentum.

Source: gurufocus.com/data API (Enterprise)
Cadence: Daily
Granularity: Symbol-level
Tags: US Equities, Fundamentals, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query, execute_many
from modules_v2.gurufocus_client import get_rankings
from modules_v2.gurufocus_symbol_map import get_all_mappings

logger = logging.getLogger("quantclaw.gurufocus.rankings")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class GurufocusRankings(BaseModule):
    name = "gurufocus_rankings"
    display_name = "GuruFocus — Stock Rankings & GF Score"
    cadence = "daily"
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
                data = get_rankings(gf_sym)
                if not data or isinstance(data, str):
                    errors += 1
                    continue

                flat = _flatten(data) if isinstance(data, dict) else data
                if isinstance(flat, list):
                    flat = flat[0] if flat else {}

                # Store structured data in GF-specific table
                self._store_ranking(etoro_sym, gf_sym, flat)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=etoro_sym,
                    cadence="daily",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "gf_symbol": gf_sym,
                        "gf_score": _safe_float(flat.get("gf_score")),
                        "financial_strength": _safe_float(flat.get("financial_strength")),
                        "profitability_rank": _safe_float(flat.get("profitability_rank")),
                        "growth_rank": _safe_float(flat.get("growth_rank")),
                        "gf_value_rank": _safe_float(flat.get("gf_value_rank")),
                        "momentum_rank": _safe_float(flat.get("momentum_rank")),
                        "predictability_rank": flat.get("predictability_rank"),
                    },
                ))
            except Exception as e:
                errors += 1
                logger.warning(f"Rankings failed for {gf_sym}: {e}")

        logger.info(f"Rankings fetched: {len(points)} ok, {errors} errors from {len(mappings)} symbols")
        return points

    def _store_ranking(self, etoro_sym: str, gf_sym: str, data: Dict):
        execute_query(
            """INSERT INTO gf_rankings (symbol, gf_symbol, gf_score, financial_strength,
                profitability_rank, growth_rank, gf_value_rank, momentum_rank,
                predictability_rank, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (symbol, fetched_at) DO UPDATE SET
                payload = EXCLUDED.payload, gf_score = EXCLUDED.gf_score""",
            (
                etoro_sym, gf_sym,
                _safe_float(data.get("gf_score")),
                _safe_float(data.get("financial_strength")),
                _safe_float(data.get("profitability_rank")),
                _safe_float(data.get("growth_rank")),
                _safe_float(data.get("gf_value_rank")),
                _safe_float(data.get("momentum_rank")),
                data.get("predictability_rank"),
                json.dumps(data, default=str),
            ),
        )


def _flatten(d: Dict, parent_key: str = "", sep: str = "_") -> Dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


if __name__ == "__main__":
    mod = GurufocusRankings()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
