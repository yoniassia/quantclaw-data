#!/usr/bin/env python3
"""
openFDA - FDA Drug Approvals, Adverse Events, and Recalls
Free public API for FDA regulatory data

Data sources:
- Drug adverse events (FAERS)
- Drug recalls
- Drug labeling and approvals
- Device adverse events
- Food recalls

Reference: https://open.fda.gov/apis/
No API key required for <240 requests/minute, <120000 requests/day
"""

import requests
import pandas as pd
import sys
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, List

OPENFDA_BASE = "https://api.fda.gov"

# API endpoints
ENDPOINTS = {
    'drug_events': f"{OPENFDA_BASE}/drug/event.json",
    'drug_recalls': f"{OPENFDA_BASE}/drug/enforcement.json",
    'drug_labels': f"{OPENFDA_BASE}/drug/label.json",
    'drug_ndc': f"{OPENFDA_BASE}/drug/ndc.json",
    'device_events': f"{OPENFDA_BASE}/device/event.json",
    'device_recalls': f"{OPENFDA_BASE}/device/enforcement.json",
    'food_recalls': f"{OPENFDA_BASE}/food/enforcement.json",
}

def fetch_drug_adverse_events(drug_name: str, limit: int = 100) -> pd.DataFrame:
    """
    Fetch adverse event reports for a specific drug from FDA FAERS database.
    
    Args:
        drug_name: Drug name (generic or brand name)
        limit: Maximum number of results (default 100, max 1000)
    
    Returns:
        DataFrame with adverse event reports including reactions, outcomes, patient demographics
    """
    try:
        # Search using openfda.brand_name field (more reliable than medicinalproduct)
        search_query = f'patient.drug.openfda.brand_name:{drug_name}'
        
        params = {
            'search': search_query,
            'limit': min(limit, 1000)
        }
        
        response = requests.get(ENDPOINTS['drug_events'], params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or len(data['results']) == 0:
            print(f"No adverse events found for {drug_name}", file=sys.stderr)
            return pd.DataFrame()
        
        # Parse results into structured format
        records = []
        for result in data['results']:
            patient = result.get('patient', {})
            
            # Extract reactions
            reactions = patient.get('reaction', [])
            reaction_list = [r.get('reactionmeddrapt', 'Unknown') for r in reactions]
            
            # Extract outcomes
            serious = result.get('serious', 0)
            death = result.get('seriousnessdeath', 0)
            
            # Extract drug info
            drugs = patient.get('drug', [])
            drug_roles = []
            for drug in drugs:
                if drug_name.lower() in drug.get('medicinalproduct', '').lower():
                    drug_roles.append(drug.get('drugcharacterization', 'Unknown'))
            
            records.append({
                'report_id': result.get('safetyreportid', 'Unknown'),
                'receive_date': result.get('receivedate', 'Unknown'),
                'drug_name': drug_name,
                'reactions': ', '.join(reaction_list[:5]),
                'reaction_count': len(reactions),
                'serious': bool(serious),
                'death': bool(death),
                'patient_age': patient.get('patientonsetage', None),
                'patient_sex': patient.get('patientsex', 'Unknown'),
                'country': result.get('primarysource', {}).get('reportercountry', 'Unknown'),
                'receiver_type': result.get('receivertype', 'Unknown'),
            })
        
        df = pd.DataFrame(records)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching drug adverse events: {e}", file=sys.stderr)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing drug adverse events: {e}", file=sys.stderr)
        return pd.DataFrame()

