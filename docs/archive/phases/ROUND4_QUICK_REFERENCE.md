# Round 4 Data Sources - Quick Reference Card

**Research Date:** 2026-02-25 03:12 UTC  
**Status:** ✅ Complete - 20 new sources added

---

## 🚀 Top 5 Priority Sources (Start Here)

| # | Source | Why Critical | Free Tier | Integration |
|---|--------|--------------|-----------|-------------|
| 1 | **FRED** | 816K+ US economic series, yield curves | 120 req/min | Easy |
| 2 | **CoinGecko** | 13K+ coins, DeFi, NFT data | 10-50 req/min | Easy |
| 3 | **Alpaca** | Free paper trading platform | Unlimited | Medium |
| 4 | **Financial Modeling Prep** | Stock fundamentals | 250 req/day | Easy |
| 5 | **Etherscan** | Ethereum blockchain explorer | 5 req/sec | Medium |

---

## 📊 All 20 Round 4 Sources

### Macro Economic (2)
1. **FRED** - Federal Reserve Economic Data (816K+ series)
   - URL: https://fred.stlouisfed.org/docs/api/fred/
   - Auth: Free API key | Rate: 120 req/min | Integration: Easy

2. **Econdb** - Global macro database (40+ countries, 500K+ series)
   - URL: https://www.econdb.com/
   - Auth: Free API key | Rate: 100K points/month | Integration: Medium

### Stock Market Data (5)
3. **Alpaca Markets** - Paper trading + real-time US equities
   - URL: https://alpaca.markets/docs/api-references/
   - Auth: Free API key | Rate: Unlimited (paper) | Integration: Medium

4. **Financial Modeling Prep** - Fundamentals, ratios, DCF models
   - URL: https://financialmodelingprep.com/developer/docs/
   - Auth: Free API key | Rate: 250 req/day | Integration: Easy

5. **Hotstoks** - SQL-powered stock queries + unusual options
   - URL: https://hotstoks.com/api
   - Auth: Free API key | Rate: 1K queries/month | Integration: High

6. **Intrinio** - Institutional-grade financial data
   - URL: https://intrinio.com/
   - Auth: Sandbox key | Rate: Limited sandbox | Integration: Medium

7. **Finage** - Global multi-asset data + emerging markets
   - URL: https://finage.co.uk/
   - Auth: Free API key | Rate: 1K req/month | Integration: Easy

### Crypto & Blockchain (5)
8. **CoinGecko** - 13K+ coins, DeFi, NFT floor prices
   - URL: https://www.coingecko.com/en/api
   - Auth: None (basic) | Rate: 10-50 req/min | Integration: Easy

9. **Kraken** - Crypto spot & futures exchange data
   - URL: https://docs.kraken.com/rest/
   - Auth: None (public) | Rate: Tier-based | Integration: Easy

10. **Etherscan** - Ethereum blockchain explorer
    - URL: https://docs.etherscan.io/
    - Auth: Free API key | Rate: 5 req/sec, 100K/day | Integration: Medium

11. **Brave NewCoin** - Institutional crypto indices (200+ exchanges)
    - URL: https://bravenewcoin.com/developers
    - Auth: Free API key | Rate: 50 req/day | Integration: Easy

12. **Gemini** - Regulated US crypto exchange
    - URL: https://docs.gemini.com/rest-api/
    - Auth: None (public) | Rate: 120 req/min | Integration: Easy

### Alternative Data (4)
13. **Plaid** - Bank account & transaction data
    - URL: https://plaid.com/docs/api/
    - Auth: Sandbox free | Rate: Unlimited (sandbox) | Integration: Medium

14. **Nordigen** - EU Open Banking consumer data
    - URL: https://nordigen.com/en/account_information_documenation/
    - Auth: Free API key | Rate: 100 users free | Integration: Medium

15. **Styvio** - Stock data + AI sentiment
    - URL: https://www.styvio.com/
    - Auth: Free API key | Rate: 100 req/day | Integration: Medium

16. **WallStreetBets API** - WSB sentiment tracking
    - URL: https://dashboard.nbshare.io/apps/reddit/api/
    - Auth: Free API key | Rate: Free tier | Integration: Medium

### Institutional & Analysis (1)
17. **Aletheia** - AI earnings call analysis + insider trading
    - URL: https://aletheiaapi.com/
    - Auth: Free API key | Rate: 100 req/day | Integration: Medium

### Portfolio Analytics (1)
18. **Portfolio Optimizer** - Mean-variance, Black-Litterman models
    - URL: https://portfoliooptimizer.io/
    - Auth: None (basic) | Rate: 3K req/month | Integration: Medium

### Reference Data - India (2)
19. **Indian Mutual Fund** - NAV history for all Indian MFs
    - URL: https://www.mfapi.in/
    - Auth: None | Rate: Fair use | Integration: Easy

20. **Razorpay IFSC** - Indian banking codes
    - URL: https://ifsc.razorpay.com/
    - Auth: None | Rate: Fair use | Integration: Easy

---

## ⚡ Quick Integration Commands

