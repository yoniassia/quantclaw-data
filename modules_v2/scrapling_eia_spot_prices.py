"""
EIA Spot Prices — Crude oil and petroleum products (daily table)

Source URL: https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm
Cadence: Daily
Granularity: Symbol (EIA series code per product row)
Tags: Commodities, Energy, Oil & Gas

Description: Scrape spot prices for crude oil and petroleum products to capture daily market levels.
Signal value: Spot prices support commodity trend signals, oil volatility context, and energy futures decisions.

Note: The page uses ``table.data1`` and ``tr.DataRow`` (not ``table.dataTable``) for the main grid.
"""
import re
import sys
import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None

SOURCE_URL = "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm"


def _parse_price(raw: Optional[str]) -> Optional[float]:
    s = (raw or "").strip().replace("\xa0", " ")
    if not s or s.upper() in ("N/A", "-", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_header_date(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        dt = datetime.strptime(s, "%m/%d/%y")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _series_from_hist_href(href: str) -> Optional[str]:
    if not href:
        return None
    try:
        q = parse_qs(urlparse(href).query)
        vals = q.get("s") or []
        return vals[0].strip() if vals else None
    except Exception:
        m = re.search(r"[?&]s=([^&]+)", href)
        return m.group(1).strip() if m else None


class ScraplingEiaSpotPrices(BaseModule):
    name = "scrapling_eia_spot_prices"
    display_name = "EIA Spot Prices — Crude & Petroleum (Scrapling)"
    cadence = "daily"
    granularity = "symbol"
    tags = ["Commodities", "Energy", "Oil & Gas"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        points: List[DataPoint] = []

        try:
            page = fetcher.get(SOURCE_URL, headers=headers)
        except Exception as e:
            self.logger.error(f"EIA spot prices page request failed: {e}")
            return []

        try:
            date_headers = page.css("table.data1 th.Series5")
        except Exception as e:
            self.logger.error(f"EIA spot prices date header parse failed: {e}")
            return []

        dates: List[datetime] = []
        for th in date_headers:
            raw = (th.text or "").replace("\n", " ").strip()
            dt = _parse_header_date(raw)
            if dt:
                dates.append(dt)

        if not dates:
            self.logger.warning("EIA spot prices: no date columns found")

        try:
            rows = page.css("table.data1 tr.DataRow")
        except Exception as e:
            self.logger.error(f"EIA spot prices table parse failed: {e}")
            return []

        current_section = ""
        ts_fetch = datetime.now(timezone.utc)

        for row in rows:
            try:
                stub2 = row.css("td.DataStub2")
                if stub2 and not row.css("td.DataStub1"):
                    # Section rows often nest two DataStub2 cells; text is usually in the inner one.
                    texts = []
                    for c in stub2:
                        t = (c.text or "").replace("\n", " ").strip()
                        if t:
                            texts.append(t)
                    if texts:
                        current_section = texts[-1]
                    continue

                stub_cells = row.css("td.DataStub1")
                if not stub_cells:
                    continue

                product = (stub_cells[0].text or "").replace("\n", " ").strip()
                if not product:
                    continue

                hist_links = row.css("td.DataHist a")
                href = (hist_links[0].attrib.get("href") or "") if hist_links else ""
                series_code = _series_from_hist_href(href) or product

                if symbols and series_code not in symbols:
                    continue

                price_cells: List[Tuple[str, str]] = []
                for cell in row.css("td"):
                    cls = (cell.attrib.get("class") or "")
                    if "DataHist" in cls:
                        break
                    if "DataB" in cls or "Current2" in cls:
                        price_cells.append((cls, (cell.text or "").strip()))

                if len(price_cells) != len(dates):
                    self.logger.debug(
                        f"EIA row column mismatch for {product}: "
                        f"{len(price_cells)} prices vs {len(dates)} dates"
                    )

                for i, dt in enumerate(dates):
                    if i >= len(price_cells):
                        break
                    _, txt = price_cells[i]
                    price = _parse_price(txt)
                    if price is None:
                        continue

                    points.append(
                        DataPoint(
                            ts=dt,
                            symbol=series_code,
                            cadence="daily",
                            payload={
                                "product": product,
                                "series_code": series_code,
                                "section": current_section,
                                "observation_date": dt.strftime("%Y-%m-%d"),
                                "spot_price": price,
                                "price_column_class": price_cells[i][0],
                                "source": "eia_dnav_scrapling",
                                "source_url": SOURCE_URL,
                                "fetched_at": ts_fetch.isoformat(),
                            },
                        )
                    )
            except Exception as e:
                self.logger.debug(f"Skipping EIA spot row: {e}")
                continue

        if not points:
            self.logger.warning("EIA spot prices scrape returned no rows")

        return points

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        cleaned = []
        seen = set()
        for point in raw_points:
            if not point.payload:
                continue
            pl = point.payload
            sym = (point.symbol or "").strip()
            price = pl.get("spot_price")
            if not sym or price is None:
                continue
            try:
                float(price)
            except (TypeError, ValueError):
                continue

            if not isinstance(point.ts, datetime):
                try:
                    point.ts = datetime.fromisoformat(str(point.ts))
                except (ValueError, TypeError):
                    continue
            if point.ts.tzinfo is None:
                point.ts = point.ts.replace(tzinfo=timezone.utc)

            point.compute_hash()
            dedup_key = (sym, point.ts.isoformat(), point.source_hash)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            point.tier = "silver"
            point.quality_score = max(point.quality_score, 50)
            cleaned.append(point)
        return cleaned

    def validate(self, clean_points: List[DataPoint]) -> QualityReport:
        report = super().validate(clean_points)
        if not clean_points:
            return report

        total = len(clean_points)
        required = ("product", "series_code", "spot_price", "observation_date")
        ok = 0
        for p in clean_points:
            pl = p.payload or {}
            if not p.symbol:
                continue
            if all(pl.get(k) not in (None, "") for k in required):
                try:
                    float(pl.get("spot_price"))
                    ok += 1
                except (TypeError, ValueError):
                    pass

        report.completeness = (ok / total * 100) if total else 0.0
        report.schema_valid = ok == total
        report.issues = []
        if not report.schema_valid:
            report.issues.append(f"Incomplete or invalid rows: {total - ok} of {total}")
        report.compute_overall()
        return report


if __name__ == "__main__":
    mod = ScraplingEiaSpotPrices()
    pts = mod.fetch()
    print(f"{len(pts)} EIA spot price points fetched")
    for p in pts[:10]:
        pl = p.payload
        print(
            f"  {p.symbol} @ {pl.get('observation_date')}: {pl.get('spot_price')} "
            f"| {pl.get('product')}"
        )
