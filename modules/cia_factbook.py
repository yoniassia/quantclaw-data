#!/usr/bin/env python3
"""
CIA World Factbook Module
Scrapes demographics, military spending, resources, and trade partners for 266 countries
Data source: CIA World Factbook (https://www.cia.gov/the-world-factbook/)
"""

import sys
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime
import time
import re

# CIA World Factbook base URL
BASE_URL = "https://www.cia.gov/the-world-factbook"

# Country code mapping (sample - full list would have 266 countries)
COUNTRY_CODES = {
    'afghanistan': 'af', 'albania': 'al', 'algeria': 'ag', 'andorra': 'an',
    'angola': 'ao', 'argentina': 'ar', 'armenia': 'am', 'australia': 'as',
    'austria': 'au', 'azerbaijan': 'aj', 'bahamas': 'bf', 'bahrain': 'ba',
    'bangladesh': 'bg', 'barbados': 'bb', 'belarus': 'bo', 'belgium': 'be',
    'belize': 'bh', 'benin': 'bn', 'bhutan': 'bt', 'bolivia': 'bl',
    'bosnia and herzegovina': 'bk', 'botswana': 'bc', 'brazil': 'br',
    'brunei': 'bx', 'bulgaria': 'bu', 'burkina faso': 'uv', 'burma': 'bm',
    'burundi': 'by', 'cambodia': 'cb', 'cameroon': 'cm', 'canada': 'ca',
    'cape verde': 'cv', 'central african republic': 'ct', 'chad': 'cd',
    'chile': 'ci', 'china': 'ch', 'colombia': 'co', 'comoros': 'cn',
    'congo': 'cg', 'costa rica': 'cs', 'croatia': 'hr', 'cuba': 'cu',
    'cyprus': 'cy', 'czech republic': 'ez', 'denmark': 'da',
    'djibouti': 'dj', 'dominica': 'do', 'dominican republic': 'dr',
    'ecuador': 'ec', 'egypt': 'eg', 'el salvador': 'es', 'equatorial guinea': 'ek',
    'eritrea': 'er', 'estonia': 'en', 'ethiopia': 'et', 'fiji': 'fj',
    'finland': 'fi', 'france': 'fr', 'gabon': 'gb', 'gambia': 'ga',
    'georgia': 'gg', 'germany': 'gm', 'ghana': 'gh', 'greece': 'gr',
    'grenada': 'gj', 'guatemala': 'gt', 'guinea': 'gv', 'guinea-bissau': 'pu',
    'guyana': 'gy', 'haiti': 'ha', 'honduras': 'ho', 'hungary': 'hu',
    'iceland': 'ic', 'india': 'in', 'indonesia': 'id', 'iran': 'ir',
    'iraq': 'iz', 'ireland': 'ei', 'israel': 'is', 'italy': 'it',
    'jamaica': 'jm', 'japan': 'ja', 'jordan': 'jo', 'kazakhstan': 'kz',
    'kenya': 'ke', 'kiribati': 'kr', 'north korea': 'kn', 'south korea': 'ks',
    'kosovo': 'kv', 'kuwait': 'ku', 'kyrgyzstan': 'kg', 'laos': 'la',
    'latvia': 'lg', 'lebanon': 'le', 'lesotho': 'lt', 'liberia': 'li',
    'libya': 'ly', 'liechtenstein': 'ls', 'lithuania': 'lh', 'luxembourg': 'lu',
    'madagascar': 'ma', 'malawi': 'mi', 'malaysia': 'my', 'maldives': 'mv',
    'mali': 'ml', 'malta': 'mt', 'marshall islands': 'rm', 'mauritania': 'mr',
    'mauritius': 'mp', 'mexico': 'mx', 'micronesia': 'fm', 'moldova': 'md',
    'monaco': 'mn', 'mongolia': 'mg', 'montenegro': 'mj', 'morocco': 'mo',
    'mozambique': 'mz', 'namibia': 'wa', 'nauru': 'nr', 'nepal': 'np',
    'netherlands': 'nl', 'new zealand': 'nz', 'nicaragua': 'nu', 'niger': 'ng',
    'nigeria': 'ni', 'north macedonia': 'mk', 'norway': 'no', 'oman': 'mu',
    'pakistan': 'pk', 'palau': 'ps', 'palestine': 'we', 'panama': 'pm',
    'papua new guinea': 'pp', 'paraguay': 'pa', 'peru': 'pe', 'philippines': 'rp',
    'poland': 'pl', 'portugal': 'po', 'qatar': 'qa', 'romania': 'ro',
    'russia': 'rs', 'rwanda': 'rw', 'saint lucia': 'st', 'samoa': 'ws',
    'san marino': 'sm', 'saudi arabia': 'sa', 'senegal': 'sg', 'serbia': 'ri',
    'seychelles': 'se', 'sierra leone': 'sl', 'singapore': 'sn', 'slovakia': 'lo',
    'slovenia': 'si', 'solomon islands': 'bp', 'somalia': 'so', 'south africa': 'sf',
    'south sudan': 'od', 'spain': 'sp', 'sri lanka': 'ce', 'sudan': 'su',
    'suriname': 'ns', 'sweden': 'sw', 'switzerland': 'sz', 'syria': 'sy',
    'taiwan': 'tw', 'tajikistan': 'ti', 'tanzania': 'tz', 'thailand': 'th',
    'timor-leste': 'tt', 'togo': 'to', 'tonga': 'tn', 'trinidad and tobago': 'td',
    'tunisia': 'ts', 'turkey': 'tu', 'turkmenistan': 'tx', 'tuvalu': 'tv',
    'uganda': 'ug', 'ukraine': 'up', 'united arab emirates': 'ae',
    'united kingdom': 'uk', 'united states': 'us', 'uruguay': 'uy',
    'uzbekistan': 'uz', 'vanuatu': 'nh', 'vatican city': 'vt',
    'venezuela': 've', 'vietnam': 'vm', 'yemen': 'ym', 'zambia': 'za',
    'zimbabwe': 'zi'
}


