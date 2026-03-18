"""
BaseModule — abstract base class for all QuantClaw data modules.

Each module inherits from BaseModule and implements:
  - fetch() → raw data (Bronze)
  - clean() → validated data (Silver)
  - validate() → quality report (Gold promotion)
"""
import hashlib
import json
import logging
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import db
from .kafka_producer import publish_event
from .redis_cache import cache_latest

logger = logging.getLogger("quantclaw.pipeline")


@dataclass
class DataPoint:
    ts: datetime
    symbol: Optional[str] = None
    cadence: str = "daily"
    tier: str = "bronze"
    quality_score: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)
    source_hash: Optional[str] = None

    def compute_hash(self) -> str:
        raw = json.dumps(self.payload, sort_keys=True, default=str)
        self.source_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self.source_hash

    def to_dict(self) -> Dict:
        d = asdict(self)
        if isinstance(d["ts"], datetime):
            d["ts"] = d["ts"].isoformat()
        return d


@dataclass
class QualityReport:
    completeness: float = 0.0
    timeliness: float = 0.0
    accuracy: float = 0.0
    consistency: float = 0.0
    schema_valid: bool = True
    overall_score: int = 0
    issues: List[str] = field(default_factory=list)
    passed_gold: bool = False

    def compute_overall(self):
        scores = [self.completeness, self.timeliness, self.accuracy, self.consistency]
        non_zero = [s for s in scores if s > 0]
        self.overall_score = int(sum(non_zero) / len(non_zero)) if non_zero else 0
        self.passed_gold = self.overall_score >= 80 and self.schema_valid


