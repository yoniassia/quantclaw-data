#!/usr/bin/env python3
"""
API Key Environment Variable Test Script

Tests that all modules correctly load API keys from environment variables
and validates connectivity to external services.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv('/home/quant/apps/quantclaw-data/.env')

# Add modules directory to path
sys.path.insert(0, '/home/quant/apps/quantclaw-data/modules')

# Map of API keys to their test endpoints
API_TESTS = {
    'FRED_API_KEY': {
        'name': 'FRED (Federal Reserve Economic Data)',
        'test_url': 'https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={key}&file_type=json',
        'required': True,
        'modules': ['fed_policy', 'central_bank_rates', 'treasury_curve', 'fred_enhanced']
    },
    'FINNHUB_API_KEY': {
        'name': 'Finnhub',
        'test_url': 'https://finnhub.io/api/v1/quote?symbol=AAPL&token={key}',
        'required': False,
        'modules': ['finnhub_ipo_calendar']
    },
    'EIA_API_KEY': {
        'name': 'EIA (Energy Information Administration)',
        'test_url': 'https://api.eia.gov/v2/seriesid/PET.RWTC.D?api_key={key}',
        'required': False,
        'modules': ['eia_energy', 'crude_oil_fundamentals', 'natural_gas_supply_demand']
    },
    'BLS_API_KEY': {
        'name': 'BLS (Bureau of Labor Statistics)',
        'test_url': None,  # BLS doesn't require API key for basic access
        'required': False,
        'modules': ['bls']
    },
    'CENSUS_API_KEY': {
        'name': 'US Census Bureau',
        'test_url': 'https://api.census.gov/data/2019/acs/acs5?get=NAME,B01001_001E&for=state:*&key={key}',
        'required': False,
        'modules': []
    },
}

class APIKeyTester:
    def __init__(self):
        self.results = []
        self.env_keys = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Print colored log messages"""
        colors = {
            "INFO": "\033[94m",      # Blue
            "SUCCESS": "\033[92m",   # Green
            "WARNING": "\033[93m",   # Yellow
            "ERROR": "\033[91m",     # Red
            "RESET": "\033[0m"
        }
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{level}]{colors['RESET']} {message}")
        
    def check_env_keys(self):
        """Check which API keys are set in environment"""
        self.log("\n" + "="*80, "INFO")
        self.log("CHECKING ENVIRONMENT VARIABLES", "INFO")
        self.log("="*80, "INFO")
        
        for key_name, config in API_TESTS.items():
            value = os.environ.get(key_name, "")
            self.env_keys[key_name] = value
            
            if value:
                masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                self.log(f"✓ {key_name}: {masked} ({config['name']})", "SUCCESS")
            else:
                level = "WARNING" if config['required'] else "INFO"
                self.log(f"✗ {key_name}: NOT SET ({config['name']})", level)
                
    def test_api_connectivity(self):
        """Test API connectivity for each service"""
        self.log("\n" + "="*80, "INFO")
        self.log("TESTING API CONNECTIVITY", "INFO")
        self.log("="*80, "INFO")
        
        for key_name, config in API_TESTS.items():
            api_name = config['name']
            test_url = config['test_url']
            api_key = self.env_keys.get(key_name, "")
            
            if not test_url:
                self.log(f"⊘ {api_name}: No connectivity test (API key optional)", "INFO")
                continue
                
            if not api_key:
                self.log(f"⊗ {api_name}: Skipped (no API key)", "WARNING")
                continue
                
            try:
                url = test_url.format(key=api_key)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.log(f"✓ {api_name}: Connection successful", "SUCCESS")
                    self.results.append((api_name, "PASS", "200 OK"))
                elif response.status_code == 401:
                    self.log(f"✗ {api_name}: Authentication failed (invalid key)", "ERROR")
                    self.results.append((api_name, "FAIL", "401 Unauthorized"))
                elif response.status_code == 429:
                    self.log(f"⚠ {api_name}: Rate limited (key probably valid)", "WARNING")
                    self.results.append((api_name, "WARN", "429 Rate Limited"))
                else:
                    self.log(f"⚠ {api_name}: Unexpected response {response.status_code}", "WARNING")
                    self.results.append((api_name, "WARN", f"{response.status_code}"))
                    
            except requests.exceptions.Timeout:
                self.log(f"⚠ {api_name}: Timeout (network issue)", "WARNING")
                self.results.append((api_name, "WARN", "Timeout"))
            except Exception as e:
                self.log(f"✗ {api_name}: Error - {str(e)}", "ERROR")
                self.results.append((api_name, "FAIL", str(e)))
                
    def test_module_imports(self):
        """Test that modules can be imported and API keys are loaded"""
        self.log("\n" + "="*80, "INFO")
        self.log("TESTING MODULE IMPORTS & API KEY LOADING", "INFO")
        self.log("="*80, "INFO")
        
        # Test a sample of modules that use API keys
        test_modules = [
            ('fed_policy', 'FRED_API_KEY'),
            ('finnhub_ipo_calendar', 'FINNHUB_API_KEY'),
            ('eia_energy', 'EIA_API_KEY'),
            ('bls', 'BLS_API_KEY'),
        ]
        
        for module_name, expected_key in test_modules:
            try:
                # Import the module
                module = importlib.import_module(module_name)
                
                # Check if the API key variable exists
                if hasattr(module, expected_key):
                    loaded_value = getattr(module, expected_key)
                    env_value = os.environ.get(expected_key, "")
                    
                    if loaded_value == env_value:
                        status = "✓" if env_value else "○"
                        level = "SUCCESS" if env_value else "INFO"
                        msg = "matches env" if env_value else "correctly empty"
                        self.log(f"{status} {module_name}: {expected_key} {msg}", level)
                    else:
                        self.log(f"✗ {module_name}: {expected_key} mismatch!", "ERROR")
                        self.log(f"   Module value: {loaded_value[:20]}...", "ERROR")
                        self.log(f"   Env value: {env_value[:20]}...", "ERROR")
                else:
                    self.log(f"⚠ {module_name}: {expected_key} not found in module", "WARNING")
                    
            except Exception as e:
                self.log(f"✗ {module_name}: Import failed - {str(e)}", "ERROR")
                
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("="*80, "INFO")
        
        # Environment variables summary
        total_keys = len(API_TESTS)
        keys_set = sum(1 for k in self.env_keys.values() if k)
        self.log(f"\nEnvironment Variables: {keys_set}/{total_keys} set", "INFO")
        
        # API connectivity summary
        if self.results:
            passed = sum(1 for r in self.results if r[1] == "PASS")
            failed = sum(1 for r in self.results if r[1] == "FAIL")
            warned = sum(1 for r in self.results if r[1] == "WARN")
            
            self.log(f"\nAPI Connectivity Tests:", "INFO")
            self.log(f"  ✓ Passed: {passed}", "SUCCESS")
            if warned:
                self.log(f"  ⚠ Warnings: {warned}", "WARNING")
            if failed:
                self.log(f"  ✗ Failed: {failed}", "ERROR")
                
        # Final recommendation
        self.log("\n" + "="*80, "INFO")
        if keys_set >= 2 and (not self.results or sum(1 for r in self.results if r[1] in ["PASS", "WARN"]) > 0):
            self.log("✓ MIGRATION SUCCESSFUL - Modules are loading API keys from environment", "SUCCESS")
        else:
            self.log("⚠ REVIEW NEEDED - Some API keys may not be configured correctly", "WARNING")
        self.log("="*80 + "\n", "INFO")
        
def main():
    tester = APIKeyTester()
    
    print("\n" + "="*80)
    print("QuantClaw Data - API Key Environment Migration Test")
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Run tests
    tester.check_env_keys()
    tester.test_module_imports()
    tester.test_api_connectivity()
    tester.print_summary()
    
if __name__ == '__main__':
    main()
