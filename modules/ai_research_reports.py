#!/usr/bin/env python3
"""AI Research Reports — One-click LLM-generated equity research"""

import yfinance as yf
import json
import os
from datetime import datetime
from typing import Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def gather_comprehensive_data(ticker: str) -> Dict:
    """Gather all available data for a ticker from multiple sources"""
    data = {
        "ticker": ticker,
        "generated_at": datetime.now().isoformat(),
        "data_sources": []
    }
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        data["company_name"] = info.get("longName", ticker)
        data["sector"] = info.get("sector", "Unknown")
        data["industry"] = info.get("industry", "Unknown")
        data["market_cap"] = info.get("marketCap", 0)
        data["current_price"] = info.get("currentPrice", 0)
        
        # Fundamentals
        data["fundamentals"] = {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
        }
        data["data_sources"].append("Yahoo Finance (Fundamentals)")
        
        # Historical performance
        hist = stock.history(period="1y")
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            start = hist['Close'].iloc[0]
            high_52w = hist['High'].max()
            low_52w = hist['Low'].min()
            
            data["performance"] = {
                "1y_return": ((current - start) / start) * 100,
                "52w_high": high_52w,
                "52w_low": low_52w,
                "distance_from_high": ((current - high_52w) / high_52w) * 100,
                "distance_from_low": ((current - low_52w) / low_52w) * 100,
                "volatility_30d": hist['Close'].tail(30).pct_change().std() * 100,
            }
            data["data_sources"].append("Yahoo Finance (Price History)")
        
        # Analyst recommendations (simplified to avoid column issues)
        try:
            if hasattr(stock, 'recommendations') and stock.recommendations is not None:
                recs = stock.recommendations
                if not recs.empty:
                    data["analyst_recommendations"] = {
                        "total_recommendations": len(recs),
                        "recent_count": min(10, len(recs)),
                    }
                    data["data_sources"].append("Yahoo Finance (Analysts)")
        except:
            pass
        
        # Insider transactions (simplified)
        try:
            if hasattr(stock, 'insider_transactions') and stock.insider_transactions is not None:
                insider = stock.insider_transactions
                if not insider.empty:
                    data["insider_activity"] = {
                        "total_transactions": len(insider),
                        "recent_count": min(10, len(insider)),
                    }
                    data["data_sources"].append("Yahoo Finance (Insiders)")
        except:
            pass
        
        # Institutional holders
        try:
            if hasattr(stock, 'institutional_holders') and stock.institutional_holders is not None:
                holders = stock.institutional_holders
                if not holders.empty and '% Out' in holders.columns:
                    data["institutional_ownership"] = {
                        "top_10_pct": holders.head(10)['% Out'].sum()
                    }
                    data["data_sources"].append("Yahoo Finance (Institutions)")
        except:
            pass
        
        # Options (IV, P/C ratio)
        try:
            options_dates = stock.options
            if options_dates:
                opt = stock.option_chain(options_dates[0])
                if opt.calls is not None and not opt.calls.empty:
                    calls = opt.calls
                    puts = opt.puts
                    
                    data["options_metrics"] = {
                        "iv_calls": float(calls['impliedVolatility'].median()),
                        "iv_puts": float(puts['impliedVolatility'].median()),
                        "put_call_ratio": float(puts['volume'].sum() / max(calls['volume'].sum(), 1)),
                    }
                    data["data_sources"].append("Yahoo Finance (Options)")
        except:
            pass
        
    except Exception as e:
        data["error"] = f"Error gathering data: {str(e)}"
    
    return data

def generate_research_report(ticker: str, model: str = "gpt-4o-mini") -> Dict:
    """Generate comprehensive equity research report using LLM"""
    data = gather_comprehensive_data(ticker)
    
    if "error" in data:
        return {"error": data["error"]}
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not OpenAI:
        return generate_structured_report(data)
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""You are a senior equity research analyst. Generate a comprehensive report for {ticker} ({data.get('company_name', ticker)}).

Data: {json.dumps(data, indent=2, default=str)}

Sections:
1. Executive Summary (2-3 sentences)
2. Investment Thesis (bull/bear)
3. Valuation Analysis
4. Financial Health
5. Growth Prospects
6. Risk Factors
7. Analyst Sentiment
8. Technical Analysis
9. Recommendation (Buy/Hold/Sell with price target)

Be concise. Use data provided."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a senior equity research analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return {
            "ticker": ticker,
            "company_name": data.get("company_name"),
            "generated_at": data["generated_at"],
            "model": model,
            "report": response.choices[0].message.content,
            "data_sources": data["data_sources"],
            "raw_data": data,
        }
        
    except Exception as e:
        return {"error": f"LLM failed: {str(e)}"}

