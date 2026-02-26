'use client';

import { useState, useEffect } from 'react';

const POPULAR_TICKERS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'BTC-USD', 'ETH-USD', 'GLD'];

interface TickerData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

export default function TickerPanel() {
  const [tickerData, setTickerData] = useState<TickerData[]>([]);

  useEffect(() => {
    const fetchTickerData = async () => {
      try {
        // Fetch data for popular tickers
        const promises = POPULAR_TICKERS.map(async (ticker) => {
          try {
            const response = await fetch(`/api/v1/prices?ticker=${ticker}`);
            if (!response.ok) throw new Error('Failed');
            const data = await response.json();
            
            // Extract price info from response
            if (data && typeof data === 'object') {
              const price = data.current_price || data.price || data.regularMarketPrice || 0;
              const change = data.change || data.regularMarketChange || 0;
              const changePercent = data.change_percent || data.regularMarketChangePercent || 0;
              
              return {
                symbol: ticker,
                price: Number(price),
                change: Number(change),
                changePercent: Number(changePercent),
              };
            }
            
            return null;
          } catch {
            return null;
          }
        });

        const results = await Promise.all(promises);
        const validResults = results.filter((r): r is TickerData => r !== null);
        setTickerData(validResults);
      } catch (err) {
        console.error('Failed to fetch ticker data:', err);
      }
    };

    fetchTickerData();
    const interval = setInterval(fetchTickerData, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  // Double the data for seamless loop
  const doubledData = [...tickerData, ...tickerData];

  return (
    <div
      className="terminal-ticker"
      style={{
        background: '#0f1629',
        borderBottom: '1px solid #1a2340',
        height: '40px',
        overflow: 'hidden',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div
        className="terminal-ticker-scroll"
        style={{
          display: 'flex',
          gap: '40px',
          animation: 'scroll 30s linear infinite',
          whiteSpace: 'nowrap',
        }}
      >
        {doubledData.map((item, index) => (
          <div
            key={`${item.symbol}-${index}`}
            className="terminal-ticker-item"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '11px',
              padding: '0 16px',
            }}
          >
            <span
              className="terminal-ticker-symbol"
              style={{
                fontWeight: 700,
                color: '#00d4ff',
              }}
            >
              {item.symbol}
            </span>
            <span
              className="terminal-ticker-price"
              style={{
                color: '#e0e8f0',
              }}
            >
              ${item.price.toFixed(2)}
            </span>
            <span
              className={`terminal-ticker-change ${item.change >= 0 ? 'positive' : 'negative'}`}
              style={{
                fontWeight: 600,
                color: item.change >= 0 ? '#00ff41' : '#ff3366',
              }}
            >
              {item.change >= 0 ? '+' : ''}
              {item.changePercent.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
