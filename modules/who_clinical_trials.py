#!/usr/bin/env python3
"""
WHO Clinical Trials Data Module

Clinical trials data via ClinicalTrials.gov API v2
- Search clinical trials by condition
- Search by drug/intervention
- Get detailed trial information
- Count active trials
- Search by sponsor/company
- Filter recruiting trials by country

Data Source: https://clinicaltrials.gov/api/v2/
Refresh: Daily updates from global clinical trial registries
Coverage: 450,000+ studies from 200+ countries
Free tier: Yes, no authentication required

Author: QUANTCLAW DATA NightBuilder
Phase: WHO_001
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Union
from datetime import datetime

# ClinicalTrials.gov API Configuration
CT_BASE_URL = "https://clinicaltrials.gov/api/v2"

def _make_request(endpoint: str, params: Dict = None) -> Dict:
    """
    Internal helper to make HTTP requests to ClinicalTrials.gov API
    
    Args:
        endpoint: API endpoint path
        params: Query parameters dict
        
    Returns:
        Parsed JSON response
    """
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{CT_BASE_URL}/{endpoint}?{query_string}"
    else:
        url = f"{CT_BASE_URL}/{endpoint}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'QuantClaw-Data/1.0')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {str(e.reason)}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}", "url": url}

def search_trials(condition: str = 'diabetes', limit: int = 10) -> List[Dict]:
    """
    Search clinical trials by medical condition
    
    Args:
        condition: Medical condition (e.g., 'diabetes', 'cancer', 'alzheimer')
        limit: Maximum number of results (1-1000)
        
    Returns:
        List of trial summaries with NCT ID, title, status, sponsor
        
    Example:
        >>> trials = search_trials('breast cancer', limit=5)
        >>> print(trials[0]['nctId'])
    """
    params = {
        'query.cond': condition,
        'pageSize': min(limit, 1000)
    }
    
    data = _make_request('studies', params)
    
    if 'error' in data:
        return [data]
    
    results = []
    for study in data.get('studies', []):
        protocol = study.get('protocolSection', {})
        ident = protocol.get('identificationModule', {})
        status_mod = protocol.get('statusModule', {})
        sponsor = protocol.get('sponsorCollaboratorsModule', {})
        
        results.append({
            'nctId': ident.get('nctId'),
            'title': ident.get('briefTitle'),
            'status': status_mod.get('overallStatus'),
            'sponsor': sponsor.get('leadSponsor', {}).get('name'),
            'startDate': status_mod.get('startDateStruct', {}).get('date'),
            'phase': protocol.get('designModule', {}).get('phases', ['N/A'])[0] if protocol.get('designModule', {}).get('phases') else 'N/A'
        })
    
    return results

def search_by_drug(intervention: str = 'pembrolizumab', limit: int = 10) -> List[Dict]:
    """
    Search clinical trials by drug or intervention name
    
    Args:
        intervention: Drug/intervention name (e.g., 'pembrolizumab', 'aspirin')
        limit: Maximum number of results (1-1000)
        
    Returns:
        List of trial summaries testing this intervention
        
    Example:
        >>> trials = search_by_drug('nivolumab', limit=5)
    """
    params = {
        'query.intr': intervention,
        'pageSize': min(limit, 1000)
    }
    
    data = _make_request('studies', params)
    
    if 'error' in data:
        return [data]
    
    results = []
    for study in data.get('studies', []):
        protocol = study.get('protocolSection', {})
        ident = protocol.get('identificationModule', {})
        status_mod = protocol.get('statusModule', {})
        sponsor = protocol.get('sponsorCollaboratorsModule', {})
        design = protocol.get('designModule', {})
        
        results.append({
            'nctId': ident.get('nctId'),
            'title': ident.get('briefTitle'),
            'status': status_mod.get('overallStatus'),
            'sponsor': sponsor.get('leadSponsor', {}).get('name'),
            'phase': design.get('phases', ['N/A'])[0] if design.get('phases') else 'N/A',
            'studyType': design.get('studyType')
        })
    
    return results

def get_trial_details(trial_id: str) -> Dict:
    """
    Get detailed information about a specific clinical trial
    
    Args:
        trial_id: NCT identifier (e.g., 'NCT04576871')
        
    Returns:
        Detailed trial information including description, eligibility, outcomes
        
    Example:
        >>> details = get_trial_details('NCT04576871')
        >>> print(details['description'])
    """
    # Use query parameter to get specific study
    params = {'query.id': trial_id}
    data = _make_request('studies', params)
    
    if 'error' in data:
        return data
    
    studies = data.get('studies', [])
    if not studies:
        return {'error': f'Trial {trial_id} not found'}
    
    study = studies[0]
    protocol = study.get('protocolSection', {})
    ident = protocol.get('identificationModule', {})
    status_mod = protocol.get('statusModule', {})
    desc = protocol.get('descriptionModule', {})
    cond = protocol.get('conditionsModule', {})
    design = protocol.get('designModule', {})
    eligibility = protocol.get('eligibilityModule', {})
    sponsor = protocol.get('sponsorCollaboratorsModule', {})
    
    return {
        'nctId': ident.get('nctId'),
        'title': ident.get('briefTitle'),
        'officialTitle': ident.get('officialTitle'),
        'status': status_mod.get('overallStatus'),
        'phase': design.get('phases', ['N/A'])[0] if design.get('phases') else 'N/A',
        'studyType': design.get('studyType'),
        'enrollment': design.get('enrollmentInfo', {}).get('count'),
        'conditions': cond.get('conditions', []),
        'sponsor': sponsor.get('leadSponsor', {}).get('name'),
        'briefSummary': desc.get('briefSummary'),
        'detailedDescription': desc.get('detailedDescription'),
        'startDate': status_mod.get('startDateStruct', {}).get('date'),
        'completionDate': status_mod.get('completionDateStruct', {}).get('date'),
        'eligibilityCriteria': eligibility.get('eligibilityCriteria'),
        'minimumAge': eligibility.get('minimumAge'),
        'maximumAge': eligibility.get('maximumAge'),
        'sex': eligibility.get('sex')
    }

def get_trial_count(condition: str = 'cancer') -> Dict:
    """
    Count active trials for a specific condition
    
    Args:
        condition: Medical condition to count
        
    Returns:
        Dictionary with count and condition info
        
    Example:
        >>> count = get_trial_count('diabetes')
        >>> print(count['totalTrials'])
    """
    params = {
        'query.cond': condition,
        'pageSize': 1  # We only need the count
    }
    
    data = _make_request('studies', params)
    
    if 'error' in data:
        return data
    
    return {
        'condition': condition,
        'totalTrials': data.get('totalCount', 0),
        'timestamp': datetime.now().isoformat()
    }

def search_by_sponsor(sponsor: str = 'Pfizer', limit: int = 10) -> List[Dict]:
    """
    Search clinical trials by sponsor/company name
    
    Args:
        sponsor: Company or institution name (e.g., 'Pfizer', 'Mayo Clinic')
        limit: Maximum number of results (1-1000)
        
    Returns:
        List of trials sponsored by this organization
        
    Example:
        >>> trials = search_by_sponsor('Moderna', limit=5)
    """
    params = {
        'query.lead': sponsor,
        'pageSize': min(limit, 1000)
    }
    
    data = _make_request('studies', params)
    
    if 'error' in data:
        return [data]
    
    results = []
    for study in data.get('studies', []):
        protocol = study.get('protocolSection', {})
        ident = protocol.get('identificationModule', {})
        status_mod = protocol.get('statusModule', {})
        cond = protocol.get('conditionsModule', {})
        design = protocol.get('designModule', {})
        
        results.append({
            'nctId': ident.get('nctId'),
            'title': ident.get('briefTitle'),
            'status': status_mod.get('overallStatus'),
            'conditions': cond.get('conditions', []),
            'phase': design.get('phases', ['N/A'])[0] if design.get('phases') else 'N/A',
            'startDate': status_mod.get('startDateStruct', {}).get('date')
        })
    
    return results

def get_recruiting_trials(condition: str = 'alzheimer', country: str = 'US', limit: int = 10) -> List[Dict]:
    """
    Get actively recruiting trials for a condition in a specific country
    
    Args:
        condition: Medical condition
        country: Two-letter country code (e.g., 'US', 'GB', 'JP')
        limit: Maximum number of results (1-1000)
        
    Returns:
        List of currently recruiting trials
        
    Example:
        >>> trials = get_recruiting_trials('alzheimer', 'US', limit=5)
    """
    params = {
        'query.cond': condition,
        'query.locn': country,
        'filter.overallStatus': 'RECRUITING',
        'pageSize': min(limit, 1000)
    }
    
    data = _make_request('studies', params)
    
    if 'error' in data:
        return [data]
    
    results = []
    for study in data.get('studies', []):
        protocol = study.get('protocolSection', {})
        ident = protocol.get('identificationModule', {})
        status_mod = protocol.get('statusModule', {})
        sponsor = protocol.get('sponsorCollaboratorsModule', {})
        design = protocol.get('designModule', {})
        contacts = protocol.get('contactsLocationsModule', {})
        
        # Extract US locations
        locations = []
        for loc in contacts.get('locations', []):
            if loc.get('country') == country:
                locations.append({
                    'facility': loc.get('facility'),
                    'city': loc.get('city'),
                    'state': loc.get('state')
                })
        
        results.append({
            'nctId': ident.get('nctId'),
            'title': ident.get('briefTitle'),
            'status': status_mod.get('overallStatus'),
            'sponsor': sponsor.get('leadSponsor', {}).get('name'),
            'phase': design.get('phases', ['N/A'])[0] if design.get('phases') else 'N/A',
            'startDate': status_mod.get('startDateStruct', {}).get('date'),
            'locations': locations[:3]  # First 3 locations
        })
    
    return results

# Aliases for convenience
search_by_condition = search_trials
search_by_intervention = search_by_drug

if __name__ == "__main__":
    # Quick test
    print("Testing WHO Clinical Trials Module...")
    
    # Test 1: Search by condition
    print("\n1. Searching for diabetes trials...")
    trials = search_trials('diabetes', limit=3)
    if trials and 'error' not in trials[0]:
        print(f"   Found {len(trials)} trials")
        print(f"   First trial: {trials[0].get('nctId')} - {trials[0].get('title')[:60]}...")
    
    # Test 2: Count trials
    print("\n2. Counting cancer trials...")
    count = get_trial_count('cancer')
    if 'error' not in count:
        print(f"   Total cancer trials: {count.get('totalTrials')}")
    
    print("\nModule test complete!")
