"""
Financial Datasets API — Daily Prices + Fundamentals

Source: financialdatasets.ai (API key required)
Cadence: Daily
Granularity: Symbol-level
Tags: US Equities, Fundamentals
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


class FinancialDatasetsPrices(BaseModule):
    name = "financial_datasets_prices"
    display_name = "Financial Datasets — Daily Prices"
    cadence = "daily"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

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

        for symbol in symbols:
            try:
                url = f"{BASE_URL}/prices/snapshot?ticker={symbol}"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                snapshot = data.get("snapshot") or data
                if not snapshot:
                    continue

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=symbol,
                    cadence="daily",
                    payload={
                        "open": snapshot.get("open"),
                        "high": snapshot.get("high"),
                        "low": snapshot.get("low"),
                        "close": snapshot.get("price") or snapshot.get("close"),
                        "volume": snapshot.get("volume"),
                        "market_cap": snapshot.get("market_cap"),
                        "pe_ratio": snapshot.get("pe_ratio"),
                        "dividend_yield": snapshot.get("dividend_yield"),
                        "change_percent": snapshot.get("change_percent"),
                        "day_high": snapshot.get("day_high"),
                        "day_low": snapshot.get("day_low"),
                        "year_high": snapshot.get("year_high"),
                        "year_low": snapshot.get("year_low"),
                        "source": "financial_datasets",
                    },
                ))
            except requests.RequestException as e:
                self.logger.warning(f"Failed for {symbol}: {e}")
                continue

        return points

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        cleaned = super().clean(raw_points)
        for p in cleaned:
            payload = p.payload
            for key in ["open", "high", "low", "close", "volume"]:
                val = payload.get(key)
                if val is not None:
                    try:
                        payload[key] = float(val)
                    except (ValueError, TypeError):
                        payload[key] = None
            if payload.get("close") and payload.get("close") <= 0:
                payload["close"] = None
        return [p for p in cleaned if p.payload.get("close") is not None]

    def validate(self, clean_points: List[DataPoint]):
        report = super().validate(clean_points)
        if clean_points:
            with_price = sum(1 for p in clean_points if p.payload.get("close"))
            report.completeness = (with_price / len(clean_points) * 100)
            valid_prices = sum(1 for p in clean_points
                             if isinstance(p.payload.get("close"), (int, float))
                             and 0.01 < p.payload["close"] < 100000)
            report.accuracy = (valid_prices / len(clean_points) * 100)
        report.compute_overall()
        return report
