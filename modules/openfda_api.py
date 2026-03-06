#!/usr/bin/env python3
"""
openFDA API Module
FDA public datasets on drug approvals, adverse events, recalls, and enforcement reports.
Useful for biotech trading strategies based on regulatory milestones.

Source: https://open.fda.gov/apis/
Category: Healthcare & Biotech
Free tier: 240 req/min, 1,000/day unregistered
Update frequency: daily
Built: 2026-03-04 by NightBuilder
"""

import requests
import json
from typing import Dict, Optional

BASE_URL = "https://api.fda.gov"

def _make_request(endpoint: str, search: str = None, limit: int = 10) -> Dict:
    """Make request to openFDA API with error handling"""
    try:
        url = f"{BASE_URL}/{endpoint}?limit={limit}"
        if search:
            url += f"&search={search}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}

def get_drug_approvals(limit: int = 20) -> Dict:
    """
    Get FDA drug approvals.
    
    Args:
        limit: Number of results (max 100)
        
    Returns:
        Dict with approval records including application numbers, sponsors, products
    """
    return _make_request("drug/drugsfda.json", limit=min(limit, 100))

def get_adverse_events(drug_name: Optional[str] = None, limit: int = 10) -> Dict:
    """
    Get adverse event reports.
    
    Args:
        drug_name: Optional drug name to filter by
        limit: Number of results (max 100)
        
    Returns:
        Dict with adverse event data including reactions and outcomes
    """
    search = None
    if drug_name:
        search = f"patient.drug.medicinalproduct:{drug_name}"
    
    return _make_request("drug/event.json", search=search, limit=min(limit, 100))

def get_drug_labels(drug_name: str, limit: int = 5) -> Dict:
    """
    Get drug labeling information.
    
    Args:
        drug_name: Brand or generic name
        limit: Number of results
        
    Returns:
        Dict with labeling data including indications and warnings
    """
    search = f"openfda.brand_name:{drug_name}"
    return _make_request("drug/label.json", search=search, limit=min(limit, 100))

def get_drug_recalls(limit: int = 20) -> Dict:
    """
    Get drug recall enforcement reports.
    
    Args:
        limit: Number of results
        
    Returns:
        Dict with recall data including reasons and products
    """
    return _make_request("drug/enforcement.json", limit=min(limit, 100))

def get_device_recalls(limit: int = 20) -> Dict:
    """
    Get medical device recalls.
    
    Args:
        limit: Number of results
        
    Returns:
        Dict with device recall data
    """
    return _make_request("device/enforcement.json", limit=min(limit, 100))

def get_drug_event_summary(drug_name: str) -> Dict:
    """
    Get summary statistics for a drug's adverse events.
    
    Args:
        drug_name: Drug name to analyze
        
    Returns:
        Summary dict with reaction counts and severity metrics
    """
    events = get_adverse_events(drug_name=drug_name, limit=100)
    
    if "results" not in events:
        return {"error": "No data found", "drug_name": drug_name}
    
    reactions = {}
    total = len(events["results"])
    serious_count = 0
    
    for event in events["results"]:
        if event.get("serious") == "1":
            serious_count += 1
            
        if "patient" in event and "reaction" in event["patient"]:
            for reaction in event["patient"]["reaction"]:
                term = reaction.get("reactionmeddrapt", "unknown")
                reactions[term] = reactions.get(term, 0) + 1
    
    top_reactions = dict(sorted(reactions.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return {
        "drug_name": drug_name,
        "total_events": total,
        "serious_events": serious_count,
        "serious_rate": round(serious_count / total * 100, 1) if total > 0 else 0,
        "top_reactions": top_reactions,
        "success": True
    }

if __name__ == "__main__":
    print("Testing openFDA API module...")
    
    print("\n1. Drug approvals:")
    approvals = get_drug_approvals(limit=2)
    if "results" in approvals:
        print(f"✓ Found {len(approvals['results'])} approvals")
    else:
        print(f"✗ Error: {approvals.get('error', 'Unknown')[:80]}")
    
    print("\n2. Adverse events:")
    events = get_adverse_events(limit=2)
    if "results" in events:
        print(f"✓ Found {len(events['results'])} events")
    else:
        print(f"✗ Error: {events.get('error', 'Unknown')[:80]}")
    
    print("\n3. Drug recalls:")
    recalls = get_drug_recalls(limit=2)
    if "results" in recalls:
        print(f"✓ Found {len(recalls['results'])} recalls")
    else:
        print(f"✗ Error: {recalls.get('error', 'Unknown')[:80]}")
    
    print("\n4. Aspirin event summary:")
    summary = get_drug_event_summary("aspirin")
    if summary.get("success"):
        print(f"✓ Total events: {summary['total_events']}, Serious: {summary['serious_events']} ({summary['serious_rate']}%)")
    else:
        print(f"✗ Error: {summary.get('error', 'Unknown')[:80]}")
    
    print("\nModule test complete!")
