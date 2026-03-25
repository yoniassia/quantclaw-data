# ✅ PHASE 55 COMPLETE: Tax Loss Harvesting

**Build Date**: 2026-02-25  
**Status**: Production-ready  
**Total LOC**: 485 lines (362 Python + 123 TypeScript)

---

## 📦 Deliverables

### 1. Core Module
**File**: `modules/tax_loss_harvesting.py` (362 lines)

**Features**:
- Portfolio scanning for YTD loss positions
- Wash sale rule enforcement (30-day window)
- Tax savings calculation with configurable rates
- Sector-based ETF replacement suggestions

**Data Sources**:
- Yahoo Finance (price history, YTD returns)
- Built-in sector mappings
- ETF replacement catalog

---

### 2. CLI Commands (4 new commands)

#### `tlh-scan`
Scan portfolio for tax loss harvesting candidates
```bash
python cli.py tlh-scan AAPL,TSLA,MSFT,AMZN,META
```

**Output**:
- Loss positions ranked by TLH score
- YTD return percentage
- Start/current prices
- Sector classification
- Portfolio summary stats

---

#### `wash-sale-check`
Verify wash sale rule compliance before selling
```bash
python cli.py wash-sale-check TSLA 2026-02-25
```

**Output**:
- 30-day window (before + after sale date)
- Safe repurchase date
- Days until safe to repurchase
- IRS compliance warnings

---

#### `tax-savings`
Estimate tax savings from harvesting a position
```bash
python cli.py tax-savings AAPL --cost-basis 180 --shares 100 --tax-rate 0.25
```

**Output**:
- Position details (cost basis, current value, shares)
- Capital loss amount and percentage
- Estimated tax savings (customizable rate)
- Offset type (capital gains vs ordinary income)
- Actionable next steps

---

#### `tlh-replacements`
Find sector ETF replacements to avoid wash sale
```bash
python cli.py tlh-replacements TSLA
```

**Output**:
- Original ticker sector
- 3-5 ETF alternatives in same sector
- Current prices and YTD returns
- Expense ratios (when available)
- Wash sale avoidance strategy notes

---

### 3. API Routes
**Endpoint**: `/api/v1/tax-loss`

**Actions**:
1. `?action=scan&tickers=AAPL,TSLA,MSFT`
2. `?action=wash-sale-check&ticker=TSLA&date=2026-02-25`
3. `?action=tax-savings&ticker=AAPL&cost_basis=180&shares=100&tax_rate=0.25`
4. `?action=replacements&ticker=TSLA`

**File**: `src/app/api/v1/tax-loss/route.ts` (123 lines)

---

### 4. Service Registry
**File**: `src/app/services.ts`

**New Services** (4 added):
- `tlh_scan`: Portfolio scanning
- `wash_sale_check`: Wash sale rule verification
- `tax_savings`: Tax savings calculator
- `tlh_replacements`: Replacement suggestions

**MCP Tools** (for Claude integration):
- `scan_tlh_opportunities`
- `check_wash_sale`
- `estimate_tax_savings`
- `suggest_tlh_replacements`

---

### 5. Roadmap Update
**File**: `src/app/roadmap.ts`

**Change**: Phase 55 status updated from `"planned"` → `"done"`
```typescript
{ 
  id: 55, 
  name: "Tax Loss Harvesting", 
  description: "Identify opportunities, track wash sale rules, estimate tax savings", 
  status: "done", 
  category: "Quant", 
  loc: 485 
}
```

---

## 🧪 Test Coverage

### Real-World Test Case
**Scenario**: MSFT position with 17.56% YTD loss

**Position**:
- 50 shares @ $471.86 cost basis
- Current price: $389.00
- Total loss: **$4,143.00**

**Tax Impact** (30% rate):
- Tax savings: **$1,242.90**
- Offset type: Capital gains

**Strategy**:
1. Sell 50 MSFT shares → Realize $4,143 loss
2. Wait 31 days (wash sale window)
3. Buy XLK (Tech sector ETF) to maintain exposure
4. Use $1,242.90 tax savings to rebalance

