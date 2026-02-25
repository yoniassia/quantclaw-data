# Alert DSL — Quick Reference Card

## 🚀 Quick Start

```bash
# Evaluate expression for a single ticker
python3 cli.py dsl-eval AAPL "price > 200 AND rsi < 30"

# Scan universe for matches
python3 cli.py dsl-scan "rsi < 25" --universe SP500 --limit 10

# Get help
python3 cli.py dsl-help
```

## 📊 Indicators

| Indicator | Syntax | Example |
|-----------|--------|---------|
| Price | `price` | `price > 200` |
| Volume | `volume` | `volume > 10M` |
| RSI | `rsi([period])` | `rsi < 30` or `rsi(14) > 70` |
| MACD | `macd([fast,slow])` | `macd > 0` or `macd(12,26) < 0` |
| MACD Signal | `macd_signal` | `macd_signal == "bullish"` |
| SMA | `sma(period)` | `sma(20) > sma(50)` |
| EMA | `ema(period)` | `ema(12) crosses_above ema(26)` |
| Change % | `change_pct(period)` | `change_pct(5d) > 10` |
| Bollinger Upper | `bb_upper([period,std])` | `price > bb_upper()` |
| Bollinger Lower | `bb_lower([period,std])` | `price < bb_lower()` |
| ATR | `atr([period])` | `atr > 5` |
| OBV | `obv()` | `obv > 1000000` |

## 🔧 Operators

**Comparison:** `>` `<` `>=` `<=` `==` `!=`  
**Logical:** `AND` `OR`  
**Cross:** `crosses_above` `crosses_below`

## 💰 Value Suffixes

| Suffix | Meaning | Example |
|--------|---------|---------|
| `M` | Million | `volume > 10M` |
| `B` | Billion | `volume > 1B` |
| `K` | Thousand | `volume > 500K` |
| `%` | Percent | `change > 5%` |
| `d` | Days | `change_pct(5d)` |

## 📖 Common Patterns

### Oversold Stock
```
rsi < 30 AND volume > 5M
```

### Golden Cross
```
sma(20) crosses_above sma(50)
```

### Momentum Breakout
```
change_pct(5d) > 10 AND volume > 10M AND rsi < 70
```

### MACD Bullish Confirmation
```
macd_signal == "bullish" AND rsi > 50 AND rsi < 70
```

### Bollinger Band Squeeze
```
price > bb_upper() OR price < bb_lower()
```

### Oversold OR Overbought
```
rsi < 25 OR rsi > 75
```

### High Volume + Price Movement
```
volume > 20M AND change_pct(1d) > 5
```

## 🌐 API Endpoints

```
GET /api/v1/alert-dsl?action=help
GET /api/v1/alert-dsl?action=eval&ticker=AAPL&expression=price > 200
GET /api/v1/alert-dsl?action=scan&expression=rsi < 25&universe=SP500&limit=10
```

## 📝 Notes

- All expressions evaluated against live Yahoo Finance data
- 3-month historical window for calculations
- Exit code 0 if condition is true, 1 if false (for scripting)
- JSON output for programmatic parsing
- S&P 500 universe built-in (`--universe SP500`)
- Custom universe: comma-separated tickers (`--universe AAPL,MSFT,GOOGL`)
