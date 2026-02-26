'use client';
import { useState, useEffect, useCallback } from 'react';
import Panel from '@/components/terminal/Panel';

interface NewsItem { headline: string; source: string; timestamp: string; sentiment: 'positive' | 'negative' | 'neutral'; url?: string; }
interface NewsPanelProps { id: string; ticker?: string; }

export default function NewsPanel({ id, ticker = 'AAPL' }: NewsPanelProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchNews = useCallback(async () => {
    setLoading(true);
    try {
      let response = await fetch(`/api/v1/news?ticker=${ticker}`);
      if (!response.ok) response = await fetch('/api/v1/breaking-news-classifier');
      
      if (response.ok) {
        const data = await response.json();
        let newsItems: NewsItem[] = [];
        if (Array.isArray(data)) {
          newsItems = data.map((item: any) => ({
            headline: item.headline || item.title || 'No headline',
            source: item.source || 'Unknown',
            timestamp: item.timestamp || new Date().toISOString(),
            sentiment: item.sentiment || 'neutral',
            url: item.url,
          }));
        }
        if (newsItems.length === 0) newsItems = generateSampleNews(ticker);
        setNews(newsItems.slice(0, 20));
      } else {
        setNews(generateSampleNews(ticker));
      }
    } catch (error) {
      setNews(generateSampleNews(ticker));
    }
    setLoading(false);
    setLastUpdate(new Date());
  }, [ticker]);

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 60000);
    return () => clearInterval(interval);
  }, [fetchNews]);

  const getSentimentColor = (s: string) => s === 'positive' ? '#00ff41' : s === 'negative' ? '#ff3366' : '#ffd700';
  const getSentimentBadge = (s: string) => s === 'positive' ? '▲' : s === 'negative' ? '▼' : '●';
  const formatTime = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return new Date(ts).toLocaleDateString();
  };

  return (
    <Panel id={id} title={`News Feed • ${ticker}`} onRefresh={fetchNews}>
      <div style={{ height: '100%', overflow: 'auto', fontFamily: "'JetBrains Mono', monospace", backgroundColor: '#0f1629' }}>
        {loading && news.length === 0 ? <div style={{ padding: '16px', color: '#00d4ff', fontSize: '12px' }}>Loading news...</div> : (
          <>
            <div style={{ padding: '8px 16px', fontSize: '10px', color: '#a0b0c0', borderBottom: '1px solid #1a2340' }}>Last update: {lastUpdate.toLocaleTimeString()}</div>
            <div style={{ padding: '4px' }}>
              {news.map((item, i) => (
                <div key={i} style={{ padding: '12px', marginBottom: '2px', backgroundColor: i % 2 === 0 ? '#0f1629' : '#121b32', borderLeft: `3px solid ${getSentimentColor(item.sentiment)}`, cursor: item.url ? 'pointer' : 'default' }} onClick={() => item.url && window.open(item.url, '_blank')}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <span style={{ color: getSentimentColor(item.sentiment), fontSize: '12px', fontWeight: 'bold', minWidth: '16px' }}>{getSentimentBadge(item.sentiment)}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', color: '#e0e8f0', marginBottom: '6px', lineHeight: '1.4' }}>{item.headline}</div>
                      <div style={{ fontSize: '10px', color: '#7080a0', display: 'flex', gap: '12px' }}><span>{item.source}</span><span>•</span><span>{formatTime(item.timestamp)}</span></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </Panel>
  );
}

function generateSampleNews(ticker: string): NewsItem[] {
  const sources = ['Bloomberg', 'Reuters', 'WSJ', 'CNBC', 'MarketWatch'];
  const sentiments: Array<'positive' | 'negative' | 'neutral'> = ['positive', 'negative', 'neutral'];
  return Array.from({ length: 15 }, (_, i) => ({
    headline: `${ticker} ${['announces', 'reports', 'sees', 'unveils', 'faces'][i % 5]} ${['strong earnings', 'new product', 'market challenges', 'innovation', 'growth'][i % 5]}`,
    source: sources[i % sources.length],
    timestamp: new Date(Date.now() - i * 1800000).toISOString(),
    sentiment: sentiments[i % sentiments.length],
  }));
}
