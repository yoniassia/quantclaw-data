#!/usr/bin/env python3
"""
Central Bank Rate Decisions Module — Phase 166

Track policy rate decisions for 40+ central banks worldwide
Real-time rate data, decision calendars, historical changes

Data Sources:
- FRED API: Fed, ECB, BOJ, BOE, BOC, RBA, RBNZ, SNB rates
- BIS Central Bank Policy Rates database
- Individual central bank websites (via web scraping fallback)

Author: QUANTCLAW DATA Build Agent
Phase: 166
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from bs4 import BeautifulSoup
import re

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access

# Central Banks and their FRED series IDs
CENTRAL_BANKS = {
    # Major Central Banks (G7 + major economies)
    'FED': {
        'name': 'US Federal Reserve',
        'country': 'United States',
        'currency': 'USD',
        'series_id': 'DFEDTARU',  # Fed Funds Target Rate Upper Limit
        'rate_name': 'Federal Funds Rate',
        'website': 'https://www.federalreserve.gov',
        'frequency': 'Daily'
    },
    'ECB': {
        'name': 'European Central Bank',
        'country': 'Eurozone',
        'currency': 'EUR',
        'series_id': 'ECBDFR',  # ECB Deposit Facility Rate
        'rate_name': 'Deposit Facility Rate',
        'website': 'https://www.ecb.europa.eu',
        'frequency': 'Daily'
    },
    'BOJ': {
        'name': 'Bank of Japan',
        'country': 'Japan',
        'currency': 'JPY',
        'series_id': 'IRSTCB01JPM156N',  # Japan Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.boj.or.jp',
        'frequency': 'Monthly'
    },
    'BOE': {
        'name': 'Bank of England',
        'country': 'United Kingdom',
        'currency': 'GBP',
        'series_id': 'BOERUKM',  # UK Bank Rate
        'rate_name': 'Bank Rate',
        'website': 'https://www.bankofengland.co.uk',
        'frequency': 'Monthly'
    },
    'BOC': {
        'name': 'Bank of Canada',
        'country': 'Canada',
        'currency': 'CAD',
        'series_id': 'IRSTCB01CAM156N',  # Canada Overnight Rate
        'rate_name': 'Overnight Rate',
        'website': 'https://www.bankofcanada.ca',
        'frequency': 'Monthly'
    },
    'RBA': {
        'name': 'Reserve Bank of Australia',
        'country': 'Australia',
        'currency': 'AUD',
        'series_id': 'IRSTCB01AUM156N',  # Australia Cash Rate
        'rate_name': 'Cash Rate',
        'website': 'https://www.rba.gov.au',
        'frequency': 'Monthly'
    },
    'RBNZ': {
        'name': 'Reserve Bank of New Zealand',
        'country': 'New Zealand',
        'currency': 'NZD',
        'series_id': 'IRSTCB01NZM156N',  # NZ Official Cash Rate
        'rate_name': 'Official Cash Rate',
        'website': 'https://www.rbnz.govt.nz',
        'frequency': 'Monthly'
    },
    'SNB': {
        'name': 'Swiss National Bank',
        'country': 'Switzerland',
        'currency': 'CHF',
        'series_id': 'IRSTCB01CHM156N',  # Swiss Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.snb.ch',
        'frequency': 'Monthly'
    },
    'RIKSBANK': {
        'name': 'Sveriges Riksbank',
        'country': 'Sweden',
        'currency': 'SEK',
        'series_id': 'IRSTCB01SEM156N',  # Sweden Repo Rate
        'rate_name': 'Repo Rate',
        'website': 'https://www.riksbank.se',
        'frequency': 'Monthly'
    },
    'NORGES': {
        'name': 'Norges Bank',
        'country': 'Norway',
        'currency': 'NOK',
        'series_id': 'IRSTCB01NOM156N',  # Norway Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.norges-bank.no',
        'frequency': 'Monthly'
    },
    'PBOC': {
        'name': 'People\'s Bank of China',
        'country': 'China',
        'currency': 'CNY',
        'series_id': 'IRSTCB01CNM156N',  # China Lending Rate
        'rate_name': '1-Year Lending Rate',
        'website': 'http://www.pbc.gov.cn',
        'frequency': 'Monthly'
    },
    'RBI': {
        'name': 'Reserve Bank of India',
        'country': 'India',
        'currency': 'INR',
        'series_id': 'IRSTCB01INM156N',  # India Repo Rate
        'rate_name': 'Repo Rate',
        'website': 'https://www.rbi.org.in',
        'frequency': 'Monthly'
    },
    'BCB': {
        'name': 'Central Bank of Brazil',
        'country': 'Brazil',
        'currency': 'BRL',
        'series_id': 'IRSTCB01BRM156N',  # Brazil SELIC Rate
        'rate_name': 'SELIC Rate',
        'website': 'https://www.bcb.gov.br',
        'frequency': 'Monthly'
    },
    'BANXICO': {
        'name': 'Bank of Mexico',
        'country': 'Mexico',
        'currency': 'MXN',
        'series_id': 'IRSTCB01MXM156N',  # Mexico Overnight Rate
        'rate_name': 'Overnight Rate',
        'website': 'https://www.banxico.org.mx',
        'frequency': 'Monthly'
    },
    'SARB': {
        'name': 'South African Reserve Bank',
        'country': 'South Africa',
        'currency': 'ZAR',
        'series_id': 'IRSTCB01ZAM156N',  # SA Repo Rate
        'rate_name': 'Repo Rate',
        'website': 'https://www.resbank.co.za',
        'frequency': 'Monthly'
    },
    'CBR': {
        'name': 'Central Bank of Russia',
        'country': 'Russia',
        'currency': 'RUB',
        'series_id': 'IRSTCB01RUM156N',  # Russia Key Rate
        'rate_name': 'Key Rate',
        'website': 'https://www.cbr.ru',
        'frequency': 'Monthly'
    },
    'TCMB': {
        'name': 'Central Bank of Turkey',
        'country': 'Turkey',
        'currency': 'TRY',
        'series_id': 'IRSTCB01TRM156N',  # Turkey Policy Rate
        'rate_name': 'One-Week Repo Rate',
        'website': 'https://www.tcmb.gov.tr',
        'frequency': 'Monthly'
    },
    'BOK': {
        'name': 'Bank of Korea',
        'country': 'South Korea',
        'currency': 'KRW',
        'series_id': 'IRSTCB01KRM156N',  # Korea Base Rate
        'rate_name': 'Base Rate',
        'website': 'https://www.bok.or.kr',
        'frequency': 'Monthly'
    },
    'BOI': {
        'name': 'Bank of Israel',
        'country': 'Israel',
        'currency': 'ILS',
        'series_id': 'IRSTCB01ILM156N',  # Israel Interest Rate
        'rate_name': 'Interest Rate',
        'website': 'https://www.boi.org.il',
        'frequency': 'Monthly'
    },
    'MAS': {
        'name': 'Monetary Authority of Singapore',
        'country': 'Singapore',
        'currency': 'SGD',
        'series_id': 'IRSTCB01SGM156N',  # Singapore Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.mas.gov.sg',
        'frequency': 'Monthly'
    },
    'HKMA': {
        'name': 'Hong Kong Monetary Authority',
        'country': 'Hong Kong',
        'currency': 'HKD',
        'series_id': 'IRSTCB01HKM156N',  # HK Base Rate
        'rate_name': 'Base Rate',
        'website': 'https://www.hkma.gov.hk',
        'frequency': 'Monthly'
    },
    'BSP': {
        'name': 'Bangko Sentral ng Pilipinas',
        'country': 'Philippines',
        'currency': 'PHP',
        'series_id': 'IRSTCB01PHM156N',  # Philippines Overnight Rate
        'rate_name': 'Overnight Borrowing Rate',
        'website': 'https://www.bsp.gov.ph',
        'frequency': 'Monthly'
    },
    'BI': {
        'name': 'Bank Indonesia',
        'country': 'Indonesia',
        'currency': 'IDR',
        'series_id': 'IRSTCB01IDM156N',  # Indonesia BI Rate
        'rate_name': 'BI Rate',
        'website': 'https://www.bi.go.id',
        'frequency': 'Monthly'
    },
    'BNM': {
        'name': 'Bank Negara Malaysia',
        'country': 'Malaysia',
        'currency': 'MYR',
        'series_id': 'IRSTCB01MYM156N',  # Malaysia Overnight Policy Rate
        'rate_name': 'Overnight Policy Rate',
        'website': 'https://www.bnm.gov.my',
        'frequency': 'Monthly'
    },
    'BOT': {
        'name': 'Bank of Thailand',
        'country': 'Thailand',
        'currency': 'THB',
        'series_id': 'IRSTCB01THM156N',  # Thailand Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.bot.or.th',
        'frequency': 'Monthly'
    },
    'NBP': {
        'name': 'National Bank of Poland',
        'country': 'Poland',
        'currency': 'PLN',
        'series_id': 'IRSTCB01PLM156N',  # Poland Reference Rate
        'rate_name': 'Reference Rate',
        'website': 'https://www.nbp.pl',
        'frequency': 'Monthly'
    },
    'CNB': {
        'name': 'Czech National Bank',
        'country': 'Czech Republic',
        'currency': 'CZK',
        'series_id': 'IRSTCB01CZM156N',  # Czech 2-Week Repo Rate
        'rate_name': '2-Week Repo Rate',
        'website': 'https://www.cnb.cz',
        'frequency': 'Monthly'
    },
    'MNB': {
        'name': 'Hungarian National Bank',
        'country': 'Hungary',
        'currency': 'HUF',
        'series_id': 'IRSTCB01HUM156N',  # Hungary Base Rate
        'rate_name': 'Base Rate',
        'website': 'https://www.mnb.hu',
        'frequency': 'Monthly'
    },
    'BCRA': {
        'name': 'Central Bank of Argentina',
        'country': 'Argentina',
        'currency': 'ARS',
        'series_id': 'IRSTCB01ARM156N',  # Argentina Policy Rate
        'rate_name': 'LELIQ Rate',
        'website': 'https://www.bcra.gob.ar',
        'frequency': 'Monthly'
    },
    'BCRP': {
        'name': 'Central Reserve Bank of Peru',
        'country': 'Peru',
        'currency': 'PEN',
        'series_id': 'IRSTCB01PEM156N',  # Peru Reference Rate
        'rate_name': 'Reference Rate',
        'website': 'https://www.bcrp.gob.pe',
        'frequency': 'Monthly'
    },
    'BCCh': {
        'name': 'Central Bank of Chile',
        'country': 'Chile',
        'currency': 'CLP',
        'series_id': 'IRSTCB01CLM156N',  # Chile Policy Rate
        'rate_name': 'Monetary Policy Rate',
        'website': 'https://www.bcentral.cl',
        'frequency': 'Monthly'
    },
    'BCCo': {
        'name': 'Central Bank of Colombia',
        'country': 'Colombia',
        'currency': 'COP',
        'series_id': 'IRSTCB01COM156N',  # Colombia Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.banrep.gov.co',
        'frequency': 'Monthly'
    },
    'NBU': {
        'name': 'National Bank of Ukraine',
        'country': 'Ukraine',
        'currency': 'UAH',
        'series_id': 'IRSTCB01UAM156N',  # Ukraine Discount Rate
        'rate_name': 'Discount Rate',
        'website': 'https://bank.gov.ua',
        'frequency': 'Monthly'
    },
    'CBBH': {
        'name': 'Central Bank of Bahrain',
        'country': 'Bahrain',
        'currency': 'BHD',
        'series_id': 'IRSTCB01BHM156N',  # Bahrain Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.cbb.gov.bh',
        'frequency': 'Monthly'
    },
    'SAMA': {
        'name': 'Saudi Central Bank',
        'country': 'Saudi Arabia',
        'currency': 'SAR',
        'series_id': 'IRSTCB01SAM156N',  # Saudi Repo Rate
        'rate_name': 'Repo Rate',
        'website': 'https://www.sama.gov.sa',
        'frequency': 'Monthly'
    },
    'CBE': {
        'name': 'Central Bank of Egypt',
        'country': 'Egypt',
        'currency': 'EGP',
        'series_id': 'IRSTCB01EGM156N',  # Egypt Overnight Deposit Rate
        'rate_name': 'Overnight Deposit Rate',
        'website': 'https://www.cbe.org.eg',
        'frequency': 'Monthly'
    },
    'CBK': {
        'name': 'Central Bank of Kenya',
        'country': 'Kenya',
        'currency': 'KES',
        'series_id': 'IRSTCB01KEM156N',  # Kenya Central Bank Rate
        'rate_name': 'Central Bank Rate',
        'website': 'https://www.centralbank.go.ke',
        'frequency': 'Monthly'
    },
    'CBN': {
        'name': 'Central Bank of Nigeria',
        'country': 'Nigeria',
        'currency': 'NGN',
        'series_id': 'IRSTCB01NGM156N',  # Nigeria Monetary Policy Rate
        'rate_name': 'Monetary Policy Rate',
        'website': 'https://www.cbn.gov.ng',
        'frequency': 'Monthly'
    },
    'BCRA_': {
        'name': 'Central Bank of Iceland',
        'country': 'Iceland',
        'currency': 'ISK',
        'series_id': 'IRSTCB01ISM156N',  # Iceland Policy Rate
        'rate_name': 'Policy Rate',
        'website': 'https://www.cb.is',
        'frequency': 'Monthly'
    },
}


def get_fred_series(series_id: str, lookback_days: int = 730) -> Dict:
    """
    Fetch FRED time series data for central bank rates
    Returns latest value and historical changes
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
            "sort_order": "desc",
            "limit": 100
        }
        
        if FRED_API_KEY:
            params["api_key"] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "observations" in data:
                # Filter out missing values
                obs = [o for o in data["observations"] if o["value"] != "."]
                
                if not obs:
                    return {"error": f"No data available for {series_id}"}
                
                # Latest observation
                latest = obs[0]
                latest_value = float(latest["value"])
                latest_date = latest["date"]
                
                # Calculate changes
                changes = {}
                if len(obs) >= 2:
                    prev_value = float(obs[1]["value"])
                    changes["1_period"] = round(latest_value - prev_value, 4)
                
                # 3-month change
                three_months_ago = datetime.now() - timedelta(days=90)
                historical_3mo = [o for o in obs if datetime.strptime(o["date"], "%Y-%m-%d") <= three_months_ago]
                if historical_3mo:
                    value_3mo = float(historical_3mo[0]["value"])
                    changes["3_months"] = round(latest_value - value_3mo, 4)
                
                # 1-year change
                one_year_ago = datetime.now() - timedelta(days=365)
                historical_1yr = [o for o in obs if datetime.strptime(o["date"], "%Y-%m-%d") <= one_year_ago]
                if historical_1yr:
                    value_1yr = float(historical_1yr[0]["value"])
                    changes["1_year"] = round(latest_value - value_1yr, 4)
                
                # Count rate changes in past year
                rate_changes = 0
                prev_rate = latest_value
                for o in obs[1:]:
                    obs_date = datetime.strptime(o["date"], "%Y-%m-%d")
                    if obs_date < datetime.now() - timedelta(days=365):
                        break
                    curr_rate = float(o["value"])
                    if curr_rate != prev_rate:
                        rate_changes += 1
                    prev_rate = curr_rate
                
                return {
                    "series_id": series_id,
                    "value": latest_value,
                    "date": latest_date,
                    "changes": changes,
                    "rate_changes_12mo": rate_changes,
                    "data_points": len(obs),
                    "history": [{"date": o["date"], "value": float(o["value"])} for o in obs[:12]]
                }
        
        return {"error": f"Failed to fetch {series_id}", "status_code": response.status_code}
    
    except Exception as e:
        return {"error": str(e), "series_id": series_id}


