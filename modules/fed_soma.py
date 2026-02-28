"""
Fed SOMA Holdings — NY Fed System Open Market Account

Tracks Federal Reserve balance sheet holdings via NY Fed API.
Data: https://markets.newyorkfed.org/api/soma/summary.json

Use cases:
- QE/QT tracking
- Fed balance sheet analysis
- Weekly changes in holdings
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "fed_soma"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://markets.newyorkfed.org/api/soma"


def fetch_soma_summary(use_cache: bool = True) -> Optional[Dict]:
    """Fetch SOMA holdings summary from NY Fed API."""
    cache_path = CACHE_DIR / "summary_latest.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/summary.json"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching SOMA data: {e}")
        return None


def get_latest_holdings() -> pd.DataFrame:
    """Get latest SOMA holdings summary."""
    data = fetch_soma_summary()
    if not data or "soma" not in data or "summary" not in data["soma"]:
        return pd.DataFrame()
    
    summaries = data["soma"]["summary"]
    if not summaries:
        return pd.DataFrame()
    
    # Get the most recent entry
    latest = summaries[-1]
    
    # Convert to DataFrame with asset classes
    records = []
    asset_map = {
        "bills": "Treasury Bills",
        "notesbonds": "Treasury Notes/Bonds",
        "tips": "TIPS",
        "agencies": "Agency Debt",
        "mbs": "Agency MBS",
        "cmbs": "Commercial MBS"
    }
    
    for key, label in asset_map.items():
        value = latest.get(key, "0")
        if value and value != "":
            # Convert to billions
            val_billions = float(value) / 1_000_000_000
            if val_billions > 0.01:  # Only show non-trivial amounts
                records.append({
                    "asset_class": label,
                    "par_value_billions": round(val_billions, 2),
                    "as_of_date": latest.get("asOfDate", "")
                })
    
    df = pd.DataFrame(records)
    return df


def get_weekly_change() -> Dict[str, float]:
    """Calculate week-over-week change in holdings."""
    data = fetch_soma_summary()
    if not data or "soma" not in data or "summary" not in data["soma"]:
        return {"note": "No data available"}
    
    summaries = data["soma"]["summary"]
    if len(summaries) < 2:
        return {"note": "Insufficient historical data"}
    
    # Get latest and previous week (summaries are weekly)
    latest = summaries[-1]
    prev = summaries[-2] if len(summaries) > 1 else summaries[-1]
    
    asset_map = {
        "bills": "Treasury Bills",
        "notesbonds": "Treasury Notes/Bonds",
        "tips": "TIPS",
        "agencies": "Agency Debt",
        "mbs": "Agency MBS",
        "cmbs": "Commercial MBS"
    }
    
    changes = {}
    for key, label in asset_map.items():
        latest_val = float(latest.get(key, "0") or "0") / 1_000_000_000
        prev_val = float(prev.get(key, "0") or "0") / 1_000_000_000
        change = latest_val - prev_val
        if abs(change) > 0.01:
            changes[label] = round(change, 2)
    
    # Calculate total change
    total_latest = float(latest.get("total", "0")) / 1_000_000_000
    total_prev = float(prev.get("total", "0")) / 1_000_000_000
    changes["Total"] = round(total_latest - total_prev, 2)
    
    changes["as_of_date"] = latest.get("asOfDate", "")
    changes["prev_date"] = prev.get("asOfDate", "")
    
    return changes


def cli_soma_summary():
    """CLI: Display current SOMA holdings summary."""
    df = get_latest_holdings()
    if df.empty:
        print("No SOMA data available")
        return
    
    print("\n=== Fed SOMA Holdings Summary ===")
    print(f"As of: {df['as_of_date'].iloc[0]}")
    print(f"\n{df[['asset_class', 'par_value_billions']].to_string(index=False)}")
    total = df['par_value_billions'].sum()
    print(f"\nTotal: ${total:,.2f}B")


def cli_soma_treasury(bucket: Optional[str] = None):
    """CLI: Show Treasury holdings (simplified - uses summary data)."""
    df = get_latest_holdings()
    if df.empty:
        print("No Treasury data available")
        return
    
    print("\n=== Fed Treasury Holdings ===")
    
    # Filter to Treasury securities only
    treasury_df = df[df['asset_class'].str.contains("Treasury")]
    
    if treasury_df.empty:
        print("No Treasury holdings found")
        return
    
    print(f"\nAs of: {treasury_df['as_of_date'].iloc[0]}")
    print(f"\n{treasury_df[['asset_class', 'par_value_billions']].to_string(index=False)}")
    print(f"\nTotal Treasury: ${treasury_df['par_value_billions'].sum():.2f}B")


def cli_soma_mbs():
    """CLI: Show MBS holdings."""
    df = get_latest_holdings()
    if df.empty:
        print("No MBS data available")
        return
    
    print("\n=== Fed MBS Holdings ===")
    
    # Filter to MBS
    mbs_df = df[df['asset_class'].str.contains("MBS")]
    
    if mbs_df.empty:
        print("No MBS holdings found")
        return
    
    print(f"\nAs of: {mbs_df['as_of_date'].iloc[0]}")
    print(f"\n{mbs_df[['asset_class', 'par_value_billions']].to_string(index=False)}")
    print(f"\nTotal MBS: ${mbs_df['par_value_billions'].sum():.2f}B")


def cli_soma_change():
    """CLI: Show week-over-week change in holdings."""
    changes = get_weekly_change()
    
    print("\n=== Fed SOMA Weekly Change ===")
    
    if "note" in changes:
        print(changes["note"])
        return
    
    as_of = changes.pop("as_of_date", "")
    prev_date = changes.pop("prev_date", "")
    total_change = changes.pop("Total", 0)
    
    print(f"Period: {prev_date} → {as_of}")
    
    for asset_class, change in sorted(changes.items(), key=lambda x: abs(x[1]), reverse=True):
        direction = "📈 QE" if change > 0 else "📉 QT" if change < 0 else "—"
        print(f"{asset_class:25s} {direction:8s} ${change:+.2f}B")
    
    print(f"\n{'Total Change':25s} {'':8s} ${total_change:+.2f}B")
    
    if total_change > 0:
        print("\n✅ Net QE (quantitative easing)")
    elif total_change < 0:
        print("\n⚠️ Net QT (quantitative tightening)")
    else:
        print("\n➖ No net change")


def cli_soma_duration():
    """CLI: Show Fed portfolio info (duration requires granular data not available in summary)."""
    df = get_latest_holdings()
    if df.empty:
        print("No data available")
        return
    
    print("\n=== Fed Portfolio Overview ===")
    print(f"As of: {df['as_of_date'].iloc[0]}")
    print(f"\nTotal Holdings: ${df['par_value_billions'].sum():,.2f}B")
    
    treasury_total = df[df['asset_class'].str.contains("Treasury")]['par_value_billions'].sum()
    mbs_total = df[df['asset_class'].str.contains("MBS")]['par_value_billions'].sum()
    
    print(f"\nComposition:")
    print(f"  Treasury Securities: ${treasury_total:,.2f}B")
    print(f"  Agency MBS: ${mbs_total:,.2f}B")
    
    print(f"\n(Note: Detailed duration analysis requires granular holdings data)")


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        cli_soma_summary()
        sys.exit(0)
    
    command = args[0]
    
    if command == "fed-soma":
        cli_soma_summary()
    elif command == "fed-soma-treasury":
        bucket = args[1] if len(args) > 1 else None
        cli_soma_treasury(bucket)
    elif command == "fed-soma-mbs":
        cli_soma_mbs()
    elif command == "fed-soma-change":
        cli_soma_change()
    elif command == "fed-soma-duration":
        cli_soma_duration()
    else:
        print(f"Unknown command: {command}")
        print("Available: fed-soma, fed-soma-treasury, fed-soma-mbs, fed-soma-change, fed-soma-duration")
        sys.exit(1)
