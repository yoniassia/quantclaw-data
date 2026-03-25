# Smart Prefetch Integration Guide

## Quick Start

### 1. Basic Usage (CLI)

```bash
# Check cache status
python cli.py cache-status

# View usage patterns
python cli.py prefetch-stats

# Warm cache with ML predictions
python cli.py prefetch-warmup

# Configure settings
python cli.py prefetch-config --top 20 --confidence 0.6
```

### 2. Integration in Your Module

Add query tracking to any data-fetching function:

```python
from modules.smart_prefetch import record_query

def fetch_stock_price(ticker):
    # Try cache first
    cached = get_from_cache(ticker, "price")
    
    if cached:
        record_query(ticker, "price", hit=True)
        return cached
    
    # Cache miss - fetch fresh data
    record_query(ticker, "price", hit=False)
    data = fetch_from_api(ticker)
    save_to_cache(ticker, "price", data)
    return data
```

### 3. API Integration

```javascript
// Get cache status
const status = await fetch('/api/v1/smart-prefetch?action=status');

// Warm cache
const warmup = await fetch('/api/v1/smart-prefetch?action=warmup');

// Record query
await fetch('/api/v1/smart-prefetch?action=record', {
  method: 'POST',
  body: JSON.stringify({ 
    ticker: 'AAPL', 
    module: 'price', 
    hit: true 
  })
});

// Update config
await fetch('/api/v1/smart-prefetch?action=config', {
  method: 'POST',
  body: JSON.stringify({ 
    top_n: 20, 
    min_confidence: 0.6 
  })
});
```

## Configuration

### Default Settings

```json
{
  "top_n": 10,
  "min_confidence": 0.5,
  "enabled": true,
  "hour_weights": {
    "9-11": 1.5,   // Market open
    "11-15": 1.2,  // Trading hours
    "15-17": 1.3,  // Market close
    "17-21": 0.8,  // After hours
    "21-9": 0.3    // Overnight
  }
}
```

### Tuning Guide

**For High-Traffic Systems:**
```bash
python cli.py prefetch-config --top 50 --confidence 0.4
```

**For Low-Latency Requirements:**
```bash
python cli.py prefetch-config --top 20 --confidence 0.7
```

**For Conservative Caching:**
```bash
python cli.py prefetch-config --top 5 --confidence 0.8
```

## Automation

### Cron Job (Recommended)

```bash
# Add to crontab
# Warm cache every 15 minutes during market hours
*/15 9-17 * * 1-5 cd /home/quant/apps/quantclaw-data && python3 cli.py prefetch-warmup

# Cleanup old cache at midnight
0 0 * * * cd /home/quant/apps/quantclaw-data && find data/prefetch_cache -mtime +7 -delete
```

### Background Service

```python
import schedule
import time
from modules.smart_prefetch import warmup_cache

def job():
    result = warmup_cache()
    print(f"Cached {result['cached']} items")

# Run every 15 minutes
schedule.every(15).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Monitoring

### Check Performance

```bash
# View hit rate
python cli.py cache-status | grep "Hit Rate"

# View top predictions
python modules/smart_prefetch.py predictions

# Analyze patterns
python cli.py prefetch-stats
```

### Expected Metrics

| Queries Tracked | Expected Hit Rate | Status |
|----------------|-------------------|--------|
| 0-50           | 30-40%           | Learning |
| 50-200         | 50-65%           | Good |
| 200-1000       | 65-80%           | Excellent |
| 1000+          | 80-90%           | Optimal |

## Troubleshooting

### Low Hit Rate (<40%)

1. Check if enough data collected:
   ```bash
   python cli.py cache-status
   ```

2. Lower confidence threshold:
   ```bash
   python cli.py prefetch-config --confidence 0.3
   ```

3. Increase prefetch pool:
   ```bash
   python cli.py prefetch-config --top 30
   ```

### High Memory Usage

1. Reduce prefetch pool:
   ```bash
   python cli.py prefetch-config --top 5
   ```

2. Clean old cache files:
   ```bash
   find data/prefetch_cache -mtime +1 -delete
   ```

### Cache Not Warming

1. Check if enabled:
   ```bash
   python cli.py cache-status | grep Enabled
   ```

2. Enable if needed:
   ```bash
   python cli.py prefetch-config --enable true
   ```

3. Check predictions:
   ```bash
   python modules/smart_prefetch.py predictions
   ```

## Advanced Usage

### Custom Hour Weights

Edit `data/prefetch_config.json`:

```json
{
  "hour_weights": {
    "6-9": 1.0,    // Pre-market
    "9-11": 2.0,   // Heavy volume at open
    "11-14": 1.5,  // Mid-day trading
    "14-16": 1.8,  // Late-day volume
    "16-20": 1.0,  // After-hours
    "20-6": 0.2    // Overnight (minimal)
  }
}
```

### Programmatic Access

```python
from modules.smart_prefetch import (
    record_query,
    analyze_patterns,
    predict_next_queries,
    warmup_cache,
    get_cache_status
)

# Record a query
record_query("AAPL", "price", hit=True)

# Get patterns
patterns = analyze_patterns()
print(patterns["patterns"]["top_tickers"])

# Get predictions
predictions = predict_next_queries()
for pred in predictions[:5]:
    print(f"{pred['ticker']}: {pred['confidence']:.1%}")

# Warm cache
result = warmup_cache()
print(f"Cached {result['cached']} items")

# Check status
status = get_cache_status()
print(f"Hit rate: {status['hit_rate']}%")
```

## Production Checklist

- [ ] Cron job configured for cache warming
- [ ] Monitoring alerts set up for low hit rates
- [ ] Cache cleanup job scheduled
- [ ] Confidence threshold tuned based on load
- [ ] Integration tested in all critical paths
- [ ] Logs reviewed for errors
- [ ] Performance baseline established

## Support

For issues or questions:
1. Check cache status: `python cli.py cache-status`
2. Review patterns: `python cli.py prefetch-stats`
3. Check logs: `tail -f logs/prefetch.log` (if logging configured)
4. Test predictions: `python modules/smart_prefetch.py predictions`

## Performance Tips

1. **Warm cache proactively:** Run warmup before peak hours
2. **Tune confidence:** Lower for broad coverage, higher for precision
3. **Monitor hit rates:** Aim for 70%+ after training period
4. **Clean old cache:** Prevent disk bloat with daily cleanup
5. **Track patterns:** Review `prefetch-stats` weekly to understand usage

---

**Built:** Phase 83  
**Status:** Production Ready  
**Version:** 1.0.0
