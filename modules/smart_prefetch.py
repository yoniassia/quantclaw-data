#!/usr/bin/env python3
"""
Smart Data Prefetching Module
ML-based prediction of which data will be requested next
Preloads during idle to improve cache hit rates
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import argparse

# Usage stats file
STATS_FILE = Path(__file__).parent.parent / "data" / "prefetch_stats.json"
CONFIG_FILE = Path(__file__).parent.parent / "data" / "prefetch_config.json"
CACHE_DIR = Path(__file__).parent.parent / "data" / "prefetch_cache"

def ensure_data_dir():
    """Ensure data directory and files exist"""
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    if not STATS_FILE.exists():
        STATS_FILE.write_text(json.dumps({
            "queries": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "total_queries": 0
        }, indent=2))
    
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps({
            "top_n": 10,
            "min_confidence": 0.5,
            "enabled": True,
            "hour_weights": {
                "9-11": 1.5,   # Market open hours - higher weight
                "11-15": 1.2,  # Trading hours
                "15-17": 1.3,  # Market close
                "17-21": 0.8,  # After hours
                "21-9": 0.3    # Overnight
            }
        }, indent=2))

def load_stats():
    """Load usage statistics"""
    ensure_data_dir()
    with open(STATS_FILE, 'r') as f:
        return json.load(f)

def save_stats(stats):
    """Save usage statistics"""
    ensure_data_dir()
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

def load_config():
    """Load prefetch configuration"""
    ensure_data_dir()
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save prefetch configuration"""
    ensure_data_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def record_query(ticker, module, hit=False):
    """Record a query for pattern analysis"""
    stats = load_stats()
    
    query = {
        "ticker": ticker,
        "module": module,
        "timestamp": datetime.utcnow().isoformat(),
        "hour": datetime.utcnow().hour,
        "day_of_week": datetime.utcnow().weekday(),
        "hit": hit
    }
    
    stats["queries"].append(query)
    stats["total_queries"] += 1
    
    if hit:
        stats["cache_hits"] += 1
    else:
        stats["cache_misses"] += 1
    
    # Keep only last 10,000 queries to prevent file bloat
    if len(stats["queries"]) > 10000:
        stats["queries"] = stats["queries"][-10000:]
    
    save_stats(stats)

def analyze_patterns():
    """Analyze usage patterns to predict next queries"""
    stats = load_stats()
    config = load_config()
    queries = stats["queries"]
    
    if len(queries) < 10:
        return {
            "message": "Not enough data for pattern analysis (need at least 10 queries)",
            "patterns": {}
        }
    
    # Get current hour and day
    now = datetime.utcnow()
    current_hour = now.hour
    current_day = now.weekday()
    
    # Analyze patterns
    patterns = {
        "most_queried_tickers": Counter(),
        "most_queried_modules": Counter(),
        "hour_patterns": defaultdict(lambda: Counter()),
        "day_patterns": defaultdict(lambda: Counter()),
        "recent_sequences": [],
        "ticker_module_pairs": Counter()
    }
    
    # Process queries
    for i, query in enumerate(queries):
        ticker = query.get("ticker", "unknown")
        module = query.get("module", "unknown")
        hour = query.get("hour", 0)
        day = query.get("day_of_week", 0)
        
        patterns["most_queried_tickers"][ticker] += 1
        patterns["most_queried_modules"][module] += 1
        patterns["hour_patterns"][hour][ticker] += 1
        patterns["day_patterns"][day][ticker] += 1
        patterns["ticker_module_pairs"][(ticker, module)] += 1
        
        # Track sequences (what comes after what)
        if i > 0:
            prev_ticker = queries[i-1].get("ticker", "unknown")
            patterns["recent_sequences"].append((prev_ticker, ticker))
    
    # Get hour weight
    hour_weight = 1.0
    for time_range, weight in config.get("hour_weights", {}).items():
        start, end = map(int, time_range.split('-'))
        if start <= current_hour < end or (start > end and (current_hour >= start or current_hour < end)):
            hour_weight = weight
            break
    
    return {
        "current_time": {
            "hour": current_hour,
            "day_of_week": current_day,
            "hour_weight": hour_weight
        },
        "patterns": {
            "top_tickers": patterns["most_queried_tickers"].most_common(20),
            "top_modules": patterns["most_queried_modules"].most_common(10),
            "current_hour_popular": patterns["hour_patterns"][current_hour].most_common(10),
            "current_day_popular": patterns["day_patterns"][current_day].most_common(10),
            "top_pairs": [(f"{t}:{m}", count) for (t, m), count in patterns["ticker_module_pairs"].most_common(15)]
        },
        "sequences": Counter(patterns["recent_sequences"]).most_common(10)
    }