---

## 📊 Sector Coverage

**Supported Sectors** (with ETF replacements):
1. **Technology**: QQQ, VGT, XLK, IGV, SMH
2. **Consumer Cyclical**: XLY, VCR, FDIS
3. **Healthcare**: XLV, VHT, IHI, IBB
4. **Financial Services**: XLF, VFH, KRE
5. **Communication Services**: XLC, VOX
6. **Energy**: XLE, VDE, IEO
7. **Consumer Defensive**: XLP, VDC
8. **Industrials**: XLI, VIS

**Expandable**: Easy to add more sectors and replacements

---

## 🔧 Technical Implementation

### Dependencies
```python
import yfinance as yf  # Yahoo Finance API
from datetime import datetime, timedelta
```

### Key Functions
1. `scan_portfolio(tickers)` → List of loss positions
2. `check_wash_sale(ticker, sale_date)` → Window calculation
3. `estimate_tax_savings(ticker, cost_basis, shares, tax_rate)` → Savings estimate
4. `suggest_replacements(ticker)` → Sector ETF list

### Error Handling
- Invalid date formats
- Missing ticker data
- API failures
- Missing parameters

---

## 🎯 Use Cases

### 1. End-of-Year Tax Planning
Scan entire portfolio in December, harvest losses strategically

### 2. Rebalancing with Tax Benefits
Replace individual stocks with sector ETFs while capturing losses

### 3. Wash Sale Avoidance
Verify compliance before executing trades

### 4. Tax Savings Maximization
Calculate optimal loss harvesting across multiple positions

### 5. Capital Gains Offsetting
Offset realized gains from winning positions

---

## 📈 Example Workflow

```bash
# Step 1: Scan portfolio
python cli.py tlh-scan AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,AMD

# Step 2: Identify biggest loss (e.g., MSFT -17.56%)
python cli.py tax-savings MSFT --cost-basis 471.86 --shares 50 --tax-rate 0.30
# → Tax savings: $1,242.90

# Step 3: Check wash sale window
python cli.py wash-sale-check MSFT 2026-02-25
# → Safe to repurchase after: 2026-03-27

# Step 4: Find replacement
python cli.py tlh-replacements MSFT
# → Suggestions: XLK, VGT, IGV

# Step 5: Execute
# - Sell 50 MSFT @ $389 → $19,450
# - Buy XLK with proceeds
# - Wait 31 days
# - Optionally buy back MSFT
# - Save $1,242.90 in taxes
```

---

## ✅ Build Verification

**Files Created**:
- ✅ `modules/tax_loss_harvesting.py` (362 lines)
- ✅ `src/app/api/v1/tax-loss/route.ts` (123 lines)

**Files Modified**:
- ✅ `cli.py` (added module registration)
- ✅ `src/app/services.ts` (added 4 services)
- ✅ `src/app/roadmap.ts` (marked phase 55 as done)

**Tests Passed**:
- ✅ TLH portfolio scan (5 tickers → 4 losses identified)
- ✅ Wash sale check (window calculated correctly)
- ✅ Tax savings estimation (MSFT: $1,242.90 @ 30%)
- ✅ Replacement suggestions (3 ETFs for TSLA)

**CLI Help**:
- ✅ Commands registered
- ✅ Documentation added
- ✅ Examples provided

---

## 🚀 Production Ready

This module is **production-ready** and can be used immediately for:
- Personal tax planning
- Portfolio management
- Financial advisory
- Automated tax optimization

**No API keys required** — Uses free Yahoo Finance data.

---

## 📝 Notes

- IRS wash sale rule: 30 days before + 30 days after = 61-day window
- $3,000 annual limit for ordinary income offset
- Unlimited capital gains offset
- Losses carry forward indefinitely
- ETF replacements avoid "substantially identical" security rule

---

**Phase 55: Tax Loss Harvesting — COMPLETE** ✅  
**Next Phase**: Ready for Phase 56 (Share Buyback Analysis) or Phase 57 (Dividend Sustainability)
