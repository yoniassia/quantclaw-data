"""
AAII Sentiment Survey — Weekly Investor Sentiment (Contrarian Indicator)

Refactored for QuantClaw Data Platform v2.
Source: American Association of Individual Investors
Cadence: Weekly (Thursday after market close)
Granularity: Market-level (no per-symbol data)
Tags: Sentiment, US Equities
"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint

AAII_URL = "https://www.aaii.com/sentimentsurvey"
HISTORICAL_AVERAGES = {"bullish": 37.5, "neutral": 31.5, "bearish": 31.0}


class AaiiSentiment(BaseModule):
    name = "aaii_sentiment"
    display_name = "AAII Investor Sentiment Survey"
    cadence = "weekly"
    granularity = "market"
    tags = ["Sentiment", "US Equities"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(AAII_URL, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()

        bullish_m = re.search(r"Bullish[:\s]+(\d+\.?\d*)%", text, re.IGNORECASE)
        bearish_m = re.search(r"Bearish[:\s]+(\d+\.?\d*)%", text, re.IGNORECASE)
        neutral_m = re.search(r"Neutral[:\s]+(\d+\.?\d*)%", text, re.IGNORECASE)

        if not (bullish_m and bearish_m):
            self.logger.warning("Scraping failed — using historical averages")
            bullish = HISTORICAL_AVERAGES["bullish"]
            bearish = HISTORICAL_AVERAGES["bearish"]
            neutral = HISTORICAL_AVERAGES["neutral"]
            is_fallback = True
        else:
            bullish = float(bullish_m.group(1))
            bearish = float(bearish_m.group(1))
            neutral = float(neutral_m.group(1)) if neutral_m else (100 - bullish - bearish)
            is_fallback = False

        spread = round(bullish - bearish, 1)
        if bullish > 50 or spread > 20:
            signal = "BEARISH_SIGNAL"
        elif bearish > 50 or spread < -20:
            signal = "BULLISH_SIGNAL"
        else:
            signal = "NEUTRAL"

        return [DataPoint(
            ts=datetime.now(timezone.utc),
            symbol=None,
            cadence="weekly",
            payload={
                "bullish": round(bullish, 1),
                "neutral": round(neutral, 1),
                "bearish": round(bearish, 1),
                "bull_bear_spread": spread,
                "vs_avg_bullish": round(bullish - HISTORICAL_AVERAGES["bullish"], 1),
                "vs_avg_bearish": round(bearish - HISTORICAL_AVERAGES["bearish"], 1),
                "contrarian_signal": signal,
                "is_fallback": is_fallback,
            },
        )]

    def validate(self, clean_points: List[DataPoint]):
        report = super().validate(clean_points)
        if clean_points:
            p = clean_points[0].payload
            if p.get("is_fallback"):
                report.accuracy = 50.0
                report.issues.append("Using fallback historical averages")
            if not (0 <= p.get("bullish", -1) <= 100):
                report.accuracy = 0.0
                report.issues.append("Bullish percentage out of range")
        report.compute_overall()
        return report
