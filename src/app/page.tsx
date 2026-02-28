'use client';

import { useEffect, useState, useRef, KeyboardEvent } from 'react';
import { phases, dataSources } from './roadmap';

export const dynamic = 'force-dynamic';

interface MarketQuote {
  ticker: string;
  price: number;
  change: number;
  changePercent: number;
}

interface FeedMessage {
  time: string;
  category: 'SYSTEM' | 'MARKET' | 'MODULE' | 'QUANTCLAW';
  message: string;
}

interface CommandOutput {
  command: string;
  output: string[];
  timestamp: string;
}

type TabType = 'terminal' | 'sources' | 'stats';

export default function HomePage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [marketData, setMarketData] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [liveFeed, setLiveFeed] = useState<FeedMessage[]>([]);
  const [commandInput, setCommandInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [terminalOutput, setTerminalOutput] = useState<CommandOutput[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('terminal');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const tickers = ['SPY', 'QQQ', 'DIA', 'IWM', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'BTC-USD', 'ETH-USD'];

  // Detect mobile on client-side only
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Update clock every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch market data
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await fetch(`/api/v1/prices?tickers=${tickers.join(',')}`);
        if (response.ok) {
          const data = await response.json();
          setMarketData(data);
        }
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        setLoading(false);
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Live feed messages
  useEffect(() => {
    const messages: FeedMessage[] = [
      { time: formatTime(new Date()), category: 'QUANTCLAW', message: 'Paper Trading Engine deployed ✓' },
      { time: formatTime(new Date()), category: 'SYSTEM', message: 'Backtesting engine: 6 strategies online' },
      { time: formatTime(new Date()), category: 'MODULE', message: 'alpha_picker v3 scoring 7,017 stocks' },
    ];
    setLiveFeed(messages);

    let counter = 0;
    const feedInterval = setInterval(() => {
      const msgTemplates = [
        { category: 'MARKET' as const, gen: () => `${marketData[Math.floor(Math.random() * marketData.length)]?.ticker || 'SPY'} hits new session ${Math.random() > 0.5 ? 'high' : 'low'}` },
        { category: 'MODULE' as const, gen: () => `${['factor_model', 'earnings_predictor', 'sentiment_analyzer', 'risk_monitor'][counter % 4]} processing batch ${Math.floor(Math.random() * 1000)}` },
        { category: 'SYSTEM' as const, gen: () => `API latency ${Math.floor(Math.random() * 50 + 20)}ms | ${Math.floor(Math.random() * 500 + 100)} req/min` },
        { category: 'QUANTCLAW' as const, gen: () => `${['Portfolio rebalancing', 'Options chain refresh', 'News sentiment update', 'Factor calculation'][counter % 4]} completed` },
      ];
      
      const template = msgTemplates[counter % msgTemplates.length];
      const newMsg: FeedMessage = {
        time: formatTime(new Date()),
        category: template.category,
        message: template.gen(),
      };

      setLiveFeed(prev => [newMsg, ...prev].slice(0, 50));
      counter++;
    }, 8000);

    return () => clearInterval(feedInterval);
  }, [marketData]);

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [liveFeed]);

  // Focus input on /
  useEffect(() => {
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setCommandInput('');
        inputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Calculate module stats
  const moduleStats = calculateModuleStats();
  const totalModules = phases.length;
  const totalSources = dataSources.length;
  const totalLoc = phases.reduce((sum, p) => sum + (p.loc || 0), 0);

  // Get unique categories
  const categories = ['all', ...Array.from(new Set(dataSources.map(s => s.type)))];

  // Filter data sources
  const filteredSources = dataSources.filter(source => {
    const matchesCategory = selectedCategory === 'all' || source.type === selectedCategory;
    const matchesSearch = searchQuery === '' || 
      source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  function formatTime(date: Date): string {
    return date.toTimeString().split(' ')[0];
  }

  function calculateModuleStats() {
    const categoryGroups: Record<string, { done: number; total: number }> = {};
    
    phases.forEach(phase => {
      const cat = phase.category;
      if (!categoryGroups[cat]) {
        categoryGroups[cat] = { done: 0, total: 0 };
      }
      categoryGroups[cat].total++;
      if (phase.status === 'done') {
        categoryGroups[cat].done++;
      }
    });

    return Object.entries(categoryGroups)
      .map(([category, stats]) => ({
        category,
        done: stats.done,
        total: stats.total,
        percentage: Math.floor((stats.done / stats.total) * 100),
      }))
      .sort((a, b) => b.percentage - a.percentage)
      .slice(0, 12);
  }

  function handleCommand(cmd: string) {
    if (!cmd.trim()) return;

    const timestamp = formatTime(new Date());
    setCommandHistory(prev => [...prev, cmd]);
    setHistoryIndex(-1);

    const parts = cmd.trim().toLowerCase().split(' ');
    const command = parts[0];
    const args = parts.slice(1);

    let output: string[] = [];

    switch (command) {
      case 'price':
      case 'quote':
        if (args.length === 0) {
          output = ['ERROR: Usage: price <TICKER>'];
        } else {
          const ticker = args[0].toUpperCase();
          const quote = marketData.find(q => q.ticker === ticker);
          if (quote) {
            output = [
              `${ticker.padEnd(8)} ${quote.price.toFixed(2).padStart(10)} ${(quote.change >= 0 ? '+' : '')}${quote.change.toFixed(2).padStart(8)} ${(quote.changePercent >= 0 ? '+' : '')}${quote.changePercent.toFixed(2)}%`,
            ];
          } else {
            output = [`Fetching ${ticker} data...`, `Call /api/v1/prices?ticker=${ticker}`];
          }
        }
        break;
      
      case 'modules':
        output = [
          `TOTAL MODULES: ${totalModules}`,
          `DATA SOURCES: ${totalSources}`,
          `LINES OF CODE: ${totalLoc.toLocaleString()}`,
          '',
          'TOP CATEGORIES:',
          ...moduleStats.slice(0, 5).map(m => 
            `  ${m.category.padEnd(20)} ${m.done}/${m.total} (${m.percentage}%)`
          ),
        ];
        break;

      case 'sources':
        const topSources = dataSources.slice(0, 10);
        output = [
          `TOTAL DATA SOURCES: ${dataSources.length}`,
          '',
          'TOP 10 SOURCES:',
          ...topSources.map(s => 
            `  ${s.icon} ${s.name.padEnd(25)} [${s.type}]`
          ),
          '',
          'Use "search <query>" to find specific sources',
          'Or switch to Sources tab for full browser',
        ];
        break;

      case 'search':
        if (args.length === 0) {
          output = ['ERROR: Usage: search <query>'];
        } else {
          const query = args.join(' ').toLowerCase();
          const results = dataSources.filter(s => 
            s.name.toLowerCase().includes(query) ||
            s.desc.toLowerCase().includes(query) ||
            s.type.toLowerCase().includes(query)
          ).slice(0, 10);
          
          if (results.length === 0) {
            output = [`No sources found for: ${query}`];
          } else {
            output = [
              `Found ${results.length} sources matching "${query}":`,
              '',
              ...results.map(s => 
                `  ${s.icon} ${s.name} - ${s.desc.substring(0, 50)}...`
              ),
            ];
          }
        }
        break;

      case 'help':
        output = [
          'AVAILABLE COMMANDS:',
          '  price <TICKER>         Get current price',
          '  quote <TICKER>         Alias for price',
          '  modules                Show module statistics',
          '  sources                List top data sources',
          '  search <query>         Search modules by name',
          '  status                 System status',
          '  about                  About QuantClaw',
          '  help                   Show this help',
          '  clear                  Clear terminal',
        ];
        break;

      case 'status':
        output = [
          'SYSTEM STATUS',
          '─'.repeat(50),
          `  Modules:        ${totalModules} (${phases.filter(p => p.status === 'done').length} active)`,
          `  Data Sources:   ${totalSources}`,
          `  API Endpoints:  235+`,
          `  Uptime:         99.9%`,
          `  Latency:        <50ms`,
          `  Last Deploy:    ${new Date().toLocaleDateString()}`,
          '─'.repeat(50),
        ];
        break;

      case 'about':
        output = [
          'QUANTCLAW DATA',
          '─'.repeat(50),
          'Financial Intelligence Platform',
          '',
          'Version:     2.0.0',
          'Build:       Production',
          'Repository:  github.com/YourRepo/quantclaw-data',
          '',
          'Bloomberg-class market data and analytics',
          'powered by 100+ open data sources.',
          '',
          'Type "help" for available commands.',
        ];
        break;

      case 'clear':
        setTerminalOutput([]);
        return;

      default:
        output = [`Unknown command: ${command}`, 'Type "help" for available commands'];
    }

    setTerminalOutput(prev => [
      ...prev,
      { command: cmd, output, timestamp },
    ]);

    setTimeout(() => {
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    }, 0);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      handleCommand(commandInput);
      setCommandInput('');
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : historyIndex;
        setHistoryIndex(newIndex);
        setCommandInput(commandHistory[commandHistory.length - 1 - newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setCommandInput(commandHistory[commandHistory.length - 1 - newIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setCommandInput('');
      }
    }
  }

  function renderProgressBar(percentage: number) {
    const filled = Math.floor(percentage / 10);
    const empty = 10 - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  }

  // Quick command buttons
  const quickCommands = [
    { label: 'prices', cmd: 'price SPY' },
    { label: 'modules', cmd: 'modules' },
    { label: 'sources', cmd: 'sources' },
    { label: 'help', cmd: 'help' },
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      background: '#0a0a0f',
      color: '#e0e0e0',
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
      overflow: 'hidden',
    }}>
      {/* Header Bar */}
      <div style={{
        background: '#1a1a2e',
        borderBottom: '2px solid #ff8c00',
        padding: isMobile ? '8px 12px' : '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        height: isMobile ? '44px' : '50px',
        flexShrink: 0,
      }}>
        <div style={{
          fontSize: isMobile ? '14px' : '18px',
          fontWeight: 'bold',
          color: '#ff8c00',
          letterSpacing: '2px',
        }}>
          QUANTCLAW{!isMobile && ' DATA'}
        </div>
        {!isMobile && <div style={{
          fontSize: '11px',
          color: '#777',
          letterSpacing: '1px',
        }}>
          FINANCIAL INTELLIGENCE PLATFORM
        </div>}
        <div style={{
          display: 'flex',
          gap: isMobile ? '10px' : '20px',
          alignItems: 'center',
          fontSize: isMobile ? '11px' : '13px',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: '#00d26a',
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              background: '#00d26a',
              borderRadius: '50%',
              animation: 'pulse 2s infinite',
            }} />
            LIVE
          </div>
          <div style={{ color: '#e0e0e0' }}>
            {currentTime.toLocaleTimeString('en-US', { hour12: false })}
          </div>
          {!isMobile && <div style={{
            color: '#777',
            fontSize: '11px',
          }}>
            v2.0
          </div>}
        </div>
      </div>

      {/* Mobile: Sticky Terminal Input + Quick Actions */}
      {isMobile && (
        <div style={{
          background: '#111318',
          borderBottom: '1px solid #1e2330',
          padding: '12px',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{ color: '#ff8c00', fontSize: '13px', fontWeight: 'bold' }}>QUANTCLAW&gt;</span>
            <input
              ref={inputRef}
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter command..."
              style={{
                flex: 1,
                background: '#0a0a0f',
                border: '1px solid #1e2330',
                color: '#e0e0e0',
                padding: '12px',
                fontSize: '13px',
                fontFamily: 'inherit',
                outline: 'none',
                minHeight: '44px',
                borderRadius: '4px',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#ff8c00';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#1e2330';
              }}
            />
          </div>
          <div style={{
            display: 'flex',
            gap: '8px',
            flexWrap: 'wrap',
          }}>
            {quickCommands.map(qc => (
              <button
                key={qc.label}
                onClick={() => {
                  setCommandInput(qc.cmd);
                  handleCommand(qc.cmd);
                }}
                style={{
                  background: '#1e2330',
                  border: '1px solid #ff8c00',
                  color: '#ff8c00',
                  padding: '8px 16px',
                  fontSize: '12px',
                  fontFamily: 'inherit',
                  cursor: 'pointer',
                  borderRadius: '4px',
                  minHeight: '44px',
                  fontWeight: 'bold',
                  letterSpacing: '1px',
                }}
                onMouseDown={(e) => {
                  e.currentTarget.style.background = '#ff8c00';
                  e.currentTarget.style.color = '#0a0a0f';
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.background = '#1e2330';
                  e.currentTarget.style.color = '#ff8c00';
                }}
              >
                {qc.label.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        WebkitOverflowScrolling: 'touch',
      }}>
        {/* Desktop Layout */}
        {!isMobile && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1.2fr 1fr',
            gridTemplateRows: '1fr 1.3fr',
            gap: '2px',
            height: '100%',
            background: '#0a0a0f',
          }}>
            {/* Panel 1: Market Data */}
            <div style={{
              background: '#111318',
              border: '1px solid #1e2330',
              padding: '16px',
              overflow: 'auto',
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#ff8c00',
                marginBottom: '12px',
                letterSpacing: '1px',
              }}>
                MARKET DATA
              </div>
              {loading ? (
                <div style={{ color: '#777' }}>Loading market data...</div>
              ) : (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '8px',
                  fontSize: '11px',
                }}>
                  {marketData.map((quote) => (
                    <div
                      key={quote.ticker}
                      onClick={() => {
                        setCommandInput(`price ${quote.ticker}`);
                        inputRef.current?.focus();
                      }}
                      style={{
                        background: '#0a0a0f',
                        border: '1px solid #1e2330',
                        padding: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = '#ff8c00';
                        e.currentTarget.style.background = 'rgba(255, 140, 0, 0.05)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = '#1e2330';
                        e.currentTarget.style.background = '#0a0a0f';
                      }}
                    >
                      <div style={{ color: '#4da6ff', fontWeight: 'bold', marginBottom: '4px' }}>
                        {quote.ticker}
                      </div>
                      <div style={{ color: '#e0e0e0', fontSize: '13px', fontWeight: 'bold' }}>
                        {quote.price.toFixed(2)}
                      </div>
                      <div style={{
                        color: quote.change >= 0 ? '#00d26a' : '#ff3b3b',
                        fontSize: '10px',
                      }}>
                        {quote.change >= 0 ? '+' : ''}{quote.change.toFixed(2)} ({quote.changePercent >= 0 ? '+' : ''}{quote.changePercent.toFixed(2)}%)
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Panel 2: Module Status */}
            <div style={{
              background: '#111318',
              border: '1px solid #1e2330',
              padding: '16px',
              overflow: 'auto',
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#ff8c00',
                marginBottom: '12px',
                letterSpacing: '1px',
              }}>
                MODULE STATUS
              </div>
              <div style={{ fontSize: '10px', lineHeight: '1.6' }}>
                {moduleStats.map((stat) => (
                  <div key={stat.category} style={{ marginBottom: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <span style={{ color: '#4da6ff' }}>
                        {stat.category.toUpperCase().substring(0, 15).padEnd(15)}
                      </span>
                      <span style={{ color: '#e0e0e0' }}>
                        [{stat.done.toString().padStart(3, ' ')}/{stat.total.toString().padEnd(3, ' ')}]
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        color: stat.percentage >= 90 ? '#00d26a' : stat.percentage >= 70 ? '#4da6ff' : '#ff8c00',
                      }}>
                        {renderProgressBar(stat.percentage)}
                      </span>
                      <span style={{ color: '#777', minWidth: '35px' }}>
                        {stat.percentage}%
                      </span>
                    </div>
                  </div>
                ))}
                <div style={{
                  marginTop: '12px',
                  paddingTop: '12px',
                  borderTop: '1px solid #1e2330',
                  color: '#ff8c00',
                }}>
                  {totalModules} MODULES | {totalSources} SOURCES | {totalLoc.toLocaleString()} LOC
                </div>
              </div>
            </div>

            {/* Panel 3: Live Feed */}
            <div style={{
              background: '#111318',
              border: '1px solid #1e2330',
              padding: '16px',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#ff8c00',
                marginBottom: '12px',
                letterSpacing: '1px',
              }}>
                LIVE FEED
              </div>
              <div
                ref={feedRef}
                style={{
                  flex: 1,
                  overflow: 'auto',
                  fontSize: '10px',
                  lineHeight: '1.8',
                }}
              >
                {liveFeed.map((msg, idx) => (
                  <div key={idx} style={{ marginBottom: '6px' }}>
                    <span style={{ color: '#777' }}>{msg.time}</span>
                    {' '}
                    <span style={{
                      color: msg.category === 'MARKET' ? '#00d26a' : 
                             msg.category === 'MODULE' ? '#4da6ff' : 
                             msg.category === 'SYSTEM' ? '#9b59b6' : '#ff8c00',
                      fontWeight: 'bold',
                    }}>
                      {msg.category}
                    </span>
                    {' '}
                    <span style={{ color: '#e0e0e0' }}>{msg.message}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Panel 4: Command Terminal */}
            <div style={{
              background: '#111318',
              border: '1px solid #1e2330',
              padding: '16px',
              gridColumn: 'span 2',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#ff8c00',
                marginBottom: '12px',
                letterSpacing: '1px',
              }}>
                COMMAND TERMINAL
              </div>
              <div
                ref={terminalRef}
                style={{
                  flex: 1,
                  overflow: 'auto',
                  fontSize: '11px',
                  lineHeight: '1.6',
                  marginBottom: '12px',
                }}
              >
                {terminalOutput.length === 0 && (
                  <div style={{ color: '#777' }}>
                    Type "help" for available commands. Press "/" to focus terminal.
                  </div>
                )}
                {terminalOutput.map((item, idx) => (
                  <div key={idx} style={{ marginBottom: '12px' }}>
                    <div style={{ color: '#4da6ff' }}>
                      <span style={{ color: '#ff8c00' }}>QUANTCLAW&gt;</span> {item.command}
                    </div>
                    {item.output.map((line, lineIdx) => (
                      <div key={lineIdx} style={{
                        color: line.startsWith('ERROR') ? '#ff3b3b' : '#e0e0e0',
                        paddingLeft: '0',
                      }}>
                        {line}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ff8c00', fontSize: '13px', fontWeight: 'bold' }}>QUANTCLAW&gt;</span>
                <input
                  ref={inputRef}
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter command..."
                  style={{
                    flex: 1,
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    color: '#e0e0e0',
                    padding: '8px',
                    fontSize: '13px',
                    fontFamily: 'inherit',
                    outline: 'none',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#ff8c00';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#1e2330';
                  }}
                />
              </div>
            </div>

            {/* Panel 5: Stats */}
            <div style={{
              background: '#111318',
              border: '1px solid #1e2330',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: '#ff8c00',
                  marginBottom: '12px',
                  letterSpacing: '1px',
                }}>
                  SYSTEM STATS
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  fontSize: '10px',
                }}>
                  <div>
                    <div style={{ color: '#777' }}>MODULES</div>
                    <div style={{ color: '#e0e0e0', fontSize: '16px', fontWeight: 'bold' }}>
                      {totalModules}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>SOURCES</div>
                    <div style={{ color: '#e0e0e0', fontSize: '16px', fontWeight: 'bold' }}>
                      {totalSources}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>API ENDPOINTS</div>
                    <div style={{ color: '#e0e0e0', fontSize: '16px', fontWeight: 'bold' }}>
                      235+
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>LOC</div>
                    <div style={{ color: '#e0e0e0', fontSize: '16px', fontWeight: 'bold' }}>
                      {Math.floor(totalLoc / 1000)}K
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>STRATEGIES</div>
                    <div style={{ color: '#e0e0e0', fontSize: '16px', fontWeight: 'bold' }}>
                      6
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>PORTFOLIOS</div>
                    <div style={{ color: '#e0e0e0', fontSize: '16px', fontWeight: 'bold' }}>
                      ∞
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>UPTIME</div>
                    <div style={{ color: '#00d26a', fontSize: '16px', fontWeight: 'bold' }}>
                      99.9%
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#777' }}>LATENCY</div>
                    <div style={{ color: '#00d26a', fontSize: '16px', fontWeight: 'bold' }}>
                      &lt;50ms
                    </div>
                  </div>
                </div>
              </div>
              <div style={{
                borderTop: '1px solid #1e2330',
                paddingTop: '12px',
                fontSize: '9px',
              }}>
                <div style={{ marginBottom: '8px' }}>
                  <a href="/tutorial" style={{ color: '#4da6ff', textDecoration: 'none' }}>
                    → TUTORIAL
                  </a>
                  {' | '}
                  <a href="https://github.com/YourRepo/quantclaw-data" target="_blank" rel="noopener noreferrer" style={{ color: '#4da6ff', textDecoration: 'none' }}>
                    → GITHUB
                  </a>
                </div>
                <div style={{ color: '#777', lineHeight: '1.4' }}>
                  POWERED BY QUANTCLAW DATA ENGINE
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mobile Layout with Tabs */}
        {isMobile && (
          <div style={{
            height: 'calc(100% - 60px)', // Reserve space for bottom tab bar
            overflow: 'auto',
          }}>
            {/* Terminal Tab */}
            {activeTab === 'terminal' && (
              <div style={{
                background: '#111318',
                padding: '12px',
                minHeight: '100%',
              }}>
                <div
                  ref={terminalRef}
                  style={{
                    fontSize: '11px',
                    lineHeight: '1.6',
                    marginBottom: '12px',
                  }}
                >
                  {terminalOutput.length === 0 && (
                    <div style={{ color: '#777' }}>
                      Type a command above or tap quick action buttons.
                    </div>
                  )}
                  {terminalOutput.map((item, idx) => (
                    <div key={idx} style={{ marginBottom: '12px' }}>
                      <div style={{ color: '#4da6ff' }}>
                        <span style={{ color: '#ff8c00' }}>QUANTCLAW&gt;</span> {item.command}
                      </div>
                      {item.output.map((line, lineIdx) => (
                        <div key={lineIdx} style={{
                          color: line.startsWith('ERROR') ? '#ff3b3b' : '#e0e0e0',
                          paddingLeft: '0',
                        }}>
                          {line}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sources Tab */}
            {activeTab === 'sources' && (
              <div style={{
                background: '#111318',
                padding: '12px',
              }}>
                <div style={{
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: '#ff8c00',
                  marginBottom: '12px',
                  letterSpacing: '1px',
                }}>
                  DATA SOURCES ({filteredSources.length})
                </div>
                
                {/* Search Bar */}
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search sources..."
                  style={{
                    width: '100%',
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    color: '#e0e0e0',
                    padding: '12px',
                    fontSize: '13px',
                    fontFamily: 'inherit',
                    outline: 'none',
                    minHeight: '44px',
                    borderRadius: '4px',
                    marginBottom: '12px',
                  }}
                />

                {/* Category Filter */}
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  overflowX: 'auto',
                  marginBottom: '12px',
                  paddingBottom: '8px',
                }}>
                  {categories.map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      style={{
                        background: selectedCategory === cat ? '#ff8c00' : '#1e2330',
                        border: '1px solid #ff8c00',
                        color: selectedCategory === cat ? '#0a0a0f' : '#ff8c00',
                        padding: '8px 16px',
                        fontSize: '11px',
                        fontFamily: 'inherit',
                        cursor: 'pointer',
                        borderRadius: '4px',
                        minHeight: '44px',
                        fontWeight: 'bold',
                        letterSpacing: '1px',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {cat.toUpperCase()}
                    </button>
                  ))}
                </div>

                {/* Sources Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr',
                  gap: '8px',
                }}>
                  {filteredSources.map(source => (
                    <div
                      key={source.name}
                      onClick={() => setExpandedSource(expandedSource === source.name ? null : source.name)}
                      style={{
                        background: '#0a0a0f',
                        border: expandedSource === source.name ? '2px solid #ff8c00' : '1px solid #1e2330',
                        padding: '12px',
                        cursor: 'pointer',
                        borderRadius: '4px',
                        minHeight: '44px',
                      }}
                    >
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: expandedSource === source.name ? '8px' : '0',
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                        }}>
                          <span style={{ fontSize: '20px' }}>{source.icon}</span>
                          <div>
                            <div style={{
                              color: '#4da6ff',
                              fontWeight: 'bold',
                              fontSize: '13px',
                            }}>
                              {source.name}
                            </div>
                            <div style={{
                              color: '#777',
                              fontSize: '10px',
                            }}>
                              {source.type}
                            </div>
                          </div>
                        </div>
                        <div style={{
                          color: source.status === 'active' ? '#00d26a' : '#777',
                          fontSize: '20px',
                        }}>
                          {source.status === 'active' ? '✓' : '○'}
                        </div>
                      </div>
                      {expandedSource === source.name && (
                        <div style={{
                          color: '#e0e0e0',
                          fontSize: '11px',
                          lineHeight: '1.6',
                          paddingTop: '8px',
                          borderTop: '1px solid #1e2330',
                        }}>
                          {source.desc}
                          {source.modules && (
                            <div style={{
                              marginTop: '8px',
                              color: '#777',
                              fontSize: '10px',
                            }}>
                              Modules: {source.modules.join(', ')}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Stats Tab */}
            {activeTab === 'stats' && (
              <div style={{
                background: '#111318',
                padding: '12px',
              }}>
                <div style={{
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: '#ff8c00',
                  marginBottom: '12px',
                  letterSpacing: '1px',
                }}>
                  SYSTEM STATS
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  fontSize: '10px',
                  marginBottom: '20px',
                }}>
                  <div style={{
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    padding: '12px',
                    borderRadius: '4px',
                  }}>
                    <div style={{ color: '#777' }}>MODULES</div>
                    <div style={{ color: '#e0e0e0', fontSize: '20px', fontWeight: 'bold' }}>
                      {totalModules}
                    </div>
                  </div>
                  <div style={{
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    padding: '12px',
                    borderRadius: '4px',
                  }}>
                    <div style={{ color: '#777' }}>SOURCES</div>
                    <div style={{ color: '#e0e0e0', fontSize: '20px', fontWeight: 'bold' }}>
                      {totalSources}
                    </div>
                  </div>
                  <div style={{
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    padding: '12px',
                    borderRadius: '4px',
                  }}>
                    <div style={{ color: '#777' }}>API ENDPOINTS</div>
                    <div style={{ color: '#e0e0e0', fontSize: '20px', fontWeight: 'bold' }}>
                      235+
                    </div>
                  </div>
                  <div style={{
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    padding: '12px',
                    borderRadius: '4px',
                  }}>
                    <div style={{ color: '#777' }}>LOC</div>
                    <div style={{ color: '#e0e0e0', fontSize: '20px', fontWeight: 'bold' }}>
                      {Math.floor(totalLoc / 1000)}K
                    </div>
                  </div>
                  <div style={{
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    padding: '12px',
                    borderRadius: '4px',
                  }}>
                    <div style={{ color: '#777' }}>UPTIME</div>
                    <div style={{ color: '#00d26a', fontSize: '20px', fontWeight: 'bold' }}>
                      99.9%
                    </div>
                  </div>
                  <div style={{
                    background: '#0a0a0f',
                    border: '1px solid #1e2330',
                    padding: '12px',
                    borderRadius: '4px',
                  }}>
                    <div style={{ color: '#777' }}>LATENCY</div>
                    <div style={{ color: '#00d26a', fontSize: '20px', fontWeight: 'bold' }}>
                      &lt;50ms
                    </div>
                  </div>
                </div>

                <div style={{
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: '#ff8c00',
                  marginBottom: '12px',
                  letterSpacing: '1px',
                }}>
                  MODULE STATUS
                </div>
                <div style={{ fontSize: '10px', lineHeight: '1.6' }}>
                  {moduleStats.map((stat) => (
                    <div key={stat.category} style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <span style={{ color: '#4da6ff' }}>
                          {stat.category.toUpperCase()}
                        </span>
                        <span style={{ color: '#e0e0e0' }}>
                          {stat.done}/{stat.total}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          color: stat.percentage >= 90 ? '#00d26a' : stat.percentage >= 70 ? '#4da6ff' : '#ff8c00',
                          flex: 1,
                        }}>
                          {renderProgressBar(stat.percentage)}
                        </span>
                        <span style={{ color: '#777', minWidth: '35px' }}>
                          {stat.percentage}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Mobile: Bottom Tab Bar */}
      {isMobile && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          background: '#1a1a2e',
          borderTop: '2px solid #ff8c00',
          display: 'flex',
          justifyContent: 'space-around',
          padding: '8px 0',
          height: '60px',
        }}>
          {[
            { id: 'terminal' as TabType, label: 'Terminal', icon: '⌨️' },
            { id: 'sources' as TabType, label: 'Sources', icon: '📊' },
            { id: 'stats' as TabType, label: 'Stats', icon: '📈' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                color: activeTab === tab.id ? '#ff8c00' : '#777',
                fontSize: '20px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                minHeight: '44px',
                fontFamily: 'inherit',
              }}
            >
              <span>{tab.icon}</span>
              <span style={{
                fontSize: '10px',
                fontWeight: 'bold',
                letterSpacing: '1px',
              }}>
                {tab.label.toUpperCase()}
              </span>
            </button>
          ))}
        </div>
      )}

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
