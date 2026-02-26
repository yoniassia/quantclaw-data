"use client";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface Step {
  id: number;
  title: string;
  command: string;
  response: string;
}

const tutorialSteps: Step[] = [
  {
    id: 1,
    title: "Getting Started",
    command: "help",
    response: `Available Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Built-in:
  help              - Show this help message
  sources           - List all data sources
  modules           - List module categories
  clear             - Clear terminal output

Data Commands:
  prices TICKER     - Real-time stock price
  options TICKER    - Options chain with Greeks
  congress-trades   - Congressional trading disclosures
  crypto SYMBOL     - Cryptocurrency data
  monte-carlo TICKER - Monte Carlo simulations
  technicals TICKER - Technical indicators
  news TICKER       - News sentiment analysis
  insider-trades TICKER - Insider trading activity

Total: 200+ data modules available`
  },
  {
    id: 2,
    title: "Check Stock Prices",
    command: "prices AAPL",
    response: `{
  "ticker": "AAPL",
  "price": 187.42,
  "change": "+1.23%",
  "changeAmount": 2.28,
  "volume": "52.3M",
  "dayHigh": 188.95,
  "dayLow": 185.10,
  "marketCap": "2.89T",
  "pe": 29.8,
  "timestamp": "2026-02-26T08:45:00Z",
  "source": "eToro API"
}`
  },
  {
    id: 3,
    title: "Options Chain",
    command: "options TSLA",
    response: `{
  "ticker": "TSLA",
  "underlyingPrice": 245.67,
  "expiration": "2026-03-21",
  "calls": [
    {
      "strike": 240,
      "bid": 12.50,
      "ask": 12.80,
      "volume": 8234,
      "openInterest": 12450,
      "delta": 0.68,
      "gamma": 0.025,
      "vega": 0.42,
      "theta": -0.18,
      "iv": 0.52
    },
    {
      "strike": 250,
      "bid": 8.20,
      "ask": 8.45,
      "volume": 15678,
      "openInterest": 24567,
      "delta": 0.45,
      "gamma": 0.032,
      "vega": 0.48,
      "theta": -0.22,
      "iv": 0.48
    }
  ],
  "puts": [
    {
      "strike": 240,
      "bid": 8.90,
      "ask": 9.15,
      "volume": 6543,
      "openInterest": 18900,
      "delta": -0.32,
      "gamma": 0.025,
      "vega": 0.42,
      "theta": -0.16,
      "iv": 0.51
    }
  ]
}`
  },
  {
    id: 4,
    title: "Congressional Trades",
    command: "congress-trades",
    response: `{
  "trades": [
    {
      "politician": "Nancy Pelosi",
      "ticker": "NVDA",
      "transactionType": "Purchase",
      "amount": "$1M - $5M",
      "date": "2026-02-20",
      "filingDate": "2026-02-24",
      "price": 850.00,
      "shares": "2,353 - 11,765"
    },
    {
      "politician": "Kevin McCarthy",
      "ticker": "TSLA",
      "transactionType": "Sale",
      "amount": "$500K - $1M",
      "date": "2026-02-18",
      "filingDate": "2026-02-22",
      "price": 248.50
    },
    {
      "politician": "Chuck Schumer",
      "ticker": "AAPL",
      "transactionType": "Purchase",
      "amount": "$100K - $250K",
      "date": "2026-02-15",
      "filingDate": "2026-02-21",
      "price": 185.20
    }
  ],
  "source": "House Stock Watcher + Senate Disclosures",
  "updated": "2026-02-26T08:00:00Z"
}`
  },
  {
    id: 5,
    title: "Monte Carlo Simulation",
    command: "monte-carlo SPY",
    response: `{
  "ticker": "SPY",
  "currentPrice": 512.34,
  "simulations": 10000,
  "timeHorizon": "30 days",
  "results": {
    "mean": 515.67,
    "median": 514.89,
    "stdDev": 18.42,
    "percentiles": {
      "p5": 478.23,
      "p10": 487.56,
      "p25": 502.18,
      "p50": 514.89,
      "p75": 527.45,
      "p90": 543.21,
      "p95": 551.78
    },
    "probability": {
      "upside": 0.58,
      "downside": 0.42,
      "breakeven": 0.51
    },
    "sharpeRatio": 1.24,
    "maxDrawdown": -12.3
  },
  "model": "Geometric Brownian Motion",
  "historicalVolatility": 0.16
}`
  },
  {
    id: 6,
    title: "Crypto Data",
    command: "crypto BTC",
    response: `{
  "symbol": "BTC",
  "name": "Bitcoin",
  "price": 94567.82,
  "change24h": "+2.45%",
  "changeAmount": 2256.34,
  "volume24h": "$42.8B",
  "marketCap": "$1.87T",
  "dominance": 57.2,
  "high24h": 95123.45,
  "low24h": 91890.12,
  "ath": 108135.00,
  "athDate": "2024-12-17",
  "athChangePercent": -12.5,
  "circulatingSupply": "19.8M",
  "maxSupply": "21M",
  "fearGreedIndex": 72,
  "sentiment": "Greedy",
  "timestamp": "2026-02-26T08:45:00Z"
}`
  },
  {
    id: 7,
    title: "MCP Integration",
    command: "mcp-config",
    response: `{
  "mcpServers": {
    "quantclaw-data": {
      "command": "node",
      "args": [
        "/path/to/quantclaw-data/dist/mcp-server.js"
      ],
      "description": "200+ financial data modules",
      "capabilities": {
        "tools": 200,
        "dataSources": 43,
        "categories": [
          "equities",
          "options",
          "crypto",
          "macro",
          "fixed-income",
          "commodities",
          "alternative-data"
        ]
      },
      "documentation": "https://quantclaw.org/llms.txt"
    }
  }
}

Add this to your Claude Desktop config at:
  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
  Windows: %APPDATA%\\Claude\\claude_desktop_config.json`
  },
  {
    id: 8,
    title: "REST API",
    command: "curl https://data.quantclaw.org/api/v1/prices?ticker=AAPL",
    response: `HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999

{
  "ticker": "AAPL",
  "price": 187.42,
  "change": "+1.23%",
  "changeAmount": 2.28,
  "volume": "52.3M",
  "dayHigh": 188.95,
  "dayLow": 185.10,
  "marketCap": "2.89T",
  "pe": 29.8,
  "timestamp": "2026-02-26T08:45:00Z",
  "source": "eToro API"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All endpoints available at: https://data.quantclaw.org/api/v1/
Full documentation: https://quantclaw.org/llms.txt`
  }
];

