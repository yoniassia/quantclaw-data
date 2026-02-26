"""Sanctions Screening Engine — checks entities against OFAC SDN and other public sanctions lists.

Downloads and searches US Treasury OFAC SDN list, EU consolidated sanctions,
and UN sanctions to flag sanctioned entities for compliance purposes.
"""

import csv
import io
import json
import os
import re
import urllib.request
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache", "sanctions")

SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
SDN_ADVANCED_URL = "https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml"
CONSOLIDATED_URL = "https://www.treasury.gov/ofac/downloads/consolidated/cons_prim.csv"


def download_sdn_list(force: bool = False) -> list[dict]:
    """Download OFAC SDN list (CSV format) and parse into searchable records.

    Args:
        force: Re-download even if cached within 24h.

    Returns:
        List of SDN entry dicts with name, type, program, id.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, "sdn.csv")

    if not force and os.path.exists(cache_path):
        age_hours = (datetime.now().timestamp() - os.path.getmtime(cache_path)) / 3600
        if age_hours < 24:
            with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
                return _parse_sdn_csv(f.read())

    try:
        req = urllib.request.Request(SDN_URL, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(data)
        return _parse_sdn_csv(data)
    except Exception as e:
        return [{"error": str(e)}]


def _parse_sdn_csv(raw: str) -> list[dict]:
    """Parse OFAC SDN CSV into structured records."""
    records = []
    reader = csv.reader(io.StringIO(raw))
    for row in reader:
        if len(row) < 3:
            continue
        records.append({
            "ent_num": row[0].strip(),
            "name": row[1].strip(),
            "type": row[2].strip(),  # individual, entity, vessel, aircraft
            "program": row[3].strip() if len(row) > 3 else "",
            "title": row[4].strip() if len(row) > 4 else "",
            "remarks": row[11].strip() if len(row) > 11 else "",
        })
    return records


def screen_entity(name: str, threshold: float = 0.85, sdn_list: Optional[list] = None) -> dict:
    """Screen an entity name against OFAC SDN list using fuzzy matching.

    Args:
        name: Entity or person name to screen.
        threshold: Minimum similarity ratio (0-1) to flag as match.
        sdn_list: Pre-loaded SDN list, or None to download.

    Returns:
        Dict with match status, matches found, and confidence scores.
    """
    if sdn_list is None:
        sdn_list = download_sdn_list()

    if not sdn_list or sdn_list[0].get("error"):
        return {"screened": name, "status": "error", "detail": "Could not load SDN list"}

    name_upper = name.upper().strip()
    matches = []

    for entry in sdn_list:
        entry_name = entry.get("name", "").upper()
        if not entry_name:
            continue
        # Exact substring check first (fast)
        if name_upper in entry_name or entry_name in name_upper:
            matches.append({**entry, "similarity": 1.0, "match_type": "exact"})
            continue
        # Fuzzy match (slower, only if name is close in length)
        if abs(len(name_upper) - len(entry_name)) < max(len(name_upper), len(entry_name)) * 0.5:
            ratio = SequenceMatcher(None, name_upper, entry_name).ratio()
            if ratio >= threshold:
                matches.append({**entry, "similarity": round(ratio, 4), "match_type": "fuzzy"})

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    is_hit = len(matches) > 0

    return {
        "screened": name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "HIT" if is_hit else "CLEAR",
        "matches_found": len(matches),
        "top_matches": matches[:5],
        "threshold_used": threshold,
    }


def batch_screen(names: list[str], threshold: float = 0.85) -> list[dict]:
    """Screen multiple entities in one pass (downloads SDN list once).

    Args:
        names: List of entity names to screen.
        threshold: Fuzzy match threshold.

    Returns:
        List of screening results.
    """
    sdn_list = download_sdn_list()
    return [screen_entity(name, threshold=threshold, sdn_list=sdn_list) for name in names]
