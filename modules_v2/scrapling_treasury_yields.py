"""
US Treasury Par Yield Curve — Daily rates (1 Mo through 30 Yr) via Scrapling

Source: U.S. Department of the Treasury (Daily Treasury Par Yield Curve Rates)
Category: fixed_income
Cadence: Daily
Granularity: Macro
Tags: fixed_income, US Treasuries, Yield Curve
"""
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None

# Legacy URL redirects to interest-rate-statistics landing (no embedded table); data is on TextView.
TARGET_URL = (
    "https://www.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "pages/textview.aspx?data=yield"
)


def _month_keys(utc_now: datetime) -> List[str]:
    """Current and previous calendar month as YYYYMM (fallback if current month is empty)."""
    y, m = utc_now.year, utc_now.month
    cur = f"{y}{m:02d}"
    if m == 1:
        prev = f"{y - 1}12"
    else:
        prev = f"{y}{m - 1:02d}"
    return [cur, prev]


def _parse_yield_text(raw: Optional[str]) -> Optional[float]:
    s = (raw or "").strip()
    if not s or s.upper() == "N/A":
        return None
    try:
        return float(s)
    except ValueError:
        return None


# Par yield curve tenors (CSS field class suffix after views-field-)
TENOR_FIELDS: List[Tuple[str, str]] = [
    ("1mo", "field-bc-1month"),
    ("1.5mo", "field-bc-1-5month"),
    ("2mo", "field-bc-2month"),
    ("3mo", "field-bc-3month"),
    ("4mo", "field-bc-4month"),
    ("6mo", "field-bc-6month"),
    ("1yr", "field-bc-1year"),
    ("2yr", "field-bc-2year"),
    ("3yr", "field-bc-3year"),
    ("5yr", "field-bc-5year"),
    ("7yr", "field-bc-7year"),
    ("10yr", "field-bc-10year"),
    ("20yr", "field-bc-20year"),
    ("30yr", "field-bc-30year"),
]


class ScraplingTreasuryYields(BaseModule):
    name = "scrapling_treasury_yields"
    display_name = "US Treasury Yield Curve (Scrapling)"
    cadence = "daily"
    granularity = "macro"
    tags = ["fixed_income", "US Treasuries", "Yield Curve"]

    def _urls_to_try(self) -> List[str]:
        keys = _month_keys(datetime.now(timezone.utc))
        out: List[str] = [TARGET_URL]
        for k in keys:
            out.append(
                "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                f"TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month={k}"
            )
            out.append(
                "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                f"TextView?type=daily_treasury_yield_curve&field_tdr_date_value={k}"
            )
        return out

    def _parse_page(self, page) -> List[DataPoint]:
        points: List[DataPoint] = []
        try:
            rows = page.css("table.views-view-table tbody tr")
        except Exception as e:
            self.logger.error(f"Treasury yield table parse failed: {e}")
            return []

        for row in rows:
            try:
                time_el = row.css("td.views-field-field-tdr-date time")
                if not time_el:
                    continue
                dt_raw = (time_el[0].attrib.get("datetime") or "").strip()
                if not dt_raw:
                    continue
                if dt_raw.endswith("Z"):
                    ts = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
                else:
                    ts = datetime.fromisoformat(dt_raw)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)

                yields: Dict[str, Any] = {}
                for key, field_suffix in TENOR_FIELDS:
                    cells = row.css(f"td.views-field-{field_suffix}")
                    if not cells:
                        continue
                    val = _parse_yield_text(cells[0].text)
                    if val is not None:
                        yields[key] = val

                if not yields:
                    continue

                date_label = (time_el[0].text or "").strip()
                points.append(
                    DataPoint(
                        ts=ts,
                        symbol=None,
                        cadence="daily",
                        payload={
                            "date": date_label,
                            "yields": yields,
                            "source": "treasury_gov_scrapling",
                            "source_url": TARGET_URL,
                        },
                    )
                )
            except Exception as e:
                self.logger.debug(f"Skipping treasury yield row: {e}")
                continue

        return points

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        for url in self._urls_to_try():
            try:
                page = fetcher.get(url, headers=headers)
            except Exception as e:
                self.logger.warning(f"Treasury request failed ({url}): {e}")
                continue

            points = self._parse_page(page)
            if points:
                for p in points:
                    if isinstance(p.payload, dict):
                        p.payload["fetched_url"] = url
                return points

        self.logger.warning("Treasury yield scrape returned no rows from any URL")
        return []

    def validate(self, clean_points: List[DataPoint]) -> QualityReport:
        report = super().validate(clean_points)
        if not clean_points:
            return report

        total = len(clean_points)
        core_tenors = ("3mo", "2yr", "10yr", "30yr")
        ok = 0
        for p in clean_points:
            pl = p.payload or {}
            y = pl.get("yields") or {}
            if isinstance(y, dict) and all(k in y for k in core_tenors):
                ok += 1

        report.completeness = (ok / total * 100) if total else 0.0
        report.schema_valid = ok == total
        report.issues = []
        if not report.schema_valid:
            report.issues.append(
                f"Incomplete curves: {total - ok} of {total} missing core tenors {core_tenors}"
            )
        report.compute_overall()
        return report


if __name__ == "__main__":
    mod = ScraplingTreasuryYields()
    pts = mod.fetch()
    print(f"{len(pts)} treasury yield curve rows fetched")
    for p in pts[:5]:
        pl = p.payload
        print(f"  {pl.get('date')}: {list((pl.get('yields') or {}).keys())}")
