#!/usr/bin/env python3
"""Download full US stock universe to local cache."""
import yfinance as yf
import os, sys, warnings, time
warnings.filterwarnings('ignore')

cache_dir = '/home/quant/apps/quantclaw-data/data/price_cache'
os.makedirs(cache_dir, exist_ok=True)
existing = set(f.replace('.csv','') for f in os.listdir(cache_dir) if f.endswith('.csv'))

# S&P 500 + NASDAQ 100 + Major ETFs + Popular stocks
ALL_TICKERS = [
    # S&P 500 (top ~500)
    'AAPL','MSFT','GOOGL','GOOG','AMZN','NVDA','TSLA','META','BRK-B','LLY',
    'AVGO','JPM','V','UNH','XOM','MA','JNJ','PG','COST','HD',
    'ABBV','WMT','MRK','NFLX','CRM','BAC','CVX','KO','AMD','PEP',
    'ORCL','TMO','ADBE','LIN','ACN','MCD','ABT','CSCO','WFC','PM',
    'TXN','GE','DHR','MS','QCOM','ISRG','IBM','RTX','INTU','GS',
    'NOW','NEE','CAT','AMGN','AMAT','T','PFE','BLK','SYK','AXP',
    'BKNG','LOW','HON','SPGI','UNP','VRTX','COP','LRCX','DE','TJX',
    'C','MDT','REGN','SCHW','PGR','PANW','ADI','BMY','ADP','KLAC',
    'BSX','ETN','SNPS','FI','GILD','CB','CME','SBUX','MU','MDLZ',
    'CDNS','SHW','CMG','ITW','PLD','MO','MCK','ZTS','CI','USB',
    'DUK','SO','GD','CL','AON','ICE','BDX','FCX','SLB','APH',
    'EQIX','NSC','TT','NOC','PYPL','CTAS','MCO','HCA','ECL','CSX',
    'EMR','WMB','PXD','COF','MMC','PH','ORLY','SRE','MAR','TDG',
    'PCAR','OXY','ROP','ADSK','PSA','NXPI','WELL','AEP','AIG','MET',
    'MNST','AFL','D','HUM','MCHP','GIS','SPG','F','GM','AZO',
    'KMB','TEL','HLT','CCI','IDXX','MSCI','STZ','BIIB','FTNT','A',
    'DXCM','NEM','ODFL','KHC','IQV','CTVA','RCL','PCG','TRGP','DVN',
    'ALL','AME','BKR','OTIS','PPG','EA','YUM','HSY','WEC','VRSK',
    'GPN','XEL','FAST','ED','GEHC','AWK','TSCO','KEYS','MLM','IR',
    'DOW','LHX','IT','VMC','CBRE','FTV','PWR','DAL','EW','DD',
    'WAB','ACGL','WTW','EXC','RMD','WST','FANG','ROK','CHD','VICI',
    'EFX','ANSS','CTSH','MTD','MPWR','ZBH','FE','ON','HPQ','CPRT',
    'IRM','GLW','HAL','TROW','STT','HPE','DFS','BRO','GWW','STE',
    'EBAY','PTC','CINF','NVR','WAT','WSO','EXPE','AVB','ALGN','DRI',
    'POOL','ZBRA','ULTA','TTWO','K','FITB','MTB','TYL','EQR','ILMN',
    'SNA','CNP','RF','ATO','NI','CMS','WRB','LNT','NTRS','ESS',
    'CE','HOLX','BEN','MKC','RL','TXT','AES','JBHT','SEE','TPR',
    'BWA','NDSN','MKTX','LKQ','EMN','IEX','PNR','BIO','TER','UDR',
    'REG','AAL','NRG','NCLH','HRL','CPB','XRAY','VTR','FRT','KIM',
    'BXP','PEAK','CZR','MGM','WYNN','LVS','HAS','PARA','DVA','DG',
    'DLTR','BBWI','AIZ','LW','GL','LUMN',
    # NASDAQ 100 additions
    'PLTR','MELI','CRWD','TEAM','DASH','MRVL','SMCI','ARM','COIN',
    'DDOG','ZS','SNOW','TTD','ABNB','RIVN','LCID','RBLX','SPOT',
    'SQ','SHOP','SE','GRAB','ROKU','U','PINS','SNAP','HOOD','MSTR',
    'NET','MDB','PATH','OKTA','TWLO','BILL','HUBS','VEEV','WDAY',
    'FICO','AXON','DECK','LULU','RH','BURL','TJX','ROST','WSM',
    # AI / Semiconductors
    'ASML','TSM','LRCX','KLAC','AMAT','MRVL','ON','MU','INTC',
    'ADI','NXPI','MCHP','TXN','QCOM','AVGO','AMD','NVDA',
    'IONQ','RGTI','QUBT','AI','BBAI','SOUN','UPST',
    # ETFs - Major
    'SPY','QQQ','IWM','IWF','IWD','DIA','RSP','MDY','SLY','IJR','IJH',
    # ETFs - Sector
    'XLF','XLK','XLE','XLV','XLI','XLC','XLY','XLP','XLU','XLB','XLRE',
    # ETFs - Thematic
    'SOXX','SMH','IBB','XBI','ITB','XHB','KRE','KWEB','HACK','CIBR',
    'BOTZ','ROBO','ARKK','ARKG','ARKW','ARKF','ARKQ',
    # ETFs - Fixed Income
    'TLT','IEF','SHY','BND','HYG','LQD','TIP','VTIP','EMB','AGG',
    # ETFs - Commodities
    'GLD','SLV','USO','UNG','DBA','DBC','WEAT','PDBC',
    # ETFs - International
    'VEA','VWO','EEM','FXI','EWJ','EWZ','EWG','EWU','INDA','EWT',
    # ETFs - Crypto
    'IBIT','ETHA','BITO',
    # ETFs - Leveraged
    'TQQQ','SQQQ','SPXL','SPXS','UVXY','SVXY','SOXL','SOXS',
    # ETFs - Income
    'VTI','VOO','VIG','SCHD','JEPI','JEPQ','VNQ','VNQI',
    # ETFs - Currency
    'UUP','FXE','FXY','FXB',
    # ETFs - Mining/Materials
    'XME','COPX','LIT','REMX','URA','PICK','SIL','GDXJ','GDX',
    # Crypto
    'BTC-USD','ETH-USD','SOL-USD','DOGE-USD','XRP-USD','ADA-USD','AVAX-USD','DOT-USD',
    'MATIC-USD','LINK-USD','UNI-USD','AAVE-USD','BNB-USD',
    # Popular / Meme
    'GME','AMC','SOFI','CLOV','WISH','BB','NIO','XPEV','LI','DKNG',
    # REITs
    'O','AMT','CCI','EQIX','PLD','SPG','DLR','PSA','WELL','AVB',
    # More blue chips
    'BRK-A','DIS','NKE','SBUX','INTC','PYPL','SQ',
    # Dividend aristocrats extras
    'MMM','AOS','ABT','ABBV','ACN','AFL','APD','ALB','ARE','ALLE',
    'LNT','AMCR','AEE','AEP','AWK','APH','APTV','ACGL',
]

