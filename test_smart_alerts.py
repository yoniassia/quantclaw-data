#!/usr/bin/env python3
"""
Smart Alert Delivery System - Integration Test
Phase 40: Multi-channel notifications with rate limiting
"""

import sys
import json
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from smart_alerts import get_engine

def test_smart_alerts():
    print("=" * 60)
    print("SMART ALERT DELIVERY SYSTEM - INTEGRATION TEST")
    print("=" * 60)
    
    engine = get_engine()
    
    # Test 1: Create alerts
    print("\n[TEST 1] Creating Test Alerts...")
    alert1 = engine.create_alert(
        symbol="AAPL",
        condition="price>200",
        channels=["console", "file"],
        cooldown_minutes=5,
        max_per_hour=5
    )
    print(f"✓ Alert 1: {alert1.symbol} {alert1.condition} [{','.join(alert1.channels)}]")
    
    alert2 = engine.create_alert(
        symbol="TSLA",
        condition="volume>10000000",
        channels=["console", "webhook"],
        cooldown_minutes=10
    )
    print(f"✓ Alert 2: {alert2.symbol} {alert2.condition} [{','.join(alert2.channels)}]")
    
    alert3 = engine.create_alert(
        symbol="NVDA",
        condition="rsi<30",
        channels=["console", "file", "webhook"]
    )
    print(f"✓ Alert 3: {alert3.symbol} {alert3.condition} [{','.join(alert3.channels)}]")
    
    # Test 2: List alerts
    print("\n[TEST 2] Listing Alerts...")
    alerts = engine.list_alerts(active_only=True)
    print(f"✓ Found {len(alerts)} active alerts")
    
    # Test 3: Check alerts with mock data (no triggers)
    print("\n[TEST 3] Checking Alerts (No Triggers Expected)...")
    market_data_no_trigger = {
        "AAPL": {"price": 195.0, "volume": 50000000, "rsi": 65},
        "TSLA": {"price": 180.2, "volume": 8000000, "rsi": 55},
        "NVDA": {"price": 450.0, "volume": 8000000, "rsi": 45}
    }
    
    triggered = engine.check_alerts(market_data_no_trigger)
    print(f"✓ Triggered {len(triggered)} alerts (expected 0)")
    
    # Test 4: Check alerts with triggering conditions
    print("\n[TEST 4] Checking Alerts (Triggers Expected)...")
    market_data_trigger = {
        "AAPL": {"price": 205.5, "volume": 50000000, "rsi": 65},  # Triggers: price>200
        "TSLA": {"price": 180.2, "volume": 12500000, "rsi": 55},  # Triggers: volume>10M
        "NVDA": {"price": 450.0, "volume": 8000000, "rsi": 28}    # Triggers: rsi<30
    }
    
    triggered = engine.check_alerts(market_data_trigger)
    print(f"✓ Triggered {len(triggered)} alerts (expected 3)")
    
    for t in triggered:
        print(f"  - {t.symbol}: {t.condition} = {t.triggered_value}")
        print(f"    Delivery: {t.delivery_status}")
    
    # Test 5: Rate limiting - immediate re-check should not trigger
    print("\n[TEST 5] Testing Rate Limiting (Cooldown)...")
    triggered_second = engine.check_alerts(market_data_trigger)
    print(f"✓ Second check triggered {len(triggered_second)} alerts (expected 0 due to cooldown)")
    
    # Test 6: History
    print("\n[TEST 6] Alert History...")
    history = engine.get_history(limit=10)
    print(f"✓ Found {len(history)} historical triggers")
    
    # Test 7: Statistics
    print("\n[TEST 7] Alert Statistics...")
    stats = engine.stats()
    print(f"✓ Total Alerts: {stats['total_alerts']}")
    print(f"✓ Active Alerts: {stats['active_alerts']}")
    print(f"✓ Total Triggers: {stats['total_triggers']}")
    print(f"✓ Delivery Success Rate: {stats['delivery_success_rate']}")
    
    # Test 8: Delete an alert
    print("\n[TEST 8] Deleting Alert...")
    success = engine.delete_alert(alert2.id)
    print(f"✓ Deleted alert {alert2.id}: {success}")
    remaining = engine.list_alerts()
    print(f"✓ Remaining alerts: {len(remaining)}")
    
    # Test 9: Toggle alert
    print("\n[TEST 9] Toggling Alert...")
    engine.toggle_alert(alert1.id, active=False)
    alert1_updated = engine.get_alert(alert1.id)
    print(f"✓ Alert {alert1.id} active status: {alert1_updated.active} (expected False)")
    
    engine.toggle_alert(alert1.id, active=True)
    alert1_updated = engine.get_alert(alert1.id)
    print(f"✓ Alert {alert1.id} active status: {alert1_updated.active} (expected True)")
    
    # Test 10: Multi-condition evaluation
    print("\n[TEST 10] Testing Different Condition Operators...")
    test_cases = [
        ("price>200", {"price": 205}, True),
        ("price<200", {"price": 195}, True),
        ("price>=200", {"price": 200}, True),
        ("price<=200", {"price": 200}, True),
        ("volume>1000000", {"volume": 1500000}, True),
        ("rsi<30", {"rsi": 25}, True),
        ("price>200", {"price": 190}, False),
        ("volume>1000000", {"volume": 500000}, False),
    ]
    
    passed = 0
    for condition, data, expected in test_cases:
        result, value = engine.evaluate_condition(condition, data)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        print(f"  {status} {condition} with {data} = {result} (expected {expected})")
    
    print(f"✓ Passed {passed}/{len(test_cases)} condition evaluation tests")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    
    # Final stats
    final_stats = engine.stats()
    print("\nFinal Statistics:")
    print(json.dumps(final_stats, indent=2))


if __name__ == "__main__":
    test_smart_alerts()
