# Product Launch Tracker — Phase 50

**Social buzz, pre-order velocity, review sentiment for new product launches**

Track product launches using real-time data from Google Trends, Reddit, and news sources to measure buzz, sentiment, and media coverage velocity.

---

## 🎯 Features

### 1. **Launch Summary** (Comprehensive Analysis)
Combines all data sources to generate a composite launch score and strength rating.

**Data Sources:**
- Google Trends (search interest, trending queries)
- Reddit (mentions, sentiment, top discussions)
- Google News RSS (article count, coverage velocity, top sources)

**Metrics:**
- Composite Launch Score (0-100)
- Launch Strength (Weak/Moderate/Strong/Very Strong)
- Buzz Score, Sentiment Label, Media Coverage Velocity

```bash
python cli.py launch-summary "iPhone 16"
python cli.py launch-summary "Tesla Cybertruck"
```

**API:**
```bash
GET /api/v1/product-launches?action=launch-summary&product=iPhone 16
```

---

### 2. **Buzz Tracking** (Google Trends)
Real-time search interest over time, peak buzz detection, related queries.

**Metrics:**
- Interest Over Time (daily/weekly data points)
- Current Average Interest (0-100 scale)
- Peak Interest
- Buzz Score (current/peak ratio)
- Top Related Queries
- Rising Queries

```bash
python cli.py buzz-tracking "PlayStation 5"
python cli.py buzz-tracking "Apple Vision Pro"
```

**API:**
```bash
GET /api/v1/product-launches?action=buzz-tracking&product=PlayStation 5
```

---

### 3. **Reddit Sentiment** (Social Analysis)
Analyze Reddit mentions and sentiment using keyword-based scoring.

**Metrics:**
- Total Mentions (last month)
- Average Sentiment Score
- Sentiment Label (Positive/Neutral/Negative)
- Top Posts (title, score, subreddit, comments)

**Positive Keywords:** great, amazing, love, excellent, best, awesome, perfect  
**Negative Keywords:** bad, terrible, hate, worst, awful, disappointing, sucks

```bash
python cli.py reddit-sentiment "iPhone 16"
python cli.py reddit-sentiment "Samsung Galaxy S24"
```

**API:**
```bash
GET /api/v1/product-launches?action=reddit-sentiment&product=iPhone 16
```

---

### 4. **News Coverage** (Media Tracking)
Track media coverage velocity via Google News RSS feeds.

**Metrics:**
- Total Articles (last 30 days)
- Coverage Velocity (articles per day)
- Top Sources (article count by publisher)
- Recent Headlines

```bash
python cli.py news-coverage "iPhone 16"
python cli.py news-coverage "Tesla Model Y"
```

**API:**
```bash
GET /api/v1/product-launches?action=news-coverage&product=iPhone 16
```

---

### 5. **Pre-Order Velocity** (Trend Acceleration)
Estimate pre-order velocity using search trend acceleration as proxy.

**Metrics:**
- Pre-Order Velocity (% change week-over-week)
- Trend Direction (Accelerating/Stable/Declining)
- Recent vs Previous Average Interest

```bash
python cli.py preorder-velocity "iPhone 16"
python cli.py preorder-velocity "PlayStation 5"
```

**API:**
```bash
GET /api/v1/product-launches?action=preorder-velocity&product=iPhone 16
```

---

### 6. **Trending Products** (Category Discovery)
Discover currently trending products by category.

**Categories:**
- `tech` — iPhone, Samsung Galaxy, PlayStation, Xbox, Apple Watch, AirPods
- `automotive` — Tesla Model, Ford F-150, Toyota Camry, BMW, Mercedes
- `consumer` — Nike Air, Adidas, Lululemon, Peloton
- `entertainment` — Marvel, Star Wars, Nintendo Switch

```bash
python cli.py trending-products tech
python cli.py trending-products automotive
```

**API:**
```bash
GET /api/v1/product-launches?action=trending-products&category=tech
```

---

## 📊 Use Cases

### Investment Research
Track product launch momentum for publicly traded companies:
- **Apple (AAPL):** iPhone launches, Vision Pro adoption
- **Tesla (TSLA):** Cybertruck, Model Y updates
- **Sony (SONY):** PlayStation console launches
- **Nike (NKE):** Sneaker releases

### Competitive Intelligence
Monitor competitor product launches:
- Launch timing and buzz comparison
- Media coverage velocity benchmarking
- Social sentiment analysis

### Marketing Analytics
Measure launch success:
- Pre-order velocity tracking
- Social engagement metrics
- News coverage penetration

---

## 🔧 Technical Details

### Data Sources
1. **Google Trends (pytrends)**
   - Free, no API key required
   - Search interest over time
   - Related/rising queries
   - Regional breakdown

2. **Reddit JSON API**
   - Free, no authentication required (fallback)
   - Post search, sorting, filtering
   - Score-weighted sentiment
   - Optional: PRAW for advanced features

3. **Google News RSS**
   - Free, no API key required
   - XML parsing for articles
   - Source attribution
   - 30-day lookback

### Dependencies
```bash
# Required
pip install pytrends requests

# Optional (for advanced Reddit analysis)
pip install praw
```

### Performance
- **Launch Summary:** ~10-15 seconds (combines 3 data sources)
- **Buzz Tracking:** ~3-5 seconds (Google Trends API)
- **Reddit Sentiment:** ~2-3 seconds (JSON API)
- **News Coverage:** ~2-3 seconds (RSS feed)
- **Trending Products:** ~30-60 seconds (queries multiple products)

---

## 📈 Example Output

### Launch Summary
```json
{
  "product": "iPhone 16",
  "analysis_date": "2026-02-25T00:43:37.082578",
  "data_sources": ["Google Trends", "Reddit", "Google News"],
  "google_trends": {
    "current_buzz": 48.1,
    "peak_buzz": 100,
    "buzz_score": 48.1,
    "trending_queries": [...]
  },
  "reddit_sentiment": {
    "total_mentions": 100,
    "sentiment": "Neutral",
    "sentiment_score": 0.01,
    "top_discussions": [...]
  },
  "news_coverage": {
    "total_articles": 20,
    "coverage_velocity": 0.67,
    "top_sources": [...],
    "recent_headlines": [...]
  },
  "composite_launch_score": 67.2,
  "launch_strength": "Strong"
}
```

---

## 🚀 Roadmap Enhancements

**Phase 50+** (Future):
- Product Hunt API integration
- Amazon review scraping
- YouTube video mentions
- TikTok hashtag tracking
- Pre-order data from retailers
- Stock price correlation analysis
- Launch success prediction model

---

## 📝 Notes

- **No API Keys Required:** All data sources are free and publicly accessible
- **Rate Limits:** Google Trends has soft rate limits — use sparingly for bulk queries
- **Sentiment Accuracy:** Keyword-based sentiment is ~70% accurate; for production use, consider FinBERT or custom ML model
- **Reddit Fallback:** JSON API used by default; install PRAW for authenticated access

---

**Built by:** QUANTCLAW DATA Build Agent  
**Phase:** 50 ✅ Done  
**LOC:** 642  
**Date:** 2026-02-25
