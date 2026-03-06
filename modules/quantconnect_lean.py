"""
QuantConnect LEAN — Open-Source Algorithmic Trading Engine

Data Source: QuantConnect (https://www.quantconnect.com)
Type: Local backtesting engine + Cloud API
Free: Yes (local engine fully open-source, cloud has free tier)
Update: Real-time during market hours

Provides:
- Local backtesting engine for Python/C# strategies
- Historical data access (stocks, forex, crypto, options)
- ML integration for alpha generation
- Performance metrics and risk analysis
- Cloud deployment for live trading (10 backtests/day free)

Usage:
- Local LEAN CLI for offline backtests
- Cloud API for data access and deployment
- Custom data feeds integration
"""

import requests
import subprocess
import json
import os
from typing import Dict, Optional, List
from datetime import datetime

# QuantConnect Cloud API (for data access)
QC_API_BASE = "https://www.quantconnect.com/api/v2"
QC_DATA_BASE = "https://cdn.quantconnect.com"

def check_lean_installed() -> bool:
    """Check if LEAN CLI is installed locally"""
    try:
        result = subprocess.run(['lean', '--version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def get_project_list() -> List[Dict]:
    """List local LEAN projects (if CLI installed)"""
    if not check_lean_installed():
        return {"error": "LEAN CLI not installed", "install": "pip install lean"}
    
    try:
        # List projects in current directory
        result = subprocess.run(['lean', 'project-list'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Parse output
            projects = []
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('---'):
                    projects.append({"name": line.strip()})
            return {"projects": projects, "count": len(projects)}
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

def run_backtest(project_name: str, start_date: Optional[str] = None, 
                 end_date: Optional[str] = None) -> Dict:
    """
    Run a backtest locally using LEAN CLI.
    
    Args:
        project_name: Name of the LEAN project to backtest
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    
    Returns:
        Backtest results dictionary
    """
    if not check_lean_installed():
        return {
            "error": "LEAN CLI not installed",
            "install_instructions": [
                "pip install lean",
                "lean init",
                "For docs: https://www.quantconnect.com/docs/v2/lean-cli"
            ]
        }
    
    try:
        cmd = ['lean', 'backtest', project_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return {
                "status": "success",
                "project": project_name,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "failed",
                "project": project_name,
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {"error": "Backtest timed out (>5 min)"}
    except Exception as e:
        return {"error": str(e)}

def get_data_links(symbol: str, resolution: str = "daily", 
                   market: str = "usa") -> Dict:
    """
    Get download links for QuantConnect historical data (free tier).
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTCUSD')
        resolution: 'daily', 'hour', 'minute' (higher res may need subscription)
        market: 'usa', 'forex', 'crypto', 'cfd', 'future', 'option'
    
    Returns:
        Data download info
    """
    # QuantConnect hosts free daily equity data
    # Format: https://cdn.quantconnect.com/equity/usa/daily/aapl.zip
    
    symbol_lower = symbol.lower()
    
    if market == "usa":
        url = f"{QC_DATA_BASE}/equity/usa/{resolution}/{symbol_lower}.zip"
    elif market == "forex":
        url = f"{QC_DATA_BASE}/forex/oanda/{resolution}/{symbol_lower}.zip"
    elif market == "crypto":
        url = f"{QC_DATA_BASE}/crypto/coinbase/{resolution}/{symbol_lower}usd.zip"
    else:
        return {"error": f"Unsupported market: {market}"}
    
    return {
        "symbol": symbol,
        "resolution": resolution,
        "market": market,
        "download_url": url,
        "note": "Some data may require QC subscription. Daily equity data is free."
    }

def get_algorithm_template(strategy_type: str = "basic") -> str:
    """
    Return a Python template for QuantConnect algorithm.
    
    Args:
        strategy_type: 'basic', 'ml', 'momentum', 'mean_reversion'
    
    Returns:
        Python code template string
    """
    if strategy_type == "basic":
        return '''
from AlgorithmImports import *

class BasicAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)
        
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        
    def OnData(self, data):
        if not self.Portfolio.Invested:
            self.SetHoldings(self.spy, 1.0)
            self.Debug(f"Purchased {self.spy}")
'''
    elif strategy_type == "ml":
        return '''
from AlgorithmImports import *
from sklearn.ensemble import RandomForestClassifier

class MLAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.model = RandomForestClassifier()
        self.features = []
        self.labels = []
        
    def OnData(self, data):
        # Collect features and train model
        # Make predictions
        pass
'''
    else:
        return f"# Template for {strategy_type} not yet implemented"

def get_lean_status() -> Dict:
    """Get LEAN installation and project status"""
    status = {
        "lean_cli_installed": check_lean_installed(),
        "timestamp": datetime.now().isoformat(),
        "documentation": "https://www.quantconnect.com/docs/v2",
        "github": "https://github.com/QuantConnect/Lean"
    }
    
    if status["lean_cli_installed"]:
        projects = get_project_list()
        status["projects"] = projects
    else:
        status["install_command"] = "pip install lean && lean init"
    
    return status

# Main functions for data access
def get_historical_data(symbol: str, start_date: str, end_date: str,
                       resolution: str = "daily") -> Dict:
    """
    Wrapper to get historical data via LEAN or provide download link.
    
    Returns download instructions or data if available.
    """
    return get_data_links(symbol, resolution)

def get_backtest_metrics(project_name: str) -> Dict:
    """
    Parse backtest results from LEAN output.
    Returns key performance metrics.
    """
    # This would parse the JSON results file from a completed backtest
    results_path = f"./{project_name}/backtests/latest/results.json"
    
    if os.path.exists(results_path):
        with open(results_path) as f:
            return json.load(f)
    else:
        return {
            "error": "No backtest results found",
            "hint": f"Run: run_backtest('{project_name}')"
        }

if __name__ == "__main__":
    # Test module
    status = get_lean_status()
    print(json.dumps(status, indent=2))
    
    # Example: Get data link for AAPL
    aapl_data = get_data_links("AAPL", "daily", "usa")
    print("\nAAPL Data Link:")
    print(json.dumps(aapl_data, indent=2))
