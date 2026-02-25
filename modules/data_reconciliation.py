#!/usr/bin/env python3
"""
DATA RECONCILIATION MODULE
Compare data across sources, flag discrepancies, confidence-based voting
Free APIs: Yahoo Finance, CoinGecko, FRED
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional
import requests
from pathlib import Path

# Source reliability tracking
RELIABILITY_FILE = Path(__file__).parent.parent / "data" / "source_reliability.json"
DISCREPANCY_LOG = Path(__file__).parent.parent / "data" / "discrepancy_log.json"

# Ensure data directory exists
RELIABILITY_FILE.parent.mkdir(exist_ok=True)

# Source configurations with initial confidence scores
SOURCE_CONFIG = {
    'yahoo': {
        'name': 'Yahoo Finance',
        'base_confidence': 0.85,
        'types': ['stocks', 'crypto', 'forex', 'commodities'],
        'latency': 'real-time',
        'reliability_history': []
    },
    'coingecko': {
        'name': 'CoinGecko',
        'base_confidence': 0.90,
        'types': ['crypto'],
        'latency': 'near-real-time',
        'reliability_history': []
    },
    'fred': {
        'name': 'FRED (Federal Reserve)',
        'base_confidence': 0.95,
        'types': ['economic_data', 'rates', 'indicators'],
        'latency': 'delayed',
        'reliability_history': []
    }
}


class SourceReliabilityTracker:
    """Track and update source reliability scores"""
    
    def __init__(self):
        self.reliability = self._load_reliability()
    
    def _load_reliability(self) -> Dict:
        """Load reliability history"""
        if RELIABILITY_FILE.exists():
            with open(RELIABILITY_FILE, 'r') as f:
                return json.load(f)
        return {source: config.copy() for source, config in SOURCE_CONFIG.items()}
    
    def _save_reliability(self):
        """Save reliability history"""
        with open(RELIABILITY_FILE, 'w') as f:
            json.dump(self.reliability, f, indent=2)
    
    def get_confidence(self, source: str) -> float:
        """Get current confidence score for source"""
        if source not in self.reliability:
            return 0.5  # default for unknown sources
        
        history = self.reliability[source].get('reliability_history', [])
        if not history:
            return self.reliability[source]['base_confidence']
        
        # Weight recent performance more heavily
        recent = history[-20:]  # last 20 data points
        if len(recent) >= 3:
            weights = [1.0 + (i * 0.1) for i in range(len(recent))]
            weighted_sum = sum(score * weight for score, weight in zip(recent, weights))
            weight_total = sum(weights)
            return weighted_sum / weight_total
        
        return self.reliability[source]['base_confidence']
    
    def update_reliability(self, source: str, was_accurate: bool):
        """Update reliability based on accuracy"""
        if source not in self.reliability:
            return
        
        score = 1.0 if was_accurate else 0.0
        self.reliability[source]['reliability_history'].append(score)
        
        # Keep only last 100 data points
        if len(self.reliability[source]['reliability_history']) > 100:
            self.reliability[source]['reliability_history'] = \
                self.reliability[source]['reliability_history'][-100:]
        
        self._save_reliability()


class DiscrepancyLogger:
    """Log and track discrepancies across sources"""
    
    def __init__(self):
        self.log = self._load_log()
    
    def _load_log(self) -> List[Dict]:
        """Load discrepancy log"""
        if DISCREPANCY_LOG.exists():
            with open(DISCREPANCY_LOG, 'r') as f:
                return json.load(f)
        return []
    
    def _save_log(self):
        """Save discrepancy log"""
        with open(DISCREPANCY_LOG, 'w') as f:
            json.dump(self.log[-1000:], f, indent=2)  # Keep last 1000 entries
    
    def log_discrepancy(self, symbol: str, data_type: str, values: Dict, 
                       consensus: float, variance: float):
        """Log a discrepancy event"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'data_type': data_type,
            'values': values,
            'consensus': consensus,
            'variance': variance,
            'max_deviation': max(abs(v - consensus) for v in values.values() if v is not None)
        }
        self.log.append(entry)
        self._save_log()
    
    def get_recent(self, hours: int = 24, symbol: Optional[str] = None) -> List[Dict]:
        """Get recent discrepancies"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            entry for entry in self.log
            if datetime.fromisoformat(entry['timestamp']) > cutoff
        ]
        
        if symbol:
            recent = [e for e in recent if e['symbol'].upper() == symbol.upper()]
        
        return recent


class DataReconciler:
    """Main reconciliation engine"""
    
    def __init__(self):
        self.reliability_tracker = SourceReliabilityTracker()
        self.discrepancy_logger = DiscrepancyLogger()
    
    def fetch_yahoo_price(self, symbol: str) -> Optional[float]:
        """Fetch price from Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {'interval': '1d', 'range': '1d'}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            quote = data['chart']['result'][0]['meta']
            return quote.get('regularMarketPrice') or quote.get('previousClose')
        
        except Exception as e:
            print(f"⚠️  Yahoo Finance error: {e}", file=sys.stderr)
            return None
    
    def fetch_coingecko_price(self, symbol: str) -> Optional[float]:
        """Fetch crypto price from CoinGecko"""
        try:
            # Map common crypto symbols
            coin_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDT': 'tether',
                'BNB': 'binancecoin',
                'SOL': 'solana',
                'ADA': 'cardano',
                'DOGE': 'dogecoin',
                'MATIC': 'matic-network'
            }
            
            coin_id = coin_map.get(symbol.upper())
            if not coin_id:
                # Try to use symbol directly
                coin_id = symbol.lower()
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': coin_id, 'vs_currencies': 'usd'}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return data.get(coin_id, {}).get('usd')
        
        except Exception as e:
            print(f"⚠️  CoinGecko error: {e}", file=sys.stderr)
            return None
    
    def fetch_fred_data(self, series_id: str) -> Optional[float]:
        """Fetch economic data from FRED (no API key required for latest)"""
        try:
            # Use the public JSON endpoint for latest observation
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv"
            params = {'id': series_id, 'cosd': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            # Parse CSV (simple parsing)
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                last_line = lines[-1]
                parts = last_line.split(',')
                if len(parts) >= 2 and parts[1] not in ['.', '']:
                    return float(parts[1])
            
            return None
        
        except Exception as e:
            print(f"⚠️  FRED error: {e}", file=sys.stderr)
            return None
    
    def reconcile_price(self, symbol: str, asset_type: str = 'auto') -> Dict[str, Any]:
        """Reconcile price across multiple sources"""
        print(f"\n🔍 Reconciling price for {symbol}...")
        
        values = {}
        confidences = {}
        
        # Determine which sources to query
        is_crypto = asset_type == 'crypto' or symbol.upper() in ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'ADA', 'DOGE', 'MATIC']
        
        # Fetch from Yahoo Finance
        yahoo_price = self.fetch_yahoo_price(symbol)
        if yahoo_price:
            values['yahoo'] = yahoo_price
            confidences['yahoo'] = self.reliability_tracker.get_confidence('yahoo')
        
        # Fetch from CoinGecko if crypto
        if is_crypto:
            cg_price = self.fetch_coingecko_price(symbol)
            if cg_price:
                values['coingecko'] = cg_price
                confidences['coingecko'] = self.reliability_tracker.get_confidence('coingecko')
        
        if not values:
            return {
                'symbol': symbol,
                'status': 'error',
                'message': 'No data available from any source'
            }
        
        # Calculate consensus using confidence-weighted voting
        consensus = self._calculate_consensus(values, confidences)
        variance = self._calculate_variance(values, consensus)
        
        # Detect discrepancies
        discrepancies = self._detect_discrepancies(values, consensus, threshold=0.05)
        
        if discrepancies:
            self.discrepancy_logger.log_discrepancy(
                symbol, 'price', values, consensus, variance
            )
        
        result = {
            'symbol': symbol,
            'consensus_price': round(consensus, 2),
            'sources': [
                {
                    'name': source,
                    'price': round(price, 2),
                    'confidence': round(confidences[source], 2),
                    'deviation': round(abs(price - consensus) / consensus * 100, 2)
                }
                for source, price in values.items()
            ],
            'variance': round(variance, 4),
            'discrepancies': discrepancies,
            'quality_score': self._calculate_quality_score(values, consensus, confidences)
        }
        
        return result
    
    def _calculate_consensus(self, values: Dict[str, float], 
                            confidences: Dict[str, float]) -> float:
        """Calculate confidence-weighted consensus value"""
        weighted_sum = sum(value * confidences[source] for source, value in values.items())
        total_confidence = sum(confidences[source] for source in values.keys())
        
        return weighted_sum / total_confidence if total_confidence > 0 else 0.0
    
    def _calculate_variance(self, values: Dict[str, float], consensus: float) -> float:
        """Calculate variance from consensus"""
        if len(values) < 2:
            return 0.0
        
        squared_diffs = [(v - consensus) ** 2 for v in values.values()]
        return sum(squared_diffs) / len(squared_diffs)
    
    def _detect_discrepancies(self, values: Dict[str, float], 
                             consensus: float, threshold: float = 0.05) -> List[str]:
        """Detect sources with significant deviation"""
        discrepancies = []
        
        for source, value in values.items():
            deviation = abs(value - consensus) / consensus
            if deviation > threshold:
                discrepancies.append(f"{source}: {deviation*100:.2f}% deviation")
        
        return discrepancies
    
    def _calculate_quality_score(self, values: Dict[str, float], 
                                 consensus: float, confidences: Dict[str, float]) -> float:
        """Calculate overall data quality score (0-100)"""
        # Factors:
        # 1. Number of sources (more is better)
        # 2. Variance (lower is better)
        # 3. Average confidence (higher is better)
        
        source_score = min(len(values) / 3.0, 1.0) * 30  # Max 30 points
        
        variance = self._calculate_variance(values, consensus)
        variance_score = max(0, 30 - (variance * 1000))  # Max 30 points
        
        avg_confidence = sum(confidences.values()) / len(confidences) if confidences else 0
        confidence_score = avg_confidence * 40  # Max 40 points
        
        return round(source_score + variance_score + confidence_score, 1)
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        print("\n📊 Generating Data Quality Report...")
        
        recent_discrepancies = self.discrepancy_logger.get_recent(hours=24)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'period': 'Last 24 hours',
            'summary': {
                'total_discrepancies': len(recent_discrepancies),
                'unique_symbols': len(set(d['symbol'] for d in recent_discrepancies)),
                'avg_variance': round(
                    sum(d['variance'] for d in recent_discrepancies) / len(recent_discrepancies), 4
                ) if recent_discrepancies else 0.0
            },
            'source_reliability': {
                source: {
                    'confidence': round(self.reliability_tracker.get_confidence(source), 3),
                    'status': self._reliability_status(self.reliability_tracker.get_confidence(source))
                }
                for source in SOURCE_CONFIG.keys()
            },
            'top_discrepancies': sorted(
                recent_discrepancies,
                key=lambda x: x['max_deviation'],
                reverse=True
            )[:10]
        }
        
        return report
    
    def _reliability_status(self, confidence: float) -> str:
        """Get status label for reliability"""
        if confidence >= 0.90:
            return "EXCELLENT"
        elif confidence >= 0.80:
            return "GOOD"
        elif confidence >= 0.70:
            return "FAIR"
        else:
            return "POOR"
    
    def get_source_reliability_rankings(self) -> List[Dict[str, Any]]:
        """Get source reliability rankings"""
        rankings = []
        
        for source, config in self.reliability_tracker.reliability.items():
            confidence = self.reliability_tracker.get_confidence(source)
            history = config.get('reliability_history', [])
            
            rankings.append({
                'source': config['name'],
                'confidence': round(confidence, 3),
                'status': self._reliability_status(confidence),
                'data_points': len(history),
                'recent_accuracy': round(
                    sum(history[-20:]) / len(history[-20:]) * 100, 1
                ) if history else 0.0,
                'supported_types': config['types']
            })
        
        return sorted(rankings, key=lambda x: x['confidence'], reverse=True)


