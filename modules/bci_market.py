"""
Brain-Computer Interface (BCI) Market Monitor — Track BCI development, clinical trials,
key companies, and regulatory milestones.

Monitors Neuralink, Synchron, Blackrock Neurotech, Paradromics, and research institutions.
Uses free public data from ClinicalTrials.gov, FDA databases, and company disclosures.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


BCI_COMPANIES = {
    "Neuralink": {
        "approach": "Invasive (implanted electrodes)",
        "status": "Human Trials (PRIME Study)",
        "electrodes": 1024,
        "funding_m": 680,
        "founded": 2016,
        "ticker": None,
        "fda_status": "IDE Approved (2023)",
        "patients": 3,
        "milestone": "First human implant Jan 2024 (Noland Arbaugh)",
    },
    "Synchron": {
        "approach": "Endovascular (Stentrode)",
        "status": "Human Trials (COMMAND)",
        "electrodes": 16,
        "funding_m": 220,
        "founded": 2016,
        "ticker": None,
        "fda_status": "IDE Approved (2022)",
        "patients": 10,
        "milestone": "No open brain surgery required — inserted via blood vessel",
    },
    "Blackrock Neurotech": {
        "approach": "Invasive (Utah Array)",
        "status": "Research / Clinical",
        "electrodes": 128,
        "funding_m": 50,
        "founded": 2008,
        "ticker": None,
        "fda_status": "Research Use",
        "patients": 40,
        "milestone": "Most implanted BCI (30+ patients with Utah Array)",
    },
    "Paradromics": {
        "approach": "Invasive (high-bandwidth)",
        "status": "Preclinical",
        "electrodes": 65536,
        "funding_m": 85,
        "founded": 2015,
        "ticker": None,
        "fda_status": "Breakthrough Device Designation",
        "patients": 0,
        "milestone": "65K electrode Connexus device — highest channel count",
    },
    "Precision Neuroscience": {
        "approach": "Minimally Invasive (Layer 7 Cortical Interface)",
        "status": "Human Trials",
        "electrodes": 4096,
        "funding_m": 100,
        "founded": 2021,
        "ticker": None,
        "fda_status": "IDE Approved",
        "patients": 5,
        "milestone": "Thin-film electrode — no penetrating the brain",
    },
    "Kernel": {
        "approach": "Non-invasive (fNIRS helmet)",
        "status": "Commercial (Research)",
        "electrodes": 0,
        "funding_m": 110,
        "founded": 2016,
        "ticker": None,
        "fda_status": "N/A (non-invasive)",
        "patients": 0,
        "milestone": "Kernel Flow — wearable brain imaging at $50K",
    },
    "Emotiv": {
        "approach": "Non-invasive (EEG headset)",
        "status": "Commercial",
        "electrodes": 0,
        "funding_m": 30,
        "founded": 2011,
        "ticker": None,
        "fda_status": "N/A (consumer)",
        "patients": 0,
        "milestone": "Consumer EEG for wellness, gaming, research",
    },
    "BrainGate": {
        "approach": "Invasive (Utah Array, research consortium)",
        "status": "Clinical Research",
        "electrodes": 192,
        "funding_m": 0,
        "founded": 2000,
        "ticker": None,
        "fda_status": "IDE (ongoing trials)",
        "patients": 15,
        "milestone": "Pioneered thought-to-text and cursor control",
    },
}

BCI_APPLICATIONS = {
    "Medical - Paralysis": "Restore communication and motor control for ALS/spinal cord injury",
    "Medical - Epilepsy": "Seizure detection and responsive neurostimulation",
    "Medical - Depression": "Deep brain stimulation for treatment-resistant depression",
    "Medical - Blindness": "Visual cortex stimulation for restored sight",
    "Consumer - Wellness": "Meditation, focus, sleep tracking via EEG",
    "Consumer - Gaming": "Thought-controlled gaming interfaces",
    "Military - Enhancement": "DARPA N3 program for enhanced cognition",
    "Research - Neuroscience": "Understanding brain function and neural coding",
}


def get_bci_companies(approach_filter: Optional[str] = None) -> List[Dict]:
    """
    Get tracked BCI companies with technical and funding details.

    Args:
        approach_filter: Optional filter ('Invasive', 'Non-invasive', 'Endovascular')

    Returns:
        List of BCI company dictionaries sorted by funding
    """
    results = []
    for name, info in BCI_COMPANIES.items():
        if approach_filter and approach_filter.lower() not in info["approach"].lower():
            continue
        results.append({"company": name, **info})
    results.sort(key=lambda x: x["funding_m"], reverse=True)
    return results


def get_bci_market_summary() -> Dict:
    """
    Calculate BCI market summary with funding totals, patient counts, and approach breakdown.

    Returns:
        Dict with market overview, funding, patient stats
    """
    total_funding = sum(c["funding_m"] for c in BCI_COMPANIES.values())
    total_patients = sum(c["patients"] for c in BCI_COMPANIES.values())
    by_approach = {}
    fda_approved = []

    for name, info in BCI_COMPANIES.items():
        approach = info["approach"].split("(")[0].strip()
        by_approach[approach] = by_approach.get(approach, 0) + 1
        if "Approved" in info["fda_status"] or "Breakthrough" in info["fda_status"]:
            fda_approved.append({"company": name, "fda_status": info["fda_status"]})

    return {
        "total_funding_m_usd": total_funding,
        "total_patients_implanted": total_patients,
        "companies_tracked": len(BCI_COMPANIES),
        "by_approach": by_approach,
        "fda_progress": fda_approved,
        "applications": list(BCI_APPLICATIONS.keys()),
        "max_electrodes": max(BCI_COMPANIES.items(), key=lambda x: x[1]["electrodes"])[0],
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_bci_applications() -> Dict[str, str]:
    """Get BCI application areas and descriptions."""
    return BCI_APPLICATIONS.copy()


def search_bci_trials(max_results: int = 10) -> List[Dict]:
    """
    Search ClinicalTrials.gov for brain-computer interface trials.

    Args:
        max_results: Maximum number of results

    Returns:
        List of clinical trial summaries
    """
    try:
        url = (
            f"https://clinicaltrials.gov/api/v2/studies?"
            f"query.cond=brain+computer+interface&filter.overallStatus=RECRUITING&pageSize={max_results}&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            trials = []
            for study in data.get("studies", []):
                proto = study.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                trials.append({
                    "nct_id": ident.get("nctId", ""),
                    "title": ident.get("briefTitle", ""),
                    "status": status_mod.get("overallStatus", ""),
                    "start_date": status_mod.get("startDateStruct", {}).get("date", ""),
                })
            return trials
    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    summary = get_bci_market_summary()
    print(f"BCI Market: ${summary['total_funding_m_usd']}M funding, {summary['total_patients_implanted']} patients")
    print(f"Highest electrode count: {summary['max_electrodes']}")
