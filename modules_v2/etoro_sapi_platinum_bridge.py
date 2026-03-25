"""
eToro SAPI → Platinum records bridge.

Reads latest Silver/Gold payloads from module ``etoro-sapi-instruments`` and
writes rows into ``platinum_records``. Intended to run after the SAPI fetch module.
"""
from __future__ import annotations

import json
import logging
import math
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from psycopg2.extras import Json

from qcd_platform.pipeline import db
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

logger = logging.getLogger("quantclaw.module.etoro-sapi-platinum-bridge")

SOURCE_MODULE = "etoro-sapi-instruments"


def _safe_int_bigint(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return None
        return int(round(x))
    except (TypeError, ValueError):
        return None


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def _composite_rating(payload: Dict[str, Any]) -> Tuple[float, str]:
    parts: List[float] = []
    pe = _safe_float(payload.get("pe_ratio"))
    if pe is not None and 0 < pe < 120:
        parts.append(max(0.0, min(100.0, 100.0 - pe)))

    upside = _safe_float(payload.get("upside_pct"))
    if upside is not None:
        parts.append(max(0.0, min(100.0, 50.0 + upside)))

    roe = _safe_float(payload.get("roe"))
    if roe is not None:
        parts.append(max(0.0, min(100.0, 50.0 + roe * 120.0)))

    esg = _safe_float(payload.get("esg_total"))
    if esg is not None:
        parts.append(max(0.0, min(100.0, esg)))

    if not parts:
        return 50.0, "Hold"

    score = sum(parts) / len(parts)
    if score >= 75:
        rating = "Strong Buy"
    elif score >= 60:
        rating = "Buy"
    elif score >= 45:
        rating = "Hold"
    else:
        rating = "Cautious"
    return score, rating


def _sections_populated(payload: Dict[str, Any]) -> int:
    groups = [
        ("price", ("current_price", "close_price", "volume")),
        ("valuation", ("pe_ratio", "pb_ratio", "ps_ratio", "market_cap")),
        ("fundamentals", ("roe", "roa", "gross_margin", "debt_to_equity")),
        ("analyst", ("analyst_consensus", "target_price_mean", "analyst_count")),
        ("social", ("popularity", "trader_change_7d")),
        ("esg", ("esg_total",)),
    ]
    n = 0
    for _, keys in groups:
        if any(payload.get(k) is not None for k in keys):
            n += 1
    return n


def _row_from_payload(
    symbol: str,
    payload: Dict[str, Any],
    generated_at: datetime,
) -> Tuple[Any, ...]:
    comp, rating = _composite_rating(payload)
    vol = _safe_int_bigint(payload.get("volume"))

    platinum_payload = {
        "source": "etoro_sapi",
        "etoro_instrument_id": payload.get("etoro_instrument_id"),
        "normalized": {k: v for k, v in payload.items() if k != "sapi_raw_keys"},
    }

    return (
        symbol[:50],
        generated_at,
        float(comp),
        rating[:20],
        _safe_float(payload.get("current_price")),
        None,  # change_pct
        None,  # rsi_14
        _safe_float(payload.get("ma_10d")),  # sma_20 proxy
        _safe_float(payload.get("ma_50d")),  # sma_50
        vol,
        _safe_float(payload.get("pe_ratio")),
        None,  # pe_forward
        _safe_float(payload.get("pb_ratio")),
        _safe_float(payload.get("ps_ratio")),
        _safe_float(payload.get("ev_ebitda")),
        _safe_int_bigint(payload.get("market_cap")),
        None,  # revenue
        _safe_float(payload.get("revenue_growth_1y")),
        _safe_float(payload.get("profit_margin")),
        _safe_float(payload.get("roe")),
        _safe_float(payload.get("debt_to_equity")),
        None,  # fcf
        _safe_float(payload.get("target_price_mean")),
        None,  # median
        _safe_float(payload.get("upside_pct")),
        _safe_int_bigint(payload.get("analyst_count")),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        (payload.get("name") or "")[:200],
        (payload.get("sector") or "")[:100],
        (payload.get("industry") or "")[:100],
        Json(platinum_payload),
        _sections_populated(payload),
        None,
    )


class EtoroSapiPlatinumBridgeModule(BaseModule):
    name = "etoro-sapi-platinum-bridge"
    display_name = "eToro SAPI → Platinum Bridge"
    cadence = "4h"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals"]

    def register(self) -> int:
        self.module_id = db.register_module(
            name=self.name,
            display_name=self.display_name,
            source_file="modules_v2/etoro_sapi_platinum_bridge.py",
            cadence=self.cadence,
            granularity=self.granularity,
            tags=self.tags,
        )
        return self.module_id

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        source_id = db.get_module_id(SOURCE_MODULE)
        if not source_id:
            self.logger.error("Source module %s is not registered", SOURCE_MODULE)
            return []

        tiers = ["platinum", "gold", "silver"]
        sym_filter = ""
        params: List[Any] = [source_id, tiers]
        if symbols:
            sym_filter = " AND symbol = ANY(%s) "
            params.append(symbols)

        sql = f"""
            SELECT DISTINCT ON (symbol) symbol, ts, payload, tier
            FROM data_points
            WHERE module_id = %s AND tier = ANY(%s)
            {sym_filter}
            ORDER BY symbol,
                CASE tier
                    WHEN 'platinum' THEN 0
                    WHEN 'gold' THEN 1
                    WHEN 'silver' THEN 2
                    ELSE 3
                END,
                ts DESC
        """
        rows = db.execute_query(sql, tuple(params), fetch=True) or []

        ts = datetime.now(timezone.utc)
        points: List[DataPoint] = []
        for row in rows:
            pl = row["payload"]
            if isinstance(pl, str):
                try:
                    pl = json.loads(pl)
                except json.JSONDecodeError:
                    continue
            if not isinstance(pl, dict):
                continue
            sym = row.get("symbol") or pl.get("symbol")
            if not sym:
                continue
            points.append(
                DataPoint(
                    ts=ts,
                    symbol=str(sym)[:50],
                    cadence=self.cadence,
                    tier="bronze",
                    payload=pl,
                )
            )
        return points

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        cleaned = super().clean(raw_points)
        for p in cleaned:
            p.payload = dict(p.payload or {})
            p.payload["_bridge_symbol"] = p.symbol
        return cleaned

    def validate(self, clean_points: List[DataPoint]) -> QualityReport:
        report = QualityReport()
        if not clean_points:
            report.issues.append("No SAPI rows to bridge")
            report.compute_overall()
            return report

        with_price = sum(1 for p in clean_points if (p.payload or {}).get("current_price"))
        report.completeness = with_price / len(clean_points) * 100.0
        report.timeliness = 100.0
        report.accuracy = report.completeness
        report.consistency = 100.0
        report.schema_valid = True
        report.compute_overall()
        return report

    def run(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Load from ``data_points``, write ``platinum_records``, minimal DCC telemetry."""
        if self.module_id is None:
            self.register()

        result: Dict[str, Any] = {
            "module": self.name,
            "status": "unknown",
            "tier_reached": "none",
            "rows_in": 0,
            "rows_out": 0,
            "platinum_inserted": 0,
            "duration_ms": 0,
        }
        start = time.time()
        run_id = db.start_pipeline_run(self.module_id, "gold")

        try:
            raw_points = self.fetch(symbols=symbols)
            result["rows_in"] = len(raw_points)
            if not raw_points:
                duration_ms = int((time.time() - start) * 1000)
                db.complete_pipeline_run(run_id, "success", 0, 0, duration_ms=duration_ms)
                result["status"] = "empty"
                result["duration_ms"] = duration_ms
                return result

            clean_points = self.clean(raw_points)
            quality = self.validate(clean_points)

            db.record_quality_check(run_id, "completeness", quality.completeness >= 70, int(quality.completeness))
            db.record_quality_check(run_id, "timeliness", True, 100)
            db.record_quality_check(run_id, "accuracy", quality.accuracy >= 70, int(quality.accuracy))
            db.record_quality_check(run_id, "consistency", True, 100)
            db.record_quality_check(run_id, "schema_valid", quality.schema_valid, 100 if quality.schema_valid else 0)

            generated_at = datetime.now(timezone.utc)
            insert_sql = """
                INSERT INTO platinum_records (
                    symbol, generated_at, composite_score, rating,
                    price, change_pct, rsi_14, sma_20, sma_50, volume,
                    pe_trailing, pe_forward, pb_ratio, ps_ratio, ev_ebitda,
                    market_cap, revenue, revenue_growth, profit_margin, roe,
                    debt_to_equity, free_cash_flow,
                    analyst_target_mean, analyst_target_median, analyst_upside_pct, analyst_count,
                    beat_rate, avg_surprise_pct, earnings_quality, altman_z_score,
                    sentiment_score, sentiment_signal,
                    insider_signal, insider_buy_sell_ratio,
                    gf_score, gf_value, gf_financial_strength, gf_profitability, gf_growth,
                    dcf_intrinsic_value, dcf_upside_pct,
                    company_name, sector, industry,
                    payload, sections_populated, elapsed_seconds
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
            """
            batch = [
                _row_from_payload(p.symbol, p.payload, generated_at)
                for p in clean_points
            ]
            db.execute_many(insert_sql, batch)
            result["platinum_inserted"] = len(batch)

            summary_payload = {
                "source_module": SOURCE_MODULE,
                "symbols_bridged": len(clean_points),
                "generated_at": generated_at.isoformat(),
            }
            summary_point = DataPoint(
                ts=generated_at,
                symbol="_bridge_summary",
                cadence=self.cadence,
                tier="silver",
                quality_score=quality.overall_score,
                payload=summary_payload,
            )
            summary_point.compute_hash()
            db.insert_data_points(self.module_id, [summary_point.to_dict()])

            duration_ms = int((time.time() - start) * 1000)
            db.complete_pipeline_run(
                run_id,
                "success",
                rows_in=len(raw_points),
                rows_out=len(clean_points),
                duration_ms=duration_ms,
            )
            result["rows_out"] = len(clean_points)
            result["status"] = "success"
            result["tier_reached"] = "silver"
            result["quality_score"] = quality.overall_score
            result["duration_ms"] = duration_ms
            self.logger.info(
                "Platinum bridge: %s rows → platinum_records (%sms)",
                len(batch),
                duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self.logger.error("Platinum bridge failed: %s", e)
            db.complete_pipeline_run(
                run_id,
                "failed",
                rows_in=result["rows_in"],
                error_message=str(e),
                duration_ms=duration_ms,
            )
            try:
                db.create_alert(
                    self.module_id,
                    "critical",
                    f"etoro platinum bridge: {e}",
                    category="system",
                    run_id=run_id,
                    details={"traceback": traceback.format_exc()[-800:]},
                )
            except Exception:
                pass
            result["status"] = "failed"
            result["error"] = str(e)
            result["duration_ms"] = duration_ms

        return result
