"""
Effective Federal Funds Rate (EFFR) — NY Fed reference rate via Scrapling

Source page: https://www.newyorkfed.org/markets/reference-rates/effr
Data: NY Fed Markets Data API (JSON backing the on-page interactive; the static HTML
      shell does not embed series values — they load from the API linked from the page).
Category: fixed_income / macro
Cadence: Daily
Granularity: Macro
Tags: fixed_income, Fed Funds, EFFR, FOMC
"""
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None

TARGET_URL = "https://www.newyorkfed.org/markets/reference-rates/effr"
MARKETS_API_URL = "https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json"


def _parse_app_config(page) -> Optional[Dict[str, Any]]:
    try:
        roots = page.css("app-root")
        if not roots:
            return None
        raw = roots[0].attrib.get("appconfig") or roots[0].attrib.get("appConfig")
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def _effr_percent(rec: Dict[str, Any]) -> Optional[float]:
    v = rec.get("percentRate")
    if v is None:
        v = rec.get("percent")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_effective_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    s = raw.strip()
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
        return d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class ScraplingFedFundsRate(BaseModule):
    name = "scrapling_fed_funds_rate"
    display_name = "Effective Federal Funds Rate (Scrapling)"
    cadence = "daily"
    granularity = "macro"
    tags = ["fixed_income", "Fed Funds", "EFFR", "Macro"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if Fetcher is None:
            self.logger.error("Scrapling not installed")
            return []

        fetcher = Fetcher()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        page_app_config: Optional[Dict[str, Any]] = None
        try:
            page = fetcher.get(TARGET_URL, headers=headers)
            page_app_config = _parse_app_config(page)
        except Exception as e:
            self.logger.warning(f"EFFR reference page request failed (continuing with API): {e}")

        try:
            api_resp = fetcher.get(MARKETS_API_URL, headers=headers)
            data = api_resp.json()
        except Exception as e:
            self.logger.error(f"EFFR Markets API request failed: {e}")
            return []

        if not isinstance(data, dict):
            self.logger.error("EFFR API returned non-object JSON")
            return []

        ref_rates = data.get("refRates") or []
        if not ref_rates:
            self.logger.warning("EFFR API returned no refRates")
            return []

        rec = ref_rates[0]
        if not isinstance(rec, dict):
            return []

        effr = _effr_percent(rec)
        eff_date = _parse_effective_date(rec.get("effectiveDate"))
        if effr is None or eff_date is None:
            self.logger.warning("EFFR record missing rate or effective date")
            return []

        tr_from = rec.get("targetRateFrom")
        tr_to = rec.get("targetRateTo")
        vol = rec.get("volumeInBillions")

        payload: Dict[str, Any] = {
            "effective_date": rec.get("effectiveDate"),
            "rate_type": rec.get("type") or "EFFR",
            "effr_percent": effr,
            "target_range": {
                "from": float(tr_from) if tr_from is not None else None,
                "to": float(tr_to) if tr_to is not None else None,
            },
            "volume_billions": float(vol) if vol is not None else None,
            "percentiles": {
                "p1": rec.get("percentPercentile1"),
                "p25": rec.get("percentPercentile25"),
                "p75": rec.get("percentPercentile75"),
                "p99": rec.get("percentPercentile99"),
            },
            "revision_indicator": (rec.get("revisionIndicator") or "").strip(),
            "page_app_config": page_app_config,
            "source": "nyfed_markets_api_scrapling",
            "source_page_url": TARGET_URL,
            "data_url": MARKETS_API_URL,
        }

        return [
            DataPoint(
                ts=eff_date,
                symbol=None,
                cadence="daily",
                payload=payload,
            )
        ]

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        cleaned = []
        seen = set()
        for point in raw_points:
            if not point.payload:
                continue
            pl = point.payload
            if pl.get("effr_percent") is None:
                continue
            try:
                float(pl["effr_percent"])
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

        # EFFR is released for the prior business day (~24–72h “age” is normal around weekends).
        latest = max(p.ts for p in clean_points)
        age_hours = (datetime.now(timezone.utc) - latest).total_seconds() / 3600
        if age_hours <= 24 * 7:
            report.timeliness = max(report.timeliness, 95.0)

        total = len(clean_points)
        required_keys = ("effr_percent", "effective_date", "volume_billions", "percentiles", "target_range")
        ok = 0
        for p in clean_points:
            pl = p.payload or {}
            if not all(k in pl for k in required_keys):
                continue
            tr = pl.get("target_range") or {}
            pct = pl.get("percentiles") or {}
            if not isinstance(tr, dict) or not isinstance(pct, dict):
                continue
            if tr.get("from") is None or tr.get("to") is None:
                continue
            if pl.get("volume_billions") is None:
                continue
            need_pct = ("p1", "p25", "p75", "p99")
            if any(pct.get(k) is None for k in need_pct):
                continue
            ok += 1

        report.completeness = (ok / total * 100) if total else 0.0
        report.schema_valid = ok == total
        report.issues = []
        if not report.schema_valid:
            report.issues.append(
                f"Incomplete EFFR rows: {total - ok} of {total} missing rate, range, volume, or percentiles"
            )
        report.compute_overall()
        return report


def run_module(symbols: List[str] = None) -> Dict[str, Any]:
    """Bronze → Silver → Gold for local testing (no DB / orchestrator)."""
    mod = ScraplingFedFundsRate()
    raw_points = mod.fetch(symbols=symbols)
    clean_points = mod.clean(raw_points)
    quality = mod.validate(clean_points)
    return {
        "module": mod.name,
        "bronze_rows": len(raw_points),
        "silver_rows": len(clean_points),
        "tier_reached": "gold" if quality.passed_gold else ("silver" if clean_points else "bronze"),
        "quality": {
            "completeness": quality.completeness,
            "timeliness": quality.timeliness,
            "accuracy": quality.accuracy,
            "consistency": quality.consistency,
            "schema_valid": quality.schema_valid,
            "overall_score": quality.overall_score,
            "passed_gold": quality.passed_gold,
            "issues": list(quality.issues),
        },
        "sample": clean_points[0].to_dict() if clean_points else None,
    }


if __name__ == "__main__":
    result = run_module()
    print(json.dumps(result, indent=2, default=str))
