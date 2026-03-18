"""
Financial Datasets API — Insider Trading Data

Source: financialdatasets.ai
Cadence: Daily
Granularity: Symbol-level
Tags: Insider, US Equities, Fundamentals
"""
import os
import requests
from datetime import datetime, timezone, timedelta
from typing import List

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

API_KEY = os.getenv("FINANCIAL_DATASETS_API_KEY", "f4cd5217-2afe-4d8e-9031-1328633c8532")
BASE_URL = "https://api.financialdatasets.ai"


class FinancialDatasetsInsider(BaseModule):
    name = "financial_datasets_insider"
    display_name = "Financial Datasets — Insider Trades"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Insider", "US Equities", "Fundamentals"]

    def _get_symbols(self) -> List[str]:
        rows = execute_query(
            """SELECT symbol FROM symbol_universe
               WHERE asset_class = 'stocks' AND is_active = true
               AND symbol NOT LIKE '%.%'
               ORDER BY symbol LIMIT 200""",
            fetch=True,
        )
        return [r["symbol"] for r in (rows or [])]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if symbols is None:
            symbols = self._get_symbols()[:50]

        headers = {"X-API-KEY": API_KEY}
        points = []
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        for symbol in symbols:
            try:
                url = f"{BASE_URL}/insider-trades?ticker={symbol}&filing_date_gte={start_date}&filing_date_lte={end_date}&limit=10"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                trades = data.get("insider_trades", [])
                for trade in trades:
                    filing_date = trade.get("filing_date")
                    try:
                        ts = datetime.fromisoformat(filing_date).replace(tzinfo=timezone.utc) if filing_date else datetime.now(timezone.utc)
                    except (ValueError, TypeError):
                        ts = datetime.now(timezone.utc)

                    points.append(DataPoint(
                        ts=ts,
                        symbol=symbol,
                        cadence="daily",
                        payload={
                            "insider_name": trade.get("owner"),
                            "title": trade.get("owner_title"),
                            "transaction_type": trade.get("transaction_type"),
                            "shares": trade.get("shares"),
                            "price_per_share": trade.get("price_per_share"),
                            "total_value": trade.get("value"),
                            "shares_owned_after": trade.get("shares_owned_following"),
                            "filing_date": filing_date,
                            "source": "financial_datasets",
                        },
                    ))
            except requests.RequestException as e:
                self.logger.warning(f"Failed for {symbol}: {e}")
                continue

        return points

    def validate(self, clean_points: List[DataPoint]):
        report = super().validate(clean_points)
        if clean_points:
            with_name = sum(1 for p in clean_points if p.payload.get("insider_name"))
            report.completeness = (with_name / len(clean_points) * 100) if clean_points else 0
        report.compute_overall()
        return report