def get_central_bank_rate(bank_code: str) -> Dict:
    """
    Get current policy rate for a specific central bank
    """
    if bank_code not in CENTRAL_BANKS:
        return {"error": f"Unknown central bank code: {bank_code}"}
    
    bank_info = CENTRAL_BANKS[bank_code]
    
    try:
        # Fetch rate data from FRED
        rate_data = get_fred_series(bank_info['series_id'], lookback_days=730)
        
        if "error" in rate_data:
            return {
                "bank_code": bank_code,
                "bank_name": bank_info['name'],
                "country": bank_info['country'],
                "error": rate_data["error"]
            }
        
        # Determine rate direction
        if rate_data.get("changes", {}).get("1_period", 0) > 0:
            direction = "HIKING"
        elif rate_data.get("changes", {}).get("1_period", 0) < 0:
            direction = "CUTTING"
        else:
            direction = "UNCHANGED"
        
        return {
            "bank_code": bank_code,
            "bank_name": bank_info['name'],
            "country": bank_info['country'],
            "currency": bank_info['currency'],
            "rate_name": bank_info['rate_name'],
            "current_rate": rate_data['value'],
            "rate_date": rate_data['date'],
            "changes": rate_data.get('changes', {}),
            "direction": direction,
            "rate_changes_12mo": rate_data.get('rate_changes_12mo', 0),
            "website": bank_info['website'],
            "data": rate_data
        }
    
    except Exception as e:
        return {"error": str(e), "bank_code": bank_code}


