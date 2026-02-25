#!/usr/bin/env python3
"""
QuantClaw Data — Data Integrity Test Suite
Tests module imports, function signatures, data types, and API responses.
Run: python tests/test_data_integrity.py
  or: python -m pytest tests/test_data_integrity.py -v
"""

import os
import sys
import importlib
import json
import time
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MODULES_DIR = PROJECT_ROOT / "modules"
API_BASE = "https://data.quantclaw.org/api/v1"

# Test results
results = {"passed": 0, "failed": 0, "skipped": 0, "errors": []}


def log_pass(msg):
    results["passed"] += 1
    print(f"  ✅ {msg}")


def log_fail(msg, err=None):
    results["failed"] += 1
    error_msg = f"{msg}: {err}" if err else msg
    results["errors"].append(error_msg)
    print(f"  ❌ {msg}" + (f" — {err}" if err else ""))


def log_skip(msg):
    results["skipped"] += 1
    print(f"  ⏭️  {msg}")


# ========== TEST 1: Module Import ==========
def test_module_imports():
    """Every .py file in modules/ must import without errors."""
    print("\n🧪 TEST 1: Module Imports")
    py_files = sorted(MODULES_DIR.glob("*.py"))
    print(f"   Found {len(py_files)} Python modules")

    for f in py_files:
        if f.name.startswith("__"):
            continue
        mod_name = f"modules.{f.stem}"
        try:
            importlib.import_module(mod_name)
            log_pass(f"{mod_name} imports OK")
        except Exception as e:
            log_fail(f"{mod_name} import failed", str(e)[:120])


# ========== TEST 2: Module Has Docstring ==========
def test_module_docstrings():
    """Every module should have a docstring."""
    print("\n🧪 TEST 2: Module Docstrings")
    py_files = sorted(MODULES_DIR.glob("*.py"))

    for f in py_files:
        if f.name.startswith("__"):
            continue
        mod_name = f"modules.{f.stem}"
        try:
            mod = importlib.import_module(mod_name)
            if mod.__doc__ and len(mod.__doc__.strip()) > 10:
                log_pass(f"{f.stem} has docstring")
            else:
                log_fail(f"{f.stem} missing or short docstring")
        except Exception:
            log_skip(f"{f.stem} (import failed)")


# ========== TEST 3: Module Has Callable Functions ==========
def test_module_functions():
    """Every module should expose at least 2 callable functions."""
    print("\n🧪 TEST 3: Module Functions (min 2 per module)")
    py_files = sorted(MODULES_DIR.glob("*.py"))

    for f in py_files:
        if f.name.startswith("__"):
            continue
        mod_name = f"modules.{f.stem}"
        try:
            mod = importlib.import_module(mod_name)
            funcs = [name for name in dir(mod) if callable(getattr(mod, name)) and not name.startswith("_")]
            if len(funcs) >= 2:
                log_pass(f"{f.stem} has {len(funcs)} functions")
            else:
                log_fail(f"{f.stem} has only {len(funcs)} functions (need ≥2)")
        except Exception:
            log_skip(f"{f.stem} (import failed)")


# ========== TEST 4: Core Module Smoke Tests ==========
def test_core_smoke():
    """Test that core modules return expected data types."""
    print("\n🧪 TEST 4: Core Module Smoke Tests")

    smoke_tests = [
        ("modules.core_market_data", "get_price", ("AAPL",), dict),
        ("modules.technicals", "get_technicals", ("AAPL",), dict),
        ("modules.fama_french", "run_regression", ("AAPL",), dict),
        ("modules.monte_carlo", "simulate", ("AAPL",), dict),
        ("modules.sector_rotation", "get_sector_performance", (), (dict, list)),
    ]

    for mod_name, func_name, args, expected_type in smoke_tests:
        try:
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name, None)
            if func is None:
                log_skip(f"{mod_name}.{func_name} not found")
                continue
            result = func(*args)
            if isinstance(result, expected_type):
                log_pass(f"{mod_name}.{func_name}() returns {type(result).__name__}")
            else:
                log_fail(f"{mod_name}.{func_name}() returned {type(result).__name__}, expected {expected_type}")
        except Exception as e:
            log_fail(f"{mod_name}.{func_name}() raised error", str(e)[:120])


# ========== TEST 5: API Endpoint Health ==========
def test_api_endpoints():
    """Test that API endpoints return valid JSON."""
    print("\n🧪 TEST 5: API Endpoint Health")

    try:
        import urllib.request
    except ImportError:
        log_skip("urllib not available")
        return

    endpoints = [
        "/prices?ticker=AAPL",
        "/monte-carlo?action=simulate&symbol=SPY&simulations=100&days=10",
        "/cds?action=credit-spreads",
        "/dark-pool?action=summary&symbol=AAPL",
        "/earnings-quality?action=analyze&symbol=MSFT",
    ]

    for ep in endpoints:
        url = f"{API_BASE}{ep}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw-Test/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                data = json.loads(resp.read())
                if status == 200 and isinstance(data, dict):
                    log_pass(f"GET {ep.split('?')[0]} → 200 OK")
                else:
                    log_fail(f"GET {ep.split('?')[0]} → {status}")
        except Exception as e:
            log_fail(f"GET {ep.split('?')[0]}", str(e)[:100])


# ========== TEST 6: No Duplicate Module Names ==========
def test_no_duplicates():
    """No duplicate module file names."""
    print("\n🧪 TEST 6: No Duplicate Modules")
    py_files = [f.stem for f in MODULES_DIR.glob("*.py") if not f.name.startswith("__")]
    dupes = [name for name in py_files if py_files.count(name) > 1]
    if dupes:
        log_fail(f"Duplicate modules found: {set(dupes)}")
    else:
        log_pass(f"All {len(py_files)} module names are unique")


# ========== TEST 7: File Size Sanity ==========
def test_file_sizes():
    """No empty or suspiciously small modules (< 100 bytes)."""
    print("\n🧪 TEST 7: File Size Sanity (min 100 bytes)")
    py_files = sorted(MODULES_DIR.glob("*.py"))
    for f in py_files:
        if f.name.startswith("__"):
            continue
        size = f.stat().st_size
        if size < 100:
            log_fail(f"{f.stem} is only {size} bytes (too small)")
        elif size < 500:
            log_pass(f"{f.stem} is {size} bytes (small but OK)")
        else:
            log_pass(f"{f.stem} is {size:,} bytes")


# ========== MAIN ==========
def main():
    print("=" * 60)
    print("🧪 QuantClaw Data — Data Integrity Test Suite")
    print(f"📁 Modules dir: {MODULES_DIR}")
    print(f"🌐 API base: {API_BASE}")
    print("=" * 60)

    start = time.time()

    test_module_imports()
    test_module_docstrings()
    test_module_functions()
    test_no_duplicates()
    test_file_sizes()
    test_core_smoke()
    test_api_endpoints()

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {results['passed']} passed, {results['failed']} failed, {results['skipped']} skipped")
    print(f"⏱️  Time: {elapsed:.1f}s")

    if results["errors"]:
        print(f"\n❌ FAILURES ({len(results['errors'])}):")
        for err in results["errors"][:20]:
            print(f"   • {err}")

    print("=" * 60)

    # Exit code for CI
    sys.exit(1 if results["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
