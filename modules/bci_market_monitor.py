"""
Brain-Computer Interface (BCI) Market Monitor — Track BCI companies, clinical
trials, regulatory milestones, and market adoption using public data.
Roadmap #396.
"""

import datetime
from typing import Dict, List, Optional

BCI_COMPANIES = [
    {"name": "Neuralink", "founder": "Elon Musk", "type": "invasive", "status": "human_trials", "patients": 3, "funding_mn": 680, "fda_status": "IDE_approved", "public": False},
    {"name": "Synchron", "founder": "Tom Oxley", "type": "endovascular", "status": "human_trials", "patients": 10, "funding_mn": 220, "fda_status": "IDE_approved", "public": False},
    {"name": "Blackrock Neurotech", "founder": "Florian Solzbacher", "type": "invasive", "status": "research", "patients": 40, "funding_mn": 80, "fda_status": "research_only", "public": False},
    {"name": "Paradromics", "founder": "Matt Angle", "type": "invasive", "status": "preclinical", "patients": 0, "funding_mn": 85, "fda_status": "pre_submission", "public": False},
    {"name": "Precision Neuroscience", "founder": "Ben Rapoport", "type": "minimally_invasive", "status": "human_trials", "patients": 5, "funding_mn": 100, "fda_status": "IDE_approved", "public": False},
    {"name": "Emotiv", "founder": "Tan Le", "type": "non_invasive", "status": "commercial", "patients": None, "funding_mn": 50, "fda_status": "consumer_device", "public": False},
    {"name": "OpenBCI", "founder": "Conor Russomanno", "type": "non_invasive", "status": "commercial", "patients": None, "funding_mn": 10, "fda_status": "research_device", "public": False},
    {"name": "Kernel", "founder": "Bryan Johnson", "type": "non_invasive", "status": "commercial", "patients": None, "funding_mn": 110, "fda_status": "consumer_device", "public": False},
]

BCI_APPLICATIONS = [
    {"application": "Paralysis Communication", "readiness": "human_trials", "companies": ["Neuralink", "Synchron", "Blackrock Neurotech"]},
    {"application": "Motor Control Restoration", "readiness": "research", "companies": ["Neuralink", "Blackrock Neurotech"]},
    {"application": "Mental Health Treatment", "readiness": "preclinical", "companies": ["Kernel"]},
    {"application": "Consumer Neurofeedback", "readiness": "commercial", "companies": ["Emotiv", "OpenBCI", "Kernel"]},
    {"application": "Gaming/Entertainment", "readiness": "early_commercial", "companies": ["Emotiv", "OpenBCI"]},
    {"application": "Military/Defense", "readiness": "research", "companies": ["Blackrock Neurotech", "Paradromics"]},
]


def get_bci_landscape() -> Dict:
    """Get overview of the BCI industry — companies, funding, applications."""
    total_funding = sum(c["funding_mn"] for c in BCI_COMPANIES)
    by_type = {}
    for c in BCI_COMPANIES:
        by_type.setdefault(c["type"], []).append(c["name"])

    total_patients = sum(c["patients"] or 0 for c in BCI_COMPANIES)

    return {
        "total_companies": len(BCI_COMPANIES),
        "total_funding_mn_usd": total_funding,
        "total_human_patients": total_patients,
        "by_type": by_type,
        "applications": BCI_APPLICATIONS,
        "companies": BCI_COMPANIES,
    }


def get_company_detail(name: str) -> Optional[Dict]:
    """Get detailed info on a specific BCI company."""
    for c in BCI_COMPANIES:
        if c["name"].lower() == name.lower():
            apps = [a for a in BCI_APPLICATIONS if c["name"] in a["companies"]]
            return {**c, "applications": apps}
    return None


def get_clinical_progress() -> Dict:
    """Track clinical trial progress across all BCI companies."""
    in_humans = [c for c in BCI_COMPANIES if c["patients"] and c["patients"] > 0]
    fda_approved = [c for c in BCI_COMPANIES if c["fda_status"] == "IDE_approved"]
    return {
        "companies_in_human_trials": len(in_humans),
        "total_human_patients_ever": sum(c["patients"] or 0 for c in BCI_COMPANIES),
        "fda_ide_approved": [c["name"] for c in fda_approved],
        "trial_details": [{"name": c["name"], "patients": c["patients"], "type": c["type"], "fda": c["fda_status"]} for c in in_humans],
    }
