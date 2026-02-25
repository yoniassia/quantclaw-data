#!/usr/bin/env python3
"""
Smart Alert Delivery System
Phase 40: Multi-channel notifications (email, SMS, Discord, Telegram) with rate limiting

Features:
- Alert rule engine (price crosses, volume spikes, RSI thresholds)
- Multi-channel delivery (webhook, file-based, console)
- Rate limiting (max N alerts per hour)
- Alert history tracking with JSON storage
- Cooldown periods to prevent spam
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import hashlib

# Storage paths
ALERTS_DIR = Path(__file__).parent.parent / "data" / "alerts"
ALERTS_FILE = ALERTS_DIR / "alerts.json"
HISTORY_FILE = ALERTS_DIR / "alert_history.json"
TRIGGERS_FILE = ALERTS_DIR / "triggered_alerts.json"

ALERTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    symbol: str
    condition: str  # e.g., "price>200", "volume>1000000", "rsi<30"
    channels: List[str]  # ["console", "webhook", "file"]
    active: bool = True
    created_at: str = ""
    cooldown_minutes: int = 60  # Minimum time between same alert triggers
    max_per_hour: int = 3  # Max alerts per hour for this rule
    last_triggered: Optional[str] = None
    trigger_count_hour: int = 0
    trigger_count_total: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AlertTrigger:
    """Alert trigger event"""
    alert_id: str
    symbol: str
    condition: str
    triggered_at: str
    triggered_value: float
    channels: List[str]
    delivery_status: Dict[str, str]  # channel -> "success" | "failed" | "rate_limited"
    message: str


class AlertEngine:
    """Alert rule engine with rate limiting and multi-channel delivery"""

    def __init__(self):
        self.alerts: List[AlertRule] = []
        self.history: List[AlertTrigger] = []
        self.load_alerts()
        self.load_history()

    def load_alerts(self):
        """Load alerts from JSON storage"""
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE, 'r') as f:
                data = json.load(f)
                self.alerts = [AlertRule(**alert) for alert in data]
        else:
            self.alerts = []

    def save_alerts(self):
        """Save alerts to JSON storage"""
        with open(ALERTS_FILE, 'w') as f:
            json.dump([asdict(alert) for alert in self.alerts], f, indent=2)

    def load_history(self):
        """Load alert history"""
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                self.history = [AlertTrigger(**trigger) for trigger in data]
        else:
            self.history = []

    def save_history(self):
        """Save alert history"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump([asdict(trigger) for trigger in self.history], f, indent=2)

    def create_alert(
        self,
        symbol: str,
        condition: str,
        channels: Optional[List[str]] = None,
        cooldown_minutes: int = 60,
        max_per_hour: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertRule:
        """
        Create a new alert rule
        
        Args:
            symbol: Stock ticker symbol
            condition: Alert condition (e.g., "price>200", "volume>1000000", "rsi<30")
            channels: Delivery channels ["console", "webhook", "file"]
            cooldown_minutes: Minimum time between triggers
            max_per_hour: Maximum triggers per hour
            metadata: Additional metadata
        """
        if channels is None:
            channels = ["console"]

        # Generate unique ID
        alert_id = hashlib.md5(
            f"{symbol}:{condition}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        alert = AlertRule(
            id=alert_id,
            symbol=symbol.upper(),
            condition=condition,
            channels=channels,
            cooldown_minutes=cooldown_minutes,
            max_per_hour=max_per_hour,
            metadata=metadata or {}
        )

        self.alerts.append(alert)
        self.save_alerts()
        return alert

    def list_alerts(self, active_only: bool = False) -> List[AlertRule]:
        """List all alerts"""
        if active_only:
            return [a for a in self.alerts if a.active]
        return self.alerts

    def get_alert(self, alert_id: str) -> Optional[AlertRule]:
        """Get alert by ID"""
        for alert in self.alerts:
            if alert.id == alert_id:
                return alert
        return None

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        for i, alert in enumerate(self.alerts):
            if alert.id == alert_id:
                self.alerts.pop(i)
                self.save_alerts()
                return True
        return False

    def toggle_alert(self, alert_id: str, active: Optional[bool] = None) -> bool:
        """Toggle or set alert active status"""
        alert = self.get_alert(alert_id)
        if alert:
            if active is None:
                alert.active = not alert.active
            else:
                alert.active = active
            self.save_alerts()
            return True
        return False

    def evaluate_condition(self, condition: str, data: Dict[str, float]) -> tuple[bool, Optional[float]]:
        """
        Evaluate alert condition against current data
        
        Args:
            condition: Condition string (e.g., "price>200", "volume>1000000")
            data: Current market data
            
        Returns:
            (triggered: bool, value: float)
        """
        try:
            # Parse condition: "field operator value"
            for op in ['>=', '<=', '>', '<', '==', '!=']:
                if op in condition:
                    field, value = condition.split(op)
                    field = field.strip().lower()
                    target_value = float(value.strip())
                    
                    if field not in data:
                        return False, None
                    
                    current_value = data[field]
                    
                    # Evaluate condition
                    result = False
                    if op == '>':
                        result = current_value > target_value
                    elif op == '<':
                        result = current_value < target_value
                    elif op == '>=':
                        result = current_value >= target_value
                    elif op == '<=':
                        result = current_value <= target_value
                    elif op == '==':
                        result = abs(current_value - target_value) < 0.01
                    elif op == '!=':
                        result = abs(current_value - target_value) >= 0.01
                    
                    return result, current_value if result else None
            
            return False, None
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False, None

    def can_trigger(self, alert: AlertRule) -> tuple[bool, str]:
        """
        Check if alert can trigger based on rate limiting and cooldown
        
        Returns:
            (can_trigger: bool, reason: str)
        """
        now = datetime.utcnow()
        
        # Check cooldown period
        if alert.last_triggered:
            last_trigger = datetime.fromisoformat(alert.last_triggered)
            cooldown_delta = timedelta(minutes=alert.cooldown_minutes)
            if now - last_trigger < cooldown_delta:
                remaining = (last_trigger + cooldown_delta - now).total_seconds() / 60
                return False, f"Cooldown active ({remaining:.1f}m remaining)"
        
        # Check hourly rate limit
        # Reset counter if hour has passed
        if alert.last_triggered:
            last_trigger = datetime.fromisoformat(alert.last_triggered)
            if (now - last_trigger) > timedelta(hours=1):
                alert.trigger_count_hour = 0
        
        if alert.trigger_count_hour >= alert.max_per_hour:
            return False, f"Hourly rate limit reached ({alert.max_per_hour}/hour)"
        
        return True, "OK"

    def deliver_alert(self, alert: AlertRule, trigger_value: float, message: str) -> Dict[str, str]:
        """
        Deliver alert to configured channels
        
        Returns:
            Dict of channel -> status
        """
        delivery_status = {}
        
        for channel in alert.channels:
            try:
                if channel == "console":
                    print(f"\n🔔 ALERT TRIGGERED: {alert.symbol}")
                    print(f"   Condition: {alert.condition}")
                    print(f"   Current Value: {trigger_value}")
                    print(f"   Message: {message}")
                    print(f"   Time: {datetime.utcnow().isoformat()}\n")
                    delivery_status[channel] = "success"
                
                elif channel == "file":
                    # Write to file-based delivery
                    output_file = ALERTS_DIR / f"alert_{alert.id}_{int(time.time())}.txt"
                    with open(output_file, 'w') as f:
                        f.write(f"Alert: {alert.symbol}\n")
                        f.write(f"Condition: {alert.condition}\n")
                        f.write(f"Value: {trigger_value}\n")
                        f.write(f"Message: {message}\n")
                        f.write(f"Time: {datetime.utcnow().isoformat()}\n")
                    delivery_status[channel] = "success"
                
                elif channel == "webhook":
                    # Webhook delivery (simulate - would use requests in production)
                    webhook_data = {
                        "alert_id": alert.id,
                        "symbol": alert.symbol,
                        "condition": alert.condition,
                        "value": trigger_value,
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    # In production: requests.post(webhook_url, json=webhook_data)
                    # For now, save to webhook log
                    webhook_log = ALERTS_DIR / "webhook_log.jsonl"
                    with open(webhook_log, 'a') as f:
                        f.write(json.dumps(webhook_data) + "\n")
                    delivery_status[channel] = "success"
                
                else:
                    delivery_status[channel] = "unsupported"
            
            except Exception as e:
                delivery_status[channel] = f"failed: {str(e)}"
        
        return delivery_status

    def check_alerts(self, market_data: Dict[str, Dict[str, float]]) -> List[AlertTrigger]:
        """
        Check all active alerts against current market data
        
        Args:
            market_data: Dict of symbol -> {price, volume, rsi, etc.}
            
        Returns:
            List of triggered alerts
        """
        triggered = []
        
        for alert in self.alerts:
            if not alert.active:
                continue
            
            # Check if we have data for this symbol
            if alert.symbol not in market_data:
                continue
            
            # Evaluate condition
            is_triggered, trigger_value = self.evaluate_condition(
                alert.condition,
                market_data[alert.symbol]
            )
            
            if not is_triggered:
                continue
            
            # Check rate limiting
            can_trigger, reason = self.can_trigger(alert)
            if not can_trigger:
                print(f"⏸️  Alert {alert.id} rate limited: {reason}")
                continue
            
            # Deliver alert
            message = f"{alert.symbol} condition '{alert.condition}' triggered at {trigger_value}"
            delivery_status = self.deliver_alert(alert, trigger_value, message)
            
            # Record trigger
            trigger = AlertTrigger(
                alert_id=alert.id,
                symbol=alert.symbol,
                condition=alert.condition,
                triggered_at=datetime.utcnow().isoformat(),
                triggered_value=trigger_value,
                channels=alert.channels,
                delivery_status=delivery_status,
                message=message
            )
            
            # Update alert state
            alert.last_triggered = trigger.triggered_at
            alert.trigger_count_hour += 1
            alert.trigger_count_total += 1
            
            triggered.append(trigger)
            self.history.append(trigger)
        
        # Save updates
        if triggered:
            self.save_alerts()
            self.save_history()
        
        return triggered

    def get_history(self, limit: int = 50, symbol: Optional[str] = None) -> List[AlertTrigger]:
        """Get alert history"""
        history = self.history
        
        if symbol:
            history = [h for h in history if h.symbol == symbol.upper()]
        
        # Return most recent first
        return sorted(history, key=lambda x: x.triggered_at, reverse=True)[:limit]

    def stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alerts)
        active_alerts = len([a for a in self.alerts if a.active])
        total_triggers = len(self.history)
        
        # Triggers by symbol
        by_symbol = {}
        for trigger in self.history:
            by_symbol[trigger.symbol] = by_symbol.get(trigger.symbol, 0) + 1
        
        # Delivery success rate
        total_deliveries = 0
        successful_deliveries = 0
        for trigger in self.history:
            for channel, status in trigger.delivery_status.items():
                total_deliveries += 1
                if status == "success":
                    successful_deliveries += 1
        
        success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "total_triggers": total_triggers,
            "triggers_by_symbol": by_symbol,
            "delivery_success_rate": f"{success_rate:.1f}%",
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries
        }