# Deduplicate
tickers = list(dict.fromkeys(ALL_TICKERS))
new = [t for t in tickers if t not in existing]
print(f"Total unique: {len(tickers)} | Already cached: {len(existing)} | New to download: {len(new)}")

downloaded = 0
failed = 0
total_rows = 0
batch_size = 10

for i, t in enumerate(new):
    try:
        data = yf.download(t, period='max', interval='1d', progress=False)
        if data.empty:
            failed += 1
            continue
        if hasattr(data.columns, 'levels') and len(data.columns.levels) > 1:
            data.columns = data.columns.get_level_values(0)
        outpath = os.path.join(cache_dir, f'{t}.csv')
        data.to_csv(outpath)
        rows = len(data)
        total_rows += rows
        downloaded += 1
        if downloaded % 50 == 0:
            print(f"  Progress: {downloaded}/{len(new)} downloaded, {total_rows:,} rows so far...")
    except Exception as e:
        failed += 1

    # Rate limit - small pause every 10
    if (i+1) % batch_size == 0:
        time.sleep(0.5)

print(f"\n=== DONE: {downloaded} new + {len(existing)} existing = {downloaded + len(existing)} total tickers ===")
print(f"New rows: {total_rows:,} | Failed: {failed}")

# Total cache stats
all_files = [f for f in os.listdir(cache_dir) if f.endswith('.csv')]
total_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in all_files)
print(f"Cache: {len(all_files)} files, {total_size/1024/1024:.1f} MB")
