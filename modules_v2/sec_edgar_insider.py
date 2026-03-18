"""
SEC EDGAR Insider Transactions — Insider buying/selling activity

Source: SEC EDGAR API (free, no key required)
Cadence: Daily
Granularity: Symbol-level
Tags: Insider, US Equities, Fundamentals
"""
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

SEC_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FILINGS = "https://efts.sec.gov/LATEST/search-index?q=%22{cik}%22&dateRange=custom&startdt={start}&enddt={end}&forms=4"
EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index?q={ticker}&forms=4&dateRange=custom&startdt={start}&enddt={end}"

SEC_HEADERS = {
    "User-Agent": "QuantClaw quantclaw@quantclaw.org",
    "Accept": "application/json",
}


class SecEdgarInsider(BaseModule):
    name = "sec_edgar_insider"
    display_name = "SEC EDGAR Insider Transactions"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Insider", "US Equities", "Fundamentals"]

    def _get_symbols(self) -> List[str]:
        rows = execute_query(
            "SELECT symbol FROM symbol_universe WHERE asset_class = 'stocks' AND is_active = true ORDER BY symbol",
            fetch=True,
        )
        return [r["symbol"] for r in (rows or [])]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if symbols is None:
            symbols = self._get_symbols()[:200]

        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        points = []
        for symbol in symbols:
            try:
                url = f"https://efts.sec.gov/LATEST/search-index?q=%22{symbol}%22&forms=4&dateRange=custom&startdt={start_date}&enddt={end_date}"
                resp = requests.get(url, headers=SEC_HEADERS, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", {}).get("hits", [])
                    if hits:
                        for hit in hits[:5]:
                            source = hit.get("_source", {})
                            points.append(DataPoint(
                                ts=datetime.now(timezone.utc),
                                symbol=symbol,
                                cadence="daily",
                                payload={
                                    "filing_date": source.get("file_date"),
                                    "form_type": source.get("form_type", "4"),
                                    "entity_name": source.get("entity_name"),
                                    "file_num": source.get("file_num"),
                                    "source": "sec_edgar",
                                },
                            ))
            except requests.RequestException:
                continue

            import time
            time.sleep(0.15)

        return points

    def validate(self, clean_points: List[DataPoint]):
        report = super().validate(clean_points)
        if clean_points:
            with_entity = sum(1 for p in clean_points if p.payload.get("entity_name"))
            report.completeness = (with_entity / len(clean_points) * 100) if clean_points else 0
        report.compute_overall()
        return report