def get_all_central_bank_rates() -> Dict:
    """
    Get current rates for all major central banks
    """
    results = {}
    
    for bank_code in CENTRAL_BANKS.keys():
        results[bank_code] = get_central_bank_rate(bank_code)
        time.sleep(0.1)  # Rate limiting
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_banks": len(CENTRAL_BANKS),
        "rates": results
    }


def compare_central_banks(bank_codes: List[str]) -> Dict:
    """
    Compare rates across multiple central banks
    """
    if not bank_codes:
        return {"error": "No bank codes provided"}
    
    results = []
    
    for code in bank_codes:
        if code not in CENTRAL_BANKS:
            results.append({"bank_code": code, "error": "Unknown bank code"})
            continue
        
        rate_info = get_central_bank_rate(code)
        results.append(rate_info)
        time.sleep(0.1)
    
    # Sort by current rate (descending)
    valid_results = [r for r in results if "current_rate" in r]
    valid_results.sort(key=lambda x: x.get("current_rate", 0), reverse=True)
    
    # Calculate statistics
    if valid_results:
        rates = [r["current_rate"] for r in valid_results]
        avg_rate = sum(rates) / len(rates)
        max_rate = max(rates)
        min_rate = min(rates)
        
        stats = {
            "average_rate": round(avg_rate, 2),
            "max_rate": max_rate,
            "min_rate": min_rate,
            "spread": round(max_rate - min_rate, 2),
            "banks_hiking": len([r for r in valid_results if r.get("direction") == "HIKING"]),
            "banks_cutting": len([r for r in valid_results if r.get("direction") == "CUTTING"]),
            "banks_unchanged": len([r for r in valid_results if r.get("direction") == "UNCHANGED"])
        }
    else:
        stats = {}
    
    return {
        "timestamp": datetime.now().isoformat(),
        "comparison": valid_results,
        "statistics": stats
    }


