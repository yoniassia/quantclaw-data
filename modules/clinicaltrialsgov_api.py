#!/usr/bin/env python3
"""
ClinicalTrials.gov API — Biotech & Pharma Pipeline Intelligence

This module provides access to the U.S. National Library of Medicine's comprehensive
database of clinical studies worldwide. Useful for:
- Tracking drug development pipelines by pharma companies
- Monitoring trial phase progression  
- Analyzing competitive landscapes in therapeutic areas
- Predicting biotech stock movements based on trial milestones

Source: https://clinicaltrials.gov/data-api/about-api
Category: Healthcare & Biotech
Free tier: True - Fully free, no rate limits, no API key required
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ClinicalTrials.gov API Configuration
CLINICALTRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"
DEFAULT_TIMEOUT = 15

# Trial status categories
TRIAL_STATUS = {
    'RECRUITING': 'Currently recruiting participants',
    'ACTIVE_NOT_RECRUITING': 'Active, not recruiting',
    'COMPLETED': 'Study has concluded',
    'ENROLLING_BY_INVITATION': 'Enrolling by invitation',
    'NOT_YET_RECRUITING': 'Not yet recruiting',
    'SUSPENDED': 'Temporarily halted',
    'TERMINATED': 'Prematurely ended',
    'WITHDRAWN': 'Withdrawn prior to enrollment'
}

# Trial phases
TRIAL_PHASES = {
    'EARLY_PHASE1': 'Early Phase 1',
    'PHASE1': 'Phase 1',
    'PHASE2': 'Phase 2',
    'PHASE3': 'Phase 3',
    'PHASE4': 'Phase 4',
    'NA': 'Not Applicable'
}


def search_trials(
    condition: str,
    status: str = 'RECRUITING',
    max_results: int = 100
) -> Dict:
    """
    Search clinical trials by condition and recruitment status
    
    Args:
        condition: Disease or condition (e.g., 'cancer', 'diabetes', 'alzheimer')
        status: Trial status (default 'RECRUITING')
        max_results: Maximum number of results to return (default 100)
    
    Returns:
        Dict with trials list, count, and search metadata
    """
    try:
        url = f"{CLINICALTRIALS_BASE_URL}/studies"
        params = {
            'query.cond': condition,
            'query.term': status,
            'pageSize': min(max_results, 1000),  # API max is 1000
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract studies
        studies = []
        if 'studies' in data:
            for study in data['studies']:
                protocol = study.get('protocolSection', {})
                id_module = protocol.get('identificationModule', {})
                status_module = protocol.get('statusModule', {})
                design_module = protocol.get('designModule', {})
                sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
                
                studies.append({
                    'nct_id': id_module.get('nctId', ''),
                    'title': id_module.get('briefTitle', ''),
                    'status': status_module.get('overallStatus', ''),
                    'phase': design_module.get('phases', ['NA'])[0] if design_module.get('phases') else 'NA',
                    'start_date': status_module.get('startDateStruct', {}).get('date', ''),
                    'completion_date': status_module.get('completionDateStruct', {}).get('date', ''),
                    'sponsor': sponsor_module.get('leadSponsor', {}).get('name', ''),
                    'enrollment': protocol.get('designModule', {}).get('enrollmentInfo', {}).get('count', 0)
                })
        
        return {
            'success': True,
            'condition': condition,
            'status': status,
            'total_count': data.get('totalCount', 0),
            'returned_count': len(studies),
            'studies': studies,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'condition': condition,
            'status': status
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'condition': condition,
            'status': status
        }


def get_trial_details(nct_id: str) -> Dict:
    """
    Get detailed information for a specific clinical trial
    
    Args:
        nct_id: NCT identifier (e.g., 'NCT06000000')
    
    Returns:
        Dict with comprehensive trial details including design, outcomes, locations
    """
    try:
        # Use query parameter instead of path
        url = f"{CLINICALTRIALS_BASE_URL}/studies"
        params = {
            'query.id': nct_id,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if 'studies' not in data or not data['studies']:
            return {
                'success': False,
                'error': 'Trial not found',
                'nct_id': nct_id
            }
        
        study = data['studies'][0]
        protocol = study.get('protocolSection', {})
        
        # Extract comprehensive details
        id_module = protocol.get('identificationModule', {})
        status_module = protocol.get('statusModule', {})
        sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
        desc_module = protocol.get('descriptionModule', {})
        design_module = protocol.get('designModule', {})
        arms_module = protocol.get('armsInterventionsModule', {})
        outcomes_module = protocol.get('outcomesModule', {})
        eligibility_module = protocol.get('eligibilityModule', {})
        contacts_module = protocol.get('contactsLocationsModule', {})
        
        details = {
            'nct_id': id_module.get('nctId', ''),
            'title': id_module.get('briefTitle', ''),
            'official_title': id_module.get('officialTitle', ''),
            'status': status_module.get('overallStatus', ''),
            'phase': design_module.get('phases', ['NA'])[0] if design_module.get('phases') else 'NA',
            'study_type': design_module.get('studyType', ''),
            'sponsor': {
                'lead': sponsor_module.get('leadSponsor', {}).get('name', ''),
                'collaborators': [c.get('name', '') for c in sponsor_module.get('collaborators', [])]
            },
            'description': desc_module.get('briefSummary', ''),
            'detailed_description': desc_module.get('detailedDescription', ''),
            'conditions': protocol.get('conditionsModule', {}).get('conditions', []),
            'interventions': [
                {
                    'type': i.get('type', ''),
                    'name': i.get('name', ''),
                    'description': i.get('description', '')
                }
                for i in arms_module.get('interventions', [])
            ],
            'primary_outcomes': [
                {
                    'measure': o.get('measure', ''),
                    'timeframe': o.get('timeFrame', '')
                }
                for o in outcomes_module.get('primaryOutcomes', [])
            ],
            'enrollment': design_module.get('enrollmentInfo', {}).get('count', 0),
            'start_date': status_module.get('startDateStruct', {}).get('date', ''),
            'primary_completion_date': status_module.get('primaryCompletionDateStruct', {}).get('date', ''),
            'completion_date': status_module.get('completionDateStruct', {}).get('date', ''),
            'study_first_posted': status_module.get('studyFirstPostDateStruct', {}).get('date', ''),
            'last_update_posted': status_module.get('lastUpdatePostDateStruct', {}).get('date', ''),
            'eligibility': {
                'criteria': eligibility_module.get('eligibilityCriteria', ''),
                'min_age': eligibility_module.get('minimumAge', ''),
                'max_age': eligibility_module.get('maximumAge', ''),
                'sex': eligibility_module.get('sex', '')
            },
            'locations_count': len(contacts_module.get('locations', []))
        }
        
        return {
            'success': True,
            'trial': details,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'nct_id': nct_id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'nct_id': nct_id
        }


def get_pharma_pipeline(sponsor: str, max_results: int = 200) -> Dict:
    """
    Get drug development pipeline for a pharmaceutical company
    
    Args:
        sponsor: Company name (e.g., 'Pfizer', 'Moderna', 'Eli Lilly')
        max_results: Maximum number of trials to return (default 200)
    
    Returns:
        Dict with company pipeline organized by phase, status breakdown
    """
    try:
        url = f"{CLINICALTRIALS_BASE_URL}/studies"
        params = {
            'query.lead': sponsor,
            'pageSize': min(max_results, 1000),
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Organize by phase and status
        by_phase = {}
        by_status = {}
        all_trials = []
        
        if 'studies' in data:
            for study in data['studies']:
                protocol = study.get('protocolSection', {})
                id_module = protocol.get('identificationModule', {})
                status_module = protocol.get('statusModule', {})
                design_module = protocol.get('designModule', {})
                
                phase = design_module.get('phases', ['NA'])[0] if design_module.get('phases') else 'NA'
                status = status_module.get('overallStatus', 'UNKNOWN')
                
                trial_info = {
                    'nct_id': id_module.get('nctId', ''),
                    'title': id_module.get('briefTitle', ''),
                    'phase': phase,
                    'status': status,
                    'start_date': status_module.get('startDateStruct', {}).get('date', ''),
                    'conditions': protocol.get('conditionsModule', {}).get('conditions', [])
                }
                
                all_trials.append(trial_info)
                
                # Count by phase
                if phase not in by_phase:
                    by_phase[phase] = 0
                by_phase[phase] += 1
                
                # Count by status
                if status not in by_status:
                    by_status[status] = 0
                by_status[status] += 1
        
        # Calculate pipeline health score (more weight to later phases)
        pipeline_score = 0
        phase_weights = {'PHASE1': 1, 'PHASE2': 2, 'PHASE3': 5, 'PHASE4': 3}
        for phase, count in by_phase.items():
            weight = phase_weights.get(phase, 0)
            pipeline_score += count * weight
        
        return {
            'success': True,
            'sponsor': sponsor,
            'total_trials': data.get('totalCount', 0),
            'returned_count': len(all_trials),
            'by_phase': by_phase,
            'by_status': by_status,
            'pipeline_score': pipeline_score,
            'trials': all_trials,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'sponsor': sponsor
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'sponsor': sponsor
        }


def get_trial_count_by_phase(condition: str) -> Dict:
    """
    Get count of trials by phase for a specific condition
    
    Args:
        condition: Disease or condition (e.g., 'alzheimer', 'multiple sclerosis')
    
    Returns:
        Dict with trial counts broken down by phase
    """
    try:
        url = f"{CLINICALTRIALS_BASE_URL}/studies"
        params = {
            'query.cond': condition,
            'pageSize': 1000,  # Get max to count accurately
            'format': 'json',
            'fields': 'NCTId,Phase,OverallStatus'
        }
        
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Count by phase
        phase_counts = {phase: 0 for phase in TRIAL_PHASES.keys()}
        active_by_phase = {phase: 0 for phase in TRIAL_PHASES.keys()}
        
        if 'studies' in data:
            for study in data['studies']:
                protocol = study.get('protocolSection', {})
                design_module = protocol.get('designModule', {})
                status_module = protocol.get('statusModule', {})
                
                phases = design_module.get('phases', ['NA'])
                status = status_module.get('overallStatus', '')
                
                for phase in phases:
                    if phase in phase_counts:
                        phase_counts[phase] += 1
                        
                        # Track active trials
                        if status in ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION']:
                            active_by_phase[phase] += 1
        
        # Calculate phase distribution percentages
        total = sum(phase_counts.values())
        phase_percentages = {}
        if total > 0:
            for phase, count in phase_counts.items():
                phase_percentages[phase] = round((count / total) * 100, 1)
        
        return {
            'success': True,
            'condition': condition,
            'total_trials': data.get('totalCount', 0),
            'phase_counts': phase_counts,
            'active_by_phase': active_by_phase,
            'phase_percentages': phase_percentages,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'condition': condition
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'condition': condition
        }


def get_recent_completions(days: int = 30, max_results: int = 100) -> Dict:
    """
    Get recently completed clinical trials
    
    Args:
        days: Number of days to look back (default 30)
        max_results: Maximum number of results (default 100)
    
    Returns:
        Dict with recently completed trials, organized by therapeutic area
    """
    try:
        url = f"{CLINICALTRIALS_BASE_URL}/studies"
        params = {
            'query.term': 'COMPLETED',
            'pageSize': min(max_results, 1000),
            'sort': 'LastUpdatePostDate:desc',
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Filter by date and organize
        cutoff_date = datetime.now() - timedelta(days=days)
        by_condition = {}
        by_phase = {}
        completions = []
        
        if 'studies' in data:
            for study in data['studies']:
                protocol = study.get('protocolSection', {})
                id_module = protocol.get('identificationModule', {})
                status_module = protocol.get('statusModule', {})
                design_module = protocol.get('designModule', {})
                sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
                conditions_module = protocol.get('conditionsModule', {})
                
                # Check if recently updated
                last_update_str = status_module.get('lastUpdatePostDateStruct', {}).get('date', '')
                if not last_update_str:
                    continue
                
                try:
                    last_update = datetime.strptime(last_update_str, '%Y-%m-%d')
                    if last_update < cutoff_date:
                        continue
                except:
                    continue
                
                conditions = conditions_module.get('conditions', ['Unknown'])
                phase = design_module.get('phases', ['NA'])[0] if design_module.get('phases') else 'NA'
                
                completion = {
                    'nct_id': id_module.get('nctId', ''),
                    'title': id_module.get('briefTitle', ''),
                    'sponsor': sponsor_module.get('leadSponsor', {}).get('name', ''),
                    'conditions': conditions,
                    'phase': phase,
                    'completion_date': status_module.get('completionDateStruct', {}).get('date', ''),
                    'last_update': last_update_str
                }
                
                completions.append(completion)
                
                # Count by condition
                for condition in conditions:
                    if condition not in by_condition:
                        by_condition[condition] = 0
                    by_condition[condition] += 1
                
                # Count by phase
                if phase not in by_phase:
                    by_phase[phase] = 0
                by_phase[phase] += 1
        
        # Sort conditions by frequency
        top_conditions = sorted(by_condition.items(), key=lambda x: x[1], reverse=True)[:10]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return {
            'success': True,
            'days_back': days,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'total_completed': len(completions),
            'returned_count': len(completions),
            'by_phase': by_phase,
            'top_conditions': dict(top_conditions),
            'completions': completions,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'days': days
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'days': days
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("ClinicalTrials.gov API - Biotech & Pharma Pipeline Intelligence")
    print("=" * 70)
    
    # Example: Search cancer trials
    print("\n[1] Searching cancer trials (RECRUITING)...")
    cancer_trials = search_trials('cancer', status='RECRUITING', max_results=10)
    if cancer_trials['success']:
        print(f"Found {cancer_trials['total_count']} total trials, showing {cancer_trials['returned_count']}")
        for trial in cancer_trials['studies'][:3]:
            print(f"  - {trial['nct_id']}: {trial['title']} [{trial['phase']}]")
    
    # Example: Get trial counts by phase
    print("\n[2] Trial count by phase for Alzheimer's disease...")
    alzheimer_phases = get_trial_count_by_phase('alzheimer')
    if alzheimer_phases['success']:
        print(f"Total trials: {alzheimer_phases['total_trials']}")
        print("Active trials by phase:")
        for phase, count in alzheimer_phases['active_by_phase'].items():
            if count > 0:
                print(f"  {phase}: {count} trials")
    
    # Example: Recent completions
    print("\n[3] Recently completed trials (last 30 days)...")
    recent = get_recent_completions(days=30, max_results=10)
    if recent['success']:
        print(f"Completed in last 30 days: {recent['total_completed']}")
        if recent['top_conditions']:
            print(f"Top conditions: {list(recent['top_conditions'].keys())[:5]}")
    
    print("\n" + "=" * 70)
