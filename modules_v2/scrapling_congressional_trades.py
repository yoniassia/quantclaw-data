"""
Congressional Stock Trading — Politician Trades via Scrapling

Source: Capitol Trades (capitoltrades.com)
Cadence: Daily
Granularity: Symbol-level
Tags: Insider, US Equities, Alternative Data
"""
import time
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


class ScraplingCongressionalTrades(BaseModule):
    name = "scrapling_congressional_trades"
    display_name = "Congressional Stock Trades (Scrapling)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Insider", "US Equities", "Alternative Data"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if StealthyFetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = StealthyFetcher()
        points = []

        try:
            page = fetcher.fetch("https://www.capitoltrades.com/trades?per_page=96")
            rows = page.css("table tbody tr")

            for row in rows:
                try:
                    cells = row.css("td")
                    if len(cells) < 8:
                        continue

                    # Cell 0: politician (link text + party/chamber/state spans)
                    pol_link = cells[0].css("a")
                    politician = (pol_link[0].text or "").strip() if pol_link else ""
                    party_spans = cells[0].css("span")
                    party = (party_spans[0].text or "").strip() if party_spans else ""
                    chamber = (party_spans[1].text or "").strip() if len(party_spans) > 1 else ""
                    state = (party_spans[2].text or "").strip() if len(party_spans) > 2 else ""

                    # Cell 1: issuer (ticker span + company link)
                    ticker_span = cells[1].css("span")
                    raw_ticker = (ticker_span[0].text or "").strip() if ticker_span else ""
                    ticker = raw_ticker.split(":")[0].upper() if raw_ticker and raw_ticker != "N/A" else ""
                    issuer_link = cells[1].css("a")
                    company = (issuer_link[0].text or "").strip() if issuer_link else ""

                    # Cell 3: trade date (div with day + div with year)
                    date_divs = cells[3].css("div")
                    trade_date = " ".join((d.text or "").strip() for d in date_divs).strip()

                    # Cell 5: owner (spouse, self, etc.)
                    owner_spans = cells[5].css("span")
                    owner = (owner_spans[0].text or "").strip() if owner_spans else ""

                    # Cell 6: transaction type (buy/sell)
                    tx_spans = cells[6].css("span")
                    tx_type = (tx_spans[0].text or "").strip() if tx_spans else ""

                    # Cell 7: amount range
                    amt_spans = cells[7].css("span")
                    amount = (amt_spans[0].text or "").strip() if amt_spans else ""

                    if not company and not ticker:
                        continue

                    if symbols and ticker and ticker not in symbols:
                        continue

                    points.append(DataPoint(
                        ts=datetime.now(timezone.utc),
                        symbol=ticker if ticker else None,
                        cadence="daily",
                        payload={
                            "politician": politician,
                            "party": party,
                            "chamber": chamber,
                            "state": state,
                            "company": company,
                            "trade_date": trade_date,
                            "owner": owner,
                            "transaction_type": tx_type,
                            "amount_range": amount,
                            "source": "capitol_trades_scrapling",
                        },
                    ))
                except Exception:
                    continue

        except Exception as e:
            self.logger.error(f"Capitol Trades scrape failed: {e}")

        return points


if __name__ == "__main__":
    mod = ScraplingCongressionalTrades()
    points = mod.fetch()
    print(f"{len(points)} congressional trade points fetched")
    for p in points[:5]:
        print(f"  {p.symbol}: {p.payload}")
