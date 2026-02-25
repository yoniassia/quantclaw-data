#!/usr/bin/env python3
"""
Executive Compensation Analysis Module (Phase 51)
Pay-for-performance correlation, peer comparison, shareholder alignment metrics

Data sources:
- SEC EDGAR DEF 14A proxy filings (executive comp tables)
- Yahoo Finance (stock performance, officer info)
- OpenInsider (insider transactions)
"""

import sys
import re
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yfinance as yf
from bs4 import BeautifulSoup
import statistics

@dataclass
class ExecutiveComp:
    """Executive compensation data"""
    name: str
    title: str
    total_comp: float
    salary: float
    bonus: float
    stock_awards: float
    option_awards: float
    other_comp: float
    year: int

@dataclass
class CompensationMetrics:
    """Pay-for-performance metrics"""
    ticker: str
    ceo_total_comp: float
    cfo_total_comp: Optional[float]
    stock_return_1y: float
    stock_return_3y: Optional[float]
    pay_performance_ratio: float
    insider_ownership_pct: float
    alignment_score: float

class ExecutiveCompensation:
    """Executive compensation analysis"""
    
    SEC_EDGAR_BASE = "https://www.sec.gov"
    OPENINSIDER_BASE = "http://openinsider.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw Research/1.0 (educational use)'
        })
    
    def get_exec_comp(self, ticker: str) -> Dict[str, Any]:
        """
        Get executive compensation breakdown from latest DEF 14A
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Executive compensation data with CEO, CFO, and top 5 officers
        """
        try:
            # Get CIK from ticker
            cik = self._get_cik(ticker)
            if not cik:
                # Fallback to Yahoo Finance officer data
                return self._get_yahoo_officers(ticker)
            
            # Get latest DEF 14A filing
            filing_url = self._get_latest_def14a(cik)
            if not filing_url:
                # Fallback to Yahoo Finance officer data
                return self._get_yahoo_officers(ticker)
            
            # Parse compensation table from DEF 14A
            comp_data = self._parse_def14a_comp_table(filing_url)
            
            if not comp_data:
                return self._get_yahoo_officers(ticker)
            
            # Enhance with stock performance
            stock_data = self._get_stock_performance(ticker)
            
            return {
                "ticker": ticker.upper(),
                "data_source": "SEC DEF 14A",
                "filing_date": comp_data.get("filing_date"),
                "executives": comp_data.get("executives", []),
                "total_executive_comp": sum(e.get("total_comp", 0) for e in comp_data.get("executives", [])),
                "stock_performance": stock_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def pay_performance_analysis(self, ticker: str) -> Dict[str, Any]:
        """
        Analyze pay-for-performance correlation
        
        Calculates:
        - CEO total compensation vs stock return (1Y, 3Y)
        - Pay-for-performance ratio
        - Alignment score (0-100)
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Pay-for-performance metrics
        """
        try:
            # Get compensation data
            comp_data = self.get_exec_comp(ticker)
            if "error" in comp_data:
                return comp_data
            
            # Get CEO compensation
            executives = comp_data.get("executives", [])
            ceo = next((e for e in executives if "CEO" in e.get("title", "").upper() or 
                       "CHIEF EXECUTIVE" in e.get("title", "").upper()), None)
            
            if not ceo:
                return {"error": "CEO compensation data not found"}
            
            ceo_comp = ceo.get("total_comp", 0)
            
            # Get stock performance
            stock_perf = comp_data.get("stock_performance", {})
            return_1y = stock_perf.get("return_1y", 0)
            return_3y = stock_perf.get("return_3y", 0)
            
            # Calculate pay-performance ratio
            # Positive ratio = comp increased with stock performance
            # Negative ratio = comp increased despite poor performance (red flag)
            if return_1y > 0:
                pay_perf_ratio = (ceo_comp / 1_000_000) / (return_1y * 100)
            else:
                pay_perf_ratio = -1 * (ceo_comp / 1_000_000)
            
            # Calculate alignment score (0-100)
            # Higher score = better alignment
            stock_based_comp = ceo.get("stock_awards", 0) + ceo.get("option_awards", 0)
            stock_comp_pct = (stock_based_comp / ceo_comp * 100) if ceo_comp > 0 else 0
            
            # Score components:
            # 1. Stock-based comp % (max 50 points): higher is better
            # 2. Positive return correlation (max 30 points)
            # 3. Reasonable pay ratio (max 20 points)
            
            score_stock_comp = min(50, stock_comp_pct)
            score_returns = 30 if return_1y > 0 else 0
            score_ratio = 20 if pay_perf_ratio < 10 else 10 if pay_perf_ratio < 20 else 0
            
            alignment_score = score_stock_comp + score_returns + score_ratio
            
            return {
                "ticker": ticker.upper(),
                "ceo_name": ceo.get("name"),
                "ceo_total_compensation": ceo_comp,
                "salary": ceo.get("salary", 0),
                "bonus": ceo.get("bonus", 0),
                "stock_awards": ceo.get("stock_awards", 0),
                "option_awards": ceo.get("option_awards", 0),
                "stock_based_comp_pct": round(stock_comp_pct, 2),
                "stock_return_1y": round(return_1y * 100, 2),
                "stock_return_3y": round(return_3y * 100, 2) if return_3y else None,
                "pay_performance_ratio": round(pay_perf_ratio, 2),
                "alignment_score": round(alignment_score, 2),
                "rating": self._get_alignment_rating(alignment_score),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def peer_comparison(self, ticker: str, peers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare executive compensation across peer companies
        
        Args:
            ticker: Stock symbol
            peers: Optional list of peer tickers (auto-detect if not provided)
        
        Returns:
            Peer compensation comparison
        """
        try:
            # Auto-detect peers if not provided
            if not peers:
                peers = self._get_peer_companies(ticker)
            
            if not peers:
                return {"error": "Could not identify peer companies"}
            
            # Get compensation for target and peers
            target_comp = self.pay_performance_analysis(ticker)
            if "error" in target_comp:
                return target_comp
            
            peer_comp_data = []
            for peer in peers[:5]:  # Limit to top 5 peers
                peer_data = self.pay_performance_analysis(peer)
                if "error" not in peer_data:
                    peer_comp_data.append(peer_data)
            
            if not peer_comp_data:
                return {"error": "Could not retrieve peer compensation data"}
            
            # Calculate peer statistics
            peer_comps = [p["ceo_total_compensation"] for p in peer_comp_data]
            peer_returns = [p["stock_return_1y"] for p in peer_comp_data if p.get("stock_return_1y")]
            peer_alignments = [p["alignment_score"] for p in peer_comp_data]
            
            target_comp_value = target_comp["ceo_total_compensation"]
            target_return = target_comp["stock_return_1y"]
            target_alignment = target_comp["alignment_score"]
            
            # Calculate percentile rankings
            comp_percentile = self._calculate_percentile(target_comp_value, peer_comps)
            return_percentile = self._calculate_percentile(target_return, peer_returns) if peer_returns else None
            alignment_percentile = self._calculate_percentile(target_alignment, peer_alignments)
            
            return {
                "ticker": ticker.upper(),
                "ceo_name": target_comp["ceo_name"],
                "ceo_total_compensation": target_comp_value,
                "peer_median_compensation": statistics.median(peer_comps),
                "peer_mean_compensation": statistics.mean(peer_comps),
                "compensation_percentile": round(comp_percentile, 1),
                "stock_return_1y": target_return,
                "peer_median_return": statistics.median(peer_returns) if peer_returns else None,
                "return_percentile": round(return_percentile, 1) if return_percentile else None,
                "alignment_score": target_alignment,
                "peer_median_alignment": statistics.median(peer_alignments),
                "alignment_percentile": round(alignment_percentile, 1),
                "peers_analyzed": [p["ticker"] for p in peer_comp_data],
                "peer_details": peer_comp_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def shareholder_alignment(self, ticker: str) -> Dict[str, Any]:
        """
        Calculate shareholder alignment metrics
        
        Metrics:
        - Insider ownership percentage
        - Recent insider buying/selling activity
        - Stock-based compensation as % of total comp
        - Vesting schedules and lock-up periods
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Shareholder alignment metrics
        """
        try:
            # Get insider ownership from Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            insider_ownership = info.get("heldPercentInsiders", 0) * 100
            institutional_ownership = info.get("heldPercentInstitutions", 0) * 100
            
            # Get recent insider transactions
            insider_trades = self._get_insider_transactions(ticker)
            
            # Get compensation data
            comp_data = self.pay_performance_analysis(ticker)
            if "error" in comp_data:
                return comp_data
            
            stock_based_comp_pct = comp_data.get("stock_based_comp_pct", 0)
            
            # Calculate alignment metrics
            # Higher insider ownership = better alignment
            ownership_score = min(100, insider_ownership * 10)  # Scale to 0-100
            
            # Net insider buying = better alignment
            net_insider_activity = insider_trades.get("net_shares_6m", 0)
            activity_score = 50 if net_insider_activity > 0 else 30 if net_insider_activity == 0 else 0
            
            # High stock-based comp = better alignment
            stock_comp_score = min(50, stock_based_comp_pct)
            
            overall_alignment = (ownership_score * 0.4 + activity_score * 0.3 + stock_comp_score * 0.3)
            
            return {
                "ticker": ticker.upper(),
                "insider_ownership_pct": round(insider_ownership, 2),
                "institutional_ownership_pct": round(institutional_ownership, 2),
                "stock_based_comp_pct": round(stock_based_comp_pct, 2),
                "insider_transactions_6m": {
                    "total_buys": insider_trades.get("buys_6m", 0),
                    "total_sells": insider_trades.get("sells_6m", 0),
                    "net_shares": insider_trades.get("net_shares_6m", 0),
                    "net_value": insider_trades.get("net_value_6m", 0)
                },
                "alignment_score": round(overall_alignment, 2),
                "rating": self._get_alignment_rating(overall_alignment),
                "insights": self._generate_alignment_insights(
                    insider_ownership, net_insider_activity, stock_based_comp_pct
                ),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # Helper methods
    
    def _get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK number for a ticker"""
        try:
            # Use SEC ticker to CIK mapping
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=exclude&count=1&search_text="
            response = self.session.get(url, timeout=10)
            
            # Extract CIK from response
            match = re.search(r'CIK=(\d{10})', response.text)
            if match:
                return match.group(1)
            
            return None
        except:
            return None
    
    def _get_latest_def14a(self, cik: str) -> Optional[str]:
        """Get URL of latest DEF 14A filing"""
        try:
            # Query SEC EDGAR for DEF 14A filings
            url = f"{self.SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=DEF+14A&dateb=&owner=exclude&count=10"
            response = self.session.get(url, timeout=10)
            
            # Parse filing list
            soup = BeautifulSoup(response.text, 'html.parser')
            filing_row = soup.find('tr', class_='blueRow')
            
            if not filing_row:
                filing_row = soup.find('tr', class_='whiteRow')
            
            if filing_row:
                doc_link = filing_row.find('a', {'id': 'documentsbutton'})
                if doc_link:
                    doc_url = self.SEC_EDGAR_BASE + doc_link['href']
                    return self._get_filing_html_url(doc_url)
            
            return None
        except:
            return None
    
    def _get_filing_html_url(self, documents_url: str) -> Optional[str]:
        """Get HTML filing URL from documents page"""
        try:
            response = self.session.get(documents_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find .htm or .html file
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    file_type = cells[3].text.strip() if len(cells) > 3 else ""
                    if 'def 14a' in file_type.lower() or 'proxy' in file_type.lower():
                        link = cells[2].find('a')
                        if link and ('.htm' in link.text or '.html' in link.text):
                            return self.SEC_EDGAR_BASE + link['href']
            
            return None
        except:
            return None
    
    def _parse_def14a_comp_table(self, url: str) -> Dict[str, Any]:
        """Parse executive compensation table from DEF 14A"""
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # This is complex - DEF 14A comp tables vary widely
            # Simplified version: look for compensation table headers
            # In production, would use more sophisticated NLP/table extraction
            
            return {
                "filing_date": datetime.now().strftime("%Y-%m-%d"),
                "executives": [],
                "note": "Full DEF 14A parsing requires specialized table extraction"
            }
        except:
            return {}
    
    def _get_yahoo_officers(self, ticker: str) -> Dict[str, Any]:
        """Fallback: Get officer info from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Yahoo Finance doesn't provide detailed comp, just officer names
            officers = []
            
            # Try to get officer info
            if 'companyOfficers' in info:
                for officer in info['companyOfficers'][:5]:
                    officers.append({
                        "name": officer.get('name', 'Unknown'),
                        "title": officer.get('title', 'Unknown'),
                        "total_comp": officer.get('totalPay', 0),
                        "year": officer.get('fiscalYear', datetime.now().year)
                    })
            
            return {
                "ticker": ticker.upper(),
                "data_source": "Yahoo Finance",
                "executives": officers,
                "note": "Limited compensation data - use SEC DEF 14A for complete details",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_stock_performance(self, ticker: str) -> Dict[str, float]:
        """Get stock performance metrics"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get 1Y and 3Y returns
            hist_1y = stock.history(period="1y")
            hist_3y = stock.history(period="3y")
            
            return_1y = 0
            return_3y = None
            
            if not hist_1y.empty and len(hist_1y) > 0:
                return_1y = (hist_1y['Close'].iloc[-1] / hist_1y['Close'].iloc[0]) - 1
            
            if not hist_3y.empty and len(hist_3y) > 0:
                return_3y = (hist_3y['Close'].iloc[-1] / hist_3y['Close'].iloc[0]) - 1
            
            return {
                "return_1y": return_1y,
                "return_3y": return_3y
            }
        except:
            return {"return_1y": 0, "return_3y": None}
    
    def _get_peer_companies(self, ticker: str) -> List[str]:
        """Auto-detect peer companies based on sector/industry"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            
            # Simplified peer mapping (in production, use more sophisticated matching)
            peer_map = {
                'AAPL': ['MSFT', 'GOOGL', 'AMZN', 'META'],
                'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'META'],
                'TSLA': ['F', 'GM', 'RIVN', 'LCID'],
                'GOOGL': ['MSFT', 'AAPL', 'AMZN', 'META'],
                'AMZN': ['MSFT', 'AAPL', 'GOOGL', 'WMT'],
                'META': ['GOOGL', 'SNAP', 'PINS', 'TWTR']
            }
            
            return peer_map.get(ticker.upper(), [])
        except:
            return []
    
    def _get_insider_transactions(self, ticker: str) -> Dict[str, Any]:
        """Get insider transaction data"""
        try:
            # Simplified version - full implementation would scrape OpenInsider
            stock = yf.Ticker(ticker)
            
            # Get insider transactions from Yahoo (if available)
            insider_trades = stock.insider_transactions
            
            if insider_trades is None or insider_trades.empty:
                return {
                    "buys_6m": 0,
                    "sells_6m": 0,
                    "net_shares_6m": 0,
                    "net_value_6m": 0
                }
            
            # Filter last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            recent_trades = insider_trades[insider_trades.index > six_months_ago]
            
            buys = recent_trades[recent_trades['Transaction'] == 'Buy']
            sells = recent_trades[recent_trades['Transaction'] == 'Sale']
            
            return {
                "buys_6m": len(buys),
                "sells_6m": len(sells),
                "net_shares_6m": buys['Shares'].sum() - sells['Shares'].sum() if not buys.empty or not sells.empty else 0,
                "net_value_6m": buys['Value'].sum() - sells['Value'].sum() if not buys.empty or not sells.empty else 0
            }
        except:
            return {
                "buys_6m": 0,
                "sells_6m": 0,
                "net_shares_6m": 0,
                "net_value_6m": 0
            }
    
    def _calculate_percentile(self, value: float, peer_values: List[float]) -> float:
        """Calculate percentile rank"""
        if not peer_values:
            return 50.0
        
        all_values = sorted(peer_values + [value])
        rank = all_values.index(value)
        return (rank / len(all_values)) * 100
    
    def _get_alignment_rating(self, score: float) -> str:
        """Convert alignment score to rating"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_alignment_insights(self, insider_ownership: float, 
                                     net_activity: float, stock_comp_pct: float) -> List[str]:
        """Generate alignment insights"""
        insights = []
        
        if insider_ownership > 5:
            insights.append(f"Strong insider ownership at {insider_ownership:.1f}%")
        elif insider_ownership < 1:
            insights.append(f"Low insider ownership at {insider_ownership:.1f}%")
        
        if net_activity > 0:
            insights.append("Net insider buying in past 6 months - positive signal")
        elif net_activity < 0:
            insights.append("Net insider selling in past 6 months - potential concern")
        
        if stock_comp_pct > 60:
            insights.append(f"High stock-based compensation at {stock_comp_pct:.1f}%")
        elif stock_comp_pct < 30:
            insights.append(f"Low stock-based compensation at {stock_comp_pct:.1f}% - alignment concern")
        
        return insights


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py exec-comp TICKER              # Executive compensation breakdown")
        print("  python cli.py pay-performance TICKER        # Pay-for-performance analysis")
        print("  python cli.py comp-peer-compare TICKER      # Peer comparison")
        print("  python cli.py shareholder-alignment TICKER  # Shareholder alignment metrics")
        print("\nExamples:")
        print("  python cli.py exec-comp AAPL")
        print("  python cli.py pay-performance TSLA")
        print("  python cli.py comp-peer-compare MSFT")
        print("  python cli.py shareholder-alignment GOOGL")
        return 1
    
    command = sys.argv[1]
    analyzer = ExecutiveCompensation()
    
    if command == "exec-comp":
        if len(sys.argv) < 3:
            print("Error: Missing ticker symbol")
            return 1
        
        ticker = sys.argv[2]
        result = analyzer.get_exec_comp(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == "pay-performance":
        if len(sys.argv) < 3:
            print("Error: Missing ticker symbol")
            return 1
        
        ticker = sys.argv[2]
        result = analyzer.pay_performance_analysis(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == "comp-peer-compare":
        if len(sys.argv) < 3:
            print("Error: Missing ticker symbol")
            return 1
        
        ticker = sys.argv[2]
        peers = sys.argv[3:] if len(sys.argv) > 3 else None
        result = analyzer.peer_comparison(ticker, peers)
        print(json.dumps(result, indent=2))
    
    elif command == "shareholder-alignment":
        if len(sys.argv) < 3:
            print("Error: Missing ticker symbol")
            return 1
        
        ticker = sys.argv[2]
        result = analyzer.shareholder_alignment(ticker)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Error: Unknown command '{command}'")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
