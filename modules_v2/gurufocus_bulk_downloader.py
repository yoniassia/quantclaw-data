"""
GuruFocus Bulk Downloader — Data package management for local caching.

Source: gurufocus.com/data API (Enterprise)
Cadence: Monthly
Granularity: Global
Tags: Fundamentals, GuruFocus
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from modules_v2.gurufocus_client import get_data_packages, get_download_url

logger = logging.getLogger("quantclaw.gurufocus.bulk")

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "gurufocus_bulk")


class GurufocusBulkDownloader(BaseModule):
    name = "gurufocus_bulk_downloader"
    display_name = "GuruFocus — Bulk Data Packages"
    cadence = "monthly"
    granularity = "global"
    tags = ["Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        try:
            packages = get_data_packages()
            if not packages:
                logger.warning("No data packages available")
                return points

            pkg_list = packages if isinstance(packages, list) else packages.get("data", packages.get("packages", []))
            if not isinstance(pkg_list, list):
                pkg_list = [packages] if isinstance(packages, dict) else []

            for pkg in pkg_list:
                pkg_id = str(pkg.get("id", pkg.get("package_id", "")))
                pkg_name = pkg.get("name", pkg.get("title", f"package_{pkg_id}"))

                points.append(DataPoint(
                    ts=datetime.now(timezone.utc),
                    symbol=None,
                    cadence="monthly",
                    tier="bronze",
                    payload={
                        "source": "gurufocus",
                        "type": "bulk_package",
                        "package_id": pkg_id,
                        "package_name": pkg_name,
                        "description": pkg.get("description", ""),
                        "size": pkg.get("size", ""),
                        "updated": pkg.get("updated_at", pkg.get("date", "")),
                    },
                ))

        except Exception as e:
            logger.warning(f"Bulk package listing failed: {e}")

        logger.info(f"Bulk packages found: {len(points)}")
        return points


if __name__ == "__main__":
    mod = GurufocusBulkDownloader()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
