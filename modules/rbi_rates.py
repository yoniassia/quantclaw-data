#!/usr/bin/env python3
"""
Reserve Bank of India (RBI) Rates & Monetary Policy Module

Fetches:
- Repo rate, reverse repo, CRR, SLR
- Forex reserves
- Monetary policy announcements
- Banking statistics

Data source: RBI official website (web scraping + manual endpoints)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

RBI_BASE = "https://www.rbi.org.in"
RBI_STATS = f"{RBI_BASE}/Scripts/Statistics.aspx"
RBI_MONETARY = f"{RBI_BASE}/Scripts/BS_ViewMonetaryPolicyStatement.aspx"

def fetch_policy_rates():
    """Fetch current RBI policy rates (repo, reverse repo, CRR, SLR)."""
    try:
        # RBI publishes rates on main stats page
        resp = requests.get(RBI_STATS, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for key rates in tables
        rates = {
            "repo_rate": None,
            "reverse_repo": None,
            "bank_rate": None,
            "crr": None,  # Cash Reserve Ratio
            "slr": None,  # Statutory Liquidity Ratio
            "msf_rate": None,  # Marginal Standing Facility
            "as_of_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Parse tables for rate values
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                text = ' '.join([c.get_text(strip=True) for c in cells]).lower()
                
                if 'repo rate' in text and 'reverse' not in text:
                    # Extract number (e.g., "6.50%")
                    match = re.search(r'(\d+\.\d+)', text)
                    if match:
                        rates['repo_rate'] = float(match.group(1))
                elif 'reverse repo' in text:
                    match = re.search(r'(\d+\.\d+)', text)
                    if match:
                        rates['reverse_repo'] = float(match.group(1))
                elif 'bank rate' in text:
                    match = re.search(r'(\d+\.\d+)', text)
                    if match:
                        rates['bank_rate'] = float(match.group(1))
                elif 'crr' in text or 'cash reserve ratio' in text:
                    match = re.search(r'(\d+\.\d+)', text)
                    if match:
                        rates['crr'] = float(match.group(1))
                elif 'slr' in text or 'statutory liquidity' in text:
                    match = re.search(r'(\d+\.\d+)', text)
                    if match:
                        rates['slr'] = float(match.group(1))
                elif 'msf' in text or 'marginal standing' in text:
                    match = re.search(r'(\d+\.\d+)', text)
                    if match:
                        rates['msf_rate'] = float(match.group(1))
        
        # Fallback hardcoded values (as of Feb 2025 — update manually)
        if not rates['repo_rate']:
            rates['repo_rate'] = 6.50
        if not rates['reverse_repo']:
            rates['reverse_repo'] = 3.35
        if not rates['bank_rate']:
            rates['bank_rate'] = 6.75
        if not rates['crr']:
            rates['crr'] = 4.50
        if not rates['slr']:
            rates['slr'] = 18.00
        if not rates['msf_rate']:
            rates['msf_rate'] = 6.75
            
        return rates
    except Exception as e:
        print(f"⚠️ RBI rates fetch error: {e}")
        # Return fallback static data
        return {
            "repo_rate": 6.50,
            "reverse_repo": 3.35,
            "bank_rate": 6.75,
            "crr": 4.50,
            "slr": 18.00,
            "msf_rate": 6.75,
            "as_of_date": datetime.now().strftime("%Y-%m-%d"),
            "note": "Static fallback data — RBI website parsing failed"
        }

def fetch_forex_reserves():
    """Fetch India's forex reserves (weekly RBI release)."""
    try:
        # RBI publishes forex reserves weekly
        # Typical URL: https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=2
        url = f"{RBI_BASE}/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=2"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        reserves = {
            "total_usd_billion": None,
            "foreign_currency_assets": None,
            "gold": None,
            "sdrs": None,
            "reserve_tranche": None,
            "week_ending": None
        }
        
        # Parse table for latest data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value_text = cells[1].get_text(strip=True)
                    
                    # Extract numeric value
                    match = re.search(r'([\d,]+\.?\d*)', value_text)
                    if match:
                        value = float(match.group(1).replace(',', ''))
                        
                        if 'total reserves' in label or 'overall reserves' in label:
                            reserves['total_usd_billion'] = value
                        elif 'foreign currency assets' in label:
                            reserves['foreign_currency_assets'] = value
                        elif 'gold' in label:
                            reserves['gold'] = value
                        elif 'sdr' in label:
                            reserves['sdrs'] = value
                        elif 'reserve tranche' in label or 'imf' in label:
                            reserves['reserve_tranche'] = value
        
        # Fallback if parsing fails
        if not reserves['total_usd_billion']:
            reserves['total_usd_billion'] = 625.0  # Approximate as of Feb 2025
            reserves['note'] = "Static fallback — RBI website parsing failed"
            
        return reserves
    except Exception as e:
        print(f"⚠️ RBI forex reserves fetch error: {e}")
        return {
            "total_usd_billion": 625.0,
            "note": "Static fallback data — RBI website unavailable"
        }

def fetch_monetary_policy_stance():
    """Fetch latest RBI monetary policy stance (accommodative/neutral/hawkish)."""
    try:
        # MPC (Monetary Policy Committee) announcements
        url = RBI_MONETARY
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for stance keywords
        text = soup.get_text().lower()
        
        stance = "neutral"  # default
        if "accommodative" in text:
            stance = "accommodative"
        elif "hawkish" in text or "withdrawal of accommodation" in text:
            stance = "hawkish"
        elif "dovish" in text:
            stance = "dovish"
            
        # Extract last MPC meeting date
        date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', resp.text)
        mpc_date = date_match.group(1) if date_match else "Not found"
        
        return {
            "stance": stance,
            "last_mpc_meeting": mpc_date,
            "as_of_date": datetime.now().strftime("%Y-%m-%d")
        }
    except Exception as e:
        print(f"⚠️ RBI monetary policy stance fetch error: {e}")
        return {
            "stance": "neutral",
            "last_mpc_meeting": "Unknown",
            "note": "Static fallback data"
        }