def generate_structured_report(data: Dict) -> Dict:
    """Generate structured report without LLM (fallback)"""
    ticker = data["ticker"]
    name = data.get("company_name", ticker)
    
    sections = []
    price = data.get("current_price", 0)
    mkt_cap = data.get("market_cap", 0) / 1e9
    sector = data.get("sector", "Unknown")
    
    sections.append(f"## Executive Summary\n{name} ({ticker}) at ${price:.2f}, ${mkt_cap:.1f}B cap in {sector}.")
    
    fund = data.get("fundamentals", {})
    if fund:
        sections.append(f"""## Valuation
- P/E: {fund.get('pe_ratio', 'N/A')}
- Fwd P/E: {fund.get('forward_pe', 'N/A')}
- PEG: {fund.get('peg_ratio', 'N/A')}
- P/B: {fund.get('price_to_book', 'N/A')}""")
        
        pm = fund.get('profit_margin', 0)
        roe = fund.get('roe', 0)
        sections.append(f"""## Financials
- Profit Margin: {pm*100:.1f}%
- ROE: {roe*100:.1f}%
- Debt/Equity: {fund.get('debt_to_equity', 'N/A')}""")
        
        rg = fund.get('revenue_growth', 0)
        eg = fund.get('earnings_growth', 0)
        sections.append(f"""## Growth
- Revenue Growth: {rg*100:.1f}%
- Earnings Growth: {eg*100:.1f}%""")
    
    perf = data.get("performance", {})
    if perf:
        sections.append(f"""## Performance
- 1Y Return: {perf.get('1y_return', 0):.1f}%
- 52W High: ${perf.get('52w_high', 0):.2f}
- 52W Low: ${perf.get('52w_low', 0):.2f}""")
    
    return {
        "ticker": ticker,
        "company_name": name,
        "generated_at": data["generated_at"],
        "model": "structured_fallback",
        "report": "\n\n".join(sections),
        "data_sources": data["data_sources"],
        "raw_data": data,
    }

def export_markdown(report: Dict, output_path: Optional[str] = None) -> str:
    """Export report to markdown"""
    ticker = report["ticker"]
    name = report.get("company_name", ticker)
    
    md = f"""# Research Report: {name} ({ticker})
**Generated**: {report['generated_at']}
**Model**: {report.get('model', 'N/A')}

---

{report['report']}

---
*Auto-generated by QuantClaw AI Research Reports*
"""
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(md)
    
    return md

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  research TICKER [--model MODEL] [--output FILE]")
        print("  ai-report TICKER [--json]")
        print("  company-report TICKER")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Commands that are aliases for research
    if command in ['research', 'ai-report', 'company-report']:
        if len(sys.argv) < 3:
            print(f"Error: {command} requires TICKER argument")
            sys.exit(1)
        
        ticker = sys.argv[2]
        model = "gpt-4o-mini"
        output_file = None
        json_output = False
        
        # Parse additional args
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--model' and i+1 < len(sys.argv):
                model = sys.argv[i+1]
                i += 2
            elif sys.argv[i] in ['-o', '--output'] and i+1 < len(sys.argv):
                output_file = sys.argv[i+1]
                i += 2
            elif sys.argv[i] == '--json':
                json_output = True
                i += 1
            else:
                i += 1
        
        print(f"Generating report for {ticker}...")
        report = generate_research_report(ticker, model=model)
        
        if "error" in report:
            print(f"ERROR: {report['error']}")
            sys.exit(1)
        
        if json_output:
            print(json.dumps(report, indent=2, default=str))
        else:
            md = export_markdown(report, output_file)
            if not output_file:
                print(md)
        
        print(f"\nUsed {len(report.get('data_sources', []))} data sources.")
    else:
        # Assume it's a ticker (backward compat)
        ticker = sys.argv[1]
        model = "gpt-4o-mini"
        output_file = None
        json_output = False
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--model' and i+1 < len(sys.argv):
                model = sys.argv[i+1]
                i += 2
            elif sys.argv[i] in ['-o', '--output'] and i+1 < len(sys.argv):
                output_file = sys.argv[i+1]
                i += 2
            elif sys.argv[i] == '--json':
                json_output = True
                i += 1
            else:
                i += 1
        
        print(f"Generating report for {ticker}...")
        report = generate_research_report(ticker, model=model)
        
        if "error" in report:
            print(f"ERROR: {report['error']}")
            sys.exit(1)
        
        if json_output:
            print(json.dumps(report, indent=2, default=str))
        else:
            md = export_markdown(report, output_file)
            if not output_file:
                print(md)
        
        print(f"\nUsed {len(report.get('data_sources', []))} data sources.")
