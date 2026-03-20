"""
Earnings Calendar — Upcoming Earnings Dates & Estimates via Scrapling

Source: Yahoo Finance Earnings Calendar
Cadence: Daily
Granularity: Symbol-level
Tags: Earnings, US Equities, Calendar

Fills the gap from broken Financial Datasets earnings endpoint (404).
"""
import time
import sys
import os
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint

try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None


class ScraplingEarningsCalendar(BaseModule):
    name = "scrapling_earnings_calendar"
    display_name = "Earnings Calendar (Scrapling)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Earnings", "US Equities", "Calendar"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        points = []

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        try:
            url = f"https://finance.yahoo.com/calendar/earnings?day={today}"
            page = fetcher.get(url, headers=headers)

            rows = page.css("table tbody tr, #cal-res-table tbody tr, #earningsBody tr")

            for row in rows:
                try:
                    cells = row.css("td")
                    if len(cells) < 3:
                        continue

                    ticker = (cells[0].text or "").strip().upper()
                    company = (cells[1].text or "").strip() if len(cells) > 1 else ""
                    call_time = (cells[2].text or "").strip() if len(cells) > 2 else ""
                    eps_estimate = (cells[3].text or "").strip() if len(cells) > 3 else ""
                    eps_actual = (cells[4].text or "").strip() if len(cells) > 4 else ""
                    surprise_pct = (cells[5].text or "").strip() if len(cells) > 5 else ""

                    # Also try link text for ticker
                    if not ticker or len(ticker) > 8:
                        links = row.css("a")
                        for link in links:
                            href = link.attrib.get("href", "")
                            if "/quote/" in href:
                                ticker = (link.text or "").strip().upper()
                                break

                    if not ticker:
                        continue

                    if symbols and ticker not in symbols:
                        continue

                    points.append(DataPoint(
                        ts=datetime.now(timezone.utc),
                        symbol=ticker,
                        cadence="daily",
                        payload={
                            "company": company,
                            "report_time": call_time,
                            "eps_estimate": eps_estimate,
                            "eps_actual": eps_actual,
                            "surprise_pct": surprise_pct,
                            "earnings_date": today,
                            "source": "yahoo_earnings_scrapling",
                        },
                    ))
                except Exception:
                    continue

        except Exception as e:
            self.logger.error(f"Earnings calendar scrape failed: {e}")

        return points


if __name__ == "__main__":
    mod = ScraplingEarningsCalendar()
    points = mod.fetch()
    print(f"{len(points)} earnings calendar points fetched")
    for p in points[:10]:
        print(f"  {p.symbol}: EPS est={p.payload.get('eps_estimate')} actual={p.payload.get('eps_actual')} time={p.payload.get('report_time')}")
