#!/usr/bin/env python3
"""openfda_drugs — OpenFDA drug data (approvals, adverse events, recalls). Source: https://api.fda.gov/. Free, no auth. Rate limit: 240 req/min."""
import requests
import os
import json
import time
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
BASE = "https://api.fda.gov"

def get_drug_approvals(days=30, limit=50, **kwargs):
    """Fetch recent drug approvals/submissions from FDA."""
    cache_file = os.path.join(CACHE_DIR, "openfda_approvals.json")
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 3600 * 6:
        with open(cache_file) as f:
            return json.load(f)
    try:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        today = datetime.now().strftime("%Y%m%d")
        url = f"{BASE}/drug/drugsfda.json"
        params = {"search": f"submissions.submission_status_date:[{cutoff}+TO+{today}]",
                  "limit": limit}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        approvals = []
        for r in results:
            products = r.get("products", [{}])
            submissions = r.get("submissions", [{}])
            approvals.append({
                "application_number": r.get("application_number", ""),
                "sponsor": r.get("sponsor_name", ""),
                "brand_name": products[0].get("brand_name", "") if products else "",
                "generic_name": products[0].get("active_ingredients", [{}])[0].get("name", "") if products and products[0].get("active_ingredients") else "",
                "submission_type": submissions[0].get("submission_type", "") if submissions else "",
                "submission_status": submissions[0].get("submission_status", "") if submissions else "",
                "submission_date": submissions[0].get("submission_status_date", "") if submissions else ""
            })
        result = {"source": "OpenFDA", "type": "drug_approvals", "days": days,
                  "count": len(approvals), "approvals": approvals,
                  "meta": data.get("meta", {}), "fetch_time": datetime.now().isoformat()}
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)
        return result
    except Exception as e:
        return {"error": str(e), "source": "openfda"}

def get_adverse_events(drug_name, limit=25, **kwargs):
    """Fetch adverse event reports for a specific drug."""
    try:
        url = f"{BASE}/drug/event.json"
        params = {"search": f'patient.drug.medicinalproduct:"{drug_name}"',
                  "limit": limit}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        events = []
        for r in results:
            reactions = [rx.get("reactionmeddrapt", "") for rx in r.get("patient", {}).get("reaction", [])]
            events.append({
                "receive_date": r.get("receivedate", ""),
                "serious": r.get("serious", ""),
                "reactions": reactions[:5],
                "outcome": r.get("patient", {}).get("patientonsetage", "")
            })
        return {"drug": drug_name, "count": len(events), "events": events,
                "meta": data.get("meta", {}), "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "drug": drug_name}

def get_recalls(days=30, limit=25, **kwargs):
    """Fetch recent drug recalls."""
    try:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        today = datetime.now().strftime("%Y%m%d")
        url = f"{BASE}/drug/enforcement.json"
        params = {"search": f"report_date:[{cutoff}+TO+{today}]", "limit": limit}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        recalls = []
        for r in results:
            recalls.append({
                "recall_number": r.get("recall_number", ""),
                "reason": r.get("reason_for_recall", ""),
                "status": r.get("status", ""),
                "classification": r.get("classification", ""),
                "product": r.get("product_description", "")[:200],
                "firm": r.get("recalling_firm", ""),
                "date": r.get("report_date", "")
            })
        return {"source": "OpenFDA", "type": "recalls", "days": days,
                "count": len(recalls), "recalls": recalls,
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}

def get_data(ticker=None, **kwargs):
    return get_drug_approvals(**kwargs)

if __name__ == "__main__":
    print("=== Drug Approvals (30d) ===")
    approvals = get_drug_approvals(30)
    print(f"Found: {approvals.get('count', 0)} approvals")
    for a in approvals.get('approvals', [])[:3]:
        print(f"  {a['brand_name']} ({a['sponsor']}) - {a['submission_status']}")
    print("\n=== Adverse Events: Ozempic ===")
    ae = get_adverse_events("OZEMPIC")
    print(f"Found: {ae.get('count', 0)} events")
    print("\n=== Recalls (30d) ===")
    recalls = get_recalls(30)
    print(f"Found: {recalls.get('count', 0)} recalls")
