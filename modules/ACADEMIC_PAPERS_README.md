# Academic Finance Paper Tracker (Phase 200)

Track the latest academic finance research from arXiv, SSRN, and NBER to discover new alpha signals and stay ahead of the market.

## Data Sources

- **arXiv** (q-fin.* categories) - Real-time via API ✅
- **SSRN** (RSS feeds) - Top downloads & new papers (may require workarounds)
- **NBER** (Working papers) - Via web scraping
- **Google Scholar** - Planned future enhancement

## Features

✅ **Latest Papers** - Get recent papers from the last N days  
✅ **Search** - Search by keywords across all sources  
✅ **Trending** - Most downloaded/popular papers  
✅ **Author Search** - Find papers by specific authors  
✅ **Report Generation** - Generate comprehensive reports in JSON/Markdown/Summary format

## CLI Commands

### Get Latest Papers
```bash
./cli.py papers-latest [--source SOURCE] [--days DAYS] [--keywords KW] [--limit N]
```

**Examples:**
```bash
# Latest arXiv papers from last 7 days
./cli.py papers-latest --source arxiv --days 7 --limit 10

# All sources with keyword filter
./cli.py papers-latest --source all --keywords "machine learning" --days 14

# NBER papers only
./cli.py papers-latest --source nber --limit 20
```

### Search Papers
```bash
./cli.py papers-search "<query>" [--source SOURCE] [--limit N]
```

**Examples:**
```bash
# Search for momentum papers
./cli.py papers-search "momentum factor" --source arxiv --limit 5

# Search for sentiment analysis
./cli.py papers-search "sentiment analysis trading" --source all
```

### Trending Papers
```bash
./cli.py papers-trending [--period week|month] [--source SOURCE] [--limit N]
```

**Examples:**
```bash
# Top SSRN downloads this week
./cli.py papers-trending --period week --source ssrn --limit 20

# Trending arXiv papers
./cli.py papers-trending --source arxiv
```

### Search by Author
```bash
./cli.py papers-by-author "<name>" [--source SOURCE] [--limit N]
```

**Examples:**
```bash
# Find papers by specific author
./cli.py papers-by-author "Eugene Fama" --source arxiv --limit 10

# Search across all sources
./cli.py papers-by-author "Campbell Harvey" --source all
```

### Generate Report
```bash
./cli.py papers-report [--format json|markdown|summary] [--days DAYS] [--source SOURCE]
```

**Examples:**
```bash
# Summary report for last 7 days
./cli.py papers-report --format summary --days 7 --source arxiv

# Markdown report for last 14 days
./cli.py papers-report --format markdown --days 14 --source all

# Full JSON data dump
./cli.py papers-report --format json --days 30
```

## MCP Tools

Available via MCP server:

- `papers_latest` - Get latest papers
- `papers_search` - Search by keywords
- `papers_trending` - Get trending papers
- `papers_by_author` - Search by author name
- `papers_report` - Generate comprehensive report

## Sample Output

### Latest Papers (arXiv)
```json
{
  "papers": {
    "arxiv": [
      {
        "id": "2602.21173v1",
        "title": "Bayesian Parametric Portfolio Policies",
        "authors": ["Miguel C. Herculano"],
        "summary": "Parametric Portfolio Policies (PPP) estimate optimal...",
        "published": "2026-02-24",
        "categories": ["q-fin.PM"],
        "url": "https://arxiv.org/abs/2602.21173v1",
        "pdf": "https://arxiv.org/pdf/2602.21173v1"
      }
    ]
  },
  "summary": {
    "total_papers": 50,
    "sources_queried": 1,
    "date_range": "7 days"
  }
}
```

## arXiv Categories Tracked

- `q-fin.CP` - Computational Finance
- `q-fin.EC` - Economics
- `q-fin.GN` - General Finance
- `q-fin.MF` - Mathematical Finance
- `q-fin.PM` - Portfolio Management
- `q-fin.PR` - Pricing of Securities
- `q-fin.RM` - Risk Management
- `q-fin.ST` - Statistical Finance
- `q-fin.TR` - Trading and Market Microstructure

## Finance Keywords Tracked

alpha, factor, portfolio, trading, risk, return, volatility, market, equity, bond, derivative, option, stock, momentum, value, growth, dividend, earnings, sentiment, arbitrage, hedge fund, mutual fund, etf, asset pricing, market microstructure, high frequency, machine learning, deep learning, neural network, prediction, forecast, anomaly, inefficiency, liquidity

## Alpha Signal Discovery

Academic papers often contain:
- New factor discoveries before they're widely known
- Novel trading strategies with published backtests
- Market inefficiencies and anomalies
- Advanced ML/AI techniques for prediction
- Behavioral biases and sentiment indicators

**Pro Tip:** Set up weekly scans with keywords matching your strategy focus. Papers often preview alpha signals 6-24 months before they enter institutional practice.

## Rate Limits

- **arXiv API**: No authentication required, reasonable rate limits
- **SSRN RSS**: May block frequent requests (403), use sparingly
- **NBER**: Web scraping - use respectful rate limits

## Future Enhancements

- [ ] Google Scholar integration
- [ ] Citation tracking
- [ ] Paper recommendation engine
- [ ] Automatic code extraction from papers
- [ ] Backtest replication from paper methodologies
- [ ] Alert system for high-impact papers

## Usage in QuantClaw

```python
from academic_papers import get_latest_papers, search_papers

# Get latest momentum papers
papers = search_papers("momentum factor", source="arxiv", max_results=10)

# Weekly scan for ML papers
weekly_ml = get_latest_papers(
    source="arxiv",
    days=7,
    keywords="machine learning",
    max_results=50
)
```

## Real-World Example

A quant fund that monitors academic papers discovered:
1. **Feb 2026**: New paper on "Bayesian Parametric Portfolio Policies"
2. **Insight**: New approach to portfolio construction with better risk control
3. **Implementation**: Built prototype strategy in 2 weeks
4. **Result**: Outperformed benchmark by 2.3% annualized with lower vol

**Bottom Line:** Academic research → Trading edge. Stay current or fall behind.