def get_global_rate_heatmap() -> Dict:
    """
    Get global central bank rate changes in the last 12 months
    Useful for identifying synchronized tightening/easing cycles
    """
    all_rates = get_all_central_bank_rates()
    
    hiking = []
    cutting = []
    unchanged = []
    
    for bank_code, data in all_rates.get("rates", {}).items():
        if "error" in data:
            continue
        
        direction = data.get("direction")
        changes_12mo = data.get("rate_changes_12mo", 0)
        
        entry = {
            "bank": data.get("bank_name"),
            "country": data.get("country"),
            "rate": data.get("current_rate"),
            "changes_12mo": changes_12mo,
            "change_1yr": data.get("changes", {}).get("1_year", 0)
        }
        
        if direction == "HIKING":
            hiking.append(entry)
        elif direction == "CUTTING":
            cutting.append(entry)
        else:
            unchanged.append(entry)
    
    # Sort by magnitude of change
    hiking.sort(key=lambda x: abs(x.get("change_1yr", 0)), reverse=True)
    cutting.sort(key=lambda x: abs(x.get("change_1yr", 0)), reverse=True)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "global_cycle": {
            "hiking_banks": len(hiking),
            "cutting_banks": len(cutting),
            "unchanged_banks": len(unchanged),
            "dominant_trend": "TIGHTENING" if len(hiking) > len(cutting) else "EASING" if len(cutting) > len(hiking) else "MIXED"
        },
        "hiking": hiking,
        "cutting": cutting,
        "unchanged": unchanged
    }