```bash
# FRED - US Economic Data
curl "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=YOUR_KEY&file_type=json"

# CoinGecko - Crypto Prices (No Key Required)
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# Alpaca - Paper Trading Quote
curl "https://paper-api.alpaca.markets/v2/stocks/AAPL/quotes/latest" \
  -H "APCA-API-KEY-ID: YOUR_KEY" \
  -H "APCA-API-SECRET-KEY: YOUR_SECRET"

# Financial Modeling Prep - Company Profile
curl "https://financialmodelingprep.com/api/v3/profile/AAPL?apikey=YOUR_KEY"

# Etherscan - Ethereum Gas Price
curl "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=YOUR_KEY"
```

---

## 🎯 Use Case Quick Reference

| Need | Use These Sources |
|------|------------------|
| **US Macro Data** | FRED, Econdb |
| **Stock Fundamentals** | Financial Modeling Prep, Aletheia |
| **Algo Trading Dev** | Alpaca (paper trading) |
| **Crypto Prices** | CoinGecko, Kraken, Gemini |
| **DeFi/Ethereum** | Etherscan, The Graph (Round 3) |
| **Social Sentiment** | WallStreetBets, Twitter (Round 3) |
| **Portfolio Analysis** | Portfolio Optimizer |
| **Global Macro** | Econdb, FRED, OECD (Round 3) |
| **Emerging Markets** | Finage |
| **India Markets** | Indian Mutual Fund, Razorpay IFSC |

---

## 📈 Data Quality Tiers

**🥇 Tier 1 - Institutional Grade**
- FRED, Econdb, Alpaca, Etherscan, Intrinio

**🥈 Tier 2 - Production Ready**
- CoinGecko, Kraken, Gemini, Financial Modeling Prep, Aletheia, Portfolio Optimizer

**🥉 Tier 3 - Community/Aggregated**
- WallStreetBets, Styvio, Indian Mutual Fund, Plaid (sandbox)

---

## ⏱️ Rate Limit Summary

**Excellent (100K+/day):**
- FRED (173K/day)
- Etherscan (432K/day)
- Gemini (173K/day)
- Alpaca (unlimited paper)

**Good (10K-100K/day):**
- CoinGecko (14K-72K/day)
- Econdb (100K points/month)

**Adequate (100-10K/day):**
- Financial Modeling Prep (250/day)
- Aletheia (100/day)
- Styvio (100/day)

**Limited:**
- Finage (1K/month)
- Hotstoks (1K queries/month)
- Brave NewCoin (50/day)

---

## 💰 Cost Structure

**Free Forever:**
- FRED, CoinGecko, Kraken, Gemini, Indian MF, Razorpay IFSC

**Free Tier → Paid Upgrades:**
- Alpaca: $0 paper → $9/mo real-time
- Financial Modeling Prep: $0 → $14/mo
- Etherscan: $0 → $49/mo Pro
- CoinGecko: $0 → $129/mo API key

**Sandbox Only (Production Paid):**
- Plaid: Sandbox free → $0.001-0.35/transaction
- Nordigen: 100 users free → $0.10-0.30/user/mo

---

## ⚠️ Important Notes

### No Rate Limits Issues
- FRED, Econdb, Alpaca (paper), Etherscan, Gemini

### Monitor Rate Limits
- Financial Modeling Prep (250/day can be limiting)
- Aletheia (100/day for heavy usage)

### Sandbox/Development Only
- Plaid (production requires payment)
- Nordigen (100 user limit)
- Intrinio (sandbox only)

### Review ToS Required
- Alpaca (brokerage regulations)
- Plaid (data usage policies)
- WallStreetBets (community API)

---

## 🏆 Key Achievements (Round 4)

✅ **First Federal Reserve data** - FRED (816K+ series)  
✅ **Most comprehensive crypto** - CoinGecko (13K+ coins)  
✅ **First paper trading** - Alpaca (free unlimited)  
✅ **First AI earnings** - Aletheia (NLP analysis)  
✅ **First portfolio optimization** - Academic-quality tools  
✅ **First Ethereum explorer** - Etherscan (on-chain data)  
✅ **First Open Banking** - Nordigen (EU consumer data)  
✅ **First India coverage** - Mutual funds + banking codes  

---

## 📥 Files Created

1. `/home/quant/apps/quantclaw-data/NEW_DATA_SOURCES.md` (29KB)
   - 60 total sources (20 × 3 previous rounds + 20 new)

2. `/home/quant/apps/quantclaw-data/RESEARCH_SUMMARY_ROUND4.md` (14KB)
   - Detailed analysis and integration guidance

3. `/home/quant/apps/quantclaw-data/ROUND4_QUICK_REFERENCE.md` (this file)
   - Quick reference card for developers

---

## 🎬 Next Actions

1. ✅ Review this quick reference
2. ⏭️ Start with FRED integration (highest ROI)
3. ⏭️ Add CoinGecko for crypto coverage
4. ⏭️ Set up Alpaca paper trading environment
5. ⏭️ Integrate Financial Modeling Prep fundamentals
6. ⏭️ Deploy Etherscan for DeFi/Ethereum work

---

*Created by ResearchClaw subagent*  
*2026-02-25 03:15 UTC*