export default function TutorialPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [displayedCommand, setDisplayedCommand] = useState("");
  const [displayedResponse, setDisplayedResponse] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isComplete, setIsComplete] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll terminal to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [displayedCommand, displayedResponse]);

  // Type text with random delay for realism
  const typeText = (
    text: string,
    setter: (text: string) => void,
    baseDelay: number = 50
  ): Promise<void> => {
    return new Promise((resolve) => {
      let index = 0;
      const type = () => {
        if (index < text.length) {
          setter(text.substring(0, index + 1));
          index++;
          const delay = (baseDelay + Math.random() * 30) / playbackSpeed;
          animationRef.current = setTimeout(type, delay);
        } else {
          resolve();
        }
      };
      type();
    });
  };

  // Play single step
  const playStep = async (stepIndex: number) => {
    if (stepIndex >= tutorialSteps.length) {
      setIsComplete(true);
      setIsPlaying(false);
      return;
    }

    setIsTyping(true);
    const step = tutorialSteps[stepIndex];
    
    // Type command
    await typeText(step.command, setDisplayedCommand, 60);
    
    // Pause after command
    await new Promise((resolve) => {
      animationRef.current = setTimeout(resolve, 500 / playbackSpeed);
    });
    
    // Show response
    await typeText(step.response, setDisplayedResponse, 20);
    
    // Pause between steps
    await new Promise((resolve) => {
      animationRef.current = setTimeout(resolve, 2000 / playbackSpeed);
    });
    
    setIsTyping(false);
    
    // Move to next step
    if (isPlaying && stepIndex < tutorialSteps.length - 1) {
      setCurrentStep(stepIndex + 1);
      setDisplayedCommand("");
      setDisplayedResponse("");
    } else if (stepIndex === tutorialSteps.length - 1) {
      setIsComplete(true);
      setIsPlaying(false);
    }
  };

  // Handle play/pause
  useEffect(() => {
    if (isPlaying && !isTyping) {
      playStep(currentStep);
    }
  }, [isPlaying, currentStep, playbackSpeed]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
    };
  }, []);

  const handlePlayPause = () => {
    if (isComplete) {
      // Restart from beginning
      setCurrentStep(0);
      setDisplayedCommand("");
      setDisplayedResponse("");
      setIsComplete(false);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  };

  const skipToStep = (stepIndex: number) => {
    if (animationRef.current) {
      clearTimeout(animationRef.current);
    }
    setCurrentStep(stepIndex);
    setDisplayedCommand("");
    setDisplayedResponse("");
    setIsTyping(false);
    setIsComplete(false);
    if (isPlaying) {
      playStep(stepIndex);
    }
  };

  const progress = ((currentStep + 1) / tutorialSteps.length) * 100;

  return (
    <div className="min-h-screen bg-[#0a0a1a] text-white font-mono">
      {/* CRT Scanline effect */}
      <div className="fixed inset-0 pointer-events-none opacity-5">
        <div
          className="h-full w-full"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, rgba(0,255,65,0.03) 0px, transparent 1px, transparent 2px, rgba(0,255,65,0.03) 3px)",
          }}
        />
      </div>

      {/* Header */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link
            href="/"
            className="text-sm text-[#C0E8FD] hover:text-[#13C636] transition-colors mb-4 inline-block"
          >
            ← Back to Terminal
          </Link>
          <h1 className="text-4xl sm:text-5xl font-bold mb-3">
            <span className="text-white">📺 QuantClaw Tutorial</span>
          </h1>
          <p className="text-lg text-white/60">
            Learn in 3 Minutes — Watch the terminal in action. No video player needed.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2 text-sm">
            <span className="text-[#13C636]">
              Step {currentStep + 1} of {tutorialSteps.length} — {tutorialSteps[currentStep]?.title}
            </span>
            <span className="text-white/40">{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-black/60 rounded-full overflow-hidden border border-white/10">
            <div
              className="h-full transition-all duration-300 ease-out"
              style={{
                width: `${progress}%`,
                background: "linear-gradient(90deg, #13C636 0%, #C0E8FD 100%)",
              }}
            />
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-3 mb-6">
          <button
            onClick={handlePlayPause}
            className="px-6 py-2 bg-[#13C636] text-black font-bold rounded hover:bg-[#13C636]/80 transition-all"
          >
            {isComplete ? "↻ Restart" : isPlaying ? "⏸ Pause" : "▶ Play"}
          </button>
          
          <div className="flex items-center gap-2 px-4 py-2 bg-black/60 border border-white/20 rounded">
            <span className="text-xs text-white/60">Speed:</span>
            {[1, 2, 3].map((speed) => (
              <button
                key={speed}
                onClick={() => setPlaybackSpeed(speed)}
                className={`px-3 py-1 text-xs rounded transition-all ${
                  playbackSpeed === speed
                    ? "bg-[#13C636] text-black"
                    : "bg-white/10 text-white/60 hover:bg-white/20"
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>

        {/* Step Skip Buttons */}
        <div className="flex flex-wrap gap-2 mb-6">
          <span className="text-xs text-white/60 self-center mr-2">Jump to:</span>
          {tutorialSteps.map((step, index) => (
            <button
              key={step.id}
              onClick={() => skipToStep(index)}
              className={`px-3 py-1 text-xs rounded transition-all ${
                currentStep === index
                  ? "bg-[#13C636] text-black"
                  : "bg-black/60 border border-white/20 text-white/60 hover:border-[#13C636]/50"
              }`}
            >
              {step.id}
            </button>
          ))}
        </div>

        {/* Terminal */}
        <div className="bg-black border border-[#13C636]/50 rounded-lg overflow-hidden shadow-lg shadow-[#13C636]/20 mb-8">
          {/* Terminal Header */}
          <div className="bg-[#13C636]/10 border-b border-[#13C636]/30 px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-[#FF6B6B]" />
                <div className="w-3 h-3 rounded-full bg-[#FFD700]" />
                <div className="w-3 h-3 rounded-full bg-[#13C636]" />
              </div>
              <span className="text-xs text-white/60 ml-2">quantclaw@tutorial</span>
            </div>
            <div className="text-xs text-white/40">
              {new Date().toLocaleTimeString()}
            </div>
          </div>

          {/* Terminal Output */}
          <div
            ref={terminalRef}
            className="h-[500px] overflow-y-auto p-4 text-sm"
          >
            {/* Welcome Message */}
            <div className="text-[#C0E8FD] mb-4 whitespace-pre-wrap">
{`QuantClaw Data Terminal v1.0
Tutorial Mode — Step-by-step walkthrough

Demo data shown. Try real queries at quantclaw.org
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`}
            </div>

            {/* Current Command */}
            {displayedCommand && (
              <div className="mb-2">
                <span className="text-[#13C636]">quantclaw&gt; </span>
                <span className="text-white">{displayedCommand}</span>
                {isTyping && displayedResponse === "" && (
                  <span className="text-[#13C636] animate-pulse">█</span>
                )}
              </div>
            )}

            {/* Current Response */}
            {displayedResponse && (
              <div className="text-[#00ff41] mb-4 whitespace-pre-wrap">
                {displayedResponse}
                {isTyping && (
                  <span className="text-[#00ff41] animate-pulse">█</span>
                )}
              </div>
            )}

            {/* Completion Message */}
            {isComplete && (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🎉</div>
                <div className="text-2xl text-[#13C636] font-bold mb-2">
                  Tutorial Complete!
                </div>
                <div className="text-white/60 mb-6">
                  You&apos;ve seen all 8 steps. Ready to try it yourself?
                </div>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Link
                    href="/"
                    className="px-6 py-3 bg-[#13C636] text-black font-bold rounded hover:bg-[#13C636]/80 transition-all text-center"
                  >
                    Launch Terminal →
                  </Link>
                  <a
                    href="https://data.quantclaw.org"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-6 py-3 border border-white/20 text-white font-bold rounded hover:bg-white/5 transition-all text-center"
                  >
                    View Dashboard
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Reference Cards */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4 text-white">
            Quick Reference — How to Use QuantClaw
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* CLI Card */}
            <div className="bg-black/60 border border-[#13C636]/30 rounded-lg p-6">
              <div className="text-2xl mb-3">💻</div>
              <h3 className="text-lg font-bold text-[#13C636] mb-2">CLI</h3>
              <p className="text-sm text-white/60 mb-3">
                Install and run locally
              </p>
              <code className="text-xs text-[#C0E8FD] block mb-2 bg-black/60 p-2 rounded">
                npm install -g quantclaw-data
              </code>
              <code className="text-xs text-[#C0E8FD] block bg-black/60 p-2 rounded">
                quantclaw prices AAPL
              </code>
            </div>

            {/* REST API Card */}
            <div className="bg-black/60 border border-[#C0E8FD]/30 rounded-lg p-6">
              <div className="text-2xl mb-3">🔌</div>
              <h3 className="text-lg font-bold text-[#C0E8FD] mb-2">REST API</h3>
              <p className="text-sm text-white/60 mb-3">
                HTTP endpoints for any language
              </p>
              <code className="text-xs text-[#00ff41] block mb-2 bg-black/60 p-2 rounded break-all">
                GET /api/v1/prices?ticker=AAPL
              </code>
              <a
                href="https://data.quantclaw.org/api"
                className="text-xs text-[#13C636] hover:underline"
              >
                API Docs →
              </a>
            </div>

            {/* MCP Card */}
            <div className="bg-black/60 border border-[#FFD700]/30 rounded-lg p-6">
              <div className="text-2xl mb-3">🤖</div>
              <h3 className="text-lg font-bold text-[#FFD700] mb-2">MCP</h3>
              <p className="text-sm text-white/60 mb-3">
                AI agent integration
              </p>
              <div className="text-xs text-white/40 mb-2">
                Supported agents:
              </div>
              <ul className="text-xs text-white/60 space-y-1">
                <li>• Claude Desktop</li>
                <li>• Continue</li>
                <li>• Cline</li>
                <li>• OpenClaw</li>
              </ul>
            </div>

            {/* Web Terminal Card */}
            <div className="bg-black/60 border border-white/30 rounded-lg p-6">
              <div className="text-2xl mb-3">🌐</div>
              <h3 className="text-lg font-bold text-white mb-2">Web Terminal</h3>
              <p className="text-sm text-white/60 mb-3">
                Try it in your browser
              </p>
              <Link
                href="/"
                className="inline-block px-4 py-2 bg-[#13C636] text-black text-xs font-bold rounded hover:bg-[#13C636]/80 transition-all mb-2"
              >
                Launch Terminal
              </Link>
              <div className="text-xs text-white/40">
                No installation required
              </div>
            </div>
          </div>
        </div>

        {/* Footer CTAs */}
        <div className="text-center py-12 border-t border-white/10">
          <h2 className="text-3xl font-bold mb-4 text-white">
            Ready to Try?
          </h2>
          <p className="text-white/60 mb-6">
            Start querying 200+ financial data modules in seconds
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <Link
              href="/"
              className="px-8 py-4 bg-[#13C636] text-black font-bold rounded text-lg hover:bg-[#13C636]/80 transition-all"
            >
              Launch Terminal →
            </Link>
            <a
              href="https://data.quantclaw.org"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 border border-white/20 text-white font-bold rounded text-lg hover:bg-white/5 transition-all"
            >
              View Dashboard
            </a>
          </div>
          
          {/* Footer Links */}
          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <a
              href="https://github.com/quantclaw/data"
              className="text-[#C0E8FD] hover:underline"
            >
              GitHub
            </a>
            <span className="text-white/20">·</span>
            <a
              href="https://quantclaw.org/llms.txt"
              className="text-[#C0E8FD] hover:underline"
            >
              llms.txt
            </a>
            <span className="text-white/20">·</span>
            <a
              href="https://terminal.quantclaw.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#C0E8FD] hover:underline"
            >
              TerminalX
            </a>
            <span className="text-white/20">·</span>
            <a
              href="https://moneyclaw.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#C0E8FD] hover:underline"
            >
              MoneyClaw
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
