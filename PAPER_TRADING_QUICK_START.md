# LIVE PAPER TRADING — QUICK START 🚀

**SA Quant Replica Alpha Picker Strategy**  
**Auto-rebalance on 1st & 15th of each month**

---

## 🎯 TL;DR

```bash
# Check portfolio
python cli.py paper-status

# Run rebalance (manual)
python cli.py paper-run

# View trade history
python cli.py paper-history

# Dry run (simulate)
python cli.py paper-run --dry-run

# Use shell script (cron-ready)
./run_paper_trading.sh --status
```

---

## 📊 STRATEGY

**Entry:**
- Score all 257 stocks in universe using Alpha Picker V3
- Filter for Buy+ rated (score ≥ 35)
- Buy top 10, allocate 15% per position
- $100K starting capital

**Exit:**
- Stock drops out of top 10 → sell
- Stop-loss at -15% from entry → sell
- Rebalance bi-weekly (1st and 15th)

**Pyramid (add to winners):**
- Position up 15%+ → add 50% more
- Position up 30%+ → add another 50%

---

## 🔧 COMMANDS

### paper-run
Execute rebalance: score → compare → trade → report

```bash
python cli.py paper-run              # Live execution
python cli.py paper-run --dry-run    # Simulate only
```

**What it does:**
1. Scores all stocks with Alpha Picker
2. Identifies top 10 Buy+ rated
3. Compares with current portfolio
4. Executes exits (no longer top 10)
5. Executes entries (new top 10)
6. Checks stop-loss triggers
7. Checks pyramid opportunities
8. Logs all trades to database
9. Generates WhatsApp-friendly report

**Output:**
```
📈 *PAPER TRADING REBALANCE COMPLETE*

💼 *PORTFOLIO*
• Value: $100,000.00
• Positions: 6
• Trades: 6

📊 *CURRENT POSITIONS*
🔴 *ADEA* $15,000 (+0.0%)
...
```

### paper-status
Show current portfolio + performance metrics

```bash
python cli.py paper-status
```

**Displays:**
- Total portfolio value
- Cash balance
- Unrealized P&L (live prices)
- Realized P&L (closed trades)
- Win rate
- Average P&L per trade
- All current positions

### paper-history
Show recent trade log

```bash
python cli.py paper-history            # Last 50 trades
python cli.py paper-history --limit 100  # Last 100 trades
```

**Shows:**
- All buy/sell trades
- Prices and timestamps
- P&L for closed positions

---

## 🤖 CRON AUTOMATION

**Setup:**

1. Add to crontab:
   ```bash
   crontab -e
   ```

2. Add this line (runs at 9:30 AM UTC on 1st and 15th):
   ```cron
   30 9 1,15 * * /home/quant/apps/quantclaw-data/run_paper_trading.sh >> /home/quant/apps/quantclaw-data/logs/paper_trading.log 2>&1
   ```

3. Verify:
   ```bash
   crontab -l
   ```

**Manual trigger:**
```bash
./run_paper_trading.sh
./run_paper_trading.sh --dry-run
./run_paper_trading.sh --status
./run_paper_trading.sh --history
```

**Logs:**
```bash
# View live log
tail -f logs/paper_trading.log

# View specific run
ls logs/paper_trading_*.log
cat logs/paper_trading_2026-02-27_07-11-38.log
```

---

## 📈 CURRENT PORTFOLIO

**As of 2026-02-27 07:11 UTC**

| Ticker | Score | Allocation | Sector |
|--------|-------|------------|---------|
| ADEA | 44.0 | $15,000 | Materials |
| AEIS | 45.0 | $15,000 | Industrials |
| HL | 44.0 | $15,000 | Materials |
| KGC | 50.0 | $15,000 | Materials |
| KMT | 46.0 | $15,000 | Industrials |
| RGLD | 44.0 | $15,000 | Materials |

**Total:** 6 positions, $90K invested, $10K cash

---

## 🔍 HOW SCORING WORKS

**Alpha Picker V3 — 4-Layer Scoring (max 55 pts):**

1. **Momentum (20 pts)**
   - 52-week high proximity
   - 3-month and 6-month returns
   - RSI indicator
   - Price vs 200-day moving average

2. **Fundamentals (15 pts)**
   - Revenue growth
   - Profit margins
   - Forward P/E ratio
   - Debt-to-equity
   - Free cash flow

3. **Earnings Catalyst (10 pts)**
   - Quarterly earnings growth
   - Revenue surprises
   - Consecutive beats

4. **Thematic/Sector (10 pts)**
   - Sector ETF momentum
   - Gold theme (GLD strength)
   - Small-cap theme (IWM vs SPY)

**Penalties (up to -15 pts):**
- Mega-cap stocks (low alpha potential)
- Micro-cap stocks (liquidity risk)
- Energy sector (volatility)
- Weak technical setups

**Buy+ Threshold:** Score ≥ 35

---

## 🎯 KEY METRICS TO WATCH

**Portfolio Health:**
- Total return vs SPY
- Win rate (target: >55%)
- Average P&L per trade
- Maximum drawdown
- Sharpe ratio (future)

**Position Management:**
- Number of positions (target: 6-10)
- Cash buffer (target: 10-15%)
- Stop-loss triggers (count per month)
- Pyramid executions (count per month)

**Rebalance Efficiency:**
- Trades per rebalance (avg 4-6)
- Turnover rate
- Overlap with previous picks
- Entry/exit slippage

---

## 🛠️ TROUBLESHOOTING

**"Insufficient cash" warnings:**
- Normal when rounding causes small overage
- System automatically skips when cash < position size
- Not an error, just portfolio math

**"Could not get price" errors:**
- yfinance occasionally fails for delisted/suspended stocks
- System skips these automatically
- Check ticker still exists on Yahoo Finance

**Negative cash balance:**
- Bug if this happens — check `get_cash_balance()` logic
- Should never occur in current version
- Report if seen

**Empty Buy+ list:**
- Means no stocks scored ≥ 35
- Rare in normal markets
- System will hold existing positions

---

## 📚 FILES

- **Module:** `modules/live_paper_trading.py`
- **CLI:** `cli.py` (commands registered)
- **Script:** `run_paper_trading.sh`
- **Database:** `data/paper_trading.db`
- **Logs:** `logs/paper_trading_*.log`

---

## 🚀 NEXT RUN

**Scheduled:** March 1, 2026 at 09:30 UTC  
**Expected:** Rebalance check, potential exits/entries, pyramid checks

Monitor with:
```bash
tail -f logs/paper_trading.log
```

---

**BUILT:** 2026-02-27  
**STATUS:** ✅ LIVE AND READY