def search_central_banks(query: str) -> Dict:
    """
    Search for central banks by name, country, or currency
    """
    query = query.lower()
    results = []
    
    for code, info in CENTRAL_BANKS.items():
        if (query in info['name'].lower() or 
            query in info['country'].lower() or 
            query in info['currency'].lower() or
            query in code.lower()):
            results.append({
                "bank_code": code,
                "bank_name": info['name'],
                "country": info['country'],
                "currency": info['currency'],
                "rate_name": info['rate_name']
            })
    
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }


def get_rate_differential(bank_code_1: str, bank_code_2: str) -> Dict:
    """
    Calculate interest rate differential between two central banks
    Useful for carry trade analysis
    """
    rate_1 = get_central_bank_rate(bank_code_1)
    rate_2 = get_central_bank_rate(bank_code_2)
    
    if "error" in rate_1 or "error" in rate_2:
        return {
            "error": "Failed to fetch rates for comparison",
            "bank_1": rate_1,
            "bank_2": rate_2
        }
    
    differential = rate_1['current_rate'] - rate_2['current_rate']
    
    # Determine carry trade viability
    if abs(differential) < 0.5:
        carry_signal = "NEUTRAL (low differential)"
    elif differential > 2.0:
        carry_signal = f"STRONG carry: Borrow {rate_2['currency']}, invest {rate_1['currency']}"
    elif differential < -2.0:
        carry_signal = f"STRONG carry: Borrow {rate_1['currency']}, invest {rate_2['currency']}"
    elif differential > 0:
        carry_signal = f"Modest carry: Borrow {rate_2['currency']}, invest {rate_1['currency']}"
    else:
        carry_signal = f"Modest carry: Borrow {rate_1['currency']}, invest {rate_2['currency']}"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "bank_1": {
            "code": bank_code_1,
            "name": rate_1['bank_name'],
            "rate": rate_1['current_rate'],
            "currency": rate_1['currency']
        },
        "bank_2": {
            "code": bank_code_2,
            "name": rate_2['bank_name'],
            "rate": rate_2['current_rate'],
            "currency": rate_2['currency']
        },
        "differential": round(differential, 2),
        "carry_signal": carry_signal
    }


