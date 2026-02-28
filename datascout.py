#!/usr/bin/env python3
"""
DataScout Agent — Persistent Research Data Agent
Uses Grok 4 (xai/grok-4) with web_search and x_search to discover
new financial data sources and map them into QuantClaw Data.

Runs hourly via OpenClaw cron.
"""

import json, os, sys, time, requests, hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Config
XAI_API_KEY = os.environ.get('XAI_API_KEY', '')
if not XAI_API_KEY:
    creds_path = Path(__file__).parent.parent / '.openclaw/workspace/.credentials/xai.json'
    if not creds_path.exists():
        creds_path = Path('/home/quant/.openclaw/workspace/.credentials/xai.json')
    if creds_path.exists():
        XAI_API_KEY = json.loads(creds_path.read_text()).get('apiKey', '')

XAI_BASE = 'https://api.x.ai/v1'
MODEL = 'grok-4'
DATA_DIR = Path(__file__).parent / 'data' / 'datascout'
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODULES_DIR = Path(__file__).parent / 'modules'
EXISTING_MODULES_CACHE = DATA_DIR / 'existing_modules.json'
DISCOVERIES_DB = DATA_DIR / 'all_discoveries.json'

# Category rotation (24 categories, cycle through hourly)
CATEGORIES = [
    {
        "name": "Macro / Central Banks",
        "x_queries": [
            "new central bank API data 2026",
            "economic data API free launch",
            "FRED new dataset released"
        ],
        "web_queries": [
            "new free macroeconomic data API 2026",
            "central bank open data portal new",
            "economic indicators API free tier"
        ]
    },
    {
        "name": "Alternative Data — Satellite & Geospatial",
        "x_queries": [
            "satellite data trading free",
            "geospatial financial data API",
            "alternative data provider launch 2026"
        ],
        "web_queries": [
            "free satellite imagery financial analysis",
            "geospatial alternative data API trading",
            "new alternative data sources quant 2026"
        ]
    },
    {
        "name": "Alternative Data — Social & Sentiment",
        "x_queries": [
            "social sentiment API stock market",
            "reddit sentiment financial data",
            "fintwit sentiment tracker API"
        ],
        "web_queries": [
            "free social media sentiment API stocks",
            "reddit wallstreetbets sentiment data API",
            "twitter financial sentiment analysis API 2026"
        ]
    },
    {
        "name": "Crypto & DeFi On-Chain",
        "x_queries": [
            "new crypto data API free",
            "on-chain analytics free API 2026",
            "DeFi protocol data API launch"
        ],
        "web_queries": [
            "free cryptocurrency on-chain data API",
            "DeFi analytics API free tier 2026",
            "blockchain data provider new launch"
        ]
    },
    {
        "name": "Earnings & Fundamentals",
        "x_queries": [
            "earnings data API free 2026",
            "SEC EDGAR new dataset",
            "financial statements API free"
        ],
        "web_queries": [
            "free earnings estimate revision data API",
            "SEC EDGAR XBRL API new features",
            "company fundamentals API free 2026"
        ]
    },
    {
        "name": "Exchanges & Market Microstructure",
        "x_queries": [
            "exchange data API new launch",
            "order book data free API",
            "market microstructure data 2026"
        ],
        "web_queries": [
            "free exchange market data API 2026",
            "level 2 order book data free",
            "tick data API free provider"
        ]
    },
    {
        "name": "ESG & Climate",
        "x_queries": [
            "ESG data API free 2026",
            "carbon credit data API",
            "climate risk financial data"
        ],
        "web_queries": [
            "free ESG ratings data API",
            "carbon emissions trading data API",
            "climate financial risk data source 2026"
        ]
    },
    {
        "name": "Commodities & Energy",
        "x_queries": [
            "commodity data API free 2026",
            "oil gas data API launch",
            "energy market data free"
        ],
        "web_queries": [
            "free commodity price data API",
            "energy market data API open source",
            "agricultural commodity data free API 2026"
        ]
    },
    {
        "name": "Fixed Income & Credit",
        "x_queries": [
            "bond data API free 2026",
            "credit spread data API",
            "treasury yield API new"
        ],
        "web_queries": [
            "free bond market data API",
            "corporate credit data API free tier",
            "government bond yield data API 2026"
        ]
    },
    {
        "name": "Real Estate & Housing",
        "x_queries": [
            "real estate data API free 2026",
            "housing market data API",
            "REIT data source free"
        ],
        "web_queries": [
            "free real estate market data API",
            "housing price index API free",
            "commercial real estate data API 2026"
        ]
    },
    {
        "name": "Labor & Demographics",
        "x_queries": [
            "labor market data API new",
            "jobs data API free 2026",
            "employment statistics API"
        ],
        "web_queries": [
            "free labor market statistics API",
            "demographic data API financial analysis",
            "wage growth data API 2026"
        ]
    },
    {
        "name": "Trade & Supply Chain",
        "x_queries": [
            "supply chain data API 2026",
            "shipping tracking data free",
            "global trade data API launch"
        ],
        "web_queries": [
            "free global trade data API",
            "supply chain disruption data API",
            "shipping AIS vessel tracking data free 2026"
        ]
    },
    {
        "name": "Options & Derivatives",
        "x_queries": [
            "options data API free 2026",
            "derivatives market data launch",
            "options flow data API"
        ],
        "web_queries": [
            "free options chain data API",
            "options unusual activity data API",
            "derivatives pricing data free 2026"
        ]
    },
    {
        "name": "Insider & Institutional",
        "x_queries": [
            "insider trading data API 2026",
            "13F filing data API free",
            "institutional holdings data"
        ],
        "web_queries": [
            "free insider trading data API SEC",
            "13F institutional holdings API",
            "hedge fund positions data API 2026"
        ]
    },
    {
        "name": "IPO & Private Markets",
        "x_queries": [
            "IPO data API free 2026",
            "private market data API",
            "SPAC data source launch"
        ],
        "web_queries": [
            "free IPO calendar data API",
            "private company valuation data API",
            "venture capital deal data free 2026"
        ]
    },
    {
        "name": "FX & Rates",
        "x_queries": [
            "forex data API free 2026",
            "interest rate data API launch",
            "currency data source new"
        ],
        "web_queries": [
            "free real-time forex data API",
            "central bank interest rate API",
            "currency forward rate data API 2026"
        ]
    },
    {
        "name": "Quant Tools & ML",
        "x_queries": [
            "quant trading tool open source 2026",
            "ML financial data pipeline",
            "alpha generation tool launch"
        ],
        "web_queries": [
            "open source quant trading framework 2026",
            "machine learning financial data tools",
            "factor investing data pipeline open source"
        ]
    },
    {
        "name": "News & NLP",
        "x_queries": [
            "financial news API free 2026",
            "NLP sentiment stock market",
            "news analytics trading data"
        ],
        "web_queries": [
            "free financial news API real-time",
            "news sentiment analysis API stocks",
            "event-driven trading data source 2026"
        ]
    },
    {
        "name": "Government & Regulatory",
        "x_queries": [
            "government open data financial 2026",
            "regulatory filing data API",
            "CFPB CFTC new data release"
        ],
        "web_queries": [
            "government open data portal financial API",
            "regulatory compliance data API free",
            "SEC CFTC CFPB data API new 2026"
        ]
    },
    {
        "name": "Emerging Markets",
        "x_queries": [
            "emerging market data API 2026",
            "India stock data API free",
            "Brazil China market data launch"
        ],
        "web_queries": [
            "free emerging market financial data API",
            "India NSE BSE data API",
            "China A-shares data API free 2026"
        ]
    },
    {
        "name": "Web Traffic & App Data",
        "x_queries": [
            "web traffic data trading API",
            "app download data investing",
            "SimilarWeb alternative free 2026"
        ],
        "web_queries": [
            "free web traffic data API financial analysis",
            "app store download data API",
            "digital footprint alternative data 2026"
        ]
    },
    {
        "name": "ETF & Fund Flows",
        "x_queries": [
            "ETF flow data API 2026",
            "fund flow tracking API free",
            "mutual fund data API launch"
        ],
        "web_queries": [
            "free ETF holdings flow data API",
            "fund flow data API real-time",
            "ETF creation redemption data free 2026"
        ]
    },
    {
        "name": "Healthcare & Biotech",
        "x_queries": [
            "FDA approval data API 2026",
            "clinical trial data API free",
            "biotech pipeline data source"
        ],
        "web_queries": [
            "free FDA drug approval data API",
            "clinical trial results data API",
            "pharmaceutical pipeline data free 2026"
        ]
    },
    {
        "name": "Infrastructure & Transport",
        "x_queries": [
            "transport data API financial 2026",
            "freight shipping data free",
            "port congestion data API"
        ],
        "web_queries": [
            "free freight transport data API",
            "port shipping volume data API",
            "infrastructure spending data API 2026"
        ]
    }
]