def predict_next_queries():
    """Predict which queries are likely to come next"""
    stats = load_stats()
    config = load_config()
    patterns = analyze_patterns()
    
    if "patterns" not in patterns or not patterns["patterns"]:
        return []
    
    predictions = []
    top_n = config.get("top_n", 10)
    
    # Score based on multiple factors
    scores = defaultdict(float)
    
    # Factor 1: Overall popularity
    for ticker, count in patterns["patterns"]["top_tickers"]:
        scores[ticker] += count * 0.3
    
    # Factor 2: Time-of-day patterns (higher weight)
    for ticker, count in patterns["patterns"]["current_hour_popular"]:
        scores[ticker] += count * patterns["current_time"]["hour_weight"] * 0.4
    
    # Factor 3: Day-of-week patterns
    for ticker, count in patterns["patterns"]["current_day_popular"]:
        scores[ticker] += count * 0.2
    
    # Factor 4: Recent sequences (what often follows recent queries)
    recent_queries = stats["queries"][-5:]
    if recent_queries:
        last_ticker = recent_queries[-1].get("ticker")
        for (prev, next_ticker), count in patterns["sequences"]:
            if prev == last_ticker:
                scores[next_ticker] += count * 0.1
    
    # Convert to predictions with confidence scores
    if scores:
        max_score = max(scores.values()) if scores else 1
        for ticker, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]:
            confidence = min(score / max_score, 1.0) if max_score > 0 else 0
            
            # Find most common module for this ticker
            module_counts = Counter()
            for query in stats["queries"]:
                if query.get("ticker") == ticker:
                    module_counts[query.get("module", "unknown")] += 1
            
            most_common_module = module_counts.most_common(1)[0][0] if module_counts else "unknown"
            
            predictions.append({
                "ticker": ticker,
                "module": most_common_module,
                "confidence": round(confidence, 3),
                "score": round(score, 2)
            })
    
    return predictions

def warmup_cache():
    """Warm cache with predicted data"""
    predictions = predict_next_queries()
    config = load_config()
    
    if not config.get("enabled", True):
        return {
            "status": "disabled",
            "message": "Prefetching is disabled in config"
        }
    
    if not predictions:
        return {
            "status": "no_predictions",
            "message": "Not enough data to make predictions",
            "cached": 0
        }
    
    min_confidence = config.get("min_confidence", 0.5)
    cached = []
    
    for pred in predictions:
        if pred["confidence"] < min_confidence:
            continue
        
        ticker = pred["ticker"]
        module = pred["module"]
        
        # Simulate cache warming (in real implementation, would fetch actual data)
        cache_key = f"{ticker}_{module}_{datetime.utcnow().strftime('%Y%m%d')}"
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        # Create dummy cache entry
        cache_data = {
            "ticker": ticker,
            "module": module,
            "prefetched_at": datetime.utcnow().isoformat(),
            "confidence": pred["confidence"],
            "data": f"Cached data for {ticker}/{module}"
        }
        
        cache_file.write_text(json.dumps(cache_data, indent=2))
        cached.append({
            "ticker": ticker,
            "module": module,
            "confidence": pred["confidence"]
        })
    
    return {
        "status": "success",
        "cached": len(cached),
        "items": cached
    }

def get_cache_status():
    """Get cache hit rate and status"""
    stats = load_stats()
    config = load_config()
    
    total = stats.get("total_queries", 0)
    hits = stats.get("cache_hits", 0)
    misses = stats.get("cache_misses", 0)
    
    hit_rate = (hits / total * 100) if total > 0 else 0
    
    # Count cached items
    cached_files = list(CACHE_DIR.glob("*.json"))
    
    # Get cache size
    cache_size = sum(f.stat().st_size for f in cached_files)
    cache_size_mb = cache_size / (1024 * 1024)
    
    return {
        "enabled": config.get("enabled", True),
        "total_queries": total,
        "cache_hits": hits,
        "cache_misses": misses,
        "hit_rate": round(hit_rate, 2),
        "cached_items": len(cached_files),
        "cache_size_mb": round(cache_size_mb, 2),
        "config": {
            "top_n": config.get("top_n", 10),
            "min_confidence": config.get("min_confidence", 0.5)
        }
    }