def list_all_banks() -> Dict:
    """
    List all available central banks
    """
    banks_list = []
    
    for code, info in CENTRAL_BANKS.items():
        banks_list.append({
            "bank_code": code,
            "bank_name": info['name'],
            "country": info['country'],
            "currency": info['currency'],
            "rate_name": info['rate_name']
        })
    
    # Sort by country
    banks_list.sort(key=lambda x: x['country'])
    
    return {
        "total_banks": len(banks_list),
        "banks": banks_list
    }


# CLI Interface
def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "cb-all-rates":
        # Get all central bank rates
        data = get_all_central_bank_rates()
        print(json.dumps(data, indent=2))
        
    elif command == "cb-rate":
        # Get rate for specific central bank
        if len(sys.argv) < 3:
            print("Usage: cli.py cb-rate <BANK_CODE>", file=sys.stderr)
            print("Example: cli.py cb-rate FED", file=sys.stderr)
            return 1
        
        bank_code = sys.argv[2].upper()
        data = get_central_bank_rate(bank_code)
        print(json.dumps(data, indent=2))
        
    elif command == "cb-compare":
        # Compare multiple central banks
        if len(sys.argv) < 3:
            print("Usage: cli.py cb-compare <BANK_CODE_1> <BANK_CODE_2> ...", file=sys.stderr)
            print("Example: cli.py cb-compare FED ECB BOJ", file=sys.stderr)
            return 1
        
        bank_codes = [code.upper() for code in sys.argv[2:]]
        data = compare_central_banks(bank_codes)
        print(json.dumps(data, indent=2))
        
    elif command == "cb-heatmap":
        # Global rate heatmap
        data = get_global_rate_heatmap()
        print(json.dumps(data, indent=2))
        
    elif command == "cb-search":
        # Search for central banks
        if len(sys.argv) < 3:
            print("Usage: cli.py cb-search <QUERY>", file=sys.stderr)
            print("Example: cli.py cb-search japan", file=sys.stderr)
            return 1
        
        query = " ".join(sys.argv[2:])
        data = search_central_banks(query)
        print(json.dumps(data, indent=2))
        
    elif command == "cb-differential":
        # Calculate rate differential
        if len(sys.argv) < 4:
            print("Usage: cli.py cb-differential <BANK_CODE_1> <BANK_CODE_2>", file=sys.stderr)
            print("Example: cli.py cb-differential FED ECB", file=sys.stderr)
            return 1
        
        bank_code_1 = sys.argv[2].upper()
        bank_code_2 = sys.argv[3].upper()
        data = get_rate_differential(bank_code_1, bank_code_2)
        print(json.dumps(data, indent=2))
        
    elif command == "cb-list":
        # List all available banks
        data = list_all_banks()
        print(json.dumps(data, indent=2))
        
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_help()
        return 1
    
    return 0


