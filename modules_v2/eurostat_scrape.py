"""
Eurostat — EU macro tables (HTML) + headline dissemination (JSON)

Source URL: https://ec.europa.eu/eurostat/data/database
Cadence: Monthly
Granularity: Macro (EU / euro area aggregates)
Tags: Macro, EU, Inflation, Trade, Employment, Alternative Data

Structured tables on the database portal use ECL styling; CSS follows
``table.eurostat-table td`` with ``table.ecl-table td`` fallback. Headline
HICP, unemployment, and extra-EU trade balance are loaded from the official
Eurostat Statistics API (same institution) when table cells alone do not
contain series values.

Signal value: Analyze regional economic trends for European equities and FX.
"""
import json
import re
import sys
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None

DATABASE_URL = "https://ec.europa.eu/eurostat/data/database"
EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _fetch_json(url: str, timeout: int = 45) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        return None


def _coords_for_flat(flat: int, sizes: List[int]) -> List[int]:
    rem = flat
    out: List[int] = []
    for s in sizes:
        out.append(rem % s)
        rem //= s
    return out


def _label_for_dim(
    data: Dict[str, Any], dim_name: str, coord: int
) -> str:
    cat = (
        data.get("dimension", {})
        .get(dim_name, {})
        .get("category", {})
        .get("index", {})
    )
    for label, idx in cat.items():
        if idx == coord:
            return str(label)
    return ""


def _latest_hicp_i15(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[float]]:
    """Latest month, HICP index unit I15 (chain-linked)."""
    vals = data.get("value") or {}
    if not vals or "id" not in data or "size" not in data:
        return None, None
    ids = data["id"]
    sizes = data["size"]
    if "time" not in ids or "unit" not in ids:
        return None, None
    ti = ids.index("time")
    ui = ids.index("unit")
    best_period: Optional[str] = None
    best_val: Optional[float] = None
    for vk, v in vals.items():
        try:
            coords = _coords_for_flat(int(vk), sizes)
        except (ValueError, IndexError):
            continue
        unit_lbl = _label_for_dim(data, "unit", coords[ui])
        if unit_lbl != "I15":
            continue
        period = _label_for_dim(data, "time", coords[ti])
        if not period:
            continue
        if best_period is None or period > best_period:
            best_period = period
            try:
                best_val = float(v)
            except (TypeError, ValueError):
                best_val = None
    return best_period, best_val


def _latest_single_time_series(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[float]]:
    """One observation per period (single series); take lexicographically max period."""
    vals = data.get("value") or {}
    if not vals or "id" not in data or "size" not in data:
        return None, None
    ids = data["id"]
    sizes = data["size"]
    if "time" not in ids:
        return None, None
    ti = ids.index("time")
    best_period: Optional[str] = None
    best_val: Optional[float] = None
    for vk, v in vals.items():
        try:
            coords = _coords_for_flat(int(vk), sizes)
        except (ValueError, IndexError):
            continue
        period = _label_for_dim(data, "time", coords[ti])
        if not period:
            continue
        if best_period is None or period > best_period:
            best_period = period
            try:
                best_val = float(v)
            except (TypeError, ValueError):
                best_val = None
    return best_period, best_val


def _slug(s: str, max_len: int = 48) -> str:
    t = re.sub(r"[^a-zA-Z0-9]+", "_", (s or "").strip())[:max_len]
    return t.strip("_") or "row"


def _since_months_ago(months: int) -> str:
    d = datetime.now(timezone.utc) - timedelta(days=30 * months)
    return d.strftime("%Y-%m")