def fetch_drug_recalls(limit: int = 100, classification: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch recent drug recalls from FDA.
    
    Args:
        limit: Maximum number of results (default 100, max 1000)
        classification: Recall classification ('Class I', 'Class II', 'Class III') or None for all
    
    Returns:
        DataFrame with recall information including product, reason, and classification
    """
    try:
        params = {
            'limit': min(limit, 1000),
        }
        
        # Add classification filter if specified
        if classification:
            params['search'] = f'classification:"{classification}"'
        
        response = requests.get(ENDPOINTS['drug_recalls'], params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or len(data['results']) == 0:
            print("No drug recalls found", file=sys.stderr)
            return pd.DataFrame()
        
        # Parse results
        records = []
        for result in data['results']:
            records.append({
                'report_date': result.get('report_date', 'Unknown'),
                'classification': result.get('classification', 'Unknown'),
                'status': result.get('status', 'Unknown'),
                'product_description': result.get('product_description', 'Unknown')[:200],
                'reason_for_recall': result.get('reason_for_recall', 'Unknown')[:200],
                'recalling_firm': result.get('recalling_firm', 'Unknown'),
                'city': result.get('city', 'Unknown'),
                'state': result.get('state', 'Unknown'),
                'country': result.get('country', 'Unknown'),
                'voluntary_mandated': result.get('voluntary_mandated', 'Unknown'),
                'recall_number': result.get('recall_number', 'Unknown'),
            })
        
        df = pd.DataFrame(records)
        # Sort by report date if available
        if 'report_date' in df.columns:
            df = df.sort_values('report_date', ascending=False)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching drug recalls: {e}", file=sys.stderr)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing drug recalls: {e}", file=sys.stderr)
        return pd.DataFrame()

def search_drug_labels(drug_name: str, limit: int = 10) -> List[Dict]:
    """
    Search drug labeling information (package inserts, prescribing information).
    
    Args:
        drug_name: Drug name to search for
        limit: Maximum number of results (default 10, max 100)
    
    Returns:
        List of dictionaries with drug label information
    """
    try:
        search_query = f'openfda.brand_name:{drug_name}'
        
        params = {
            'search': search_query,
            'limit': min(limit, 100)
        }
        
        response = requests.get(ENDPOINTS['drug_labels'], params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or len(data['results']) == 0:
            print(f"No drug labels found for {drug_name}", file=sys.stderr)
            return []
        
        # Parse results
        labels = []
        for result in data['results']:
            openfda = result.get('openfda', {})
            
            label_info = {
                'brand_name': openfda.get('brand_name', ['Unknown'])[0] if openfda.get('brand_name') else 'Unknown',
                'generic_name': openfda.get('generic_name', ['Unknown'])[0] if openfda.get('generic_name') else 'Unknown',
                'manufacturer_name': openfda.get('manufacturer_name', ['Unknown'])[0] if openfda.get('manufacturer_name') else 'Unknown',
                'product_type': openfda.get('product_type', ['Unknown'])[0] if openfda.get('product_type') else 'Unknown',
                'route': ', '.join(openfda.get('route', ['Unknown'])[:3]),
                'substance_name': ', '.join(openfda.get('substance_name', ['Unknown'])[:3]),
                'indications_and_usage': ' '.join(result.get('indications_and_usage', ['Not available']))[:300],
                'warnings': ' '.join(result.get('warnings', ['Not available']))[:300],
                'dosage_and_administration': ' '.join(result.get('dosage_and_administration', ['Not available']))[:200],
            }
            labels.append(label_info)
        
        return labels
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching drug labels: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error processing drug labels: {e}", file=sys.stderr)
        return []

def fetch_device_recalls(limit: int = 100, classification: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch recent medical device recalls from FDA.
    
    Args:
        limit: Maximum number of results (default 100, max 1000)
        classification: Recall classification ('Class I', 'Class II', 'Class III') or None for all
    
    Returns:
        DataFrame with device recall information
    """
    try:
        params = {
            'limit': min(limit, 1000),
        }
        
        if classification:
            params['search'] = f'classification:"{classification}"'
        
        response = requests.get(ENDPOINTS['device_recalls'], params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or len(data['results']) == 0:
            print("No device recalls found", file=sys.stderr)
            return pd.DataFrame()
        
        records = []
        for result in data['results']:
            records.append({
                'report_date': result.get('report_date', 'Unknown'),
                'classification': result.get('classification', 'Unknown'),
                'status': result.get('status', 'Unknown'),
                'product_description': result.get('product_description', 'Unknown')[:200],
                'reason_for_recall': result.get('reason_for_recall', 'Unknown')[:200],
                'recalling_firm': result.get('recalling_firm', 'Unknown'),
                'product_code': result.get('product_code', 'Unknown'),
                'code_info': result.get('code_info', 'Unknown')[:100],
                'recall_number': result.get('recall_number', 'Unknown'),
            })
        
        df = pd.DataFrame(records)
        if 'report_date' in df.columns:
            df = df.sort_values('report_date', ascending=False)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching device recalls: {e}", file=sys.stderr)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing device recalls: {e}", file=sys.stderr)
        return pd.DataFrame()

def get_adverse_events_stats(drug_name: str, limit: int = 1000) -> Dict:
    """
    Get statistical summary of adverse events for a drug.
    
    Args:
        drug_name: Drug name to analyze
        limit: Number of events to analyze (default 1000)
    
    Returns:
        Dictionary with statistics (total_events, serious_rate, death_rate, top_reactions)
    """
    try:
        df = fetch_drug_adverse_events(drug_name, limit=limit)
        
        if df.empty:
            return {
                'drug_name': drug_name,
                'total_events': 0,
                'error': 'No data found'
            }
        
        # Calculate statistics
        stats = {
            'drug_name': drug_name,
            'total_events': len(df),
            'serious_events': df['serious'].sum(),
            'serious_rate': (df['serious'].sum() / len(df) * 100) if len(df) > 0 else 0,
            'deaths': df['death'].sum(),
            'death_rate': (df['death'].sum() / len(df) * 100) if len(df) > 0 else 0,
            'avg_patient_age': df['patient_age'].mean() if 'patient_age' in df.columns else None,
            'top_countries': df['country'].value_counts().head(5).to_dict() if 'country' in df.columns else {},
            'date_range': f"{df['receive_date'].min()} to {df['receive_date'].max()}" if 'receive_date' in df.columns else 'Unknown'
        }
        
        return stats
        
    except Exception as e:
        print(f"Error calculating adverse event stats: {e}", file=sys.stderr)
        return {'drug_name': drug_name, 'error': str(e)}

def search_recalls_by_firm(firm_name: str, limit: int = 50) -> pd.DataFrame:
    """
    Search drug recalls by recalling firm name.
    
    Args:
        firm_name: Name of the recalling firm
        limit: Maximum number of results
    
    Returns:
        DataFrame with recall information
    """
    try:
        search_query = f'recalling_firm:"{firm_name}"'
        
        params = {
            'search': search_query,
            'limit': min(limit, 1000)
        }
        
        response = requests.get(ENDPOINTS['drug_recalls'], params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or len(data['results']) == 0:
            print(f"No recalls found for {firm_name}", file=sys.stderr)
            return pd.DataFrame()
        
        records = []
        for result in data['results']:
            records.append({
                'report_date': result.get('report_date', 'Unknown'),
                'classification': result.get('classification', 'Unknown'),
                'product_description': result.get('product_description', 'Unknown')[:200],
                'reason_for_recall': result.get('reason_for_recall', 'Unknown')[:200],
                'status': result.get('status', 'Unknown'),
            })
        
        df = pd.DataFrame(records)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error searching recalls by firm: {e}", file=sys.stderr)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing firm recalls: {e}", file=sys.stderr)
        return pd.DataFrame()

# Export main functions
__all__ = [
    'fetch_drug_adverse_events',
    'fetch_drug_recalls',
    'search_drug_labels',
    'fetch_device_recalls',
    'get_adverse_events_stats',
    'search_recalls_by_firm',
]

if __name__ == "__main__":
    # Quick test
    print("Testing openFDA module...")
    
    # Test 1: Drug recalls
    print("\n1. Recent drug recalls:")
    recalls = fetch_drug_recalls(limit=5)
    print(recalls[['report_date', 'classification', 'recalling_firm', 'reason_for_recall']].head() if not recalls.empty else "No recalls found")
    
    # Test 2: Adverse events for Lipitor
    print("\n2. Adverse events for Lipitor:")
    events = fetch_drug_adverse_events('lipitor', limit=10)
    print(events[['receive_date', 'reactions', 'serious', 'patient_age']].head() if not events.empty else "No events found")
    
    # Test 3: Drug labels
    print("\n3. Drug label for Lipitor:")
    labels = search_drug_labels('lipitor', limit=1)
    if labels:
        print(f"Brand: {labels[0]['brand_name']}, Generic: {labels[0]['generic_name']}")
        print(f"Indications: {labels[0]['indications_and_usage'][:150]}...")
    
    print("\nModule tests complete!")
