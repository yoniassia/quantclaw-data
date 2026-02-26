"""
Clinical Trial Monitor — Track clinical trials from ClinicalTrials.gov v2 API.

Search active trials by condition, sponsor, drug, phase. Monitor enrollment,
completion dates, and trial status changes for pharmaceutical investment signals.
"""

import json
import urllib.request
import urllib.parse
from typing import Any


BASE_URL = "https://clinicaltrials.gov/api/v2"


def search_trials(query: str, status: str = "RECRUITING", limit: int = 15) -> dict[str, Any]:
    """Search clinical trials by keyword, condition, or intervention."""
    params = urllib.parse.urlencode({
        "query.term": query,
        "filter.overallStatus": status,
        "pageSize": min(limit, 50),
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,EnrollmentCount,LeadSponsorName,StartDate,CompletionDate,Condition,InterventionName",
        "sort": "LastUpdatePostDate:desc",
    })
    url = f"{BASE_URL}/studies?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        trials = []
        for study in data.get("studies", []):
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            sponsor = proto.get("sponsorCollaboratorsModule", {})
            cond = proto.get("conditionsModule", {})
            interv = proto.get("armsInterventionsModule", {})
            interventions = [i.get("name", "") for i in interv.get("interventions", [])[:3]]
            trials.append({
                "nct_id": ident.get("nctId", "N/A"),
                "title": ident.get("briefTitle", "N/A"),
                "status": status_mod.get("overallStatus", "N/A"),
                "phase": ", ".join(design.get("phases", ["N/A"])),
                "enrollment": design.get("enrollmentInfo", {}).get("count", "N/A"),
                "sponsor": sponsor.get("leadSponsor", {}).get("name", "N/A"),
                "conditions": cond.get("conditions", [])[:3],
                "interventions": interventions,
                "start_date": status_mod.get("startDateStruct", {}).get("date", "N/A"),
                "completion_date": status_mod.get("completionDateStruct", {}).get("date", "N/A"),
            })
        return {"trials": trials, "total": data.get("totalCount", 0), "query": query}
    except Exception as e:
        return {"error": str(e)}


def get_trial_details(nct_id: str) -> dict[str, Any]:
    """Get full details for a specific clinical trial by NCT ID."""
    url = f"{BASE_URL}/studies/{nct_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        proto = data.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        desc = proto.get("descriptionModule", {})
        elig = proto.get("eligibilityModule", {})
        return {
            "nct_id": ident.get("nctId"),
            "title": ident.get("officialTitle", ident.get("briefTitle")),
            "status": status_mod.get("overallStatus"),
            "brief_summary": desc.get("briefSummary", "N/A"),
            "eligibility_criteria": elig.get("eligibilityCriteria", "N/A")[:500],
            "sex": elig.get("sex", "N/A"),
            "min_age": elig.get("minimumAge", "N/A"),
            "max_age": elig.get("maximumAge", "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_sponsor_pipeline(sponsor: str, limit: int = 20) -> dict[str, Any]:
    """Get all active trials for a specific pharmaceutical company/sponsor."""
    return search_trials(query=sponsor, status="RECRUITING", limit=limit)


def get_phase3_completions(condition: str = "", limit: int = 20) -> dict[str, Any]:
    """Find Phase 3 trials nearing completion — potential catalyst events."""
    params = urllib.parse.urlencode({
        "query.term": condition,
        "filter.overallStatus": "ACTIVE_NOT_RECRUITING",
        "filter.phase": "PHASE3",
        "pageSize": min(limit, 50),
        "fields": "NCTId,BriefTitle,LeadSponsorName,CompletionDate,Condition,InterventionName",
        "sort": "CompletionDate:asc",
    })
    url = f"{BASE_URL}/studies?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        trials = []
        for study in data.get("studies", []):
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            sponsor = proto.get("sponsorCollaboratorsModule", {})
            trials.append({
                "nct_id": ident.get("nctId"),
                "title": ident.get("briefTitle"),
                "sponsor": sponsor.get("leadSponsor", {}).get("name"),
                "completion_date": status_mod.get("completionDateStruct", {}).get("date"),
            })
        return {"phase3_completions": trials, "total": data.get("totalCount", 0)}
    except Exception as e:
        return {"error": str(e)}