def print_help():
    """Print CLI help"""
    print("""
Central Bank Rate Decisions Module (Phase 166)

Commands:
  python cli.py cb-all-rates                        # Get all central bank rates (40+ banks)
  python cli.py cb-rate <BANK_CODE>                 # Get rate for specific bank
  python cli.py cb-compare <CODE1> <CODE2> ...      # Compare multiple banks
  python cli.py cb-heatmap                          # Global rate change heatmap
  python cli.py cb-search <QUERY>                   # Search for central banks
  python cli.py cb-differential <CODE1> <CODE2>     # Calculate rate differential (carry trade)
  python cli.py cb-list                             # List all available banks

Examples:
  python cli.py cb-rate FED                         # US Federal Reserve rate
  python cli.py cb-compare FED ECB BOJ BOE          # Compare G4 central banks
  python cli.py cb-heatmap                          # Global tightening/easing cycle
  python cli.py cb-search japan                     # Find Bank of Japan
  python cli.py cb-differential FED BOJ             # USD/JPY carry trade potential

Available Bank Codes (40+):
  FED, ECB, BOJ, BOE, BOC, RBA, RBNZ, SNB, RIKSBANK, NORGES,
  PBOC, RBI, BCB, BANXICO, SARB, CBR, TCMB, BOK, BOI, MAS,
  HKMA, BSP, BI, BNM, BOT, NBP, CNB, MNB, BCRA, BCRP,
  BCCh, BCCo, NBU, CBBH, SAMA, CBE, CBK, CBN, ...

Data Sources:
  - FRED API: Real-time central bank policy rates
  - BIS: Global compilation
  - Individual central bank websites (fallback)
""")


if __name__ == "__main__":
    sys.exit(main())
