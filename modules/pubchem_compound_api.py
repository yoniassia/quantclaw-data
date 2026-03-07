#!/usr/bin/env python3
"""
PubChem Compound API — Healthcare & Biotech Chemical Data

PubChem is NIH's open chemistry database providing comprehensive data on chemical compounds,
bioactivity, drug development pipelines, and patent information. Critical for quantitative
analysis of pharmaceutical and biotech company drug candidates, competitive landscapes, and
pipeline assessment.

Source: https://pubchem.ncbi.nlm.nih.gov/rest/pug/
Category: Healthcare & Biotech
Free tier: True (No API key required; rate limit 5 requests/second)
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import requests
import json
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

# PubChem PUG REST API Configuration
PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
RATE_LIMIT_DELAY = 0.21  # 5 req/sec = 0.2s between requests, add buffer

# Default properties to fetch
DEFAULT_PROPERTIES = [
    'MolecularFormula',
    'MolecularWeight',
    'CanonicalSMILES',
    'IsomericSMILES',
    'InChI',
    'InChIKey',
    'IUPACName',
    'XLogP',
    'TPSA',
    'HBondDonorCount',
    'HBondAcceptorCount'
]


def _rate_limit():
    """Enforce rate limit (5 req/sec)"""
    time.sleep(RATE_LIMIT_DELAY)


def _make_request(url: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to PubChem API with error handling
    
    Args:
        url: API endpoint URL
        params: Optional query parameters
    
    Returns:
        Dict with response data or error
    """
    try:
        _rate_limit()
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        return {
            'success': True,
            'data': response.json()
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                'success': False,
                'error': 'Compound not found',
                'status_code': 404
            }
        return {
            'success': False,
            'error': f'HTTP {e.response.status_code}: {str(e)}',
            'status_code': e.response.status_code
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def get_compound_by_name(name: str) -> Dict:
    """
    Look up compound by common name or IUPAC name
    
    Args:
        name: Compound name (e.g., 'aspirin', 'ibuprofen', 'caffeine')
    
    Returns:
        Dict with compound data including CID, molecular formula, structure, properties
    
    Example:
        >>> result = get_compound_by_name('aspirin')
        >>> print(result['cid'], result['molecular_formula'])
    """
    url = f"{PUBCHEM_BASE_URL}/compound/name/{name}/JSON"
    response = _make_request(url)
    
    if not response['success']:
        return response
    
    try:
        compounds = response['data'].get('PC_Compounds', [])
        if not compounds:
            return {
                'success': False,
                'error': f'No compound data found for "{name}"'
            }
        
        compound = compounds[0]
        cid = compound['id']['id']['cid']
        
        # Extract properties
        props = {}
        for prop in compound.get('props', []):
            urn = prop.get('urn', {})
            label = urn.get('label', '')
            
            if 'sval' in prop['value']:
                props[label] = prop['value']['sval']
            elif 'fval' in prop['value']:
                props[label] = prop['value']['fval']
            elif 'ival' in prop['value']:
                props[label] = prop['value']['ival']
        
        return {
            'success': True,
            'cid': cid,
            'name': name,
            'molecular_formula': props.get('Molecular Formula', 'N/A'),
            'molecular_weight': props.get('Molecular Weight', 'N/A'),
            'iupac_name': props.get('IUPAC Name', 'N/A'),
            'canonical_smiles': props.get('Canonical SMILES', 'N/A'),
            'inchi': props.get('InChI', 'N/A'),
            'inchi_key': props.get('InChIKey', 'N/A'),
            'properties': props,
            'timestamp': datetime.now().isoformat()
        }
    
    except (KeyError, IndexError) as e:
        return {
            'success': False,
            'error': f'Failed to parse compound data: {str(e)}'
        }


def get_compound_by_cid(cid: int) -> Dict:
    """
    Look up compound by PubChem Compound ID (CID)
    
    Args:
        cid: PubChem Compound ID (integer)
    
    Returns:
        Dict with compound data
    
    Example:
        >>> result = get_compound_by_cid(2244)  # Aspirin
        >>> print(result['molecular_formula'])
    """
    url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/JSON"
    response = _make_request(url)
    
    if not response['success']:
        return response
    
    try:
        compounds = response['data'].get('PC_Compounds', [])
        if not compounds:
            return {
                'success': False,
                'error': f'No compound data found for CID {cid}'
            }
        
        compound = compounds[0]
        
        # Extract properties
        props = {}
        for prop in compound.get('props', []):
            urn = prop.get('urn', {})
            label = urn.get('label', '')
            
            if 'sval' in prop['value']:
                props[label] = prop['value']['sval']
            elif 'fval' in prop['value']:
                props[label] = prop['value']['fval']
            elif 'ival' in prop['value']:
                props[label] = prop['value']['ival']
        
        return {
            'success': True,
            'cid': cid,
            'molecular_formula': props.get('Molecular Formula', 'N/A'),
            'molecular_weight': props.get('Molecular Weight', 'N/A'),
            'iupac_name': props.get('IUPAC Name', 'N/A'),
            'canonical_smiles': props.get('Canonical SMILES', 'N/A'),
            'inchi': props.get('InChI', 'N/A'),
            'inchi_key': props.get('InChIKey', 'N/A'),
            'properties': props,
            'timestamp': datetime.now().isoformat()
        }
    
    except (KeyError, IndexError) as e:
        return {
            'success': False,
            'error': f'Failed to parse compound data: {str(e)}'
        }


def get_compound_properties(
    name_or_cid: Union[str, int],
    properties: Optional[List[str]] = None
) -> Dict:
    """
    Get specific properties for a compound
    
    Args:
        name_or_cid: Compound name or CID
        properties: List of property names to fetch (default: DEFAULT_PROPERTIES)
    
    Returns:
        Dict with requested properties
    
    Available properties:
        MolecularFormula, MolecularWeight, CanonicalSMILES, IsomericSMILES,
        InChI, InChIKey, IUPACName, XLogP, TPSA, Complexity,
        HBondDonorCount, HBondAcceptorCount, RotatableBondCount, etc.
    
    Example:
        >>> result = get_compound_properties('aspirin', ['MolecularWeight', 'XLogP'])
        >>> print(result['properties'])
    """
    if properties is None:
        properties = DEFAULT_PROPERTIES
    
    props_str = ','.join(properties)
    
    # Determine if input is CID or name
    if isinstance(name_or_cid, int) or (isinstance(name_or_cid, str) and name_or_cid.isdigit()):
        identifier = f"cid/{name_or_cid}"
    else:
        identifier = f"name/{name_or_cid}"
    
    url = f"{PUBCHEM_BASE_URL}/compound/{identifier}/property/{props_str}/JSON"
    response = _make_request(url)
    
    if not response['success']:
        return response
    
    try:
        props_data = response['data'].get('PropertyTable', {}).get('Properties', [])
        if not props_data:
            return {
                'success': False,
                'error': 'No properties found'
            }
        
        result = props_data[0]
        
        return {
            'success': True,
            'cid': result.get('CID'),
            'properties': result,
            'requested_properties': properties,
            'timestamp': datetime.now().isoformat()
        }
    
    except (KeyError, IndexError) as e:
        return {
            'success': False,
            'error': f'Failed to parse properties: {str(e)}'
        }


def search_compounds(query: str, max_results: int = 10) -> Dict:
    """
    Search compounds by name, formula, or other criteria
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default 10)
    
    Returns:
        Dict with list of matching compound CIDs and names
    
    Example:
        >>> results = search_compounds('statin', max_results=5)
        >>> for cid in results['cids']:
        ...     print(cid)
    """
    url = f"{PUBCHEM_BASE_URL}/compound/name/{query}/cids/JSON"
    response = _make_request(url)
    
    if not response['success']:
        return response
    
    try:
        cids = response['data'].get('IdentifierList', {}).get('CID', [])
        
        if not cids:
            return {
                'success': False,
                'error': f'No compounds found matching "{query}"'
            }
        
        # Limit results
        cids = cids[:max_results]
        
        return {
            'success': True,
            'query': query,
            'count': len(cids),
            'cids': cids,
            'timestamp': datetime.now().isoformat()
        }
    
    except KeyError as e:
        return {
            'success': False,
            'error': f'Failed to parse search results: {str(e)}'
        }


def get_compound_synonyms(name_or_cid: Union[str, int], max_synonyms: int = 50) -> Dict:
    """
    Get all synonyms and brand names for a compound
    
    Args:
        name_or_cid: Compound name or CID
        max_synonyms: Maximum number of synonyms to return (default 50)
    
    Returns:
        Dict with list of synonyms including brand names, generic names, IUPAC names
    
    Example:
        >>> result = get_compound_synonyms('aspirin')
        >>> print(result['synonyms'][:10])  # First 10 synonyms
    """
    # Determine if input is CID or name
    if isinstance(name_or_cid, int) or (isinstance(name_or_cid, str) and name_or_cid.isdigit()):
        identifier = f"cid/{name_or_cid}"
    else:
        identifier = f"name/{name_or_cid}"
    
    url = f"{PUBCHEM_BASE_URL}/compound/{identifier}/synonyms/JSON"
    response = _make_request(url)
    
    if not response['success']:
        return response
    
    try:
        info_list = response['data'].get('InformationList', {}).get('Information', [])
        
        if not info_list:
            return {
                'success': False,
                'error': 'No synonym data found'
            }
        
        info = info_list[0]
        cid = info.get('CID')
        synonyms = info.get('Synonym', [])
        
        # Limit synonyms
        synonyms = synonyms[:max_synonyms]
        
        return {
            'success': True,
            'cid': cid,
            'count': len(synonyms),
            'synonyms': synonyms,
            'timestamp': datetime.now().isoformat()
        }
    
    except (KeyError, IndexError) as e:
        return {
            'success': False,
            'error': f'Failed to parse synonyms: {str(e)}'
        }


def get_bioactivity(name_or_cid: Union[str, int]) -> Dict:
    """
    Get bioactivity data for a compound (assays, targets, pharmacology)
    Note: This is a simplified version - full bioactivity data requires complex queries
    
    Args:
        name_or_cid: Compound name or CID
    
    Returns:
        Dict with bioactivity summary and assay counts
    
    Example:
        >>> result = get_bioactivity('aspirin')
        >>> print(result['bioactivity_summary'])
    """
    # First get CID if name provided
    if isinstance(name_or_cid, str) and not name_or_cid.isdigit():
        compound = get_compound_by_name(name_or_cid)
        if not compound['success']:
            return compound
        cid = compound['cid']
    else:
        cid = int(name_or_cid)
    
    # Get assay summary
    url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/assaysummary/JSON"
    response = _make_request(url)
    
    if not response['success']:
        # Bioactivity data may not be available for all compounds
        return {
            'success': True,
            'cid': cid,
            'bioactivity_available': False,
            'message': 'No bioactivity data available for this compound',
            'timestamp': datetime.now().isoformat()
        }
    
    try:
        table = response['data'].get('Table', {})
        rows = table.get('Row', [])
        
        bioactivity_summary = {
            'active_assays': 0,
            'inactive_assays': 0,
            'inconclusive_assays': 0,
            'total_assays': 0
        }
        
        for row in rows:
            cells = row.get('Cell', [])
            if len(cells) >= 2:
                activity_type = str(cells[0]).lower()
                count_str = str(cells[1]).strip()
                
                # Skip empty or non-numeric counts
                if not count_str or not count_str.isdigit():
                    continue
                
                count = int(count_str)
                
                if 'active' in activity_type and 'inactive' not in activity_type:
                    bioactivity_summary['active_assays'] = count
                elif 'inactive' in activity_type:
                    bioactivity_summary['inactive_assays'] = count
                elif 'inconclusive' in activity_type or 'unspecified' in activity_type:
                    bioactivity_summary['inconclusive_assays'] = count
        
        bioactivity_summary['total_assays'] = sum([
            bioactivity_summary['active_assays'],
            bioactivity_summary['inactive_assays'],
            bioactivity_summary['inconclusive_assays']
        ])
        
        return {
            'success': True,
            'cid': cid,
            'bioactivity_available': True,
            'bioactivity_summary': bioactivity_summary,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to parse bioactivity data: {str(e)}'
        }


def get_drug_info(name_or_cid: Union[str, int]) -> Dict:
    """
    Get comprehensive drug information for pharma/biotech analysis
    Combines compound data, synonyms, and bioactivity
    
    Args:
        name_or_cid: Drug name or CID
    
    Returns:
        Dict with complete drug profile for investment analysis
    
    Example:
        >>> drug = get_drug_info('remdesivir')
        >>> print(drug['molecular_weight'], drug['synonym_count'])
    """
    # Get compound data
    if isinstance(name_or_cid, str) and not name_or_cid.isdigit():
        compound = get_compound_by_name(name_or_cid)
    else:
        compound = get_compound_by_cid(int(name_or_cid))
    
    if not compound['success']:
        return compound
    
    cid = compound['cid']
    
    # Get synonyms
    synonyms = get_compound_synonyms(cid, max_synonyms=20)
    
    # Get bioactivity
    bioactivity = get_bioactivity(cid)
    
    return {
        'success': True,
        'cid': cid,
        'name': compound.get('name', name_or_cid),
        'molecular_formula': compound.get('molecular_formula'),
        'molecular_weight': compound.get('molecular_weight'),
        'iupac_name': compound.get('iupac_name'),
        'synonyms': synonyms.get('synonyms', []),
        'synonym_count': synonyms.get('count', 0),
        'bioactivity_available': bioactivity.get('bioactivity_available', False),
        'bioactivity_summary': bioactivity.get('bioactivity_summary', {}),
        'canonical_smiles': compound.get('canonical_smiles'),
        'inchi_key': compound.get('inchi_key'),
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("PubChem Compound API - Healthcare & Biotech Chemical Data")
    print("=" * 70)
    
    # Test with aspirin
    print("\n[TEST 1] Compound lookup: Aspirin")
    aspirin = get_compound_by_name('aspirin')
    if aspirin['success']:
        print(f"  CID: {aspirin['cid']}")
        print(f"  Formula: {aspirin['molecular_formula']}")
        print(f"  Weight: {aspirin['molecular_weight']}")
        print(f"  IUPAC: {aspirin['iupac_name'][:60]}...")
    else:
        print(f"  ERROR: {aspirin['error']}")
    
    # Test synonyms
    print("\n[TEST 2] Synonyms for Aspirin")
    synonyms = get_compound_synonyms('aspirin', max_synonyms=10)
    if synonyms['success']:
        print(f"  Found {synonyms['count']} synonyms:")
        for syn in synonyms['synonyms'][:5]:
            print(f"    - {syn}")
    else:
        print(f"  ERROR: {synonyms['error']}")
    
    # Test bioactivity
    print("\n[TEST 3] Bioactivity for Aspirin (CID 2244)")
    bioactivity = get_bioactivity(2244)
    if bioactivity['success']:
        if bioactivity.get('bioactivity_available'):
            summary = bioactivity['bioactivity_summary']
            print(f"  Total assays: {summary['total_assays']}")
            print(f"  Active: {summary['active_assays']}")
            print(f"  Inactive: {summary['inactive_assays']}")
        else:
            print(f"  {bioactivity.get('message', 'No bioactivity data')}")
    else:
        print(f"  ERROR: {bioactivity['error']}")
    
    print("\n" + "=" * 70)
    print("Module ready for QuantClaw Data integration")
    print("=" * 70)