def show_stats():
    """Display usage statistics"""
    patterns = analyze_patterns()
    
    print("📊 SMART PREFETCH - USAGE PATTERNS\n")
    
    if "message" in patterns:
        print(f"⚠️  {patterns['message']}\n")
        return
    
    print(f"⏰ Current Time: Hour {patterns['current_time']['hour']:02d}:00, "
          f"Day {patterns['current_time']['day_of_week']} (0=Mon), "
          f"Weight: {patterns['current_time']['hour_weight']}x\n")
    
    print("🔥 Top Tickers (Overall):")
    for ticker, count in patterns["patterns"]["top_tickers"][:10]:
        print(f"  {ticker:8s} - {count:4d} queries")
    
    print("\n📦 Top Modules:")
    for module, count in patterns["patterns"]["top_modules"][:8]:
        print(f"  {module:20s} - {count:4d} queries")
    
    print(f"\n🕐 Popular This Hour (Hour {patterns['current_time']['hour']:02d}):")
    for ticker, count in patterns["patterns"]["current_hour_popular"][:8]:
        print(f"  {ticker:8s} - {count:4d} queries")
    
    print("\n🔗 Common Ticker-Module Pairs:")
    for pair, count in patterns["patterns"]["top_pairs"][:8]:
        print(f"  {pair:30s} - {count:4d} queries")
    
    print("\n➡️  Query Sequences (what follows what):")
    for (prev, next_t), count in patterns["sequences"][:8]:
        print(f"  {prev:8s} → {next_t:8s} - {count:3d} times")

def show_predictions():
    """Display predicted next queries"""
    predictions = predict_next_queries()
    
    print("🔮 SMART PREFETCH - PREDICTIONS\n")
    
    if not predictions:
        print("⚠️  Not enough data to make predictions\n")
        return
    
    print("Likely next queries (sorted by confidence):\n")
    for i, pred in enumerate(predictions, 1):
        confidence_bar = "█" * int(pred["confidence"] * 20)
        print(f"{i:2d}. {pred['ticker']:8s} / {pred['module']:20s} "
              f"[{pred['confidence']:.1%}] {confidence_bar}")

def configure(args):
    """Update prefetch configuration"""
    config = load_config()
    
    if args.top is not None:
        config["top_n"] = args.top
        print(f"✓ Set top_n to {args.top}")
    
    if args.confidence is not None:
        config["min_confidence"] = args.confidence
        print(f"✓ Set min_confidence to {args.confidence}")
    
    if args.enable is not None:
        config["enabled"] = args.enable
        status = "enabled" if args.enable else "disabled"
        print(f"✓ Prefetching {status}")
    
    save_config(config)
    print("\n📝 Current Config:")
    print(json.dumps(config, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Smart Data Prefetching")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # prefetch-stats
    subparsers.add_parser('prefetch-stats', help='Show usage patterns and statistics')
    
    # prefetch-warmup
    subparsers.add_parser('prefetch-warmup', help='Warm cache with predicted data')
    
    # cache-status
    subparsers.add_parser('cache-status', help='Show cache hit rates and status')
    
    # prefetch-config
    config_parser = subparsers.add_parser('prefetch-config', help='Configure prefetch settings')
    config_parser.add_argument('--top', type=int, help='Number of top predictions to cache')
    config_parser.add_argument('--confidence', type=float, help='Minimum confidence threshold (0-1)')
    config_parser.add_argument('--enable', type=lambda x: x.lower() == 'true', help='Enable/disable prefetching')
    
    # predictions (hidden command for testing)
    subparsers.add_parser('predictions', help='Show predicted next queries')
    
    # record-query (hidden command for API integration)
    record_parser = subparsers.add_parser('record-query', help='Record a query')
    record_parser.add_argument('ticker', help='Ticker symbol')
    record_parser.add_argument('module', help='Module name')
    record_parser.add_argument('--hit', action='store_true', help='Was this a cache hit?')
    
    args = parser.parse_args()
    
    if args.command == 'prefetch-stats':
        show_stats()
    
    elif args.command == 'prefetch-warmup':
        result = warmup_cache()
        print("🔄 CACHE WARMUP\n")
        print(f"Status: {result['status']}")
        if result.get('message'):
            print(f"Message: {result['message']}")
        if result.get('cached', 0) > 0:
            print(f"\n✓ Cached {result['cached']} items:\n")
            for item in result['items']:
                print(f"  • {item['ticker']:8s} / {item['module']:20s} "
                      f"[confidence: {item['confidence']:.1%}]")
    
    elif args.command == 'cache-status':
        status = get_cache_status()
        print("💾 CACHE STATUS\n")
        print(f"Enabled: {'✓' if status['enabled'] else '✗'}")
        print(f"Total Queries: {status['total_queries']}")
        print(f"Cache Hits: {status['cache_hits']}")
        print(f"Cache Misses: {status['cache_misses']}")
        print(f"Hit Rate: {status['hit_rate']}%")
        print(f"Cached Items: {status['cached_items']}")
        print(f"Cache Size: {status['cache_size_mb']:.2f} MB")
        print(f"\n⚙️  Config:")
        print(f"  Top N: {status['config']['top_n']}")
        print(f"  Min Confidence: {status['config']['min_confidence']}")
    
    elif args.command == 'prefetch-config':
        configure(args)
    
    elif args.command == 'predictions':
        show_predictions()
    
    elif args.command == 'record-query':
        record_query(args.ticker, args.module, args.hit)
        print(f"✓ Recorded query: {args.ticker}/{args.module} (hit={args.hit})")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
