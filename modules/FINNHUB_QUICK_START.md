# Finnhub IPO Calendar - Quick Start

## 60-Second Setup

1. **Get API Key** (free, 2 minutes)
   ```bash
   # Visit https://finnhub.io and sign up
   # Copy your API key
   ```

2. **Run Setup**
   ```bash
   cd /home/quant/apps/quantclaw-data/modules
   ./setup_finnhub.sh
   # Paste your API key when prompted
   ```

3. **Test It**
   ```bash
   cd /home/quant/apps/quantclaw-data
   python3 modules/finnhub_ipo_calendar.py upcoming
   ```

## Basic Usage

```python
from modules import finnhub_ipo_calendar

# Upcoming IPOs
df = finnhub_ipo_calendar.get_data(period='upcoming')

# Recent IPOs with performance
df = finnhub_ipo_calendar.get_data(period='recent', fetch_prices=True)

# Filter by NASDAQ
df = finnhub_ipo_calendar.get_data(period='upcoming', exchange='NASDAQ')
```

## Full Documentation

- Complete README: `modules/FINNHUB_IPO_CALENDAR_README.md`
- Setup Guide: `modules/FINNHUB_SETUP_INSTRUCTIONS.txt`
- Build Report: `FINNHUB_IPO_MODULE_COMPLETION.md`

## Test Commands

```bash
# Comprehensive test suite
./test_finnhub_ipo.sh

# Interactive setup
./modules/setup_finnhub.sh

# Manual tests
python3 modules/finnhub_ipo_calendar.py test
python3 modules/finnhub_ipo_calendar.py upcoming
python3 modules/finnhub_ipo_calendar.py recent
```

---

**Ready to use!** Just add your Finnhub API key (free at finnhub.io)