def get_existing_modules():
    """Get list of existing module names to avoid duplicates"""
    if EXISTING_MODULES_CACHE.exists():
        age = time.time() - EXISTING_MODULES_CACHE.stat().st_mtime
        if age < 3600:  # refresh hourly
            return json.loads(EXISTING_MODULES_CACHE.read_text())
    
    modules = []
    for f in MODULES_DIR.glob('*.py'):
        name = f.stem
        # Read first 5 lines for description
        try:
            lines = f.read_text().split('\n')[:10]
            desc = ' '.join(l.strip('#" ') for l in lines if l.strip().startswith(('#', '"""', "'''"))).strip()[:200]
        except:
            desc = ''
        modules.append({'name': name, 'description': desc})
    
    EXISTING_MODULES_CACHE.write_text(json.dumps(modules, indent=2))
    return modules


def get_hour_category():
    """Determine which category to search based on current hour"""
    hour = datetime.utcnow().hour
    idx = hour % len(CATEGORIES)
    return idx, CATEGORIES[idx]


def call_grok(messages, tools=None, max_tokens=4096):
    """Call Grok 4 API"""
    headers = {
        'Authorization': f'Bearer {XAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': MODEL,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': 0.7
    }
    
    if tools:
        payload['tools'] = tools
    
    resp = requests.post(f'{XAI_BASE}/chat/completions', headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def search_and_discover(category):
    """Use Grok 4 with built-in search to discover data sources"""
    
    existing = get_existing_modules()
    existing_names = [m['name'] for m in existing]
    existing_summary = ', '.join(existing_names[:50]) + f'... ({len(existing_names)} total modules)'
    
    # Build search prompt
    all_queries = category['x_queries'] + category['web_queries']
    
    prompt = f"""You are DataScout, a research agent for QuantClaw — a quantitative financial data platform with {len(existing_names)} existing data modules.

CATEGORY: {category['name']}

YOUR TASK:
1. Search the web and X/Twitter for NEW financial data sources in the "{category['name']}" category
2. Find APIs, datasets, or data providers that are:
   - Free or have free tiers
   - Relevant to quantitative trading / financial analysis
   - Not already in our existing modules
3. Evaluate each discovery

SEARCH QUERIES TO USE:
X/Twitter: {json.dumps(category['x_queries'])}
Web: {json.dumps(category['web_queries'])}

EXISTING MODULES (don't duplicate these): {existing_summary}

For EACH discovery, provide:
1. name: Short name
2. url: API docs or homepage URL
3. description: What data it provides (2-3 sentences)
4. data_type: "api" | "dataset" | "scrape" | "feed"
5. free_tier: true/false + details (rate limits, quotas)
6. data_points: What specific data fields/metrics are available
7. update_frequency: real-time, daily, weekly, quarterly, etc.
8. relevance_score: 1-10 (how useful for quant trading)
9. integration_ease: 1-10 (how easy to build a module)
10. uniqueness_score: 1-10 (does this fill a gap we don't have?)
11. gap_fills: What gap in our existing modules does this fill?
12. python_approach: Brief description of how to integrate (requests, websocket, etc.)
13. sample_endpoint: One example API call

Search thoroughly using both web and X. Find at least 3-5 new sources. Prioritize sources announced or updated in 2025-2026.

Respond in JSON format:
{{
  "category": "{category['name']}",
  "search_date": "YYYY-MM-DD",
  "discoveries": [...],
  "x_insights": "Notable discussions or trends found on X",
  "market_context": "Why this category matters right now"
}}"""

    messages = [
        {"role": "system", "content": "You are a financial data research agent. Use web_search and x_search tools to find real, current data sources. Be thorough and accurate. Only report sources that actually exist and are accessible."},
        {"role": "user", "content": prompt}
    ]
    
    # Call Grok with built-in tools
    result = call_grok(messages, max_tokens=8192)
    
    # Extract response
    choice = result.get('choices', [{}])[0]
    content = choice.get('message', {}).get('content', '')
    
    return content, result.get('usage', {})


def parse_discoveries(raw_response):
    """Parse Grok's response into structured discoveries"""
    # Try to extract JSON from response
    try:
        # Find JSON block
        start = raw_response.find('{')
        end = raw_response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(raw_response[start:end])
    except json.JSONDecodeError:
        pass
    
    # Return raw if can't parse
    return {"raw_response": raw_response, "discoveries": []}


def deduplicate(discoveries):
    """Remove discoveries we've already found"""
    if not DISCOVERIES_DB.exists():
        return discoveries
    
    existing = json.loads(DISCOVERIES_DB.read_text())
    existing_hashes = set(d.get('hash', '') for d in existing.get('all', []))
    
    new = []
    for d in discoveries:
        h = hashlib.md5(json.dumps(d.get('name', '') + d.get('url', '')).encode()).hexdigest()
        d['hash'] = h
        if h not in existing_hashes:
            new.append(d)
    
    return new


def save_discoveries(parsed, usage):
    """Save discoveries to files"""
    today = datetime.now().strftime('%Y-%m-%d')
    hour = datetime.now().strftime('%H')
    
    # Save hourly result
    hourly_file = DATA_DIR / f'{today}_{hour}h.json'
    parsed['usage'] = usage
    parsed['timestamp'] = datetime.now().isoformat()
    hourly_file.write_text(json.dumps(parsed, indent=2, default=str))
    
    # Append to master DB
    if DISCOVERIES_DB.exists():
        master = json.loads(DISCOVERIES_DB.read_text())
    else:
        master = {'all': [], 'stats': {'total_searches': 0, 'total_discoveries': 0}}
    
    new_discoveries = parsed.get('discoveries', [])
    for d in new_discoveries:
        d['found_date'] = today
        d['category'] = parsed.get('category', 'unknown')
        d['hash'] = hashlib.md5(json.dumps(d.get('name', '') + d.get('url', '')).encode()).hexdigest()
    
    deduped = deduplicate(new_discoveries)
    master['all'].extend(deduped)
    master['stats']['total_searches'] += 1
    master['stats']['total_discoveries'] += len(deduped)
    master['stats']['last_search'] = datetime.now().isoformat()
    
    DISCOVERIES_DB.write_text(json.dumps(master, indent=2, default=str))
    
    return len(deduped)


def generate_module_stub(discovery):
    """Generate a Python module stub for a discovery"""
    name = discovery.get('name', 'unknown').lower().replace(' ', '_').replace('-', '_')
    name = ''.join(c for c in name if c.isalnum() or c == '_')
    
    stub = f'''#!/usr/bin/env python3
"""
{discovery.get('name', 'Unknown')} — Auto-generated by DataScout
{discovery.get('description', '')}

Source: {discovery.get('url', '')}
Category: {discovery.get('category', '')}
Free tier: {discovery.get('free_tier', 'unknown')}
Update frequency: {discovery.get('update_frequency', 'unknown')}
Generated: {datetime.now().strftime('%Y-%m-%d')}

Integration approach: {discovery.get('python_approach', 'requests-based REST API')}
"""

import requests
import json
from datetime import datetime

# TODO: Implement data fetching
# Sample endpoint: {discovery.get('sample_endpoint', 'N/A')}

def fetch_data():
    """Fetch data from {discovery.get('name', 'source')}"""
    # TODO: Implement
    raise NotImplementedError("Module stub - needs implementation")

def get_latest():
    """Get latest data point"""
    # TODO: Implement
    raise NotImplementedError("Module stub - needs implementation")

if __name__ == "__main__":
    print(json.dumps({{"module": "{name}", "status": "stub", "source": "{discovery.get('url', '')}"}}, indent=2))
'''
    
    stub_dir = DATA_DIR / 'stubs'
    stub_dir.mkdir(exist_ok=True)
    stub_path = stub_dir / f'{name}.py'
    stub_path.write_text(stub)
    return stub_path


def run():
    """Main entry point — run one search cycle"""
    print(f"{'='*60}")
    print(f"🔍 DataScout — Hourly Research Scan")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Model: Grok 4 (xai/{MODEL})")
    print(f"{'='*60}")
    
    # Determine category
    idx, category = get_hour_category()
    print(f"\n📂 Category [{idx+1}/{len(CATEGORIES)}]: {category['name']}")
    
    # Get existing module count
    existing = get_existing_modules()
    print(f"📦 Existing modules: {len(existing)}")
    
    # Search and discover
    print(f"\n🔎 Searching with Grok 4...")
    print(f"   X queries: {category['x_queries']}")
    print(f"   Web queries: {category['web_queries']}")
    
    try:
        raw_response, usage = search_and_discover(category)
        print(f"\n📊 Grok usage: {usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out")
    except Exception as e:
        print(f"\n❌ Grok API error: {e}")
        return
    
    # Parse
    parsed = parse_discoveries(raw_response)
    discoveries = parsed.get('discoveries', [])
    print(f"\n📋 Discoveries: {len(discoveries)}")
    
    # Save and deduplicate
    new_count = save_discoveries(parsed, usage)
    print(f"🆕 New (deduplicated): {new_count}")
    
    # Generate stubs for high-value discoveries
    stubs_created = 0
    for d in discoveries:
        relevance = d.get('relevance_score', 0)
        uniqueness = d.get('uniqueness_score', 0)
        if isinstance(relevance, (int, float)) and isinstance(uniqueness, (int, float)):
            if relevance >= 7 and uniqueness >= 6:
                stub_path = generate_module_stub(d)
                stubs_created += 1
                print(f"  📝 Stub: {stub_path.name} (relevance={relevance}, uniqueness={uniqueness})")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"✅ SCAN COMPLETE")
    print(f"   Category: {category['name']}")
    print(f"   Discoveries: {len(discoveries)} found, {new_count} new")
    print(f"   Stubs generated: {stubs_created}")
    
    if discoveries:
        print(f"\n🏆 TOP DISCOVERIES:")
        sorted_disc = sorted(discoveries, key=lambda x: (
            x.get('relevance_score', 0) if isinstance(x.get('relevance_score', 0), (int, float)) else 0
        ), reverse=True)
        for i, d in enumerate(sorted_disc[:5]):
            print(f"   {i+1}. {d.get('name', '?')} — relevance:{d.get('relevance_score','?')}/10, unique:{d.get('uniqueness_score','?')}/10")
            print(f"      {d.get('description', '')[:100]}")
            print(f"      URL: {d.get('url', 'N/A')}")
    
    # X insights
    x_insights = parsed.get('x_insights', '')
    if x_insights:
        print(f"\n🐦 X INSIGHTS: {x_insights[:200]}")
    
    # Output for WhatsApp (weekly digest will use this)
    report = {
        'date': datetime.now().isoformat(),
        'category': category['name'],
        'discoveries': len(discoveries),
        'new': new_count,
        'stubs': stubs_created,
        'top': [{'name': d.get('name'), 'relevance': d.get('relevance_score')} for d in sorted(discoveries, key=lambda x: x.get('relevance_score', 0) if isinstance(x.get('relevance_score', 0), (int, float)) else 0, reverse=True)[:3]]
    }
    
    print(f"\n---REPORT_JSON---")
    print(json.dumps(report, default=str))
    print(f"---END_REPORT---")


if __name__ == '__main__':
    run()