# Singleton instance
_engine: Optional[AlertEngine] = None


def get_engine() -> AlertEngine:
    """Get or create AlertEngine singleton"""
    global _engine
    if _engine is None:
        _engine = AlertEngine()
    return _engine


# CLI-friendly functions
def create_alert(symbol: str, condition: str, channels: Optional[List[str]] = None, **kwargs) -> dict:
    """Create alert (CLI wrapper)"""
    engine = get_engine()
    alert = engine.create_alert(symbol, condition, channels, **kwargs)
    return {
        "id": alert.id,
        "symbol": alert.symbol,
        "condition": alert.condition,
        "channels": alert.channels,
        "active": alert.active,
        "created_at": alert.created_at
    }


def list_alerts(active_only: bool = False) -> List[dict]:
    """List alerts (CLI wrapper)"""
    engine = get_engine()
    alerts = engine.list_alerts(active_only)
    return [
        {
            "id": a.id,
            "symbol": a.symbol,
            "condition": a.condition,
            "channels": a.channels,
            "active": a.active,
            "triggers": a.trigger_count_total,
            "last_triggered": a.last_triggered
        }
        for a in alerts
    ]


def check_alerts(market_data: Dict[str, Dict[str, float]]) -> dict:
    """Check alerts (CLI wrapper)"""
    engine = get_engine()
    triggered = engine.check_alerts(market_data)
    return {
        "checked_at": datetime.utcnow().isoformat(),
        "triggered_count": len(triggered),
        "alerts": [
            {
                "alert_id": t.alert_id,
                "symbol": t.symbol,
                "condition": t.condition,
                "value": t.triggered_value,
                "message": t.message,
                "channels": t.channels,
                "delivery": t.delivery_status
            }
            for t in triggered
        ]
    }


