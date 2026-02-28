"""COT Positioning Extreme Detector — CFTC Commitments of Traders analysis.

Analyzes CFTC COT reports to detect extreme positioning by commercials,
large speculators, and small speculators. Identifies potential reversals
when net positioning hits historical extremes. Uses free CFTC data.

Roadmap #365
"""

import datetime
import json
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote


# CFTC COT report categories
POSITION_TYPES = ["commercial", "large_speculator", "small_speculator"]

# Common commodity COT contract codes (CFTC)
COT_CONTRACTS = {
    "crude_oil": "067651",
    "natural_gas": "023651",
    "gold": "088691",
    "silver": "084691",
    "copper": "085692",
    "corn": "002602",
    "soybeans": "005602",
    "wheat": "001602",
    "cotton": "033661",
    "sugar": "080732",
    "coffee": "083731",
    "sp500": "13874A",
    "nasdaq": "20974A",
    "eurusd": "099741",
    "jpyusd": "097741",
    "gbpusd": "096742",
    "aud": "232741",
    "cad": "090741",
    "vix": "1170E1",
    "10yr_treasury": "043602",
    "5yr_treasury": "044601",
    "2yr_treasury": "042601",
}

# Quandl-compatible CFTC data endpoint
CFTC_BASE_URL = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"


def fetch_cot_data(
    contract_code: str,
    weeks: int = 52,
) -> List[Dict]:
    """Fetch COT data from CFTC public API.

    Args:
        contract_code: CFTC contract market code
        weeks: Number of weeks of history

    Returns:
        List of weekly COT records
    """
    params = quote(f"$where=cftc_contract_market_code='{contract_code}'&$order=report_date_as_yyyy_mm_dd DESC&$limit={weeks}", safe="$&='")
    url = f"{CFTC_BASE_URL}?{params}"

    try:
        req = Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        return [{"error": f"Failed to fetch COT data: {str(e)}"}]


def analyze_positioning(
    commodity: str = "crude_oil",
    weeks: int = 52,
    extreme_percentile: float = 90.0,
) -> Dict:
    """Analyze COT positioning and detect extremes.

    Args:
        commodity: Commodity name (key from COT_CONTRACTS) or direct code
        weeks: Weeks of history for percentile calculation
        extreme_percentile: Percentile threshold for extreme detection

    Returns:
        Dict with current positioning, percentiles, and extreme flags
    """
    code = COT_CONTRACTS.get(commodity, commodity)
    records = fetch_cot_data(code, weeks)

    if not records or (len(records) == 1 and "error" in records[0]):
        return {"error": records[0].get("error", "No data") if records else "No data"}

    # Parse net positions
    net_positions = []
    for rec in records:
        try:
            comm_long = int(rec.get("comm_positions_long_all", 0))
            comm_short = int(rec.get("comm_positions_short_all", 0))
            noncomm_long = int(rec.get("noncomm_positions_long_all", 0))
            noncomm_short = int(rec.get("noncomm_positions_short_all", 0))
            nonrep_long = int(rec.get("nonrept_positions_long_all", 0))
            nonrep_short = int(rec.get("nonrept_positions_short_all", 0))

            net_positions.append({
                "date": rec.get("report_date_as_yyyy_mm_dd", ""),
                "commercial_net": comm_long - comm_short,
                "speculator_net": noncomm_long - noncomm_short,
                "small_trader_net": nonrep_long - nonrep_short,
                "open_interest": int(rec.get("open_interest_all", 0)),
            })
        except (ValueError, TypeError):
            continue

    if not net_positions:
        return {"error": "Could not parse COT positions"}

    current = net_positions[0]

    # Calculate percentiles
    def percentile_rank(values: List[float], current_val: float) -> float:
        below = sum(1 for v in values if v <= current_val)
        return round(below / len(values) * 100, 1)

    comm_nets = [p["commercial_net"] for p in net_positions]
    spec_nets = [p["speculator_net"] for p in net_positions]

    comm_pctile = percentile_rank(comm_nets, current["commercial_net"])
    spec_pctile = percentile_rank(spec_nets, current["speculator_net"])

    # Detect extremes
    extremes = []
    if spec_pctile >= extreme_percentile:
        extremes.append({"type": "SPECULATOR_EXTREME_LONG", "percentile": spec_pctile})
    elif spec_pctile <= (100 - extreme_percentile):
        extremes.append({"type": "SPECULATOR_EXTREME_SHORT", "percentile": spec_pctile})

    if comm_pctile >= extreme_percentile:
        extremes.append({"type": "COMMERCIAL_EXTREME_LONG", "percentile": comm_pctile})
    elif comm_pctile <= (100 - extreme_percentile):
        extremes.append({"type": "COMMERCIAL_EXTREME_SHORT", "percentile": comm_pctile})

    # Signal: commercials are "smart money" — their extremes often precede reversals
    signal = "NEUTRAL"
    if any(e["type"] == "COMMERCIAL_EXTREME_LONG" for e in extremes):
        signal = "BULLISH_REVERSAL_POSSIBLE"
    elif any(e["type"] == "COMMERCIAL_EXTREME_SHORT" for e in extremes):
        signal = "BEARISH_REVERSAL_POSSIBLE"

    return {
        "commodity": commodity,
        "report_date": current["date"],
        "commercial_net": current["commercial_net"],
        "speculator_net": current["speculator_net"],
        "small_trader_net": current["small_trader_net"],
        "open_interest": current["open_interest"],
        "commercial_percentile": comm_pctile,
        "speculator_percentile": spec_pctile,
        "extremes_detected": extremes,
        "signal": signal,
        "weeks_analyzed": len(net_positions),
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def scan_all_extremes(
    extreme_percentile: float = 90.0,
) -> List[Dict]:
    """Scan all tracked commodities for positioning extremes.

    Args:
        extreme_percentile: Percentile threshold

    Returns:
        List of commodities with extreme positioning, sorted by significance
    """
    results = []
    for commodity in COT_CONTRACTS:
        analysis = analyze_positioning(commodity, weeks=52, extreme_percentile=extreme_percentile)
        if "error" not in analysis and analysis.get("extremes_detected"):
            results.append({
                "commodity": commodity,
                "signal": analysis["signal"],
                "extremes": analysis["extremes_detected"],
                "commercial_net": analysis["commercial_net"],
                "speculator_net": analysis["speculator_net"],
                "commercial_percentile": analysis["commercial_percentile"],
                "speculator_percentile": analysis["speculator_percentile"],
            })

    results.sort(key=lambda x: len(x["extremes"]), reverse=True)
    return results