class BaseModule(ABC):
    name: str = "unnamed"
    display_name: str = ""
    cadence: str = "daily"
    granularity: str = "symbol"  # symbol | market | macro | global
    tags: List[str] = []
    symbols: Optional[List[str]] = None  # None = all symbols in universe

    def __init__(self):
        self.module_id: Optional[int] = None
        self.logger = logging.getLogger(f"quantclaw.module.{self.name}")

    def register(self) -> int:
        self.module_id = db.register_module(
            name=self.name,
            display_name=self.display_name or self.name,
            source_file=f"modules/{self.name}.py",
            cadence=self.cadence,
            granularity=self.granularity,
            tags=self.tags,
        )
        return self.module_id

    @abstractmethod
    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        """Bronze: fetch raw data from external source. Returns list of DataPoints."""
        ...

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        """Silver: validate schema, clean nulls, normalize timestamps, deduplicate.
        Override for module-specific cleaning logic."""
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
        """Gold: run quality checks. Override for module-specific validation."""
        report = QualityReport()

        if not clean_points:
            report.issues.append("No data points to validate")
            report.compute_overall()
            return report

        total = len(clean_points)
        with_payload = sum(1 for p in clean_points if p.payload)
        report.completeness = (with_payload / total * 100) if total > 0 else 0

        now = datetime.now(timezone.utc)
        cadence_hours = {
            "realtime": 0.1, "1min": 0.05, "5min": 0.15, "15min": 0.5,
            "1h": 2, "4h": 8, "daily": 48, "weekly": 336,
            "monthly": 1440, "quarterly": 4320,
        }
        max_age_hours = cadence_hours.get(self.cadence, 48)
        latest = max(p.ts for p in clean_points)
        age_hours = (now - latest).total_seconds() / 3600
        report.timeliness = max(0, min(100, (1 - age_hours / max_age_hours) * 100))

        report.accuracy = 100.0
        report.consistency = 100.0
        report.schema_valid = True

        report.compute_overall()
        return report

    def run(self, symbols: List[str] = None) -> Dict:
        """Execute full Bronze → Silver → Gold pipeline for this module."""
        if self.module_id is None:
            self.register()

        result = {
            "module": self.name,
            "status": "unknown",
            "tier_reached": "none",
            "rows_in": 0,
            "rows_out": 0,
            "duration_ms": 0,
        }

        start_time = time.time()
        run_id = db.start_pipeline_run(self.module_id, "gold")

        try:
            # Bronze: fetch
            self.logger.info(f"[{self.name}] Fetching data...")
            raw_points = self.fetch(symbols=symbols)
            result["rows_in"] = len(raw_points)

            if not raw_points:
                self.logger.warning(f"[{self.name}] No data returned from fetch")
                duration_ms = int((time.time() - start_time) * 1000)
                db.complete_pipeline_run(run_id, "success", rows_in=0, rows_out=0, duration_ms=duration_ms)
                result["status"] = "empty"
                result["duration_ms"] = duration_ms
                return result

            for p in raw_points:
                p.compute_hash()

            # Store bronze
            inserted = db.insert_data_points(self.module_id, [p.to_dict() for p in raw_points])
            self.logger.info(f"[{self.name}] Bronze: {inserted} points stored")

            domain_tag = self._primary_domain()
            publish_event(f"quantclaw.pipeline.bronze.{domain_tag}", {
                "module": self.name,
                "count": inserted,
                "ts": datetime.now(timezone.utc).isoformat(),
            })

            # Silver: clean
            self.logger.info(f"[{self.name}] Cleaning data...")
            clean_points = self.clean(raw_points)

            if clean_points:
                db.insert_data_points(self.module_id, [p.to_dict() for p in clean_points])
                publish_event(f"quantclaw.pipeline.silver.{domain_tag}", {
                    "module": self.name,
                    "count": len(clean_points),
                    "ts": datetime.now(timezone.utc).isoformat(),
                })

            # Gold: validate
            self.logger.info(f"[{self.name}] Validating quality...")
            quality = self.validate(clean_points)

            db.record_quality_check(run_id, "completeness", quality.completeness >= 80, int(quality.completeness))
            db.record_quality_check(run_id, "timeliness", quality.timeliness >= 60, int(quality.timeliness))
            db.record_quality_check(run_id, "accuracy", quality.accuracy >= 80, int(quality.accuracy))
            db.record_quality_check(run_id, "consistency", quality.consistency >= 80, int(quality.consistency))
            db.record_quality_check(run_id, "schema_valid", quality.schema_valid, 100 if quality.schema_valid else 0)

            if quality.passed_gold:
                for p in clean_points:
                    p.tier = "gold"
                    p.quality_score = quality.overall_score
                db.insert_data_points(self.module_id, [p.to_dict() for p in clean_points])
                publish_event(f"quantclaw.pipeline.gold.{domain_tag}", {
                    "module": self.name,
                    "count": len(clean_points),
                    "quality_score": quality.overall_score,
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
                tier_reached = "gold"
            else:
                tier_reached = "silver" if clean_points else "bronze"

            # Update module tier
            db.execute_query(
                "UPDATE modules SET current_tier = %s, quality_score = %s WHERE id = %s",
                (tier_reached, quality.overall_score, self.module_id),
            )

            # Cache latest values in Redis
            for p in clean_points:
                if p.symbol:
                    cache_latest(self.name, p.symbol, p.payload)

            duration_ms = int((time.time() - start_time) * 1000)
            result["rows_out"] = len(clean_points)
            result["status"] = "success"
            result["tier_reached"] = tier_reached
            result["quality_score"] = quality.overall_score
            result["duration_ms"] = duration_ms
            result["issues"] = quality.issues

            db.complete_pipeline_run(
                run_id, "success",
                rows_in=len(raw_points), rows_out=len(clean_points),
                duration_ms=duration_ms,
            )

            self.logger.info(
                f"[{self.name}] Complete: {len(clean_points)} points → {tier_reached} "
                f"(score={quality.overall_score}, {duration_ms}ms)"
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self.logger.error(f"[{self.name}] Failed: {error_msg}")

            db.complete_pipeline_run(
                run_id, "failed",
                rows_in=result["rows_in"],
                error_message=error_msg,
                duration_ms=duration_ms,
            )

            publish_event("quantclaw.pipeline.errors", {
                "module": self.name,
                "error": error_msg,
                "traceback": traceback.format_exc()[-500:],
                "ts": datetime.now(timezone.utc).isoformat(),
            })

            result["status"] = "failed"
            result["error"] = error_msg
            result["duration_ms"] = duration_ms

        return result

    def _primary_domain(self) -> str:
        domain_map = {
            "US Equities": "us_equities",
            "Sentiment": "sentiment",
            "Earnings": "earnings",
            "Fundamentals": "fundamentals",
            "Corporate Actions": "corporate_actions",
            "Macro": "macro",
            "Crypto": "crypto",
            "FX": "fx",
            "Commodities": "commodities",
        }
        for tag in self.tags:
            if tag in domain_map:
                return domain_map[tag]
        return "us_equities"