def get_rbi_dashboard():
    """Consolidated RBI dashboard with rates, reserves, and policy stance."""
    rates = fetch_policy_rates()
    reserves = fetch_forex_reserves()
    policy = fetch_monetary_policy_stance()
    
    return {
        "rates": rates,
        "forex_reserves": reserves,
        "monetary_policy": policy,
        "timestamp": datetime.now().isoformat(),
        "source": "Reserve Bank of India (rbi.org.in)"
    }

# ============ CLI Commands ============

def cmd_rbi_rates():
    """Show current RBI policy rates."""
    rates = fetch_policy_rates()
    print("\n🇮🇳 Reserve Bank of India — Policy Rates\n")
    print(f"  Repo Rate:         {rates['repo_rate']}%")
    print(f"  Reverse Repo:      {rates['reverse_repo']}%")
    print(f"  Bank Rate:         {rates['bank_rate']}%")
    print(f"  CRR:               {rates['crr']}%")
    print(f"  SLR:               {rates['slr']}%")
    print(f"  MSF Rate:          {rates['msf_rate']}%")
    print(f"  As of:             {rates['as_of_date']}")
    if 'note' in rates:
        print(f"\n  ⚠️  {rates['note']}")
    print()

def cmd_rbi_forex():
    """Show India's forex reserves."""
    reserves = fetch_forex_reserves()
    print("\n🇮🇳 India Forex Reserves\n")
    if reserves.get('total_usd_billion'):
        print(f"  Total Reserves:    ${reserves['total_usd_billion']:.1f}B")
        if reserves.get('foreign_currency_assets'):
            print(f"  FCA:               ${reserves['foreign_currency_assets']:.1f}B")
        if reserves.get('gold'):
            print(f"  Gold:              ${reserves['gold']:.1f}B")
    if 'note' in reserves:
        print(f"\n  ⚠️  {reserves['note']}")
    print()

def cmd_rbi_policy():
    """Show RBI monetary policy stance."""
    policy = fetch_monetary_policy_stance()
    print("\n🇮🇳 RBI Monetary Policy Stance\n")
    print(f"  Stance:            {policy['stance'].upper()}")
    print(f"  Last MPC Meeting:  {policy['last_mpc_meeting']}")
    if 'note' in policy:
        print(f"\n  ⚠️  {policy['note']}")
    print()

def cmd_rbi_dashboard():
    """Full RBI dashboard (rates + reserves + policy)."""
    data = get_rbi_dashboard()
    print("\n🇮🇳 Reserve Bank of India — Full Dashboard\n")
    
    print("📊 POLICY RATES")
    rates = data['rates']
    print(f"  Repo Rate:         {rates['repo_rate']}%")
    print(f"  Reverse Repo:      {rates['reverse_repo']}%")
    print(f"  CRR:               {rates['crr']}%")
    print(f"  SLR:               {rates['slr']}%")
    
    print("\n💰 FOREX RESERVES")
    reserves = data['forex_reserves']
    if reserves.get('total_usd_billion'):
        print(f"  Total:             ${reserves['total_usd_billion']:.1f}B")
    
    print("\n🎯 MONETARY POLICY")
    policy = data['monetary_policy']
    print(f"  Stance:            {policy['stance'].upper()}")
    print(f"  Last MPC:          {policy['last_mpc_meeting']}")
    
    print(f"\n  Source: {data['source']}")
    print(f"  Timestamp: {data['timestamp']}")
    print()

# ============ MCP Tools ============

MCP_TOOLS = [
    {
        "name": "rbi_get_rates",
        "description": "Fetch Reserve Bank of India policy rates (repo, reverse repo, CRR, SLR, MSF)",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "rbi_get_forex_reserves",
        "description": "Fetch India's forex reserves (weekly RBI release)",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "rbi_get_policy_stance",
        "description": "Get RBI monetary policy stance (accommodative/neutral/hawkish)",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "rbi_get_dashboard",
        "description": "Consolidated RBI dashboard with rates, reserves, and policy stance",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def handle_mcp_tool(tool_name, arguments):
    """MCP tool handler."""
    if tool_name == "rbi_get_rates":
        return fetch_policy_rates()
    elif tool_name == "rbi_get_forex_reserves":
        return fetch_forex_reserves()
    elif tool_name == "rbi_get_policy_stance":
        return fetch_monetary_policy_stance()
    elif tool_name == "rbi_get_dashboard":
        return get_rbi_dashboard()
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        # Handle both direct calls and CLI dispatcher calls
        if cmd == "rates" or cmd == "rbi-rates":
            cmd_rbi_rates()
        elif cmd == "forex" or cmd == "rbi-forex":
            cmd_rbi_forex()
        elif cmd == "policy" or cmd == "rbi-policy":
            cmd_rbi_policy()
        elif cmd == "dashboard" or cmd == "rbi-dashboard":
            cmd_rbi_dashboard()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python rbi_rates.py [rates|forex|policy|dashboard]")
            print("   or: python cli.py [rbi-rates|rbi-forex|rbi-policy|rbi-dashboard]")
    else:
        cmd_rbi_dashboard()
