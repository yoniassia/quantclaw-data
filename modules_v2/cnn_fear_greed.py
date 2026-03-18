"""
CNN Fear & Greed Index — Market Sentiment Gauge

Source: CNN Business
Cadence: Daily
Granularity: Market-level
Tags: Sentiment, US Equities
"""
import requests
from datetime import datetime, timezone
from typing import List

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint

CNN_API = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


class CnnFearGreed(BaseModule):
    name = "cnn_fear_greed"
    display_name = "CNN Fear & Greed Index"
    cadence = "daily"
    granularity = "market"
    tags = ["Sentiment", "US Equities"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(CNN_API, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        fg = data.get("fear_and_greed", {})
        score = fg.get("score", 0)
        rating = fg.get("rating", "unknown")
        previous_close = fg.get("previous_close", 0)
        previous_1_week = fg.get("previous_1_week", 0)
        previous_1_month = fg.get("previous_1_month", 0)
        previous_1_year = fg.get("previous_1_year", 0)

        indicators = {}
        for key in ["market_momentum", "stock_price_strength", "stock_price_breadth",
                     "put_call_options", "market_volatility_vix",
                     "junk_bond_demand", "safe_haven_demand"]:
            ind = data.get("fear_and_greed_historical", {}).get(key) or data.get(key, {})
            if isinstance(ind, dict):
                indicators[key] = {
                    "score": ind.get("score", ind.get("value")),
                    "rating": ind.get("rating"),
                }

        return [DataPoint(
            ts=datetime.now(timezone.utc),
            symbol=None,
            cadence="daily",
            payload={
                "score": round(score, 1) if isinstance(score, (int, float)) else score,
                "rating": rating,
                "previous_close": previous_close,
                "previous_1_week": previous_1_week,
                "previous_1_month": previous_1_month,
                "previous_1_year": previous_1_year,
                "change_1d": round(score - previous_close, 1) if isinstance(score, (int, float)) and isinstance(previous_close, (int, float)) else None,
                "indicators": indicators,
            },
        )]

    def validate(self, clean_points: List[DataPoint]):
        report = super().validate(clean_points)
        if clean_points:
            score = clean_points[0].payload.get("score")
            if isinstance(score, (int, float)) and 0 <= score <= 100:
                report.accuracy = 100.0
            else:
                report.accuracy = 0.0
                report.issues.append(f"Score out of range: {score}")
        report.compute_overall()
        return report
