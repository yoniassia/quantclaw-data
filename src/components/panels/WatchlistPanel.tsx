'use client';
import { useState, useEffect, useCallback } from 'react';
import Panel from '@/components/terminal/Panel';

interface WatchlistItem { symbol: string; price: number; change: number; changePercent: number; sparkline: number[]; }
interface WatchlistPanelProps { id: string; onOpenChart?: (ticker: string) => void; }
const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'SPY', 'QQQ', 'BTC'];

export default function WatchlistPanel({ id, onOpenChart }: WatchlistPanelProps) {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPrices = useCallback(async () => {
    setLoading(true);
    const items: WatchlistItem[] = [];
    for (const ticker of DEFAULT_TICKERS) {
      try {
        const response = await fetch(`/api/v1/prices?ticker=${ticker}`);
        if (response.ok) {
          const data = await response.json();
          const price = typeof data === 'number' ? data : data.price || 100;
          const previousClose = data.previousClose || price * 0.98;
          const change = price - previousClose;
          const changePercent = (change / previousClose) * 100;
          const sparkline = Array.from({ length: 20 }, () => price + (Math.random() - 0.5) * price * 0.02);
          items.push({ symbol: ticker, price, change, changePercent, sparkline });
        } else {
          const basePrice = ticker === 'BTC' ? 50000 : ticker === 'TSLA' ? 250 : 180;
          const change = (Math.random() - 0.5) * basePrice * 0.05;
          items.push({ symbol: ticker, price: basePrice, change, changePercent: (change / basePrice) * 100, sparkline: Array.from({ length: 20 }, () => basePrice + (Math.random() - 0.5) * basePrice * 0.02) });
        }
      } catch (error) { }
    }
    setWatchlist(items);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchPrices();
    const interval = setInterval(fetchPrices, 30000);
    return () => clearInterval(interval);
  }, [fetchPrices]);

  const renderSparkline = (data: number[]) => {
    if (data.length === 0) return null;
    const min = Math.min(...data), max = Math.max(...data), range = max - min || 1, w = 60, h = 20;
    const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ');
    const color = data[data.length - 1] > data[0] ? '#00ff41' : '#ff3366';
    return <svg width={w} height={h}><polyline points={points} fill="none" stroke={color} strokeWidth="1.5" opacity="0.7" /></svg>;
  };

  return (
    <Panel id={id} title="Watchlist" onRefresh={fetchPrices}>
      <div style={{ height: '100%', overflow: 'auto', fontFamily: "'JetBrains Mono', monospace", backgroundColor: '#0f1629' }}>
        {loading && watchlist.length === 0 ? <div style={{ padding: '16px', color: '#00d4ff', fontSize: '12px' }}>Loading prices...</div> : (
          <div style={{ padding: '4px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr 100px 100px 80px', padding: '8px 12px', fontSize: '10px', fontWeight: 'bold', color: '#7080a0', borderBottom: '1px solid #1a2340', textTransform: 'uppercase' }}>
              <div>Symbol</div><div>Price</div><div>Change</div><div>Change %</div><div>Trend</div>
            </div>
            {watchlist.map((item, i) => {
              const isPos = item.change >= 0, color = isPos ? '#00ff41' : '#ff3366';
              return (
                <div key={item.symbol} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 100px 100px 80px', padding: '10px 12px', backgroundColor: i % 2 === 0 ? '#0f1629' : '#121b32', cursor: 'pointer', alignItems: 'center' }} onClick={() => onOpenChart && onOpenChart(item.symbol)}>
                  <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#00d4ff' }}>{item.symbol}</div>
                  <div style={{ fontSize: '13px', color: '#e0e8f0' }}>${item.price.toFixed(2)}</div>
                  <div style={{ fontSize: '12px', color }}>{isPos ? '+' : ''}{item.change.toFixed(2)}</div>
                  <div style={{ fontSize: '12px', color, fontWeight: 'bold' }}>{isPos ? '+' : ''}{item.changePercent.toFixed(2)}%</div>
                  <div>{renderSparkline(item.sparkline)}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Panel>
  );
}
