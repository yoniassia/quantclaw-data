"""
Biopharm Pipeline — Drug development pipeline and FDA catalyst tracking.

Tracks biotech drug pipelines, clinical trials, FDA catalyst dates (PDUFA dates),
trial results, and drug development phases. Primary source: ClinicalTrials.gov API v2.

Source: https://clinicaltrials.gov/api/v2/studies
Category: Healthcare & Biotech
Free tier: Unlimited (no API key required)
Update frequency: Daily
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


API_BASE = "https://clinicaltrials.gov/api/v2"


def get_clinical_trials(
    condition: Optional[str] = None,
    sponsor: Optional[str] = None,
    phase: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
) -> dict[str, Any]:
    """
    Search clinical trials from ClinicalTrials.gov database.
    
    Args:
        condition: Disease/condition (e.g., 'cancer', 'diabetes', 'alzheimer')
        sponsor: Company/sponsor name (e.g., 'Moderna', 'Pfizer')
        phase: Trial phase ('PHASE1', 'PHASE2', 'PHASE3', 'PHASE4', or 'EARLY_PHASE1')
        status: Trial status ('RECRUITING', 'ACTIVE_NOT_RECRUITING', 'COMPLETED', 'TERMINATED')
        limit: Max number of results (default 20, max 1000)
        
    Returns:
        dict with trials list and metadata
        
    Example:
        >>> trials = get_clinical_trials(sponsor='Moderna', phase='PHASE3')
        >>> for trial in trials.get('trials', []):
        ...     print(trial['title'], trial['phase'])
    """
    endpoint = f"{API_BASE}/studies"
    
    # Build query filters
    query_parts = []
    if condition:
        query_parts.append(f"AREA[ConditionSearch]{condition}")
    if sponsor:
        query_parts.append(f"AREA[SponsorSearch]{sponsor}")
    if phase:
        query_parts.append(f"AREA[Phase]{phase}")
    if status:
        query_parts.append(f"AREA[OverallStatus]{status}")
    
    query = " AND ".join(query_parts) if query_parts else None
    
    params = {
        "format": "json",
        "pageSize": min(limit, 1000)
    }
    
    if query:
        params["query.cond"] = query
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            trials = []
            studies = data.get("studies", [])
            
            for study in studies:
                protocol = study.get("protocolSection", {})
                ident = protocol.get("identificationModule", {})
                status_mod = protocol.get("statusModule", {})
                design = protocol.get("designModule", {})
                sponsor_mod = protocol.get("sponsorCollaboratorsModule", {})
                conditions_mod = protocol.get("conditionsModule", {})
                
                phases = design.get("phases", [])
                phase_str = phases[0] if phases else "UNKNOWN"
                
                trial = {
                    "nct_id": ident.get("nctId"),
                    "title": ident.get("briefTitle"),
                    "official_title": ident.get("officialTitle"),
                    "phase": phase_str,
                    "status": status_mod.get("overallStatus"),
                    "start_date": status_mod.get("startDateStruct", {}).get("date"),
                    "completion_date": status_mod.get("completionDateStruct", {}).get("date"),
                    "primary_completion_date": status_mod.get("primaryCompletionDateStruct", {}).get("date"),
                    "sponsor": sponsor_mod.get("leadSponsor", {}).get("name"),
                    "conditions": conditions_mod.get("conditions", []),
                    "enrollment": design.get("enrollmentInfo", {}).get("count"),
                    "study_type": design.get("studyType"),
                    "last_update": status_mod.get("lastUpdatePostDateStruct", {}).get("date")
                }
                trials.append(trial)
            
            return {
                "total": data.get("totalCount", 0),
                "count": len(trials),
                "trials": trials,
                "filters": {
                    "condition": condition,
                    "sponsor": sponsor,
                    "phase": phase,
                    "status": status
                },
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {"error": str(e), "endpoint": url}


def search_pipeline(
    company: Optional[str] = None,
    phase: Optional[str] = None,
    disease: Optional[str] = None,
    limit: int = 50
) -> dict[str, Any]:
    """
    Search drug pipeline by company, phase, and/or disease.
    
    Args:
        company: Company/sponsor name (e.g., 'Pfizer', 'Moderna', 'BioNTech')
        phase: Development phase ('PHASE1', 'PHASE2', 'PHASE3', 'PHASE4')
        disease: Disease/condition area (e.g., 'cancer', 'covid', 'diabetes')
        limit: Max results (default 50)
        
    Returns:
        dict with pipeline data grouped by phase and drug
        
    Example:
        >>> pipeline = search_pipeline(company='Pfizer', disease='cancer')
        >>> print(f"Found {len(pipeline.get('drugs', []))} drugs in pipeline")
    """
    # Search active and recruiting trials
    trials_data = get_clinical_trials(
        condition=disease,
        sponsor=company,
        phase=phase,
        status="RECRUITING",
        limit=limit
    )
    
    if "error" in trials_data:
        return trials_data
    
    # Group by drug/intervention
    drugs = {}
    for trial in trials_data.get("trials", []):
        title = trial.get("title", "")
        nct_id = trial.get("nct_id")
        
        # Create a simplified drug entry
        drug_key = f"{trial.get('sponsor', 'Unknown')}_{title[:50]}"
        
        if drug_key not in drugs:
            drugs[drug_key] = {
                "title": title,
                "sponsor": trial.get("sponsor"),
                "phase": trial.get("phase"),
                "conditions": trial.get("conditions", []),
                "status": trial.get("status"),
                "expected_completion": trial.get("primary_completion_date"),
                "trials": []
            }
        
        drugs[drug_key]["trials"].append(nct_id)
    
    return {
        "total_drugs": len(drugs),
        "drugs": list(drugs.values()),
        "filters": {
            "company": company,
            "phase": phase,
            "disease": disease
        },
        "timestamp": datetime.utcnow().isoformat()
    }


def get_fda_calendar(days_ahead: int = 30) -> dict[str, Any]:
    """
    Get upcoming FDA catalyst dates (PDUFA dates, trial completion dates).
    
    Note: ClinicalTrials.gov doesn't directly track PDUFA dates, so this
    returns upcoming trial completion dates as proxy for catalyst events.
    
    Args:
        days_ahead: Number of days to look ahead (default 30)
        
    Returns:
        dict with upcoming catalyst dates
        
    Example:
        >>> calendar = get_fda_calendar(days_ahead=60)
        >>> for event in calendar.get('events', []):
        ...     print(event['date'], event['sponsor'], event['title'])
    """
    # Get trials completing soon
    trials_data = get_clinical_trials(
        status="ACTIVE_NOT_RECRUITING",
        limit=100
    )
    
    if "error" in trials_data:
        return trials_data
    
    cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
    
    events = []
    for trial in trials_data.get("trials", []):
        completion_str = trial.get("primary_completion_date") or trial.get("completion_date")
        
        if completion_str:
            try:
                # Parse date (format: YYYY-MM-DD or YYYY-MM)
                if len(completion_str) == 7:  # YYYY-MM
                    completion_str += "-01"
                
                completion_date = datetime.strptime(completion_str, "%Y-%m-%d")
                
                if datetime.utcnow() <= completion_date <= cutoff_date:
                    events.append({
                        "date": completion_str,
                        "nct_id": trial.get("nct_id"),
                        "title": trial.get("title"),
                        "sponsor": trial.get("sponsor"),
                        "phase": trial.get("phase"),
                        "conditions": trial.get("conditions", []),
                        "event_type": "trial_completion",
                        "days_until": (completion_date - datetime.utcnow()).days
                    })
            except:
                continue
    
    # Sort by date
    events.sort(key=lambda x: x["date"])
    
    return {
        "total_events": len(events),
        "events": events,
        "days_ahead": days_ahead,
        "start_date": datetime.utcnow().isoformat()[:10],
        "end_date": cutoff_date.isoformat()[:10],
        "note": "Shows trial completion dates (proxy for FDA catalyst events)",
        "timestamp": datetime.utcnow().isoformat()
    }


def get_drug_status(drug_name: str) -> dict[str, Any]:
    """
    Get current development status of a specific drug.
    
    Args:
        drug_name: Drug or intervention name
        
    Returns:
        dict with drug status across all trials
        
    Example:
        >>> status = get_drug_status('pembrolizumab')
        >>> print(status.get('highest_phase'), status.get('total_trials'))
    """
    # Search by condition/intervention name
    trials_data = get_clinical_trials(
        condition=drug_name,
        limit=100
    )
    
    if "error" in trials_data:
        return trials_data
    
    trials = trials_data.get("trials", [])
    
    if not trials:
        return {
            "drug_name": drug_name,
            "found": False,
            "message": "No trials found for this drug name"
        }
    
    # Analyze phases
    phase_counts = {}
    sponsors = set()
    conditions = set()
    statuses = set()
    
    for trial in trials:
        phase = trial.get("phase", "UNKNOWN")
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        if trial.get("sponsor"):
            sponsors.add(trial.get("sponsor"))
        
        for cond in trial.get("conditions", []):
            conditions.add(cond)
        
        if trial.get("status"):
            statuses.add(trial.get("status"))
    
    # Determine highest phase
    phase_order = ["PHASE4", "PHASE3", "PHASE2", "PHASE1", "EARLY_PHASE1"]
    highest_phase = "UNKNOWN"
    for phase in phase_order:
        if phase in phase_counts:
            highest_phase = phase
            break
    
    return {
        "drug_name": drug_name,
        "found": True,
        "total_trials": len(trials),
        "highest_phase": highest_phase,
        "phase_breakdown": phase_counts,
        "sponsors": list(sponsors),
        "conditions": list(conditions)[:20],  # Limit for readability
        "statuses": list(statuses),
        "recent_trials": trials[:5],  # Show 5 most recent
        "timestamp": datetime.utcnow().isoformat()
    }


def get_upcoming_catalysts(ticker: Optional[str] = None, days_ahead: int = 60) -> dict[str, Any]:
    """
    Get upcoming catalysts for biotech stocks (trial results, FDA decisions).
    
    Note: ClinicalTrials.gov doesn't track stock tickers directly.
    If ticker provided, this attempts to match company name.
    
    Args:
        ticker: Stock ticker (e.g., 'MRNA', 'PFE', 'BNTX')
        days_ahead: Days to look ahead (default 60)
        
    Returns:
        dict with upcoming catalyst events
        
    Example:
        >>> catalysts = get_upcoming_catalysts(ticker='MRNA')
        >>> print(f"Found {len(catalysts.get('events', []))} upcoming events")
    """
    # Ticker to company name mapping (common biotech stocks)
    ticker_map = {
        "MRNA": "Moderna",
        "PFE": "Pfizer",
        "BNTX": "BioNTech",
        "JNJ": "Johnson",
        "GILD": "Gilead",
        "REGN": "Regeneron",
        "VRTX": "Vertex",
        "BIIB": "Biogen",
        "AMGN": "Amgen",
        "BMY": "Bristol-Myers"
    }
    
    company = None
    if ticker:
        company = ticker_map.get(ticker.upper(), ticker)
    
    # Get FDA calendar
    calendar = get_fda_calendar(days_ahead=days_ahead)
    
    if "error" in calendar:
        return calendar
    
    # Filter by company if specified
    events = calendar.get("events", [])
    
    if company:
        filtered_events = [
            e for e in events
            if company.lower() in e.get("sponsor", "").lower()
        ]
    else:
        filtered_events = events
    
    return {
        "ticker": ticker,
        "company": company,
        "total_catalysts": len(filtered_events),
        "events": filtered_events,
        "days_ahead": days_ahead,
        "note": "Based on trial completion dates from ClinicalTrials.gov",
        "timestamp": datetime.utcnow().isoformat()
    }


# Demo function
def demo():
    """Run demo queries to test the module."""
    print("=== Biopharm Pipeline Module Demo ===\n")
    
    # Test 1: Search Moderna trials
    print("1. Moderna COVID trials:")
    moderna = get_clinical_trials(sponsor="Moderna", condition="covid", limit=3)
    print(f"   Found {moderna.get('total', 0)} total trials")
    for trial in moderna.get('trials', [])[:2]:
        print(f"   - {trial.get('title')} [{trial.get('phase')}]")
    
    print("\n2. Cancer drug pipeline:")
    cancer = search_pipeline(disease="cancer", phase="PHASE3", limit=5)
    print(f"   Found {cancer.get('total_drugs', 0)} drugs in Phase 3")
    
    print("\n3. Upcoming catalysts (30 days):")
    catalysts = get_fda_calendar(days_ahead=30)
    print(f"   Found {catalysts.get('total_events', 0)} upcoming events")
    
    print("\nDemo complete!")


if __name__ == "__main__":
    demo()