def get_alert_stats() -> dict:
    """Get alert statistics"""
    engine = get_engine()
    return engine.stats()


def delete_alert(alert_id: str) -> dict:
    """Delete alert (CLI wrapper)"""
    engine = get_engine()
    success = engine.delete_alert(alert_id)
    return {"success": success, "alert_id": alert_id}


def get_history(limit: int = 50, symbol: Optional[str] = None) -> List[dict]:
    """Get alert history (CLI wrapper)"""
    engine = get_engine()
    history = engine.get_history(limit, symbol)
    return [
        {
            "alert_id": h.alert_id,
            "symbol": h.symbol,
            "condition": h.condition,
            "triggered_at": h.triggered_at,
            "value": h.triggered_value,
            "channels": h.channels,
            "delivery": h.delivery_status
        }
        for h in history
    ]


def run_cli():
    """CLI entry point"""
    import sys
    import argparse
    
    if len(sys.argv) < 2:
        print("Usage: python smart_alerts.py <command> [options]")
        print("Commands: alert-create, alert-list, alert-check, alert-delete, alert-history, alert-stats")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "alert-create":
        parser = argparse.ArgumentParser(description="Create alert")
        parser.add_argument("symbol", help="Stock symbol")
        parser.add_argument("--condition", required=True, help="Alert condition (e.g., 'price>200')")
        parser.add_argument("--channels", default="console", help="Comma-separated channels (console,file,webhook)")
        parser.add_argument("--cooldown", type=int, default=60, help="Cooldown minutes between triggers")
        parser.add_argument("--max-per-hour", type=int, default=3, help="Max alerts per hour")
        
        args = parser.parse_args(sys.argv[2:])
        channels = [c.strip() for c in args.channels.split(",")]
        
        result = create_alert(
            symbol=args.symbol,
            condition=args.condition,
            channels=channels,
            cooldown_minutes=args.cooldown,
            max_per_hour=args.max_per_hour
        )
        print(json.dumps(result, indent=2))
    
    elif command == "alert-list":
        parser = argparse.ArgumentParser(description="List alerts")
        parser.add_argument("--active", action="store_true", help="Show only active alerts")
        args = parser.parse_args(sys.argv[2:])
        
        alerts = list_alerts(active_only=args.active)
        print(json.dumps(alerts, indent=2))
    
    elif command == "alert-check":
        parser = argparse.ArgumentParser(description="Check alerts against current market data")
        parser.add_argument("--symbols", help="Comma-separated symbols to check (or blank for all)")
        args = parser.parse_args(sys.argv[2:])
        
        # Fetch real market data (simplified - would use actual data sources)
        symbols = []
        if args.symbols:
            symbols = [s.strip().upper() for s in args.symbols.split(",")]
        else:
            # Get all alert symbols
            engine = get_engine()
            symbols = list(set(a.symbol for a in engine.alerts if a.active))
        
        if not symbols:
            print(json.dumps({"error": "No symbols to check"}, indent=2))
            sys.exit(1)
        
        # Simulate market data (in production, fetch from real sources)
        market_data = {}
        for symbol in symbols:
            # TODO: Fetch real data from yfinance or other source
            market_data[symbol] = {
                "price": 0,  # Would fetch real price
                "volume": 0,  # Would fetch real volume
                "rsi": 50     # Would calculate real RSI
            }
        
        result = check_alerts(market_data)
        print(json.dumps(result, indent=2))
    
    elif command == "alert-delete":
        if len(sys.argv) < 3:
            print("Usage: python smart_alerts.py alert-delete ALERT_ID")
            sys.exit(1)
        
        alert_id = sys.argv[2]
        result = delete_alert(alert_id)
        print(json.dumps(result, indent=2))
    
    elif command == "alert-history":
        parser = argparse.ArgumentParser(description="View alert history")
        parser.add_argument("--symbol", help="Filter by symbol")
        parser.add_argument("--limit", type=int, default=50, help="Max records to show")
        args = parser.parse_args(sys.argv[2:])
        
        history = get_history(limit=args.limit, symbol=args.symbol)
        print(json.dumps(history, indent=2))
    
    elif command == "alert-stats":
        stats = get_alert_stats()
        print(json.dumps(stats, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
