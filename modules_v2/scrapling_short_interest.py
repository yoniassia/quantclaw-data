"""
High Short Interest — Stocks with Short Interest > 20% via Scrapling

Source: HighShortInterest.com (main listing)
Cadence: Daily
Granularity: Symbol-level
Tags: US Equities, Short Interest, Alternative Data
"""
import sys
import os
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None


class ScraplingShortInterest(BaseModule):
    name = "scrapling_short_interest"
    display_name = "High Short Interest (Scrapling)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["US Equities", "Short Interest", "Alternative Data"]

    MAIN_URL = "https://www.highshortinterest.com/"

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        points: List[DataPoint] = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        try:
            page = fetcher.get(self.MAIN_URL, headers=headers)
        except Exception as e:
            self.logger.error(f"High short interest page request failed: {e}")
            return []

        try:
            rows = page.css("table.stocks tr")
        except Exception as e:
            self.logger.error(f"High short interest table parse failed: {e}")
            return []

        ts = datetime.now(timezone.utc)

        for row in rows:
            try:
                cells = row.css("td")
                if len(cells) < 7:
                    continue

                hdr_class = (cells[0].attrib.get("class") or "")
                if "tblhdr" in hdr_class:
                    continue

                links = cells[0].css("a")
                ticker = (links[0].text or "").strip().upper() if links else ""
                if not ticker:
                    ticker = (cells[0].text or "").strip().upper()
                if not ticker or ticker == "TICKER":
                    continue

                if symbols and ticker not in symbols:
                    continue

                company = (cells[1].text or "").strip()
                exchange = (cells[2].text or "").strip()
                short_int = (cells[3].text or "").strip()
                float_shares = (cells[4].text or "").strip()
                outstanding = (cells[5].text or "").strip()
                industry = (cells[6].text or "").strip()

                points.append(DataPoint(
                    ts=ts,
                    symbol=ticker,
                    cadence="daily",
                    payload={
                        "company": company,
                        "exchange": exchange,
                        "short_interest_pct": short_int,
                        "float": float_shares,
                        "outstanding_shares": outstanding,
                        "industry": industry,
                        "source": "highshortinterest_scrapling",
                    },
                ))
            except Exception as e:
                self.logger.debug(f"Skipping short interest row: {e}")
                continue

        if not points:
            self.logger.warning("High short interest scrape returned no rows")

        return points

    def validate(self, clean_points: List[DataPoint]) -> QualityReport:
        """Gold: require core fields used for short-interest analytics."""
        report = super().validate(clean_points)
        if not clean_points:
            return report

        total = len(clean_points)
        required = ("company", "exchange", "short_interest_pct", "float", "outstanding_shares")
        ok = 0
        for p in clean_points:
            pl = p.payload or {}
            if not p.symbol:
                continue
            if all(str(pl.get(k, "")).strip() for k in required):
                ok += 1

        report.completeness = (ok / total * 100) if total else 0.0
        report.schema_valid = ok == total
        report.issues = []
        if not report.schema_valid:
            report.issues.append(f"Incomplete rows: {total - ok} of {total} missing required fields")
        report.compute_overall()
        return report


if __name__ == "__main__":
    mod = ScraplingShortInterest()
    points = mod.fetch()
    print(f"{len(points)} high short interest points fetched")
    for p in points[:10]:
        pl = p.payload
        print(
            f"  {p.symbol}: {pl.get('short_interest_pct')} | "
            f"float={pl.get('float')} outstd={pl.get('outstanding_shares')} | {pl.get('exchange')}"
        )