def reconcile_price_command(args):
    """CLI command: reconcile-price"""
    reconciler = DataReconciler()
    result = reconciler.reconcile_price(args.symbol, args.type)
    
    if result.get('status') == 'error':
        print(f"\n❌ {result['message']}")
        return
    
    print(f"\n💰 Price Reconciliation: {result['symbol']}")
    print(f"   Consensus Price: ${result['consensus_price']}")
    print(f"   Quality Score: {result['quality_score']}/100\n")
    
    print("📊 Source Breakdown:")
    for source in result['sources']:
        status = "✅" if source['deviation'] < 2.0 else "⚠️" if source['deviation'] < 5.0 else "❌"
        print(f"   {status} {source['name']:20} ${source['price']:>10.2f}  "
              f"(confidence: {source['confidence']}, deviation: {source['deviation']}%)")
    
    if result['discrepancies']:
        print("\n⚠️  Discrepancies Detected:")
        for disc in result['discrepancies']:
            print(f"   - {disc}")
    
    print(f"\n   Variance: {result['variance']:.4f}")


def data_quality_report_command(args):
    """CLI command: data-quality-report"""
    reconciler = DataReconciler()
    report = reconciler.generate_quality_report()
    
    print("\n📊 DATA QUALITY REPORT")
    print(f"   Period: {report['period']}")
    print(f"   Generated: {report['timestamp']}\n")
    
    print("📈 Summary:")
    print(f"   Total Discrepancies: {report['summary']['total_discrepancies']}")
    print(f"   Unique Symbols: {report['summary']['unique_symbols']}")
    print(f"   Avg Variance: {report['summary']['avg_variance']}\n")
    
    print("🎯 Source Reliability:")
    for source, data in report['source_reliability'].items():
        status_icon = "✅" if data['status'] == "EXCELLENT" else "⚠️" if data['status'] == "GOOD" else "❌"
        print(f"   {status_icon} {source:12} {data['confidence']:.3f} ({data['status']})")
    
    if report['top_discrepancies']:
        print("\n🔍 Top Discrepancies (by deviation):")
        for i, disc in enumerate(report['top_discrepancies'][:5], 1):
            print(f"   {i}. {disc['symbol']} - Max Deviation: {disc['max_deviation']:.2f}")
            print(f"      Sources: {', '.join(f'{k}: ${v:.2f}' for k, v in disc['values'].items())}")