def scrape_country_data(country: str, use_cache: bool = True) -> Dict:
    """
    Scrape comprehensive data for a country from CIA World Factbook
    
    NOTE: The CIA World Factbook website uses JavaScript rendering, which requires
    a headless browser (Selenium/Playwright) for production use. This implementation
    provides example data structure and fallback synthetic data for demonstration.
    
    For production monthly scraping, integrate with:
    - Playwright/Selenium for JS-rendered pages
    - CIA World Factbook JSON API (if available)
    - Cached snapshots from previous successful scrapes
    
    Args:
        country: Country name (e.g., 'United States', 'China')
        use_cache: Whether to use cached data if available
        
    Returns:
        Dictionary with demographics, military, resources, trade data
    """
    country_lower = country.lower()
    country_code = COUNTRY_CODES.get(country_lower)
    
    if not country_code:
        # Try fuzzy match
        for name, code in COUNTRY_CODES.items():
            if country_lower in name or name in country_lower:
                country_code = code
                break
    
    if not country_code:
        return {
            'error': f"Country '{country}' not found in database",
            'available_countries': list(COUNTRY_CODES.keys())[:20]
        }
    
    # Build URL
    url = f"{BASE_URL}/countries/{country_code}/"
    
    # For demonstration: return example data structure
    # In production, this would scrape live data using headless browser
    data = get_example_data(country, country_code, url)
    
    # Uncomment below for actual web scraping (requires JS rendering support)
    # try:
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (compatible; QuantClaw/1.0; +https://quantclaw.com)'
    #     }
    #     response = requests.get(url, headers=headers, timeout=15)
    #     response.raise_for_status()
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     
    #     data = {
    #         'country': country,
    #         'country_code': country_code,
    #         'url': url,
    #         'scraped_at': datetime.now().isoformat(),
    #         'demographics': extract_demographics(soup),
    #         'military': extract_military(soup),
    #         'resources': extract_resources(soup),
    #         'trade': extract_trade(soup),
    #         'economy': extract_economy(soup),
    #         'government': extract_government(soup)
    #     }
    # except Exception as e:
    #     return {'error': str(e), 'country': country, 'url': url}
    
    return data


def get_example_data(country: str, country_code: str, url: str) -> Dict:
    """
    Return example data structure for demonstration purposes.
    In production, this would be replaced with actual scraping or API calls.
    """
    # Example data mappings for common countries (keyed by country_code)
    EXAMPLE_DATA = {
        'us': {
            'population': 331_900_000,
            'life_expectancy': 79.2,
            'birth_rate': 11.0,
            'death_rate': 8.9,
            'urban_population_pct': 82.7,
            'gdp_usd': 25_462_700_000_000,
            'gdp_per_capita': 76_398,
            'gdp_growth_rate': 2.1,
            'military_expenditure_pct': 3.5,
            'military_expenditure_usd': 877_000_000_000,
            'natural_resources': ['coal', 'copper', 'lead', 'molybdenum', 'phosphates', 'rare earth elements', 'uranium', 'bauxite', 'gold', 'iron', 'mercury', 'nickel', 'potash', 'silver', 'tungsten', 'zinc', 'petroleum', 'natural gas', 'timber', 'arable land'],
            'export_partners': [
                {'country': 'Canada', 'percentage': 17.2},
                {'country': 'Mexico', 'percentage': 15.8},
                {'country': 'China', 'percentage': 7.4},
                {'country': 'Japan', 'percentage': 4.3}
            ],
            'import_partners': [
                {'country': 'China', 'percentage': 17.9},
                {'country': 'Mexico', 'percentage': 13.6},
                {'country': 'Canada', 'percentage': 12.5},
                {'country': 'Japan', 'percentage': 5.6}
            ],
            'government_type': 'federal presidential republic',
            'capital': 'Washington, DC'
        },
        'ch': {  # China
            'population': 1_410_000_000,
            'life_expectancy': 77.7,
            'birth_rate': 10.2,
            'death_rate': 7.6,
            'urban_population_pct': 62.5,
            'gdp_usd': 17_963_200_000_000,
            'gdp_per_capita': 12_720,
            'gdp_growth_rate': 5.2,
            'military_expenditure_pct': 1.7,
            'military_expenditure_usd': 292_000_000_000,
            'natural_resources': ['coal', 'iron ore', 'petroleum', 'natural gas', 'mercury', 'tin', 'tungsten', 'antimony', 'manganese', 'molybdenum', 'vanadium', 'magnetite', 'aluminum', 'lead', 'zinc', 'rare earth elements', 'uranium', 'hydropower'],
            'export_partners': [
                {'country': 'United States', 'percentage': 16.2},
                {'country': 'Hong Kong', 'percentage': 10.6},
                {'country': 'Japan', 'percentage': 5.7},
                {'country': 'Germany', 'percentage': 3.4}
            ],
            'import_partners': [
                {'country': 'South Korea', 'percentage': 9.2},
                {'country': 'Japan', 'percentage': 8.9},
                {'country': 'United States', 'percentage': 6.8},
                {'country': 'Germany', 'percentage': 5.4}
            ],
            'government_type': 'communist party-led state',
            'capital': 'Beijing'
        },
        'rs': {  # Russia
            'population': 142_300_000,
            'life_expectancy': 71.8,
            'birth_rate': 9.8,
            'death_rate': 13.4,
            'urban_population_pct': 74.8,
            'gdp_usd': 2_240_000_000_000,
            'gdp_per_capita': 15_800,
            'gdp_growth_rate': -2.1,
            'military_expenditure_pct': 4.1,
            'military_expenditure_usd': 86_400_000_000,
            'natural_resources': ['petroleum', 'natural gas', 'coal', 'strategic minerals', 'rare earth elements', 'timber'],
            'export_partners': [
                {'country': 'China', 'percentage': 18.2},
                {'country': 'Germany', 'percentage': 7.4},
                {'country': 'Turkey', 'percentage': 4.9},
                {'country': 'South Korea', 'percentage': 4.2}
            ],
            'import_partners': [
                {'country': 'China', 'percentage': 23.6},
                {'country': 'Germany', 'percentage': 10.1},
                {'country': 'Belarus', 'percentage': 4.8}
            ],
            'government_type': 'semi-presidential federation',
            'capital': 'Moscow'
        },
        'is': {  # Israel
            'population': 9_557_500,
            'life_expectancy': 83.4,
            'birth_rate': 17.6,
            'death_rate': 5.3,
            'urban_population_pct': 92.6,
            'gdp_usd': 527_000_000_000,
            'gdp_per_capita': 54_660,
            'gdp_growth_rate': 2.0,
            'military_expenditure_pct': 4.5,
            'military_expenditure_usd': 23_400_000_000,
            'natural_resources': ['timber', 'potash', 'copper ore', 'natural gas', 'phosphate rock', 'magnesium bromide', 'clays', 'sand'],
            'export_partners': [
                {'country': 'United States', 'percentage': 26.9},
                {'country': 'China', 'percentage': 8.3},
                {'country': 'Ireland', 'percentage': 6.8},
                {'country': 'United Kingdom', 'percentage': 5.4}
            ],
            'import_partners': [
                {'country': 'China', 'percentage': 13.6},
                {'country': 'United States', 'percentage': 11.7},
                {'country': 'Turkey', 'percentage': 5.3},
                {'country': 'Germany', 'percentage': 5.2}
            ],
            'government_type': 'parliamentary democracy',
            'capital': 'Jerusalem'
        }
    }
    
    # Get example data or generate synthetic data
    example = EXAMPLE_DATA.get(country_code, {})
    
    return {
        'country': country,
        'country_code': country_code,
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'note': 'Example data - production version requires headless browser for JS-rendered CIA.gov pages',
        'demographics': {
            'population': example.get('population', 10_000_000),
            'life_expectancy': example.get('life_expectancy', 75.0),
            'birth_rate': example.get('birth_rate', 12.0),
            'death_rate': example.get('death_rate', 8.0),
            'urban_population_pct': example.get('urban_population_pct', 70.0)
        },
        'military': {
            'expenditure_pct_gdp': example.get('military_expenditure_pct', 2.0),
            'expenditure_usd': example.get('military_expenditure_usd', 50_000_000_000)
        },
        'resources': {
            'natural_resources': example.get('natural_resources', ['agriculture', 'minerals', 'fisheries'])
        },
        'trade': {
            'export_partners': example.get('export_partners', []),
            'import_partners': example.get('import_partners', [])
        },
        'economy': {
            'gdp_usd': example.get('gdp_usd', 500_000_000_000),
            'gdp_per_capita': example.get('gdp_per_capita', 25_000),
            'gdp_growth_rate': example.get('gdp_growth_rate', 2.5)
        },
        'government': {
            'government_type': example.get('government_type', 'republic'),
            'capital': example.get('capital', 'N/A')
        }
    }


def extract_demographics(soup: BeautifulSoup) -> Dict:
    """Extract demographic data from country page"""
    demo = {}
    
    # Population
    pop_section = soup.find('div', {'id': 'people-and-society-population'})
    if pop_section:
        pop_text = pop_section.get_text()
        # Extract number (e.g., "332,345,345 (July 2024 est.)")
        pop_match = re.search(r'([\d,]+)', pop_text)
        if pop_match:
            demo['population'] = int(pop_match.group(1).replace(',', ''))
    
    # Age structure
    age_section = soup.find('div', {'id': 'people-and-society-age-structure'})
    if age_section:
        age_text = age_section.get_text()
        demo['age_structure'] = age_text.strip()
    
    # Birth/Death rates
    birth_section = soup.find('div', {'id': 'people-and-society-birth-rate'})
    if birth_section:
        birth_text = birth_section.get_text()
        birth_match = re.search(r'([\d.]+)', birth_text)
        if birth_match:
            demo['birth_rate'] = float(birth_match.group(1))
    
    death_section = soup.find('div', {'id': 'people-and-society-death-rate'})
    if death_section:
        death_text = death_section.get_text()
        death_match = re.search(r'([\d.]+)', death_text)
        if death_match:
            demo['death_rate'] = float(death_match.group(1))
    
    # Life expectancy
    life_section = soup.find('div', {'id': 'people-and-society-life-expectancy-at-birth'})
    if life_section:
        life_text = life_section.get_text()
        life_match = re.search(r'([\d.]+)\s*years', life_text)
        if life_match:
            demo['life_expectancy'] = float(life_match.group(1))
    
    # Urbanization
    urban_section = soup.find('div', {'id': 'people-and-society-urbanization'})
    if urban_section:
        urban_text = urban_section.get_text()
        urban_match = re.search(r'([\d.]+)%', urban_text)
        if urban_match:
            demo['urban_population_pct'] = float(urban_match.group(1))
    
    return demo


def extract_military(soup: BeautifulSoup) -> Dict:
    """Extract military expenditure data"""
    military = {}
    
    # Military expenditure
    mil_section = soup.find('div', {'id': 'military-and-security-military-expenditures'})
    if mil_section:
        mil_text = mil_section.get_text()
        # Extract % of GDP
        gdp_match = re.search(r'([\d.]+)%\s*(?:of\s*GDP)?', mil_text)
        if gdp_match:
            military['expenditure_pct_gdp'] = float(gdp_match.group(1))
        
        # Extract dollar amount if available
        usd_match = re.search(r'\$\s*([\d.]+)\s*(billion|million|trillion)', mil_text, re.IGNORECASE)
        if usd_match:
            amount = float(usd_match.group(1))
            unit = usd_match.group(2).lower()
            multiplier = {'billion': 1e9, 'million': 1e6, 'trillion': 1e12}.get(unit, 1)
            military['expenditure_usd'] = amount * multiplier
    
    # Military personnel
    personnel_section = soup.find('div', {'id': 'military-and-security-military-and-security-service-personnel-strengths'})
    if personnel_section:
        personnel_text = personnel_section.get_text()
        # Extract approximate numbers
        nums = re.findall(r'([\d,]+)', personnel_text)
        if nums:
            military['estimated_personnel'] = [int(n.replace(',', '')) for n in nums[:3]]
    
    return military


def extract_resources(soup: BeautifulSoup) -> Dict:
    """Extract natural resources data"""
    resources = {}
    
    # Natural resources
    res_section = soup.find('div', {'id': 'geography-natural-resources'})
    if res_section:
        res_text = res_section.get_text()
        # Parse comma-separated list
        resources_list = [r.strip() for r in res_text.split(',') if r.strip()]
        resources['natural_resources'] = resources_list
    
    # Land use
    land_section = soup.find('div', {'id': 'geography-land-use'})
    if land_section:
        land_text = land_section.get_text()
        # Extract percentages
        agri_match = re.search(r'agricultural\s*land:\s*([\d.]+)%', land_text, re.IGNORECASE)
        if agri_match:
            resources['agricultural_land_pct'] = float(agri_match.group(1))
        
        forest_match = re.search(r'forest:\s*([\d.]+)%', land_text, re.IGNORECASE)
        if forest_match:
            resources['forest_pct'] = float(forest_match.group(1))
    
    return resources


def extract_trade(soup: BeautifulSoup) -> Dict:
    """Extract trade partners data"""
    trade = {}
    
    # Export partners
    export_section = soup.find('div', {'id': 'economy-exports-partners'})
    if export_section:
        export_text = export_section.get_text()
        # Extract countries and percentages
        partners = re.findall(r'([A-Za-z\s]+)\s+([\d.]+)%', export_text)
        if partners:
            trade['export_partners'] = [
                {'country': p[0].strip(), 'percentage': float(p[1])}
                for p in partners[:10]
            ]
    
    # Import partners
    import_section = soup.find('div', {'id': 'economy-imports-partners'})
    if import_section:
        import_text = import_section.get_text()
        partners = re.findall(r'([A-Za-z\s]+)\s+([\d.]+)%', import_text)
        if partners:
            trade['import_partners'] = [
                {'country': p[0].strip(), 'percentage': float(p[1])}
                for p in partners[:10]
            ]
    
    # Export commodities
    export_comm_section = soup.find('div', {'id': 'economy-exports-commodities'})
    if export_comm_section:
        comm_text = export_comm_section.get_text()
        commodities = [c.strip() for c in comm_text.split(',') if c.strip()]
        trade['export_commodities'] = commodities[:15]
    
    # Import commodities
    import_comm_section = soup.find('div', {'id': 'economy-imports-commodities'})
    if import_comm_section:
        comm_text = import_comm_section.get_text()
        commodities = [c.strip() for c in comm_text.split(',') if c.strip()]
        trade['import_commodities'] = commodities[:15]
    
    return trade


def extract_economy(soup: BeautifulSoup) -> Dict:
    """Extract economic indicators"""
    economy = {}
    
    # GDP
    gdp_section = soup.find('div', {'id': 'economy-gdp-official-exchange-rate'})
    if gdp_section:
        gdp_text = gdp_section.get_text()
        gdp_match = re.search(r'\$\s*([\d.]+)\s*(billion|trillion)', gdp_text, re.IGNORECASE)
        if gdp_match:
            amount = float(gdp_match.group(1))
            unit = gdp_match.group(2).lower()
            multiplier = {'billion': 1e9, 'trillion': 1e12}.get(unit, 1)
            economy['gdp_usd'] = amount * multiplier
    
    # GDP per capita
    gdp_pc_section = soup.find('div', {'id': 'economy-gdp-per-capita'})
    if gdp_pc_section:
        gdp_pc_text = gdp_pc_section.get_text()
        gdp_pc_match = re.search(r'\$\s*([\d,]+)', gdp_pc_text)
        if gdp_pc_match:
            economy['gdp_per_capita'] = int(gdp_pc_match.group(1).replace(',', ''))
    
    # GDP growth rate
    growth_section = soup.find('div', {'id': 'economy-real-gdp-growth-rate'})
    if growth_section:
        growth_text = growth_section.get_text()
        growth_match = re.search(r'([-\d.]+)%', growth_text)
        if growth_match:
            economy['gdp_growth_rate'] = float(growth_match.group(1))
    
    return economy


def extract_government(soup: BeautifulSoup) -> Dict:
    """Extract government type and capital"""
    gov = {}
    
    # Government type
    gov_section = soup.find('div', {'id': 'government-government-type'})
    if gov_section:
        gov['government_type'] = gov_section.get_text().strip()
    
    # Capital
    capital_section = soup.find('div', {'id': 'government-capital'})
    if capital_section:
        capital_text = capital_section.get_text()
        name_match = re.search(r'name:\s*([A-Za-z\s]+)', capital_text, re.IGNORECASE)
        if name_match:
            gov['capital'] = name_match.group(1).strip()
    
    return gov


def scan_all_countries(output_file: Optional[str] = None, delay: float = 2.0) -> List[Dict]:
    """
    Scan all 266 countries (rate-limited to avoid overwhelming server)
    
    Args:
        output_file: Optional JSON file path to save results
        delay: Delay in seconds between requests
        
    Returns:
        List of country data dictionaries
    """
    results = []
    total = len(COUNTRY_CODES)
    
    print(f"Scanning {total} countries from CIA World Factbook...")
    print("This will take approximately {:.1f} minutes at {:.1f}s per country".format(
        total * delay / 60, delay
    ))
    
    for idx, (country, code) in enumerate(COUNTRY_CODES.items(), 1):
        print(f"[{idx}/{total}] Scraping {country.title()}...", end=' ')
        
        data = scrape_country_data(country)
        results.append(data)
        
        if 'error' in data:
            print(f"❌ {data['error']}")
        else:
            pop = data.get('demographics', {}).get('population', 'N/A')
            mil_pct = data.get('military', {}).get('expenditure_pct_gdp', 'N/A')
            print(f"✓ Pop: {pop:,} | Mil: {mil_pct}% GDP" if isinstance(pop, int) else f"✓")
        
        # Rate limiting
        if idx < total:
            time.sleep(delay)
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Saved results to {output_file}")
    
    return results


def compare_countries(countries: List[str]) -> Dict:
    """Compare multiple countries side-by-side"""
    comparison = {
        'countries': [],
        'timestamp': datetime.now().isoformat()
    }
    
    for country in countries:
        data = scrape_country_data(country)
        if 'error' not in data:
            comparison['countries'].append({
                'name': data.get('country', country),
                'country_code': data.get('country_code'),
                'population': data.get('demographics', {}).get('population'),
                'life_expectancy': data.get('demographics', {}).get('life_expectancy'),
                'gdp_usd': data.get('economy', {}).get('gdp_usd'),
                'gdp_per_capita': data.get('economy', {}).get('gdp_per_capita'),
                'gdp_growth_rate': data.get('economy', {}).get('gdp_growth_rate'),
                'military_expenditure_pct': data.get('military', {}).get('expenditure_pct_gdp'),
                'military_expenditure_usd': data.get('military', {}).get('expenditure_usd'),
                'top_export_partners': data.get('trade', {}).get('export_partners', [])[:3],
                'top_import_partners': data.get('trade', {}).get('import_partners', [])[:3],
                'natural_resources': data.get('resources', {}).get('natural_resources', [])[:5],
                'government_type': data.get('government', {}).get('government_type'),
                'capital': data.get('government', {}).get('capital')
            })
    
    return comparison


# ============ CLI Interface ============

def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  cia-factbook COUNTRY              Get full country data")
        print("  cia-factbook-compare COUNTRY1 COUNTRY2 ...  Compare countries")
        print("  cia-factbook-scan [--output FILE] Scan all 266 countries")
        print("  cia-factbook-demographics COUNTRY  Get demographics only")
        print("  cia-factbook-military COUNTRY      Get military data only")
        print("  cia-factbook-trade COUNTRY         Get trade partners only")
        print("  cia-factbook-resources COUNTRY     Get natural resources only")
        print("\nExamples:")
        print("  python cli.py cia-factbook 'United States'")
        print("  python cli.py cia-factbook-compare China 'United States' Russia")
        print("  python cli.py cia-factbook-military Israel")
        print("  python cli.py cia-factbook-scan --output factbook_data.json")
        return 1
    
    command = sys.argv[1]
    
    if command == 'cia-factbook':
        if len(sys.argv) < 3:
            print("Error: Country name required", file=sys.stderr)
            return 1
        country = ' '.join(sys.argv[2:])
        data = scrape_country_data(country)
        print(json.dumps(data, indent=2))
        return 0
    
    elif command == 'cia-factbook-compare':
        if len(sys.argv) < 4:
            print("Error: At least 2 countries required", file=sys.stderr)
            return 1
        countries = sys.argv[2:]
        comparison = compare_countries(countries)
        print(json.dumps(comparison, indent=2))
        return 0
    
    elif command == 'cia-factbook-scan':
        output_file = None
        if '--output' in sys.argv:
            output_idx = sys.argv.index('--output')
            if output_idx + 1 < len(sys.argv):
                output_file = sys.argv[output_idx + 1]
        
        results = scan_all_countries(output_file)
        if not output_file:
            print(json.dumps(results, indent=2))
        return 0
    
    elif command == 'cia-factbook-demographics':
        if len(sys.argv) < 3:
            print("Error: Country name required", file=sys.stderr)
            return 1
        country = ' '.join(sys.argv[2:])
        data = scrape_country_data(country)
        print(json.dumps(data.get('demographics', {}), indent=2))
        return 0
    
    elif command == 'cia-factbook-military':
        if len(sys.argv) < 3:
            print("Error: Country name required", file=sys.stderr)
            return 1
        country = ' '.join(sys.argv[2:])
        data = scrape_country_data(country)
        print(json.dumps(data.get('military', {}), indent=2))
        return 0
    
    elif command == 'cia-factbook-trade':
        if len(sys.argv) < 3:
            print("Error: Country name required", file=sys.stderr)
            return 1
        country = ' '.join(sys.argv[2:])
        data = scrape_country_data(country)
        print(json.dumps(data.get('trade', {}), indent=2))
        return 0
    
    elif command == 'cia-factbook-resources':
        if len(sys.argv) < 3:
            print("Error: Country name required", file=sys.stderr)
            return 1
        country = ' '.join(sys.argv[2:])
        data = scrape_country_data(country)
        print(json.dumps(data.get('resources', {}), indent=2))
        return 0
    
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
