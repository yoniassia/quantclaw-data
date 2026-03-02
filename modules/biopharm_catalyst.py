#!/usr/bin/env python3
"""biopharm_catalyst — BioPharmCatalyst FDA pipeline tracker. Source: https://www.biopharmcatalyst.com/. Free, no auth. Scrape-based."""
import requests
import os
import json
import time
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
BASE = "https://www.biopharmcatalyst.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"}

def get_pdufa_calendar(**kwargs):
    """Fetch upcoming PDUFA (FDA decision) dates."""
    cache_file = os.path.join(CACHE_DIR, "biopharm_pdufa.json")
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 3600 * 6:
        with open(cache_file) as f:
            return json.load(f)
    try:
        url = f"{BASE}/calendars/pdufa-calendar"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        events = []
        rows = soup.select("table tbody tr, .calendar-item, .event-row")
        for row in rows[:100]:
            cells = row.find_all(["td", "span", "div"])
            texts = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]
            if len(texts) >= 2:
                events.append({"raw": texts, "ticker": texts[0] if len(texts[0]) <= 6 else "",
                                "drug": texts[1] if len(texts) > 1 else "",
                                "date": texts[2] if len(texts) > 2 else "",
                                "catalyst": texts[3] if len(texts) > 3 else ""})
        # Fallback: try API endpoint
        if not events:
            api_url = f"{BASE}/api/v1/pdufa"
            resp2 = requests.get(api_url, headers=HEADERS, timeout=10)
            if resp2.status_code == 200:
                events = resp2.json() if isinstance(resp2.json(), list) else [resp2.json()]
        result = {"source": "BioPharmCatalyst", "calendar": "PDUFA",
                  "count": len(events), "events": events,
                  "fetch_time": datetime.now().isoformat()}
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)
        return result
    except Exception as e:
        return {"error": str(e), "source": "biopharmcatalyst"}

def get_fda_decisions(days=30, **kwargs):
    """Fetch recent FDA approval/rejection decisions."""
    cache_file = os.path.join(CACHE_DIR, "biopharm_fda_decisions.json")
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 3600 * 6:
        with open(cache_file) as f:
            return json.load(f)
    try:
        url = f"{BASE}/calendars/fda-calendar"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        decisions = []
        rows = soup.select("table tbody tr, .calendar-item")
        for row in rows[:50]:
            cells = row.find_all(["td", "span", "div"])
            texts = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]
            if len(texts) >= 2:
                decisions.append({"raw": texts})
        result = {"source": "BioPharmCatalyst", "type": "FDA decisions",
                  "days": days, "count": len(decisions), "decisions": decisions,
                  "fetch_time": datetime.now().isoformat()}
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)
        return result
    except Exception as e:
        return {"error": str(e)}

def get_pipeline_by_phase(phase="3", **kwargs):
    """Fetch drug pipeline filtered by clinical phase."""
    try:
        url = f"{BASE}/pipeline"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        drugs = []
        rows = soup.select("table tbody tr, .pipeline-item")
        for row in rows[:200]:
            text = row.get_text(strip=True)
            if f"Phase {phase}" in text or f"phase {phase}" in text.lower():
                cells = row.find_all(["td", "span"])
                texts = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]
                drugs.append({"raw": texts, "phase": phase})
        return {"phase": phase, "count": len(drugs), "drugs": drugs,
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "phase": phase}

def get_data(ticker=None, **kwargs):
    return get_pdufa_calendar(**kwargs)

if __name__ == "__main__":
    result = get_pdufa_calendar()
    print(f"PDUFA events: {result.get('count', 0)}")
    for e in result.get('events', [])[:5]:
        print(f"  {e}")
