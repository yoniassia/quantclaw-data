"""
GuruFocus Profile Module — Company profiles with sector, industry, description, market cap.

Source: gurufocus.com/data API (Enterprise)
Cadence: Weekly (profiles rarely change)
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
from modules_v2.gurufocus_client import get_profile
from modules_v2.gurufocus_symbol_map import get_all_mappings

logger = logging.getLogger("quantclaw.gurufocus.profile")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


class GurufocusProfile(BaseModule):
    name = "gurufocus_profile"
    display_name = "GuruFocus — Company Profiles"
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
                data = get_profile(gf_sym)
                if not data or isinstance(data, str):
                    errors += 1
                    continue

                company = data.get("company", data.get("name", data.get("company_name", "")))
                sector = data.get("sector", "")
                industry = data.get("industry", "")
                country = data.get("country", data.get("headquarter_country", ""))
                mktcap = _safe_float(data.get("marketcap", data.get("market_cap")))
                employees = _safe_int(data.get("employees", data.get("num_employees")))
                desc = data.get("description", data.get("company_description", ""))

                self._store_profile(etoro_sym, gf_sym, company, sector, industry, country, mktcap, employees, desc, data)

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=etoro_sym,
                    cadence="weekly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "gf_symbol": gf_sym,
                        "company_name": company,
                        "sector": sector,
                        "industry": industry,
                        "country": country,
                        "market_cap": mktcap,
                        "employees": employees,
                    },
                ))
            except Exception as e:
                errors += 1
                logger.warning(f"Profile failed for {gf_sym}: {e}")

        logger.info(f"Profiles fetched: {len(points)} ok, {errors} errors")
        return points

    def _store_profile(self, etoro_sym, gf_sym, company, sector, industry, country, mktcap, employees, desc, data):
        execute_query(
            """INSERT INTO gf_profiles (symbol, gf_symbol, company_name, sector, industry,
                country, market_cap, employees, description, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (symbol) DO UPDATE SET
                company_name = EXCLUDED.company_name, sector = EXCLUDED.sector,
                industry = EXCLUDED.industry, country = EXCLUDED.country,
                market_cap = EXCLUDED.market_cap, employees = EXCLUDED.employees,
                description = EXCLUDED.description, payload = EXCLUDED.payload,
                fetched_at = NOW()""",
            (etoro_sym, gf_sym, company, sector, industry, country, mktcap, employees,
             (desc or "")[:5000], json.dumps(data, default=str)[:10000]),
        )


if __name__ == "__main__":
    mod = GurufocusProfile()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
