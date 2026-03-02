#!/usr/bin/env python3
"""
TipRanks Analyst Consensus — stub module.
Returns simulated analyst consensus data (TipRanks blocks scraping).
"""
import json
import datetime
from typing import Dict, List, Optional

def get_consensus(ticker: str = "AAPL") -> Dict:
    return {
        "ticker": ticker.upper(),
        "source": "tipranks_consensus",
        "note": "Simulated - TipRanks blocks automated scraping",
        "consensus": "Moderate Buy",
        "num_analysts": 28,
        "avg_price_target": 245.0,
        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

def get_top_analysts(sector: Optional[str] = None) -> List[Dict]:
    return [{"name": "Stub Analyst", "firm": "N/A", "success_rate": 0.0, "note": "Simulated"}]

def get_data(ticker: str = "AAPL") -> Dict:
    return get_consensus(ticker)

if __name__ == "__main__":
    print(json.dumps(get_data(), indent=2))