class EurostatScrape(BaseModule):
    name = "eurostat_scrape"
    display_name = "Eurostat — EU macro (scrape + dissemination)"
    cadence = "monthly"
    granularity = "macro"
    tags = ["Macro", "EU", "Inflation", "Trade", "Employment", "Alternative Data"]

    def _fetch_html_datapoints(self) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        headers = {"User-Agent": UA}
        try:
            page = fetcher.get(DATABASE_URL, headers=headers)
        except Exception as e:
            self.logger.error(f"Eurostat database page request failed: {e}")
            return []

        ts = datetime.now(timezone.utc)
        points: List[DataPoint] = []

        try:
            tds = page.css("table.eurostat-table td")
            table_sel = "table.eurostat-table"
            if not tds:
                tds = page.css("table.ecl-table td")
                table_sel = "table.ecl-table"
            if not tds:
                self.logger.warning("No table cells matched table.eurostat-table td or ecl fallback")
                return []
            rows = page.css(f"{table_sel} tr")
        except Exception as e:
            self.logger.error(f"Eurostat table row parse failed: {e}")
            return []

        for row in rows:
            try:
                cells = row.css("td, th")
                if len(cells) < 2:
                    continue
                a = (cells[0].text or "").strip().replace("\xa0", " ")
                b = (cells[1].text or "").strip().replace("\xa0", " ")
                if not a and not b:
                    continue
                lowa = a.lower()
                if lowa in ("icon", "explanation", "obs_status code", "conf_status code",
                            "previous flag", "value", "symbol"):
                    continue
                sym = f"EUROSTAT_TABLE:{_slug(a)}"
                points.append(
                    DataPoint(
                        ts=ts,
                        symbol=sym,
                        cadence=self.cadence,
                        payload={
                            "source": "eurostat_scrape",
                            "kind": "portal_table",
                            "code_or_label": a,
                            "description": b,
                            "page": DATABASE_URL,
                        },
                    )
                )
            except Exception as e:
                self.logger.debug(f"Skipping Eurostat HTML row: {e}")
                continue

        return points

    def _fetch_macro_api_points(self) -> List[DataPoint]:
        ts = datetime.now(timezone.utc)
        out: List[DataPoint] = []

        # HICP — euro area, all-items monthly index (I15)
        q_hicp = urllib.parse.urlencode(
            {
                "format": "JSON",
                "geo": "EA20",
                "coicop": "CP00",
                "sinceTimePeriod": _since_months_ago(8),
            }
        )
        hicp = _fetch_json(f"{EUROSTAT_API}/prc_hicp_midx?{q_hicp}")
        if hicp:
            period, val = _latest_hicp_i15(hicp)
            if period and val is not None:
                out.append(
                    DataPoint(
                        ts=ts,
                        symbol="EU_HICP_MIDX_EA20_CP00",
                        cadence=self.cadence,
                        payload={
                            "source": "eurostat_scrape",
                            "kind": "inflation",
                            "metric": "HICP_monthly_index",
                            "geo": "EA20",
                            "coicop": "CP00",
                            "unit": "I15",
                            "period": period,
                            "value": val,
                            "dataset": "prc_hicp_midx",
                        },
                    )
                )

        q_un = urllib.parse.urlencode(
            {
                "format": "JSON",
                "geo": "EA20",
                "s_adj": "SA",
                "age": "TOTAL",
                "sex": "T",
                "unit": "PC_ACT",
                "sinceTimePeriod": _since_months_ago(8),
            }
        )
        une = _fetch_json(f"{EUROSTAT_API}/une_rt_m?{q_un}")
        if une:
            period, val = _latest_single_time_series(une)
            if period and val is not None:
                out.append(
                    DataPoint(
                        ts=ts,
                        symbol="EU_UNEMP_RATE_EA20",
                        cadence=self.cadence,
                        payload={
                            "source": "eurostat_scrape",
                            "kind": "employment",
                            "metric": "unemployment_rate_pct",
                            "geo": "EA20",
                            "period": period,
                            "value": val,
                            "dataset": "une_rt_m",
                        },
                    )
                )

        q_tr = urllib.parse.urlencode(
            {
                "format": "JSON",
                "geo": "EU27_2020",
                "partner": "EXT_EU27_2020",
                "indic_et": "MIO_BAL_VAL",
                "sitc06": "TOTAL",
                "sinceTimePeriod": str(datetime.now(timezone.utc).year - 3),
            }
        )
        trd = _fetch_json(f"{EUROSTAT_API}/ext_lt_intertrd?{q_tr}")
        if trd:
            period, val = _latest_single_time_series(trd)
            if period and val is not None:
                out.append(
                    DataPoint(
                        ts=ts,
                        symbol="EU_TRADE_BAL_EXTRA_EU27",
                        cadence=self.cadence,
                        payload={
                            "source": "eurostat_scrape",
                            "kind": "trade",
                            "metric": "trade_balance_million_eur",
                            "geo": "EU27_2020",
                            "partner": "EXT_EU27_2020",
                            "period": period,
                            "value": val,
                            "dataset": "ext_lt_intertrd",
                        },
                    )
                )

        return out

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points: List[DataPoint] = []
        try:
            points.extend(self._fetch_html_datapoints())
        except Exception as e:
            self.logger.error(f"Eurostat HTML scrape failed: {e}")

        try:
            points.extend(self._fetch_macro_api_points())
        except Exception as e:
            self.logger.error(f"Eurostat API fetch failed: {e}")

        if not points:
            self.logger.warning("Eurostat scrape returned no data points")
            return []

        if symbols:
            symset = {s.upper() for s in symbols}
            points = [p for p in points if p.symbol and p.symbol.upper() in symset]

        return points

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        cleaned = []
        seen = set()
        for point in raw_points:
            if not point.payload:
                continue
            if not isinstance(point.ts, datetime):
                try:
                    point.ts = datetime.fromisoformat(str(point.ts))
                except (ValueError, TypeError):
                    continue
            if point.ts.tzinfo is None:
                point.ts = point.ts.replace(tzinfo=timezone.utc)

            pl = dict(point.payload)
            pl.setdefault("source", "eurostat_scrape")
            point.payload = pl

            point.compute_hash()
            dedup_key = (point.symbol, point.ts.isoformat(), point.source_hash)
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
        macro_ok = 0
        for p in clean_points:
            pl = p.payload or {}
            k = pl.get("kind")
            if k in ("inflation", "employment", "trade"):
                if pl.get("period") is not None and pl.get("value") is not None:
                    macro_ok += 1
            elif k == "portal_table":
                if pl.get("code_or_label") or pl.get("description"):
                    macro_ok += 1

        report.completeness = (macro_ok / total * 100) if total else 0.0
        report.schema_valid = macro_ok == total
        report.issues = []
        if not report.schema_valid:
            report.issues.append(f"Incomplete or empty rows: {total - macro_ok} of {total}")
        report.compute_overall()
        return report


if __name__ == "__main__":
    mod = EurostatScrape()
    pts = mod.fetch()
    print(f"{len(pts)} points")
    for p in pts[:12]:
        print(f"  {p.symbol}: {p.payload}")
