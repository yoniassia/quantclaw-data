"""Frankfurter API — ECB exchange rates for 30+ currencies.

Provides current and historical exchange rates from the European Central Bank
via the open-source Frankfurter API. No API key required.

Data source: https://api.frankfurter.app/ (ECB data, updated daily on business days).
"""

import json
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

BASE_URL = "https://api.frankfurter.app"
_HEADERS = {"User-Agent": "QuantClaw/1.0"}


def _fetch(path: str) -> Any:
    """Fetch JSON from the Frankfurter API.

    Args:
        path: URL path with query string (e.g. '/latest?from=USD').

    Returns:
        Parsed JSON response.
    """
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_latest_rates(base: str = "USD", symbols: list[str] | None = None) -> dict[str, Any]:
    """Fetch current exchange rates for a base currency.

    Args:
        base: Base currency code (e.g. 'USD', 'EUR').
        symbols: Optional list of target currency codes. None = all available.

    Returns:
        Dict with base, date, and rates mapping.
    """
    path = f"/latest?from={base.upper()}"
    if symbols:
        path += f"&to={','.join(s.upper() for s in symbols)}"
    try:
        data = _fetch(path)
        return {
            "base": data.get("base", base.upper()),
            "date": data.get("date"),
            "rates": data.get("rates", {}),
            "count": len(data.get("rates", {})),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "base": base.upper()}


def get_historical_rates(
    base: str,
    symbols: list[str] | None,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Fetch historical exchange rate time series.

    Args:
        base: Base currency code.
        symbols: List of target currency codes (or None for all).
        start_date: Start date as 'YYYY-MM-DD'.
        end_date: End date as 'YYYY-MM-DD'.

    Returns:
        Dict with base, start/end dates, and rates keyed by date.
    """
    path = f"/{start_date}..{end_date}?from={base.upper()}"
    if symbols:
        path += f"&to={','.join(s.upper() for s in symbols)}"
    try:
        data = _fetch(path)
        rates = data.get("rates", {})
        return {
            "base": data.get("base", base.upper()),
            "start_date": data.get("start_date", start_date),
            "end_date": data.get("end_date", end_date),
            "rates": rates,
            "data_points": len(rates),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "base": base.upper()}


def get_supported_currencies() -> dict[str, Any]:
    """List all currencies supported by the Frankfurter API.

    Returns:
        Dict with currencies mapping (code -> name) and count.
    """
    try:
        data = _fetch("/currencies")
        return {
            "currencies": data,
            "count": len(data),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_rate_change(base: str, target: str, days: int = 30) -> dict[str, Any]:
    """Calculate percentage change of a currency pair over a period.

    Args:
        base: Base currency code.
        target: Target currency code.
        days: Lookback period in calendar days.

    Returns:
        Dict with start/end rates, absolute and percentage change.
    """
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)
    try:
        data = _fetch(f"/{start}..{end}?from={base.upper()}&to={target.upper()}")
        rates = data.get("rates", {})
        if len(rates) < 2:
            return {"error": "Insufficient data points", "base": base.upper(), "target": target.upper()}

        sorted_dates = sorted(rates.keys())
        first_rate = rates[sorted_dates[0]][target.upper()]
        last_rate = rates[sorted_dates[-1]][target.upper()]
        change = last_rate - first_rate
        pct_change = (change / first_rate) * 100

        return {
            "base": base.upper(),
            "target": target.upper(),
            "period_days": days,
            "start_date": sorted_dates[0],
            "end_date": sorted_dates[-1],
            "start_rate": first_rate,
            "end_rate": last_rate,
            "change": round(change, 6),
            "pct_change": round(pct_change, 4),
            "direction": "strengthened" if change < 0 else "weakened" if change > 0 else "unchanged",
            "data_points": len(sorted_dates),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "base": base.upper(), "target": target.upper()}


def fx_cross_rate(from_currency: str, to_currency: str) -> dict[str, Any]:
    """Compute a cross rate between two non-USD currencies via USD triangulation.

    Args:
        from_currency: Source currency code.
        to_currency: Destination currency code.

    Returns:
        Dict with the cross rate and intermediate rates used.
    """
    try:
        data = _fetch(f"/latest?from={from_currency.upper()}&to={to_currency.upper()}")
        rate = data.get("rates", {}).get(to_currency.upper())
        if rate is None:
            return {"error": f"Rate not found for {from_currency}/{to_currency}"}
        return {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "rate": rate,
            "inverse": round(1 / rate, 6) if rate else None,
            "date": data.get("date"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def fx_analysis(base: str = "USD", targets: list[str] | None = None) -> dict[str, Any]:
    """Comprehensive FX snapshot with current rates, 7d and 30d trends.

    Args:
        base: Base currency code.
        targets: Target currencies (defaults to major pairs).

    Returns:
        Dict with current rates, short/medium-term trends, and strongest/weakest.
    """
    if targets is None:
        targets = ["EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "CNY"]

    base = base.upper()
    targets = [t.upper() for t in targets]

    try:
        # Current rates
        current = get_latest_rates(base, targets)
        if "error" in current:
            return current

        # 7-day and 30-day changes
        changes_7d = {}
        changes_30d = {}
        for t in targets:
            c7 = get_rate_change(base, t, 7)
            c30 = get_rate_change(base, t, 30)
            changes_7d[t] = c7.get("pct_change", 0) if "error" not in c7 else None
            changes_30d[t] = c30.get("pct_change", 0) if "error" not in c30 else None

        # Find strongest/weakest (most negative pct = base strengthened most vs that currency)
        valid_30d = {k: v for k, v in changes_30d.items() if v is not None}
        strongest_against = max(valid_30d, key=valid_30d.get) if valid_30d else None
        weakest_against = min(valid_30d, key=valid_30d.get) if valid_30d else None

        pairs = []
        for t in targets:
            pairs.append({
                "target": t,
                "rate": current["rates"].get(t),
                "change_7d_pct": changes_7d.get(t),
                "change_30d_pct": changes_30d.get(t),
            })

        return {
            "base": base,
            "date": current.get("date"),
            "pairs": pairs,
            "strongest_against": strongest_against,
            "weakest_against": weakest_against,
            "currencies_analyzed": len(targets),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    print("=== Frankfurter API Module Test ===")
    r = get_latest_rates("USD", ["EUR", "GBP", "JPY"])
    print(f"Latest USD rates: {json.dumps(r, indent=2)}")
    c = get_supported_currencies()
    print(f"Supported currencies: {c.get('count', 'error')}")
    ch = get_rate_change("USD", "EUR", 30)
    print(f"USD/EUR 30d change: {json.dumps(ch, indent=2)}")
