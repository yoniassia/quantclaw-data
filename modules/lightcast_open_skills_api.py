#!/usr/bin/env python3
"""
Lightcast Open Skills API — Labor Market Skills Taxonomy

Lightcast (formerly EMSI/Burning Glass) provides comprehensive labor market data
including skills taxonomy, job postings analysis, and workforce trends.

Useful for:
- Labor market health indicators (job market strength/weakness)
- Sector rotation signals (growing vs declining skill demands)
- Wage growth tracking (skill premium trends)
- Macro economic indicators (employment trends)

Source: https://lightcast.io/open-skills
Category: Labor & Demographics
API Docs: https://api.lightcast.io/docs
Free tier: Requires API key (check LIGHTCAST_API_KEY env var)
Update frequency: Real-time job postings, monthly taxonomy updates

Author: QuantClaw Data NightBuilder
Phase: 106
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Lightcast API Configuration
LIGHTCAST_BASE_URL = "https://api.lightcast.io"
LIGHTCAST_API_KEY = os.environ.get("LIGHTCAST_API_KEY", "")
LIGHTCAST_CLIENT_ID = os.environ.get("LIGHTCAST_CLIENT_ID", "")
LIGHTCAST_CLIENT_SECRET = os.environ.get("LIGHTCAST_CLIENT_SECRET", "")

# Cache for OAuth token
_token_cache = {
    'access_token': None,
    'expires_at': None
}


def get_auth_token() -> Optional[str]:
    """
    Get OAuth2 access token for Lightcast API
    Caches token until expiration
    
    Returns:
        Access token string or None if authentication fails
    """
    global _token_cache
    
    # Check if we have valid credentials
    if not LIGHTCAST_CLIENT_ID or not LIGHTCAST_CLIENT_SECRET:
        return None
    
    # Check cache
    if _token_cache['access_token'] and _token_cache['expires_at']:
        if datetime.now() < _token_cache['expires_at']:
            return _token_cache['access_token']
    
    # Get new token
    try:
        auth_url = f"{LIGHTCAST_BASE_URL}/auth/connect/token"
        data = {
            'client_id': LIGHTCAST_CLIENT_ID,
            'client_secret': LIGHTCAST_CLIENT_SECRET,
            'grant_type': 'client_credentials',
            'scope': 'emsi_open'
        }
        
        response = requests.post(auth_url, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        _token_cache['access_token'] = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)
        _token_cache['expires_at'] = datetime.now() + timedelta(seconds=expires_in - 60)
        
        return _token_cache['access_token']
    
    except Exception as e:
        return None


def _make_request(endpoint: str, params: Optional[Dict] = None, method: str = 'GET') -> Dict:
    """
    Helper function to make authenticated requests to Lightcast API
    
    Args:
        endpoint: API endpoint path (e.g., '/skills')
        params: Query parameters
        method: HTTP method
    
    Returns:
        Dict with success flag and data or error
    """
    # Check for API key
    token = get_auth_token()
    if not token:
        return {
            'success': False,
            'error': 'Missing Lightcast credentials. Set LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET env vars.',
            'requires_auth': True
        }
    
    try:
        url = f"{LIGHTCAST_BASE_URL}{endpoint}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params or {}, timeout=15)
        else:
            response = requests.post(url, headers=headers, json=params or {}, timeout=15)
        
        response.raise_for_status()
        
        return {
            'success': True,
            'data': response.json(),
            'status_code': response.status_code
        }
    
    except requests.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP {e.response.status_code}: {e.response.text}',
            'status_code': e.response.status_code if hasattr(e, 'response') else None
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


def list_skills(query: Optional[str] = None, limit: int = 25) -> Dict:
    """
    List or search skills in the Lightcast taxonomy
    
    Args:
        query: Optional search term to filter skills (e.g., 'python', 'data analysis')
        limit: Maximum number of results (default 25, max 100)
    
    Returns:
        Dict with list of skills matching query
    
    Example:
        >>> result = list_skills(query='python', limit=10)
        >>> for skill in result.get('skills', []):
        ...     print(f"{skill['name']} - {skill['id']}")
    """
    params = {'limit': min(limit, 100)}
    
    if query:
        params['q'] = query
    
    result = _make_request('/skills', params=params)
    
    if not result['success']:
        return result
    
    data = result['data']
    
    # Format skills for easy consumption
    skills = []
    if isinstance(data, dict) and 'data' in data:
        for skill in data.get('data', []):
            skills.append({
                'id': skill.get('id'),
                'name': skill.get('name'),
                'type': skill.get('type', {}).get('name') if isinstance(skill.get('type'), dict) else skill.get('type'),
                'category': skill.get('category', {}).get('name') if isinstance(skill.get('category'), dict) else None
            })
    
    return {
        'success': True,
        'skills': skills,
        'count': len(skills),
        'query': query,
        'timestamp': datetime.now().isoformat()
    }


def get_skill_details(skill_id: str) -> Dict:
    """
    Get detailed information about a specific skill
    
    Args:
        skill_id: Lightcast skill identifier (e.g., 'KS120076FGP5WGWYMP0F')
    
    Returns:
        Dict with skill details including related skills, demand trends, descriptions
    
    Example:
        >>> details = get_skill_details('KS120076FGP5WGWYMP0F')
        >>> print(f"Skill: {details['skill']['name']}")
        >>> print(f"Category: {details['skill']['category']}")
    """
    if not skill_id:
        return {
            'success': False,
            'error': 'skill_id is required'
        }
    
    result = _make_request(f'/skills/{skill_id}')
    
    if not result['success']:
        return result
    
    data = result['data']
    
    # Extract key fields
    skill_info = {
        'id': data.get('id'),
        'name': data.get('name'),
        'description': data.get('description'),
        'type': data.get('type', {}).get('name') if isinstance(data.get('type'), dict) else data.get('type'),
        'category': data.get('category', {}).get('name') if isinstance(data.get('category'), dict) else None,
        'subcategory': data.get('subcategory', {}).get('name') if isinstance(data.get('subcategory'), dict) else None,
        'tags': data.get('tags', []),
        'infoUrl': data.get('infoUrl')
    }
    
    return {
        'success': True,
        'skill': skill_info,
        'raw_data': data,
        'timestamp': datetime.now().isoformat()
    }


def get_related_skills(skill_id: str, limit: int = 10) -> Dict:
    """
    Get skills related to a given skill
    
    Args:
        skill_id: Lightcast skill identifier
        limit: Maximum number of related skills (default 10)
    
    Returns:
        Dict with list of related skills and relationship types
    
    Example:
        >>> related = get_related_skills('KS120076FGP5WGWYMP0F', limit=5)
        >>> for skill in related.get('related_skills', []):
        ...     print(f"{skill['name']} (similarity: {skill.get('similarity', 'N/A')})")
    """
    if not skill_id:
        return {
            'success': False,
            'error': 'skill_id is required'
        }
    
    result = _make_request(f'/skills/{skill_id}/related', params={'limit': limit})
    
    if not result['success']:
        return result
    
    data = result['data']
    
    # Format related skills
    related = []
    if isinstance(data, dict) and 'data' in data:
        for skill in data.get('data', []):
            related.append({
                'id': skill.get('id'),
                'name': skill.get('name'),
                'type': skill.get('type', {}).get('name') if isinstance(skill.get('type'), dict) else skill.get('type'),
                'similarity': skill.get('similarity')
            })
    
    return {
        'success': True,
        'skill_id': skill_id,
        'related_skills': related,
        'count': len(related),
        'timestamp': datetime.now().isoformat()
    }


def get_skill_categories() -> Dict:
    """
    List all skill categories in the taxonomy
    
    Returns:
        Dict with hierarchical list of categories and subcategories
    
    Example:
        >>> categories = get_skill_categories()
        >>> for cat in categories.get('categories', []):
        ...     print(f"{cat['name']}: {cat.get('skill_count', 0)} skills")
    """
    result = _make_request('/taxonomies/skills')
    
    if not result['success']:
        return result
    
    data = result['data']
    
    # Extract categories
    categories = []
    if isinstance(data, dict):
        # Try to find categories in the response structure
        cat_data = data.get('categories') or data.get('data') or []
        for cat in cat_data:
            categories.append({
                'id': cat.get('id'),
                'name': cat.get('name'),
                'skill_count': cat.get('skillCount') or cat.get('skill_count'),
                'subcategories': cat.get('subcategories', [])
            })
    
    return {
        'success': True,
        'categories': categories,
        'count': len(categories),
        'timestamp': datetime.now().isoformat()
    }


def search_skills_by_occupation(occupation: str, limit: int = 20) -> Dict:
    """
    Search for skills associated with a given occupation
    
    Args:
        occupation: Occupation name or description (e.g., 'software engineer', 'data analyst')
        limit: Maximum number of skills (default 20)
    
    Returns:
        Dict with skills commonly required for the occupation
    
    Example:
        >>> skills = search_skills_by_occupation('data scientist', limit=15)
        >>> for skill in skills.get('skills', []):
        ...     print(f"- {skill['name']}")
    """
    if not occupation:
        return {
            'success': False,
            'error': 'occupation parameter is required'
        }
    
    # First, search for matching occupations
    occ_result = _make_request('/titles', params={'q': occupation, 'limit': 5})
    
    if not occ_result['success']:
        return occ_result
    
    occ_data = occ_result['data']
    
    # Get the first matching occupation's skills
    occupations = occ_data.get('data', []) if isinstance(occ_data, dict) else []
    
    if not occupations:
        return {
            'success': False,
            'error': f'No occupations found matching "{occupation}"'
        }
    
    # Get skills for the top matching occupation
    occ_id = occupations[0].get('id')
    skills_result = _make_request(f'/titles/{occ_id}/skills', params={'limit': limit})
    
    if not skills_result['success']:
        return skills_result
    
    skills_data = skills_result['data']
    
    # Format skills
    skills = []
    if isinstance(skills_data, dict) and 'data' in skills_data:
        for skill in skills_data.get('data', []):
            skills.append({
                'id': skill.get('id'),
                'name': skill.get('name'),
                'importance': skill.get('importance'),
                'category': skill.get('category', {}).get('name') if isinstance(skill.get('category'), dict) else None
            })
    
    return {
        'success': True,
        'occupation': occupations[0].get('name'),
        'occupation_id': occ_id,
        'skills': skills,
        'count': len(skills),
        'timestamp': datetime.now().isoformat()
    }


def get_skill_trends(skill_name: str, months: int = 12) -> Dict:
    """
    Get trending data for a skill (demand growth, popularity)
    
    Args:
        skill_name: Skill name to analyze (e.g., 'Python', 'Machine Learning')
        months: Number of months to look back (default 12)
    
    Returns:
        Dict with skill trend data including growth rates and demand indicators
    
    Example:
        >>> trends = get_skill_trends('Python', months=24)
        >>> print(f"Growth: {trends.get('growth_rate', 'N/A')}%")
    """
    if not skill_name:
        return {
            'success': False,
            'error': 'skill_name parameter is required'
        }
    
    # First, find the skill ID
    search_result = list_skills(query=skill_name, limit=5)
    
    if not search_result['success']:
        return search_result
    
    skills = search_result.get('skills', [])
    if not skills:
        return {
            'success': False,
            'error': f'No skills found matching "{skill_name}"'
        }
    
    skill_id = skills[0]['id']
    skill_exact_name = skills[0]['name']
    
    # Try to get postings timeline data
    timeline_result = _make_request(f'/skills/{skill_id}/postings/timeline', 
                                    params={'months': months})
    
    if not timeline_result['success']:
        # Fallback: just return basic skill info
        return {
            'success': True,
            'skill_name': skill_exact_name,
            'skill_id': skill_id,
            'trends_available': False,
            'message': 'Trend data requires additional API access',
            'timestamp': datetime.now().isoformat()
        }
    
    timeline_data = timeline_result['data']
    
    # Calculate growth rate if we have timeline data
    postings = timeline_data.get('data', []) if isinstance(timeline_data, dict) else []
    
    growth_rate = None
    if len(postings) >= 2:
        earliest = postings[0].get('unique_postings', 0)
        latest = postings[-1].get('unique_postings', 0)
        if earliest > 0:
            growth_rate = ((latest - earliest) / earliest) * 100
    
    return {
        'success': True,
        'skill_name': skill_exact_name,
        'skill_id': skill_id,
        'growth_rate': round(growth_rate, 2) if growth_rate is not None else None,
        'timeline': postings,
        'months_analyzed': months,
        'timestamp': datetime.now().isoformat()
    }


def get_labor_market_snapshot() -> Dict:
    """
    Get snapshot of labor market indicators from skills data
    Useful for macro trading signals
    
    Returns:
        Dict with top trending skills, fastest growing categories, market health indicators
    """
    # Get top skills overall
    top_skills = list_skills(limit=50)
    
    if not top_skills['success']:
        return top_skills
    
    # Analyze top categories
    categories = get_skill_categories()
    
    snapshot = {
        'top_skills_count': top_skills.get('count', 0),
        'sample_top_skills': [s['name'] for s in top_skills.get('skills', [])[:10]],
        'categories_count': categories.get('count', 0) if categories['success'] else 0,
        'data_source': 'Lightcast Open Skills API',
        'market_health': 'Active' if top_skills.get('count', 0) > 0 else 'Unknown'
    }
    
    return {
        'success': True,
        'snapshot': snapshot,
        'timestamp': datetime.now().isoformat()
    }


def check_auth_status() -> Dict:
    """
    Check if Lightcast API credentials are configured
    
    Returns:
        Dict with authentication status and instructions
    """
    has_client_id = bool(LIGHTCAST_CLIENT_ID)
    has_client_secret = bool(LIGHTCAST_CLIENT_SECRET)
    
    if has_client_id and has_client_secret:
        # Try to get token
        token = get_auth_token()
        if token:
            return {
                'success': True,
                'authenticated': True,
                'message': 'Lightcast API credentials configured and valid'
            }
        else:
            return {
                'success': False,
                'authenticated': False,
                'error': 'Credentials configured but authentication failed',
                'instructions': 'Check LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET values'
            }
    else:
        return {
            'success': False,
            'authenticated': False,
            'error': 'Missing Lightcast API credentials',
            'instructions': 'Set LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET in .env file',
            'signup_url': 'https://lightcast.io/open-skills'
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Lightcast Open Skills API - Labor Market Skills Data")
    print("=" * 60)
    
    # Check authentication
    auth_status = check_auth_status()
    print(f"\nAuthentication Status:")
    print(json.dumps(auth_status, indent=2))
    
    if not auth_status.get('authenticated'):
        print("\n⚠️  API credentials not configured.")
        print("To use this module, set environment variables:")
        print("  LIGHTCAST_CLIENT_ID=your_client_id")
        print("  LIGHTCAST_CLIENT_SECRET=your_client_secret")
        print(f"\nSign up at: {auth_status.get('signup_url', 'https://lightcast.io')}")
    else:
        print("\n✅ Credentials valid! Testing API...")
        
        # Test list_skills
        print("\n" + "-" * 60)
        print("Testing: list_skills(query='python', limit=5)")
        result = list_skills(query='python', limit=5)
        print(json.dumps(result, indent=2))
        
        # Test get_skill_categories
        print("\n" + "-" * 60)
        print("Testing: get_skill_categories()")
        result = get_skill_categories()
        print(json.dumps(result, indent=2)[:500] + "...")
