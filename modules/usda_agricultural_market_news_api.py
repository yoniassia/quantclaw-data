#!/usr/bin/env python3
"""
USDA Agricultural Market News API — Commodities & Livestock Prices

Provides access to USDA Market News reports on grains, livestock, dairy, fruits/vegetables.
Requires API key from https://mymarketnews.ams.usda.gov/ (free registration).
Data primarily in PDF reports; module fetches lists and filters.

Source: https://mymarketnews.ams.usda.gov/
Category: Commodities & Agriculture
Free tier: True (requires free API key registration)
Update frequency: Daily/Real-time reports
Author: QuantClaw Data NightBuilder
Setup: Set USDA_MARKET_NEWS_KEY in .env file
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import time

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = "https://marsapi.ams.usda.gov/services/v1.2"
API_KEY = os.environ.get("USDA_MARKET_NEWS_KEY", "")
HEADERS = {"User-Agent": "QuantClaw-Data/1.0"}

def _request(endpoint: str, params: Dict = None) -> Dict:
    """Helper for API requests with retries."""
    if not API_KEY:
        return {
            "error": "USDA_MARKET_NEWS_KEY not set. Get free API key from https://mymarketnews.ams.usda.gov/",
            "results": []
        }
    
    url = f"{BASE_URL}/{endpoint}"
    params = params or {}
    params["apiKey"] = API_KEY
    
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                return {
                    "error": "API access denied - check your USDA_MARKET_NEWS_KEY or get one from https://mymarketnews.ams.usda.gov/",
                    "results": []
                }
            time.sleep(1 * attempt)
        except Exception as e:
            time.sleep(1 * attempt)
    return {"error": f"API request failed: {endpoint}", "results": []}

def get_report_list(limit: int = 50, commodity_id: Optional[int] = None) -> List[Dict]:
    """List recent published reports."""
    params = {}
    if commodity_id:
        params["commodityId"] = str(commodity_id)
    data = _request("reports", params)
    results = data.get("results", [])
    return results[:limit] if results else []

def search_reports(query: str, limit: int = 20) -> List[Dict]:
    """Search reports by title/query (client-side filter)."""
    reports = get_report_list(limit=100)
    q_lower = query.lower()
    return [r for r in reports if q_lower in r.get("reportTitle", "").lower()][:limit]

def get_market_reports(commodity: str = "Cattle") -> List[Dict]:
    """Fetch recent market reports for commodity (filter by title)."""
    return search_reports(commodity, limit=20)

def get_livestock_prices(type_: str = "Cattle") -> List[Dict]:
    """Livestock auction/market prices (filter reports)."""
    return search_reports(f"{type_} Livestock", limit=10)

def get_grain_prices(grain: str = "Corn") -> List[Dict]:
    """Grain price data/bids (filter reports)."""
    return search_reports(f"{grain} Grain", limit=10) or search_reports(grain, limit=10)

def get_dairy_prices() -> List[Dict]:
    """Dairy market prices (milk, cheese, etc.)."""
    return search_reports("Dairy", limit=10) or search_reports("Milk", limit=10)

def get_report(report_id: int) -> Dict:
    """Get single report metadata."""
    data = _request(f"getReport/{report_id}")
    # PDF URL example: https://marketnews.usda.gov/mprApi/gw/{data['fileName']}.{data['fileExtension']}
    if "fileName" in data:
        data["pdf_url"] = f"https://marketnews.usda.gov/mprApi/gw/{data['fileName']}.{data['fileExtension']}"
    return data

if __name__ == "__main__":
    print(json.dumps({"module": "usda_agricultural_market_news_api", "status": "ready"}, indent=2))
