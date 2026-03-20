"""
Economic Event Calendar — via Scrapling

Source: TradingEconomics Calendar
Cadence: Daily
Granularity: Market-level
Tags: Macro, Calendar, Events
"""
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


class ScraplingEconomicCalendar(BaseModule):
    name = "scrapling_economic_calendar"
    display_name = "Economic Calendar (Scrapling)"
    cadence = "daily"
    granularity = "market"
    tags = ["Macro", "Calendar", "Events"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        points = []

        try:
            page = fetcher.get("https://tradingeconomics.com/calendar")
            rows = page.css("tr[data-event]")

            for row in rows:
                try:
                    event = (row.attrib.get("data-event") or "").strip()
                    country = (row.attrib.get("data-country") or "").strip()
                    category = (row.attrib.get("data-category") or "").strip()
                    te_symbol = (row.attrib.get("data-symbol") or "").strip()

                    cells = row.css("td")
                    if len(cells) < 7:
                        continue

                    def span_text(cell):
                        spans = cell.css("span")
                        return (spans[0].text or "").strip() if spans else ""

                    event_time = span_text(cells[0])
                    date_str = (cells[0].attrib.get("class") or "").strip()
                    period = span_text(cells[4]) if len(cells) > 4 else ""
                    actual = span_text(cells[5]) if len(cells) > 5 else ""
                    previous = span_text(cells[6]) if len(cells) > 6 else ""
                    forecast = span_text(cells[7]) if len(cells) > 7 else ""

                    if not event:
                        continue

                    # Extract date from cell class (e.g. "2026-03-20")
                    ts = datetime.now(timezone.utc)
                    for part in date_str.split():
                        try:
                            ts = datetime.strptime(part, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            break
                        except ValueError:
                            continue

                    points.append(DataPoint(
                        ts=ts,
                        symbol=None,
                        cadence="daily",
                        payload={
                            "event_name": event,
                            "country": country,
                            "category": category,
                            "te_symbol": te_symbol,
                            "event_time": event_time,
                            "period": period,
                            "actual": actual,
                            "forecast": forecast,
                            "previous": previous,
                            "source": "tradingeconomics_scrapling",
                        },
                    ))
                except Exception:
                    continue

        except Exception as e:
            self.logger.error(f"Economic calendar scrape failed: {e}")

        return points


if __name__ == "__main__":
    mod = ScraplingEconomicCalendar()
    points = mod.fetch()
    print(f"{len(points)} economic events fetched")
    for p in points[:10]:
        print(f"  {p.payload.get('country')}: {p.payload.get('event_name')} "
              f"actual={p.payload.get('actual')} prev={p.payload.get('previous')}")
