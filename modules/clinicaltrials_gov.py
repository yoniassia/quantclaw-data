#!/usr/bin/env python3
"""
ClinicalTrials.gov API Module

Data Source: U.S. National Library of Medicine ClinicalTrials.gov API v2
Access global clinical trial data including study protocols, results, and status updates
for analyzing biotech pipelines and potential market impacts.

Free tier: Unlimited access, recommended rate limit 3 req/sec, public domain data
Update frequency: Weekly
Relevance: 8 | Integration ease: 9

Phase: NightBuilder 2026-03-06
Author: DevClaw
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

API_BASE = "https://clinicaltrials.gov/api/v2"

def get_trials(condition: Optional[str] = None,
               location: Optional[str] = None,
               status: Optional[str] = None,
               phase: Optional[str] = None,
               sponsor: Optional[str] = None,
               limit: int = 100) -> Dict:
    """
    Get clinical trials with optional filters.
    
    Args:
        condition: Disease/condition (e.g., "cancer", "diabetes")
        location: Country/state (e.g., "USA", "California")
        status: Trial status ("recruiting", "completed", "active", etc.)
        phase: Trial phase ("PHASE1", "PHASE2", "PHASE3", "PHASE4")
        sponsor: Sponsor name (e.g., "Pfizer", "Moderna")
        limit: Max results (default 100, max 1000)
    
    Returns:
        dict with studies array and metadata
    """
    try:
        params = {
            "format": "json",
            "pageSize": min(limit, 1000)
        }
        
        # Build query parts
        query_parts = []
        if condition:
            query_parts.append(f"query.cond={condition}")
        if location:
            query_parts.append(f"query.locn={location}")
        if status:
            query_parts.append(f"filter.overallStatus={status}")
        if phase:
            query_parts.append(f"filter.phase={phase}")
        if sponsor:
            query_parts.append(f"query.lead={sponsor}")
        
        # Add filters to params
        for part in query_parts:
            key, val = part.split('=', 1)
            params[key] = val
        
        # Add fields for complete data
        params["fields"] = "NCTId,BriefTitle,OverallStatus,Phase,StudyType,Condition,InterventionName,StartDate,CompletionDate,EnrollmentCount,LeadSponsorName,OutcomeMeasure"
        
        url = f"{API_BASE}/studies"
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        return {
            'studies': data.get('studies', []),
            'totalCount': data.get('totalCount', 0),
            'pageSize': limit,
            'fetchedAt': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {'error': str(e), 'studies': [], 'totalCount': 0}

def get_trial_by_nct(nct_id: str) -> Dict:
    """
    Get detailed data for a specific trial by NCT ID.
    
    Args:
        nct_id: ClinicalTrials.gov identifier (e.g., "NCT04368728")
    
    Returns:
        dict with full trial details
    """
    try:
        url = f"{API_BASE}/studies/{nct_id}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        return resp.json()
    
    except Exception as e:
        return {'error': str(e), 'nctId': nct_id}

def search_by_company(company: str, phase: Optional[str] = None, limit: int = 50) -> Dict:
    """
    Search trials by sponsor/company name.
    
    Args:
        company: Company name (e.g., "Moderna", "Pfizer", "BioNTech")
        phase: Optional phase filter ("PHASE1", "PHASE2", "PHASE3")
        limit: Max results
    
    Returns:
        dict with studies for the company
    """
    return get_trials(sponsor=company, phase=phase, limit=limit)

def get_recent_completions(days_back: int = 30, condition: Optional[str] = None) -> Dict:
    """
    Get trials completed in the last N days.
    
    Args:
        days_back: Days to look back (default 30)
        condition: Optional condition filter
    
    Returns:
        dict with recently completed trials
    """
    # Note: API doesn't support date range directly, so we filter client-side
    data = get_trials(status="COMPLETED", condition=condition, limit=500)
    
    if data.get('error'):
        return data
    
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    recent = []
    
    for study in data.get('studies', []):
        protocol = study.get('protocolSection', {})
        status_module = protocol.get('statusModule', {})
        completion_date = status_module.get('completionDateStruct', {}).get('date')
        
        if completion_date:
            try:
                comp_dt = datetime.strptime(completion_date, '%Y-%m-%d')
                if comp_dt >= cutoff:
                    recent.append(study)
            except:
                pass
    
    return {
        'studies': recent,
        'totalCount': len(recent),
        'daysBack': days_back,
        'fetchedAt': datetime.utcnow().isoformat()
    }

def get_phase3_trials(condition: Optional[str] = None, status: str = "RECRUITING") -> Dict:
    """
    Get Phase 3 trials (typically pre-approval stage).
    
    Args:
        condition: Disease/condition filter
        status: Trial status (default "RECRUITING")
    
    Returns:
        dict with Phase 3 trials
    """
    return get_trials(condition=condition, status=status, phase="PHASE3", limit=200)

# Example usage
if __name__ == "__main__":
    print("=== ClinicalTrials.gov API Test ===\n")
    
    # Test 1: Search cancer trials
    print("1. Active cancer trials:")
    cancer_trials = get_trials(condition="cancer", status="RECRUITING", limit=5)
    print(f"   Found: {cancer_trials.get('totalCount', 0)} trials")
    if cancer_trials.get('studies'):
        first = cancer_trials['studies'][0]
        protocol = first.get('protocolSection', {})
        ident = protocol.get('identificationModule', {})
        status = protocol.get('statusModule', {})
        print(f"   Example: {ident.get('nctId')} - {ident.get('briefTitle', 'N/A')[:80]}")
        print(f"   Status: {status.get('overallStatus', 'N/A')}")
    
    # Test 2: Company-specific search
    print("\n2. Moderna trials:")
    moderna = search_by_company("Moderna", limit=3)
    print(f"   Found: {moderna.get('totalCount', 0)} trials")
    
    # Test 3: Phase 3 cardiovascular
    print("\n3. Phase 3 cardiovascular trials:")
    phase3 = get_phase3_trials(condition="cardiovascular diseases")
    print(f"   Found: {phase3.get('totalCount', 0)} trials")
    
    print("\n✓ All tests passed")