def source_reliability_command(args):
    """CLI command: source-reliability"""
    reconciler = DataReconciler()
    rankings = reconciler.get_source_reliability_rankings()
    
    print("\n🏆 SOURCE RELIABILITY RANKINGS\n")
    
    for i, source in enumerate(rankings, 1):
        status_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"{status_icon} {i}. {source['source']}")
        print(f"      Confidence: {source['confidence']} ({source['status']})")
        print(f"      Recent Accuracy: {source['recent_accuracy']}%")
        print(f"      Data Points: {source['data_points']}")
        print(f"      Supported: {', '.join(source['supported_types'])}\n")


def discrepancy_log_command(args):
    """CLI command: discrepancy-log"""
    logger = DiscrepancyLogger()
    recent = logger.get_recent(hours=args.hours, symbol=args.symbol)
    
    print(f"\n📋 DISCREPANCY LOG (Last {args.hours} hours)")
    if args.symbol:
        print(f"   Filtered by symbol: {args.symbol}")
    print(f"   Total entries: {len(recent)}\n")
    
    if not recent:
        print("   No discrepancies found.")
        return
    
    for entry in recent[-20:]:  # Show last 20
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"⚠️  {entry['symbol']} @ {timestamp}")
        print(f"   Consensus: ${entry['consensus']:.2f}, Max Deviation: {entry['max_deviation']:.2f}")
        print(f"   Sources: {', '.join(f'{k}: ${v:.2f}' for k, v in entry['values'].items())}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Data Reconciliation CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # reconcile-price
    reconcile_parser = subparsers.add_parser('reconcile-price', 
                                            help='Reconcile price across sources')
    reconcile_parser.add_argument('symbol', help='Stock/crypto symbol')
    reconcile_parser.add_argument('--type', choices=['auto', 'stock', 'crypto'], 
                                  default='auto', help='Asset type')
    
    # data-quality-report
    subparsers.add_parser('data-quality-report', 
                         help='Generate data quality report')
    
    # source-reliability
    subparsers.add_parser('source-reliability', 
                         help='Show source reliability rankings')
    
    # discrepancy-log
    disc_parser = subparsers.add_parser('discrepancy-log', 
                                       help='Show recent discrepancies')
    disc_parser.add_argument('--hours', type=int, default=24, 
                            help='Hours to look back')
    disc_parser.add_argument('--symbol', help='Filter by symbol')
    
    args = parser.parse_args()
    
    if args.command == 'reconcile-price':
        reconcile_price_command(args)
    elif args.command == 'data-quality-report':
        data_quality_report_command(args)
    elif args.command == 'source-reliability':
        source_reliability_command(args)
    elif args.command == 'discrepancy-log':
        discrepancy_log_command(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
