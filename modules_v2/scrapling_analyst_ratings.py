"""
Analyst Ratings & Upgrades/Downgrades — via Scrapling

Source: Finviz
Cadence: Daily
Granularity: Symbol-level
Tags: Analyst, US Equities, Sentiment
"""
import time
import sys
import os
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

try:
    from scrapling import StealthyFetcher
except ImportError:
    StealthyFetcher = None


class ScraplingAnalystRatings(BaseModule):
    name = "scrapling_analyst_ratings"
    display_name = "Analyst Ratings (Scrapling)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Analyst", "US Equities", "Sentiment"]

    def _get_symbols(self) -> List[str]:
        rows = execute_query(
            "SELECT symbol FROM symbol_universe WHERE asset_class = 'stocks' AND is_active = true "
            "ORDER BY symbol LIMIT 50",
            fetch=True,
        )
        return [r["symbol"] for r in (rows or [])]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if StealthyFetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        if symbols is None:
            symbols = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "AMD", "NFLX", "CRM"]

        fetcher = StealthyFetcher()
        points = []

        for symbol in symbols:
            try:
                url = f"https://finviz.com/quote.ashx?t={symbol}&ty=c&p=d&b=1"
                page = fetcher.fetch(url)

                tables = page.css("table")
                for table in tables:
                    header_row = table.css("tr")
                    if not header_row:
                        continue
                    first_cells = header_row[0].css("td, th")
                    headers = [(c.text or "").strip().lower() for c in first_cells[:5]]
                    if "date" not in headers or "analyst" not in headers:
                        continue

                    for row in header_row[1:]:
                        cells = row.css("td")
                        if len(cells) < 4:
                            continue

                        date_str = (cells[0].text or "").strip()
                        action = (cells[1].text or "").strip()
                        firm = (cells[2].text or "").strip()
                        rating = (cells[3].text or "").strip()
                        price_target = (cells[4].text or "").strip() if len(cells) > 4 else ""

                        if not firm:
                            continue

                        try:
                            ts = datetime.strptime(date_str, "%b-%d-%y").replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            ts = datetime.now(timezone.utc)

                        points.append(DataPoint(
                            ts=ts,
                            symbol=symbol,
                            cadence="daily",
                            payload={
                                "analyst_firm": firm,
                                "action": action,
                                "rating": rating,
                                "price_target": price_target,
                                "source": "finviz_scrapling",
                            },
                        ))
                    break

                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Finviz scrape failed for {symbol}: {e}")
                continue

        return points


if __name__ == "__main__":
    mod = ScraplingAnalystRatings()
    points = mod.fetch(["AAPL", "TSLA"])
    print(f"{len(points)} analyst rating points fetched")
    for p in points[:10]:
        print(f"  {p.symbol} {p.ts.strftime('%Y-%m-%d')}: {p.payload.get('firm', p.payload.get('analyst_firm'))} "
              f"{p.payload.get('action')} → {p.payload.get('rating')} {p.payload.get('price_target')}")
