"""
ClinicalTrials.gov API v2 — Clinical Trial Data for Biotech/Pharma Analysis

Data Source: U.S. National Library of Medicine (ClinicalTrials.gov)
API: https://clinicaltrials.gov/api/v2/
Update: Daily
Free: Yes — No API key required (rate limit ~3 req/sec)
Studies: 574,000+ globally registered trials

Provides:
- Search trials by condition, intervention, sponsor, status
- Individual trial details (design, outcomes, eligibility)
- Pipeline analysis for pharma/biotech companies
- Trial phase distribution and success rates
- Enrollment statistics and geographic distribution

Investment Use Cases:
- Track drug pipeline progress for biotech stocks
- Monitor competitor trials in therapeutic areas
- Detect phase transitions (Phase 2→3 = potential catalyst)
- Assess trial enrollment pace as leading indicator
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

BASE_URL = "https://clinicaltrials.gov/api/v2"

# Useful status values
STATUSES = [
    "RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED",
    "NOT_YET_RECRUITING", "TERMINATED", "WITHDRAWN",
    "SUSPENDED", "ENROLLING_BY_INVITATION", "UNKNOWN"
]

PHASES = ["EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4", "NA"]


def _request(endpoint: str, params: Optional[Dict] = None, timeout: int = 15, add_format: bool = True) -> Dict:
    """Make a request to the ClinicalTrials.gov API v2."""
    url = f"{BASE_URL}/{endpoint}"
    if params is None:
        params = {}
    if add_format:
        params["format"] = "json"
    
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _parse_study(study: Dict) -> Dict:
    """Extract key fields from a raw study object into a flat dict."""
    proto = study.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status = proto.get("statusModule", {})
    design = proto.get("designModule", {})
    desc = proto.get("descriptionModule", {})
    sponsor = proto.get("sponsorCollaboratorsModule", {})
    conditions = proto.get("conditionsModule", {})
    arms = proto.get("armsInterventionsModule", {})
    eligibility = proto.get("eligibilityModule", {})
    
    lead = sponsor.get("leadSponsor", {})
    phases = design.get("phases", [])
    interventions = arms.get("interventions", [])
    
    # Enrollment
    enroll_info = design.get("enrollmentInfo", {})
    
    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "official_title": ident.get("officialTitle"),
        "status": status.get("overallStatus"),
        "start_date": _extract_date(status.get("startDateStruct")),
        "completion_date": _extract_date(status.get("completionDateStruct")),
        "primary_completion_date": _extract_date(status.get("primaryCompletionDateStruct")),
        "last_update": status.get("lastUpdateSubmitDate"),
        "study_type": design.get("studyType"),
        "phases": phases,
        "phase_str": ", ".join(phases) if phases else "N/A",
        "enrollment": enroll_info.get("count"),
        "enrollment_type": enroll_info.get("type"),
        "conditions": conditions.get("conditions", []),
        "interventions": [
            {"name": i.get("name"), "type": i.get("type")}
            for i in interventions
        ],
        "sponsor": lead.get("name"),
        "sponsor_class": lead.get("class"),
        "brief_summary": desc.get("briefSummary", "")[:500],
        "sex": eligibility.get("sex"),
        "min_age": eligibility.get("minimumAge"),
        "max_age": eligibility.get("maximumAge"),
        "org": ident.get("organization", {}).get("fullName"),
    }


def _extract_date(date_struct: Optional[Dict]) -> Optional[str]:
    """Extract date string from a date struct."""
    if not date_struct:
        return None
    return date_struct.get("date")


def search_trials(
    condition: Optional[str] = None,
    intervention: Optional[str] = None,
    sponsor: Optional[str] = None,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = 10,
    sort: str = "LastUpdatePostDate:desc"
) -> Dict:
    """
    Search clinical trials with flexible filters.
    
    Args:
        condition: Disease/condition (e.g., 'cancer', 'diabetes', 'Alzheimer')
        intervention: Drug/treatment name (e.g., 'pembrolizumab', 'CAR-T')
        sponsor: Sponsor organization (e.g., 'Pfizer', 'Novartis')
        status: Trial status filter (e.g., 'RECRUITING', 'COMPLETED')
        phase: Phase filter (e.g., 'PHASE3')
        query: Free-text search across all fields
        page_size: Results per page (max 1000)
        sort: Sort field and direction
    
    Returns:
        dict with 'studies' list (parsed) and 'total_count'
    """
    params = {"pageSize": min(page_size, 1000), "sort": sort, "countTotal": "true"}
    
    if condition:
        params["query.cond"] = condition
    if intervention:
        params["query.intr"] = intervention
    if sponsor:
        params["query.spons"] = sponsor
    if status:
        # Can be comma-separated for multiple
        params["filter.overallStatus"] = status
    if phase:
        params["filter.advanced"] = f"AREA[Phase]{phase}"
    if query:
        params["query.term"] = query
    
    data = _request("studies", params)
    studies = [_parse_study(s) for s in data.get("studies", [])]
    
    return {
        "total_count": data.get("totalCount", len(studies)),
        "studies": studies,
        "next_page_token": data.get("nextPageToken"),
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_trial(nct_id: str) -> Dict:
    """
    Get full details for a specific trial by NCT ID.
    
    Args:
        nct_id: ClinicalTrials.gov identifier (e.g., 'NCT04576871')
    
    Returns:
        Parsed trial dict with all key fields
    """
    data = _request(f"studies/{nct_id}")
    parsed = _parse_study(data)
    
    # Add extra detail fields from the full record
    proto = data.get("protocolSection", {})
    outcomes = proto.get("outcomesModule", {})
    contacts = proto.get("contactsLocationsModule", {})
    
    parsed["primary_outcomes"] = [
        {"measure": o.get("measure"), "timeFrame": o.get("timeFrame")}
        for o in outcomes.get("primaryOutcomes", [])
    ]
    parsed["secondary_outcomes"] = [
        {"measure": o.get("measure"), "timeFrame": o.get("timeFrame")}
        for o in outcomes.get("secondaryOutcomes", [])
    ]
    
    locations = contacts.get("locations", [])
    parsed["location_count"] = len(locations)
    parsed["countries"] = list(set(
        loc.get("country", "") for loc in locations if loc.get("country")
    ))
    
    # Results section if available
    results = data.get("resultsSection")
    parsed["has_results"] = results is not None
    
    return parsed


def get_sponsor_pipeline(
    sponsor: str,
    active_only: bool = True,
    page_size: int = 50
) -> Dict:
    """
    Get all trials for a pharmaceutical sponsor — pipeline analysis.
    
    Args:
        sponsor: Company name (e.g., 'Pfizer', 'Moderna', 'Eli Lilly')
        active_only: If True, only recruiting/active trials
        page_size: Max results
    
    Returns:
        dict with pipeline summary and trial list
    """
    status_filter = None
    if active_only:
        status_filter = "RECRUITING,ACTIVE_NOT_RECRUITING,NOT_YET_RECRUITING,ENROLLING_BY_INVITATION"
    
    result = search_trials(sponsor=sponsor, status=status_filter, page_size=page_size)
    
    # Build phase distribution
    phase_dist = {}
    condition_set = set()
    for trial in result["studies"]:
        for p in trial.get("phases", ["N/A"]):
            phase_dist[p] = phase_dist.get(p, 0) + 1
        for c in trial.get("conditions", []):
            condition_set.add(c)
    
    return {
        "sponsor": sponsor,
        "total_trials": result["total_count"],
        "fetched_count": len(result["studies"]),
        "active_only": active_only,
        "phase_distribution": phase_dist,
        "therapeutic_areas": sorted(condition_set)[:30],
        "trials": result["studies"],
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_condition_landscape(
    condition: str,
    page_size: int = 50
) -> Dict:
    """
    Analyze the trial landscape for a disease/condition.
    
    Args:
        condition: Disease name (e.g., 'breast cancer', 'NASH', 'obesity')
        page_size: Max results per status query
    
    Returns:
        dict with status breakdown, top sponsors, phase distribution
    """
    # Get recruiting trials
    recruiting = search_trials(condition=condition, status="RECRUITING", page_size=page_size)
    # Get completed trials (recent)
    completed = search_trials(condition=condition, status="COMPLETED", page_size=page_size)
    
    all_trials = recruiting["studies"] + completed["studies"]
    
    # Analyze sponsors
    sponsor_counts = {}
    phase_counts = {}
    intervention_types = {}
    
    for trial in all_trials:
        sp = trial.get("sponsor", "Unknown")
        sponsor_counts[sp] = sponsor_counts.get(sp, 0) + 1
        
        for p in trial.get("phases", ["N/A"]):
            phase_counts[p] = phase_counts.get(p, 0) + 1
        
        for intr in trial.get("interventions", []):
            itype = intr.get("type", "OTHER")
            intervention_types[itype] = intervention_types.get(itype, 0) + 1
    
    top_sponsors = sorted(sponsor_counts.items(), key=lambda x: -x[1])[:15]
    
    return {
        "condition": condition,
        "recruiting_count": recruiting["total_count"],
        "completed_count": completed["total_count"],
        "phase_distribution": phase_counts,
        "intervention_types": intervention_types,
        "top_sponsors": [{"name": s, "count": c} for s, c in top_sponsors],
        "sample_trials": all_trials[:10],
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_recent_updates(
    condition: Optional[str] = None,
    days: int = 7,
    page_size: int = 20
) -> Dict:
    """
    Get recently updated trials — detect pipeline catalysts.
    
    Args:
        condition: Optional condition filter
        days: Look back window in days
        page_size: Max results
    
    Returns:
        dict with recently updated trials sorted by update date
    """
    params = {
        "pageSize": min(page_size, 100),
        "sort": "LastUpdatePostDate:desc",
        "countTotal": "true"
    }
    if condition:
        params["query.cond"] = condition
    
    data = _request("studies", params)
    studies = [_parse_study(s) for s in data.get("studies", [])]
    
    return {
        "condition_filter": condition,
        "total_available": data.get("totalCount", 0),
        "fetched": len(studies),
        "studies": studies,
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_trial_stats() -> Dict:
    """
    Get overall ClinicalTrials.gov database statistics.
    
    Returns:
        dict with total studies count, size info
    """
    data = _request("stats/size", add_format=False)
    return {
        "total_studies": data.get("totalStudies"),
        "average_size_bytes": data.get("averageSizeBytes"),
        "largest_studies": data.get("largestStudies", [])[:5],
        "fetched_at": datetime.utcnow().isoformat()
    }


def search_by_intervention(
    drug_name: str,
    status: Optional[str] = None,
    page_size: int = 20
) -> Dict:
    """
    Search trials by drug/intervention name — track a specific drug's progress.
    
    Args:
        drug_name: Drug or intervention name (e.g., 'semaglutide', 'pembrolizumab')
        status: Optional status filter
        page_size: Max results
    
    Returns:
        dict with matching trials and summary
    """
    result = search_trials(intervention=drug_name, status=status, page_size=page_size)
    
    # Summarize phases
    phase_summary = {}
    status_summary = {}
    for trial in result["studies"]:
        for p in trial.get("phases", ["N/A"]):
            phase_summary[p] = phase_summary.get(p, 0) + 1
        st = trial.get("status", "UNKNOWN")
        status_summary[st] = status_summary.get(st, 0) + 1
    
    return {
        "drug": drug_name,
        "total_trials": result["total_count"],
        "phase_summary": phase_summary,
        "status_summary": status_summary,
        "trials": result["studies"],
        "fetched_at": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "clinicaltrialsgov_api",
        "status": "active",
        "source": "https://clinicaltrials.gov/api/v2/",
        "functions": [
            "search_trials", "get_trial", "get_sponsor_pipeline",
            "get_condition_landscape", "get_recent_updates",
            "get_trial_stats", "search_by_intervention"
        ]
    }, indent=2))
