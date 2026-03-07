"""Exchange Rate API — Live currency exchange rates from open.er-api.com.

Provides real-time FX rates for 150+ currencies via the free Open Exchange Rate API.
No API key required. Supports conversion, multi-currency quotes, and FX summaries.

Data source: https://open.er-api.com/ (free, no auth)
Update frequency: ~daily
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

_BASE_URL = "https://open.er-api.com/v6/latest"
_MAJOR_PAIRS = ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]


def _fetch_rates(base: str = "USD") -> dict[str, Any]:
    """Internal: fetch latest rates for a base currency.

    Args:
        base: ISO 4217 currency code.

    Returns:
        Full API response dict with 'rates', 'base_code', 'time_last_update_utc'.
    """
    url = f"{_BASE_URL}/{base.upper()}"
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data.get("result") != "success":
        raise ValueError(f"API error: {data.get('error-type', 'unknown')}")
    return data


def get_latest_rates(base: str = "USD") -> dict[str, Any]:
    """Get all current exchange rates for a base currency.

    Args:
        base: Base currency code (default USD).

    Returns:
        Dict with base, update time, and rates mapping {currency: rate}.
    """
    try:
        data = _fetch_rates(base)
        return {
            "base": data["base_code"],
            "last_update": data.get("time_last_update_utc", ""),
            "rates": data["rates"],
            "count": len(data["rates"]),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "base": base.upper()}


def get_rate(base: str, target: str) -> dict[str, Any]:
    """Get exchange rate for a single currency pair.

    Args:
        base: Base currency code (e.g. 'USD').
        target: Target currency code (e.g. 'EUR').

    Returns:
        Dict with pair, rate, and timestamp.
    """
    try:
        data = _fetch_rates(base)
        target_upper = target.upper()
        rates = data["rates"]
        if target_upper not in rates:
            return {"error": f"Currency {target_upper} not found", "available": len(rates)}
        return {
            "pair": f"{data['base_code']}/{target_upper}",
            "rate": rates[target_upper],
            "last_update": data.get("time_last_update_utc", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def convert(amount: float, from_currency: str, to_currency: str) -> dict[str, Any]:
    """Convert an amount between two currencies.

    Args:
        amount: Amount to convert.
        from_currency: Source currency code.
        to_currency: Target currency code.

    Returns:
        Dict with original amount, converted amount, rate used, and pair.
    """
    try:
        data = _fetch_rates(from_currency)
        to_upper = to_currency.upper()
        rates = data["rates"]
        if to_upper not in rates:
            return {"error": f"Currency {to_upper} not found"}
        rate = rates[to_upper]
        return {
            "from": data["base_code"],
            "to": to_upper,
            "amount": amount,
            "rate": rate,
            "converted": round(amount * rate, 4),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_supported_currencies() -> dict[str, Any]:
    """List all available currency codes.

    Returns:
        Dict with sorted list of currency codes and count.
    """
    try:
        data = _fetch_rates("USD")
        currencies = sorted(data["rates"].keys())
        return {
            "currencies": currencies,
            "count": len(currencies),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def multi_convert(amount: float, from_currency: str, targets: list[str]) -> dict[str, Any]:
    """Convert an amount to multiple target currencies in one call.

    Args:
        amount: Amount to convert.
        from_currency: Source currency code.
        targets: List of target currency codes.

    Returns:
        Dict with conversions list and summary.
    """
    try:
        data = _fetch_rates(from_currency)
        rates = data["rates"]
        base = data["base_code"]
        conversions = {}
        errors = []
        for t in targets:
            t_upper = t.upper()
            if t_upper in rates:
                conversions[t_upper] = {
                    "rate": rates[t_upper],
                    "converted": round(amount * rates[t_upper], 4),
                }
            else:
                errors.append(t_upper)
        result = {
            "from": base,
            "amount": amount,
            "conversions": conversions,
            "count": len(conversions),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        if errors:
            result["not_found"] = errors
        return result
    except Exception as e:
        return {"error": str(e)}


def fx_summary(base: str = "USD") -> dict[str, Any]:
    """Summary of major FX pairs (EUR, GBP, JPY, CHF, CAD, AUD).

    Args:
        base: Base currency code (default USD).

    Returns:
        Dict with major pair rates, inverse rates, and metadata.
    """
    try:
        data = _fetch_rates(base)
        rates = data["rates"]
        base_code = data["base_code"]
        majors = {}
        for ccy in _MAJOR_PAIRS:
            if ccy in rates:
                rate = rates[ccy]
                majors[ccy] = {
                    "rate": rate,
                    "inverse": round(1.0 / rate, 6) if rate else None,
                    "pair": f"{base_code}/{ccy}",
                }
        return {
            "base": base_code,
            "majors": majors,
            "last_update": data.get("time_last_update_utc", ""),
            "total_currencies": len(rates),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    print("=== Exchange Rate API Module ===")
    r = get_latest_rates("USD")
    if "error" in r:
        print(f"ERROR: {r['error']}")
        sys.exit(1)
    print(f"Base: {r['base']} | Currencies: {r['count']}")
    s = fx_summary("USD")
    for ccy, info in s.get("majors", {}).items():
        print(f"  {info['pair']}: {info['rate']}")
