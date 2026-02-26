"""
FDA Drug Pipeline Tracker — Monitor FDA drug approvals, submissions, and pipeline status.

Tracks NDA/BLA submissions, PDUFA dates, accelerated approvals, breakthrough therapy
designations, and novel drug approvals using openFDA and FDA public datasets.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any


def get_recent_approvals(limit: int = 20, months_back: int = 6) -> dict[str, Any]:
    """Fetch recent FDA drug approvals from openFDA."""
    end = datetime.now()
    start = end - timedelta(days=months_back * 30)
    date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
    url = (
        f"https://api.fda.gov/drug/drugsfda.json?"
        f"search=submissions.submission_status_date:{date_range}"
        f"&limit={limit}"
        f"&sort=submissions.submission_status_date:desc"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = []
        for r in data.get("results", []):
            products = r.get("products", [{}])
            brand = products[0].get("brand_name", "N/A") if products else "N/A"
            active = products[0].get("active_ingredients", []) if products else []
            ingredients = ", ".join(i.get("name", "") for i in active[:3])
            subs = r.get("submissions", [])
            latest = subs[0] if subs else {}
            results.append({
                "sponsor": r.get("sponsor_name", "N/A"),
                "brand_name": brand,
                "active_ingredients": ingredients,
                "application_number": r.get("application_number", "N/A"),
                "submission_type": latest.get("submission_type", "N/A"),
                "submission_status": latest.get("submission_status", "N/A"),
                "submission_date": latest.get("submission_status_date", "N/A"),
            })
        return {"approvals": results, "total": data.get("meta", {}).get("results", {}).get("total", 0)}
    except Exception as e:
        return {"error": str(e)}


def search_drug_pipeline(query: str, limit: int = 10) -> dict[str, Any]:
    """Search FDA drug database by sponsor, brand name, or ingredient."""
    encoded = urllib.parse.quote(query) if hasattr(urllib, 'parse') else query.replace(" ", "+")
    url = (
        f"https://api.fda.gov/drug/drugsfda.json?"
        f"search={encoded}&limit={limit}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = []
        for r in data.get("results", []):
            products = r.get("products", [{}])
            brand = products[0].get("brand_name", "N/A") if products else "N/A"
            subs = r.get("submissions", [])
            results.append({
                "sponsor": r.get("sponsor_name", "N/A"),
                "brand_name": brand,
                "application_number": r.get("application_number", "N/A"),
                "submissions_count": len(subs),
                "latest_status": subs[0].get("submission_status", "N/A") if subs else "N/A",
            })
        return {"results": results, "query": query}
    except Exception as e:
        return {"error": str(e)}


def get_novel_drug_approvals_summary(year: int = None) -> dict[str, Any]:
    """Get summary statistics of novel drug approvals for a given year."""
    if year is None:
        year = datetime.now().year
    date_range = f"[{year}0101+TO+{year}1231]"
    url = (
        f"https://api.fda.gov/drug/drugsfda.json?"
        f"search=submissions.submission_status_date:{date_range}+AND+"
        f"submissions.submission_type:ORIG&limit=100"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        sponsors = {}
        for r in data.get("results", []):
            s = r.get("sponsor_name", "Unknown")
            sponsors[s] = sponsors.get(s, 0) + 1
        top_sponsors = sorted(sponsors.items(), key=lambda x: -x[1])[:10]
        return {
            "year": year,
            "total_original_submissions": total,
            "top_sponsors": [{"sponsor": s, "count": c} for s, c in top_sponsors],
        }
    except Exception as e:
        return {"error": str(e)}
