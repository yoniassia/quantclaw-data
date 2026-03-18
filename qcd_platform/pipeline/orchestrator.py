"""
Pipeline Orchestrator — schedules and runs modules based on cadence.
Handles retry logic, error escalation, and health monitoring.
"""
import importlib
import importlib.util
import logging
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from . import db
from .kafka_producer import publish_event
from .redis_cache import set_module_health, publish_update

logger = logging.getLogger("quantclaw.orchestrator")

CADENCE_INTERVALS = {
    "realtime": timedelta(minutes=1),
    "1min": timedelta(minutes=1),
    "5min": timedelta(minutes=5),
    "15min": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
    "quarterly": timedelta(days=90),
}


class PipelineOrchestrator:
    def __init__(self, modules_dir: str = None, max_workers: int = 4):
        self.modules_dir = modules_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "modules_v2"
        )
        self.max_workers = max_workers
        self._module_cache: Dict[str, object] = {}

    def discover_modules(self) -> List[Dict]:
        """Find all registered modules due for execution."""
        rows = db.execute_query(
            """SELECT id, name, cadence, last_run_at, next_run_at, consecutive_failures
               FROM modules
               WHERE is_active = true
               ORDER BY next_run_at NULLS FIRST, last_run_at NULLS FIRST""",
            fetch=True,
        )
        return rows or []

    def get_due_modules(self) -> List[Dict]:
        """Return modules whose next_run_at is in the past or null."""
        now = datetime.now(timezone.utc)
        modules = self.discover_modules()
        due = []
        for m in modules:
            if m["consecutive_failures"] >= 3:
                continue
            if m["next_run_at"] is None or m["next_run_at"] <= now:
                due.append(m)
        return due

    def load_module_class(self, module_name: str):
        """Dynamically load a module class from modules_v2 directory."""
        if module_name in self._module_cache:
            return self._module_cache[module_name]

        module_path = os.path.join(self.modules_dir, f"{module_name}.py")
        if not os.path.exists(module_path):
            logger.warning(f"Module file not found: {module_path}")
            return None

        spec = importlib.util.spec_from_file_location(f"modules_v2.{module_name}", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find the BaseModule subclass
        from .base_module import BaseModule
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (isinstance(attr, type) and issubclass(attr, BaseModule)
                    and attr is not BaseModule):
                instance = attr()
                self._module_cache[module_name] = instance
                return instance

        logger.warning(f"No BaseModule subclass found in {module_path}")
        return None

    def run_module(self, module_name: str, symbols: List[str] = None) -> Dict:
        """Run a single module through the full pipeline."""
        module = self.load_module_class(module_name)
        if module is None:
            return {"module": module_name, "status": "not_found"}

        set_module_health(module_name, "running")
        result = module.run(symbols=symbols)

        health_status = "healthy" if result["status"] == "success" else "error"
        set_module_health(module_name, health_status, {
            "tier": result.get("tier_reached", "none"),
            "quality": result.get("quality_score", 0),
            "duration_ms": result.get("duration_ms", 0),
            "last_run": datetime.now(timezone.utc).isoformat(),
        })

        # Schedule next run
        interval = CADENCE_INTERVALS.get(module.cadence, timedelta(days=1))
        next_run = datetime.now(timezone.utc) + interval
        db.execute_query(
            "UPDATE modules SET next_run_at = %s WHERE name = %s",
            (next_run, module_name),
        )

        publish_update("qcd:updates", {
            "type": "module_complete",
            "module": module_name,
            "result": result,
        })

        return result

    def run_module_with_retry(self, module_name: str, max_retries: int = 3,
                              symbols: List[str] = None) -> Dict:
        """Run module with retry logic. After max_retries, create an alert."""
        last_result = None
        for attempt in range(1, max_retries + 1):
            result = self.run_module(module_name, symbols=symbols)
            last_result = result

            if result["status"] in ("success", "empty"):
                return result

            logger.warning(f"[{module_name}] Attempt {attempt}/{max_retries} failed: {result.get('error', 'unknown')}")

            if attempt < max_retries:
                time.sleep(60 * attempt)

        module_id = db.get_module_id(module_name)
        if module_id:
            db.create_alert(
                module_id=module_id,
                severity="critical",
                message=f"Module {module_name} failed {max_retries} consecutive times: {last_result.get('error', 'unknown')}",
                category="source_down",
                details=last_result,
            )

            publish_event("quantclaw.pipeline.alerts", {
                "module": module_name,
                "severity": "critical",
                "message": f"Module failed {max_retries}x — needs human intervention",
                "error": last_result.get("error", "unknown"),
                "ts": datetime.now(timezone.utc).isoformat(),
            })

            try:
                from ..scripts.alert_notifier import check_and_notify
                check_and_notify()
            except Exception as e:
                logger.warning(f"WhatsApp alert delivery failed: {e}")

        return last_result

    def run_batch(self, module_names: List[str] = None, symbols: List[str] = None) -> List[Dict]:
        """Run multiple modules in parallel."""
        if module_names is None:
            due = self.get_due_modules()
            module_names = [m["name"] for m in due]

        if not module_names:
            logger.info("No modules due for execution")
            return []

        logger.info(f"Running batch of {len(module_names)} modules...")
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.run_module_with_retry, name, 3, symbols): name
                for name in module_names
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"[{name}] Unexpected error: {e}")
                    results.append({"module": name, "status": "error", "error": str(e)})

        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Batch complete: {success_count}/{len(results)} succeeded")

        publish_update("qcd:updates", {
            "type": "batch_complete",
            "total": len(results),
            "success": success_count,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        return results

    def run_overnight(self, cadences: List[str] = None):
        """Overnight batch: run all modules matching given cadences."""
        cadences = cadences or ["daily", "weekly", "monthly", "quarterly"]
        now = datetime.now(timezone.utc)

        modules = db.execute_query(
            """SELECT name FROM modules
               WHERE is_active = true AND cadence = ANY(%s)
               AND (next_run_at IS NULL OR next_run_at <= %s)
               AND consecutive_failures < 3
               ORDER BY cadence, name""",
            (cadences, now),
            fetch=True,
        )

        if not modules:
            logger.info("No modules due for overnight run")
            return []

        module_names = [m["name"] for m in modules]
        logger.info(f"Overnight run: {len(module_names)} modules due")
        return self.run_batch(module_names)
