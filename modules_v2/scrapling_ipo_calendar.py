"""
IPO Calendar — Upcoming & Recent IPOs via Scrapling

Source: Stock Analysis (stockanalysis.com)
Cadence: Daily
Granularity: Symbol-level
Tags: IPO, US Equities, Corporate Actions
"""
import sys
import os
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint

try:
    from scrapling import StealthyFetcher
except ImportError:
    StealthyFetcher = None


class ScraplingIPOCalendar(BaseModule):
    name = "scrapling_ipo_calendar"
    display_name = "IPO Calendar (Scrapling)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["IPO", "US Equities", "Corporate Actions"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if StealthyFetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = StealthyFetcher()
        points = []

        for endpoint in ["calendar", "filings"]:
            try:
                url = f"https://stockanalysis.com/ipos/{endpoint}/"
                page = fetcher.fetch(url)

                tables = page.css("table")
                for table in tables:
                    rows = table.css("tr")
                    if len(rows) < 2:
                        continue

                    headers = [(c.text or "").strip().lower() for c in rows[0].css("td, th")]
                    sym_idx = next((i for i, h in enumerate(headers) if "symbol" in h), 1)
                    name_idx = next((i for i, h in enumerate(headers) if "company" in h), 2)
                    exch_idx = next((i for i, h in enumerate(headers) if "exchange" in h), 3)
                    price_idx = next((i for i, h in enumerate(headers) if "price" in h), 4)
                    shares_idx = next((i for i, h in enumerate(headers) if "shares" in h), 5)

                    for row in rows[1:]:
                        try:
                            cells = row.css("td")
                            if len(cells) < 3:
                                continue

                            date_str = (cells[0].text or "").strip()
                            ticker = (cells[sym_idx].text or "").strip().upper() if sym_idx < len(cells) else ""
                            company = (cells[name_idx].text or "").strip() if name_idx < len(cells) else ""
                            exchange = (cells[exch_idx].text or "").strip() if exch_idx < len(cells) else ""
                            price_range = (cells[price_idx].text or "").strip() if price_idx < len(cells) else ""
                            shares = (cells[shares_idx].text or "").strip() if shares_idx < len(cells) else ""

                            if not company:
                                continue

                            try:
                                ts = datetime.strptime(date_str, "%b %d, %Y").replace(tzinfo=timezone.utc)
                            except (ValueError, TypeError):
                                ts = datetime.now(timezone.utc)

                            points.append(DataPoint(
                                ts=ts,
                                symbol=ticker if ticker else None,
                                cadence="daily",
                                payload={
                                    "company": company,
                                    "ticker": ticker,
                                    "exchange": exchange,
                                    "price_range": price_range,
                                    "shares_offered": shares,
                                    "ipo_status": endpoint,
                                    "source": "stockanalysis_scrapling",
                                },
                            ))
                        except Exception:
                            continue

            except Exception as e:
                self.logger.error(f"StockAnalysis IPO scrape failed for {endpoint}: {e}")
                continue

        return points


if __name__ == "__main__":
    mod = ScraplingIPOCalendar()
    points = mod.fetch()
    print(f"{len(points)} IPO calendar points fetched")
    for p in points[:10]:
        print(f"  {p.payload.get('ticker', '?')}: {p.payload.get('company')} "
              f"({p.payload.get('exchange')}) {p.payload.get('price_range')} [{p.payload.get('ipo_status')}]")
