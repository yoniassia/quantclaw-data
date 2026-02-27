#!/usr/bin/env python3
"""
KOSTAT - Korean Statistical Information Service
GDP, CPI, employment, industrial production from South Korea
Uses FRED API for Korean economic data
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os


class KOSTATData:
    """Korean Statistical Information Service data via FRED"""
    
    def __init__(self):
        self.fred_key = os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        
    def _fetch_fred_series(self, series_id: str, limit: int = 24) -> Dict[str, Any]:
        """Fetch FRED series data"""
        if not self.fred_key:
            return {"error": "FRED_API_KEY not set"}
            
        params = {
            "series_id": series_id,
            "api_key": self.fred_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "observations" not in data:
                return {"error": "No data available"}
                
            obs = data["observations"]
            if not obs:
                return {"error": "Empty dataset"}
                
            return {"observations": obs, "series_id": series_id}
            
        except Exception as e:
            return {"error": str(e)}
            
    def get_gdp(self) -> Dict[str, Any]:
        """
        Get South Korea GDP
        Source: FRED series NAEXKP01KRQ657S (Real GDP, quarterly)
        """
        result = self._fetch_fred_series("NAEXKP01KRQ657S", 20)
        
        if "error" in result:
            return result
            
        obs = result["observations"]
        latest = obs[0]
        
        # Calculate YoY growth
        yoy_growth = None
        if len(obs) >= 5:  # Need 4 quarters back for YoY
            current_val = float(latest["value"])
            yoy_val = float(obs[4]["value"])
            yoy_growth = ((current_val / yoy_val) - 1) * 100
            
        return {
            "gdp_index": float(latest["value"]),
            "date": latest["date"],
            "period": "quarterly",
            "yoy_growth_pct": round(yoy_growth, 2) if yoy_growth else None,
            "series": result["series_id"],
            "history": [
                {"date": o["date"], "gdp": float(o["value"])} 
                for o in obs if o["value"] != "."
            ][:8]
        }
        
    def get_cpi(self) -> Dict[str, Any]:
        """
        Get South Korea CPI inflation
        Source: FRED series FPCPITOTLZGKOR (CPI YoY%)
        """
        result = self._fetch_fred_series("FPCPITOTLZGKOR", 24)
        
        if "error" in result:
            return result
            
        obs = result["observations"]
        latest = obs[0]
        
        # Calculate average inflation
        values = [float(o["value"]) for o in obs[:12] if o["value"] != "."]
        avg_12m = sum(values) / len(values) if values else None
        
        return {
            "cpi_yoy_pct": float(latest["value"]),
            "date": latest["date"],
            "avg_12m_pct": round(avg_12m, 2) if avg_12m else None,
            "series": result["series_id"],
            "history": [
                {"date": o["date"], "cpi_yoy": float(o["value"])} 
                for o in obs if o["value"] != "."
            ][:12]
        }
        
    def get_unemployment(self) -> Dict[str, Any]:
        """
        Get South Korea unemployment rate
        Source: FRED series LRUNTTTTKRM156S
        """
        result = self._fetch_fred_series("LRUNTTTTKRM156S", 24)
        
        if "error" in result:
            return result
            
        obs = result["observations"]
        latest = obs[0]
        
        # Calculate trend
        values = [float(o["value"]) for o in obs[:6] if o["value"] != "."]
        trend = "increasing" if len(values) >= 2 and values[0] > values[-1] else "decreasing"
        
        return {
            "unemployment_pct": float(latest["value"]),
            "date": latest["date"],
            "trend_6m": trend,
            "series": result["series_id"],
            "history": [
                {"date": o["date"], "unemployment": float(o["value"])} 
                for o in obs if o["value"] != "."
            ][:12]
        }
        
    def get_industrial_production(self) -> Dict[str, Any]:
        """
        Get South Korea industrial production index
        Source: FRED series KORPROINDMISMEI (Production index)
        """
        result = self._fetch_fred_series("KORPROINDMISMEI", 24)
        
        if "error" in result:
            return result
            
        obs = result["observations"]
        latest = obs[0]
        
        # Calculate YoY growth
        yoy_growth = None
        if len(obs) >= 13:
            current_val = float(latest["value"])
            yoy_val = float(obs[12]["value"])
            yoy_growth = ((current_val / yoy_val) - 1) * 100
            
        return {
            "production_index": float(latest["value"]),
            "date": latest["date"],
            "yoy_growth_pct": round(yoy_growth, 2) if yoy_growth else None,
            "series": result["series_id"],
            "history": [
                {"date": o["date"], "production": float(o["value"])} 
                for o in obs if o["value"] != "."
            ][:12]
        }
        
    def get_exports(self) -> Dict[str, Any]:
        """
        Get South Korea exports
        Source: FRED series XTEXVA01KRM667S (Exports of goods and services)
        """
        result = self._fetch_fred_series("XTEXVA01KRM667S", 20)
        
        if "error" in result:
            return result
            
        obs = result["observations"]
        latest = obs[0]
        
        # Calculate YoY growth
        yoy_growth = None
        if len(obs) >= 5:  # Quarterly data
            current_val = float(latest["value"])
            yoy_val = float(obs[4]["value"])
            yoy_growth = ((current_val / yoy_val) - 1) * 100
            
        return {
            "exports_usd_millions": float(latest["value"]),
            "date": latest["date"],
            "yoy_growth_pct": round(yoy_growth, 2) if yoy_growth else None,
            "series": result["series_id"],
            "history": [
                {"date": o["date"], "exports": float(o["value"])} 
                for o in obs if o["value"] != "."
            ][:8]
        }
        
    def get_retail_sales(self) -> Dict[str, Any]:
        """
        Get South Korea retail sales
        Source: FRED series SLRTTO01KRM657S (Retail sales volume)
        """
        result = self._fetch_fred_series("SLRTTO01KRM657S", 24)
        
        if "error" in result:
            return result
            
        obs = result["observations"]
        latest = obs[0]
        
        # Calculate MoM change
        mom_change = None
        if len(obs) >= 2:
            current_val = float(latest["value"])
            prev_val = float(obs[1]["value"])
            mom_change = ((current_val / prev_val) - 1) * 100
            
        return {
            "retail_sales_index": float(latest["value"]),
            "date": latest["date"],
            "mom_change_pct": round(mom_change, 2) if mom_change else None,
            "series": result["series_id"],
            "history": [
                {"date": o["date"], "sales": float(o["value"])} 
                for o in obs if o["value"] != "."
            ][:12]
        }
        
    def get_dashboard(self) -> Dict[str, Any]:
        """Get complete KOSTAT dashboard snapshot"""
        return {
            "kostat_dashboard": {
                "gdp": self.get_gdp(),
                "cpi": self.get_cpi(),
                "unemployment": self.get_unemployment(),
                "industrial_production": self.get_industrial_production(),
                "exports": self.get_exports(),
                "retail_sales": self.get_retail_sales()
            },
            "country": "South Korea",
            "timestamp": datetime.now().isoformat(),
            "source": "FRED (St. Louis Fed)"
        }


def cli_get_kostat_gdp():
    """CLI: Get South Korea GDP"""
    kostat = KOSTATData()
    result = kostat.get_gdp()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
        
    print(f"South Korea GDP Index: {result['gdp_index']:.2f}")
    print(f"As of: {result['date']}")
    if result.get('yoy_growth_pct'):
        print(f"YoY Growth: {result['yoy_growth_pct']}%")


def cli_get_kostat_cpi():
    """CLI: Get South Korea CPI"""
    kostat = KOSTATData()
    result = kostat.get_cpi()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
        
    print(f"South Korea CPI Inflation: {result['cpi_yoy_pct']}% YoY")
    print(f"As of: {result['date']}")
    if result.get('avg_12m_pct'):
        print(f"12-month average: {result['avg_12m_pct']}%")


def cli_get_kostat_dashboard():
    """CLI: Get complete KOSTAT dashboard"""
    kostat = KOSTATData()
    result = kostat.get_dashboard()
    
    data = result['kostat_dashboard']
    
    print("=== KOSTAT SOUTH KOREA DASHBOARD ===\n")
    
    if "error" not in data['gdp']:
        gdp = data['gdp']
        print(f"GDP Index: {gdp['gdp_index']:.2f}", end="")
        if gdp.get('yoy_growth_pct'):
            print(f" ({gdp['yoy_growth_pct']:+.1f}% YoY)")
        else:
            print()
    
    if "error" not in data['cpi']:
        cpi = data['cpi']
        print(f"CPI Inflation: {cpi['cpi_yoy_pct']:.1f}% YoY ({cpi['date']})")
    
    if "error" not in data['unemployment']:
        unemp = data['unemployment']
        print(f"Unemployment: {unemp['unemployment_pct']:.1f}% ({unemp['date']})")
    
    if "error" not in data['industrial_production']:
        ip = data['industrial_production']
        print(f"Industrial Production: {ip['production_index']:.2f}", end="")
        if ip.get('yoy_growth_pct'):
            print(f" ({ip['yoy_growth_pct']:+.1f}% YoY)")
        else:
            print()
    
    if "error" not in data['exports']:
        exp = data['exports']
        print(f"Exports: ${exp['exports_usd_millions']:,.0f}M", end="")
        if exp.get('yoy_growth_pct'):
            print(f" ({exp['yoy_growth_pct']:+.1f}% YoY)")
        else:
            print()
    
    if "error" not in data['retail_sales']:
        retail = data['retail_sales']
        print(f"Retail Sales Index: {retail['retail_sales_index']:.2f}", end="")
        if retail.get('mom_change_pct'):
            print(f" ({retail['mom_change_pct']:+.1f}% MoM)")
        else:
            print()
    
    print(f"\nSource: {result['source']}")


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KOSTAT Korean Statistics - Phase 636')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # kostat-dashboard command
    subparsers.add_parser('kostat-dashboard', help='Get complete KOSTAT dashboard')
    
    # kostat-gdp command
    subparsers.add_parser('kostat-gdp', help='Get South Korea GDP')
    
    # kostat-cpi command
    subparsers.add_parser('kostat-cpi', help='Get South Korea CPI inflation')
    
    args = parser.parse_args()
    
    if args.command == 'kostat-dashboard':
        cli_get_kostat_dashboard()
    elif args.command == 'kostat-gdp':
        cli_get_kostat_gdp()
    elif args.command == 'kostat-cpi':
        cli_get_kostat_cpi()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
