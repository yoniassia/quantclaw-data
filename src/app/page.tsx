"use client";
import { useState, useEffect } from "react";
import { services, categories } from "./services";
import { phases, dataSources } from "./roadmap";
import { mcpConfig } from "./install";

const doneCount = phases.filter(p => p.status === "done").length;
const totalLoc = phases.filter(p => p.loc).reduce((a, p) => a + (p.loc || 0), 0);

export default function Home() {
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const copyCommand = (cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(cmd);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const exampleCommands = [
    { cmd: "python cli.py monte-carlo SPY", desc: "Run Monte Carlo simulation on SPY" },
    { cmd: "python cli.py congress-trades", desc: "Latest Congressional stock trades" },
    { cmd: "python cli.py insider-trades AAPL", desc: "Insider trading activity for AAPL" },
    { cmd: "python cli.py sentiment-analysis TSLA", desc: "News sentiment for TSLA" },
    { cmd: "python cli.py backtest-strategy momentum", desc: "Backtest momentum strategy" },
    { cmd: "python cli.py dsl-scan \"rsi < 25 AND volume > 10M\"", desc: "Scan for oversold high-volume stocks" },
  ];

  // Group data sources by category
  const dataSourcesByCategory = dataSources.reduce((acc, ds) => {
    const category = ds.name.includes("SEC") || ds.name.includes("Congress") ? "Regulatory" :
                     ds.name.includes("News") || ds.name.includes("Reddit") || ds.name.includes("Sentiment") ? "Sentiment" :
                     ds.name.includes("Options") || ds.name.includes("Derivatives") ? "Derivatives" :
                     "Market Data";
    if (!acc[category]) acc[category] = [];
    acc[category].push(ds);
    return acc;
  }, {} as Record<string, typeof dataSources>);

  const categoryStats = Object.entries(dataSourcesByCategory).map(([name, sources]) => ({
    name,
    count: sources.length,
    icon: name === "Regulatory" ? "⚖️" : name === "Sentiment" ? "💭" : name === "Derivatives" ? "📊" : "💹"
  }));

  return (
    <div className="min-h-screen bg-[#000021] text-white">
      
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden border-b border-white/10">
        {/* Animated gradient background */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#13C636] rounded-full blur-[120px] animate-pulse" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#C0E8FD] rounded-full blur-[120px] animate-pulse" style={{ animationDelay: "1s" }} />
        </div>

        <div className="relative max-w-6xl mx-auto px-6 py-20 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8">
            <span className="w-2 h-2 rounded-full bg-[#13C636] animate-pulse" />
            <span className="text-sm text-white/60">Live • {doneCount} modules built • Self-evolving</span>
          </div>

          <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold mb-6 leading-tight">
            <span className={`bg-gradient-to-r from-[#13C636] to-[#C0E8FD] bg-clip-text text-transparent ${mounted ? 'animate-pulse' : ''}`}>
              AI Agents That Build
            </span>
            <br />
            <span className="text-white">Their Own Financial Arsenal</span>
          </h1>

          <p className="text-xl text-white/60 max-w-3xl mx-auto mb-4 leading-relaxed">
            From fragmented APIs and Excel chaos to AI-orchestrated market intelligence.
            <br />
            <span className="text-[#C0E8FD]">{doneCount} self-built modules. {dataSources.length} data sources. {totalLoc.toLocaleString()} lines of autonomous code.</span>
          </p>

          {/* Key stats row */}
          <div className="flex flex-wrap justify-center gap-6 sm:gap-12 mt-10 mb-12">
            <div className="text-center">
              <div className="text-4xl font-bold text-[#13C636] mb-1">{doneCount}</div>
              <div className="text-sm text-white/40">Modules Built</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-[#C0E8FD] mb-1">{dataSources.length}</div>
              <div className="text-sm text-white/40">Data Sources</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-[#FFD700] mb-1">{totalLoc.toLocaleString()}</div>
              <div className="text-sm text-white/40">Lines of Code</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-white mb-1">$0</div>
              <div className="text-sm text-white/40">Per Month</div>
            </div>
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="https://data.quantclaw.org" 
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-[#13C636] text-black font-bold rounded-xl hover:bg-[#13C636]/80 transition-all transform hover:scale-105 shadow-lg shadow-[#13C636]/20"
            >
              Launch Dashboard →
            </a>
            <a 
              href="#" 
              className="px-8 py-4 border-2 border-white/20 text-white font-bold rounded-xl hover:bg-white/5 transition-all"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>

      {/* 2. THE PROBLEM */}
      <section className="py-20 px-6 border-b border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              Data Hides in the <span className="text-[#FF6B6B]">Shadows</span>
            </h2>
            <p className="text-xl text-white/60 max-w-2xl mx-auto">
              In a $100T global market, hesitation costs millions
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 rounded-2xl p-8 hover:border-[#FF6B6B]/50 transition-all">
              <div className="text-5xl mb-4">😰</div>
              <h3 className="text-xl font-bold mb-3 text-[#FF6B6B]">Drowning in APIs</h3>
              <p className="text-white/60">
                Traders juggle 20+ data providers. Each with different formats, rate limits, and documentation gaps. Hours wasted on data plumbing instead of analysis.
              </p>
            </div>

            <div className="bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 rounded-2xl p-8 hover:border-[#FF6B6B]/50 transition-all">
              <div className="text-5xl mb-4">🔧</div>
              <h3 className="text-xl font-bold mb-3 text-[#FF6B6B]">Rebuilding the Wheel</h3>
              <p className="text-white/60">
                Every quant writes the same code. Monte Carlo simulations. Options Greeks. Sentiment analysis. Thousands of duplicated hours across the industry.
              </p>
            </div>

            <div className="bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 rounded-2xl p-8 hover:border-[#FF6B6B]/50 transition-all">
              <div className="text-5xl mb-4">⏰</div>
              <h3 className="text-xl font-bold mb-3 text-[#FF6B6B]">Missed Opportunities</h3>
              <p className="text-white/60">
                By the time you&apos;ve normalized the data, run the backtest, and generated the report — the market has moved. Alpha decays while you code.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. THE TRANSFORMATION */}
      <section className="py-20 px-6 bg-gradient-to-b from-transparent to-white/[0.02] border-b border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              Enter <span className="bg-gradient-to-r from-[#13C636] to-[#C0E8FD] bg-clip-text text-transparent">QuantClaw</span>
            </h2>
            <p className="text-xl text-white/60 max-w-2xl mx-auto">
              The platform that builds itself while you sleep
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="bg-white/[0.03] border border-[#13C636]/30 rounded-2xl p-8 hover:bg-white/[0.05] transition-all">
              <div className="w-14 h-14 rounded-xl bg-[#13C636]/20 flex items-center justify-center text-3xl mb-4">
                🤖
              </div>
              <h3 className="text-xl font-bold mb-3 text-[#13C636]">Self-Evolving AI Agents</h3>
              <p className="text-white/60 text-sm leading-relaxed">
                Every 30 minutes, an AI agent builds a new module, tests it, and suggests 3 more features. The platform compounds its own capabilities autonomously.
              </p>
            </div>

            <div className="bg-white/[0.03] border border-[#C0E8FD]/30 rounded-2xl p-8 hover:bg-white/[0.05] transition-all">
              <div className="w-14 h-14 rounded-xl bg-[#C0E8FD]/20 flex items-center justify-center text-3xl mb-4">
                ⚡
              </div>
              <h3 className="text-xl font-bold mb-3 text-[#C0E8FD]">200+ CLI Commands</h3>
              <p className="text-white/60 text-sm leading-relaxed">
                From Monte Carlo simulations to insider trading alerts. From sentiment analysis to options Greeks. Every tool you need, one command away.
              </p>
            </div>

            <div className="bg-white/[0.03] border border-[#FFD700]/30 rounded-2xl p-8 hover:bg-white/[0.05] transition-all">
              <div className="w-14 h-14 rounded-xl bg-[#FFD700]/20 flex items-center justify-center text-3xl mb-4">
                🔓
              </div>
              <h3 className="text-xl font-bold mb-3 text-[#FFD700]">Zero API Keys Required</h3>
              <p className="text-white/60 text-sm leading-relaxed">
                {dataSources.length} data sources. All free. No rate limits. No registration walls. Just clone and run. Open source, open data.
              </p>
            </div>
          </div>

          {/* Key differentiators */}
          <div className="bg-gradient-to-r from-[#13C636]/10 to-[#C0E8FD]/10 border border-[#13C636]/30 rounded-2xl p-8">
            <h3 className="text-2xl font-bold mb-6 text-center">Why QuantClaw is Different</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex gap-4">
                <div className="text-2xl">✅</div>
                <div>
                  <div className="font-semibold text-[#13C636] mb-1">MCP-Ready</div>
                  <div className="text-white/60 text-sm">Plug directly into Claude, ChatGPT, or any AI agent. Every module becomes a callable tool.</div>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="text-2xl">✅</div>
                <div>
                  <div className="font-semibold text-[#13C636] mb-1">REST API Included</div>
                  <div className="text-white/60 text-sm">Every CLI command is also an HTTP endpoint. Build web apps, mobile apps, or integrate anywhere.</div>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="text-2xl">✅</div>
                <div>
                  <div className="font-semibold text-[#13C636] mb-1">Self-Building</div>
                  <div className="text-white/60 text-sm">Roadmap started at 24 phases. Now at {phases.length}+. The AI suggests what to build next based on what it just completed.</div>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="text-2xl">✅</div>
                <div>
                  <div className="font-semibold text-[#13C636] mb-1">Production-Grade</div>
                  <div className="text-white/60 text-sm">Caching, error handling, rate limiting, retry logic. Built by AI, tested by AI, deployed by AI.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. DATA SOURCES SHOWCASE */}
      <section className="py-20 px-6 border-b border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              <span className="text-[#C0E8FD]">{dataSources.length}</span> Data Sources, Zero Setup
            </h2>
            <p className="text-white/60">From SEC filings to Reddit sentiment — all integrated and ready</p>
          </div>

          {/* Category overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
            {categoryStats.map(cat => (
              <div key={cat.name} className="bg-white/[0.03] border border-white/10 rounded-xl p-6 text-center hover:border-[#13C636]/50 transition-all">
                <div className="text-4xl mb-2">{cat.icon}</div>
                <div className="text-3xl font-bold text-[#13C636] mb-1">{cat.count}</div>
                <div className="text-sm text-white/60">{cat.name}</div>
              </div>
            ))}
          </div>

          {/* Data sources grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dataSources.slice(0, 12).map(ds => (
              <div key={ds.name} className="bg-white/[0.02] border border-white/10 rounded-xl p-5 hover:bg-white/[0.04] hover:border-[#13C636]/30 transition-all">
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-2xl">{ds.icon}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white mb-1">{ds.name}</h3>
                    <p className="text-white/50 text-xs leading-relaxed">{ds.desc}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {ds.modules.slice(0, 3).map(m => (
                    <span key={m} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40 font-mono">
                      {m}
                    </span>
                  ))}
                  {ds.modules.length > 3 && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#13C636]/20 text-[#13C636] font-mono">
                      +{ds.modules.length - 3}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-8">
            <a 
              href="https://data.quantclaw.org" 
              className="inline-flex items-center gap-2 text-[#13C636] hover:text-[#13C636]/80 transition-colors"
            >
              <span>View all {dataSources.length} data sources</span>
              <span>→</span>
            </a>
          </div>
        </div>
      </section>

      {/* 5. LIVE DEMO SECTION */}
      <section className="py-20 px-6 bg-gradient-to-b from-white/[0.02] to-transparent border-b border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              Try It <span className="text-[#13C636]">Right Now</span>
            </h2>
            <p className="text-white/60">Copy any command and run it in your terminal</p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {exampleCommands.map((item, i) => (
              <div 
                key={i}
                onClick={() => copyCommand(item.cmd)}
                className="bg-black/40 border border-white/10 rounded-xl p-5 hover:border-[#13C636]/50 transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="text-xs text-white/40 group-hover:text-[#13C636] transition-colors">
                    {item.desc}
                  </div>
                  <button className="text-white/30 group-hover:text-[#13C636] transition-colors">
                    {copiedCmd === item.cmd ? "✅" : "📋"}
                  </button>
                </div>
                <code className="block text-sm font-mono text-[#13C636] break-all">
                  {item.cmd}
                </code>
              </div>
            ))}
          </div>

          <div className="mt-12 bg-gradient-to-r from-[#13C636]/10 to-[#C0E8FD]/10 border border-[#13C636]/30 rounded-2xl p-8 text-center">
            <h3 className="text-xl font-bold mb-3">Want to see the full dashboard?</h3>
            <p className="text-white/60 mb-6">Explore all {doneCount} modules with interactive UI, real-time data, and visual analytics</p>
            <a 
              href="https://data.quantclaw.org" 
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-8 py-3 bg-[#13C636] text-black font-bold rounded-xl hover:bg-[#13C636]/80 transition-all"
            >
              Launch Full Dashboard →
            </a>
          </div>
        </div>
      </section>

      {/* 6. BUILD PROGRESS */}
      <section className="py-20 px-6 border-b border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              Built by AI, <span className="text-[#C0E8FD]">for AI</span>
            </h2>
            <p className="text-white/60">This platform writes itself. Every 30 minutes, a new module goes live.</p>
          </div>

          {/* Progress bar */}
          <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-8 mb-12">
            <div className="flex justify-between items-center mb-4">
              <div>
                <div className="text-sm text-white/40 mb-1">Build Progress</div>
                <div className="text-2xl font-bold">
                  Phase <span className="text-[#13C636]">{doneCount}</span> of {phases.length}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-white/40 mb-1">Completion</div>
                <div className="text-2xl font-bold text-[#13C636]">
                  {Math.round(doneCount / phases.length * 100)}%
                </div>
              </div>
            </div>
            
            <div className="h-4 bg-white/10 rounded-full overflow-hidden mb-8">
              <div 
                className="h-full bg-gradient-to-r from-[#13C636] to-[#C0E8FD] rounded-full transition-all duration-1000"
                style={{ width: `${doneCount / phases.length * 100}%` }}
              />
            </div>

            {/* Category breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
              {[...new Set(phases.map(p => p.category))].map(cat => {
                const catPhases = phases.filter(p => p.category === cat);
                const catDone = catPhases.filter(p => p.status === "done").length;
                const percentage = Math.round((catDone / catPhases.length) * 100);
                return (
                  <div key={cat} className="text-center">
                    <div className="text-3xl font-bold text-white/80 mb-1">
                      {catDone}<span className="text-white/30">/{catPhases.length}</span>
                    </div>
                    <div className="text-xs text-white/40 mb-2">{cat}</div>
                    <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#13C636] rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Self-evolution explanation */}
          <div className="bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 rounded-2xl p-8">
            <h3 className="text-2xl font-bold mb-6 text-center">🧬 How Self-Evolution Works</h3>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#13C636] text-black font-bold flex items-center justify-center shrink-0">1</div>
                  <div>
                    <div className="font-semibold text-white mb-1">Cron triggers every 30 min</div>
                    <div className="text-sm text-white/60">An isolated AI agent spins up in a clean environment</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#13C636] text-black font-bold flex items-center justify-center shrink-0">2</div>
                  <div>
                    <div className="font-semibold text-white mb-1">Reads BUILD_QUEUE.md</div>
                    <div className="text-sm text-white/60">Finds the next unchecked phase to build</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#13C636] text-black font-bold flex items-center justify-center shrink-0">3</div>
                  <div>
                    <div className="font-semibold text-white mb-1">Builds the module</div>
                    <div className="text-sm text-white/60">Writes Python, tests it, integrates with CLI and API</div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#C0E8FD] text-black font-bold flex items-center justify-center shrink-0">4</div>
                  <div>
                    <div className="font-semibold text-white mb-1">Marks phase complete</div>
                    <div className="text-sm text-white/60">Updates BUILD_QUEUE.md and deployment status</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#C0E8FD] text-black font-bold flex items-center justify-center shrink-0">5</div>
                  <div>
                    <div className="font-semibold text-white mb-1">Suggests 3 new features</div>
                    <div className="text-sm text-white/60">Based on what it just built — compounding ideas</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#C0E8FD] text-black font-bold flex-items-center justify-center shrink-0">6</div>
                  <div>
                    <div className="font-semibold text-white mb-1">Announces to team</div>
                    <div className="text-sm text-white/60">Posts summary to monitoring channels</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-white/10 text-center">
              <p className="text-sm text-white/40">
                <span className="text-[#13C636]">Cost per phase:</span> ~$0.15 | 
                <span className="text-[#C0E8FD]"> Build time:</span> ~5 min | 
                <span className="text-[#FFD700]"> Growth:</span> Started at 24 phases, now {phases.length}+ and counting
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 7. MCP INTEGRATION */}
      <section className="py-20 px-6 bg-gradient-to-b from-transparent to-white/[0.02] border-b border-white/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              Add to Any AI Agent with <span className="text-[#C0E8FD]">One Config</span>
            </h2>
            <p className="text-white/60">MCP-ready. Plug into Claude, ChatGPT, or any AI that supports Model Context Protocol.</p>
          </div>

          <div className="bg-black/60 border border-white/10 rounded-2xl p-8 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm text-[#13C636] font-mono">claude_desktop_config.json</div>
              <button 
                onClick={() => copyCommand(mcpConfig.config)}
                className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-white/60 hover:text-[#13C636] transition-all"
              >
                {copiedCmd === mcpConfig.config ? "✅ Copied" : "📋 Copy"}
              </button>
            </div>
            <pre className="text-sm text-[#C0E8FD] font-mono overflow-x-auto whitespace-pre-wrap">
{mcpConfig.config}
            </pre>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-6">
              <div className="text-3xl mb-3">🤖</div>
              <h3 className="font-bold mb-2 text-white">AI Agent Integration</h3>
              <p className="text-sm text-white/60">
                Every module becomes a callable tool. Your AI can now analyze stocks, run backtests, and pull market data autonomously.
              </p>
            </div>

            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-6">
              <div className="text-3xl mb-3">🔌</div>
              <h3 className="font-bold mb-2 text-white">REST API Fallback</h3>
              <p className="text-sm text-white/60">
                Don&apos;t use MCP? Every tool is also available via REST API at <code className="text-[#13C636]">data.quantclaw.org/api</code>
              </p>
            </div>

            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-6">
              <div className="text-3xl mb-3">⚡</div>
              <h3 className="font-bold mb-2 text-white">Real-Time Data</h3>
              <p className="text-sm text-white/60">
                Smart caching ensures fast responses while keeping data fresh. Most queries return in under 100ms.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 8. CALL TO ACTION */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6 leading-tight">
            What Will You <span className="bg-gradient-to-r from-[#13C636] to-[#C0E8FD] bg-clip-text text-transparent">Claw</span> From the Markets Today?
          </h2>
          <p className="text-xl text-white/60 mb-12">
            {doneCount} modules. {dataSources.length} data sources. {totalLoc.toLocaleString()} lines of code. All free. All open source.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <a 
              href="https://data.quantclaw.org" 
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-[#13C636] text-black font-bold rounded-xl hover:bg-[#13C636]/80 transition-all transform hover:scale-105 shadow-lg shadow-[#13C636]/20"
            >
              Launch Dashboard →
            </a>
            <a 
              href="#" 
              className="px-8 py-4 border-2 border-white/20 text-white font-bold rounded-xl hover:bg-white/5 transition-all"
            >
              View on GitHub
            </a>
            <a 
              href="#" 
              className="px-8 py-4 border-2 border-white/20 text-white font-bold rounded-xl hover:bg-white/5 transition-all"
            >
              Browse ClawHub
            </a>
          </div>

          {/* Quick links */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-12">
            <a href="https://data.quantclaw.org" target="_blank" rel="noopener noreferrer" className="group">
              <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4 hover:border-[#13C636]/50 transition-all">
                <div className="text-2xl mb-2">📊</div>
                <div className="text-sm font-semibold text-white/80 group-hover:text-[#13C636] transition-colors">Dashboard</div>
              </div>
            </a>
            <a href="https://terminal.quantclaw.org" target="_blank" rel="noopener noreferrer" className="group">
              <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4 hover:border-[#13C636]/50 transition-all">
                <div className="text-2xl mb-2">💹</div>
                <div className="text-sm font-semibold text-white/80 group-hover:text-[#13C636] transition-colors">TerminalX</div>
              </div>
            </a>
            <a href="https://quantclaw.org" className="group">
              <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4 hover:border-[#13C636]/50 transition-all">
                <div className="text-2xl mb-2">🦞</div>
                <div className="text-sm font-semibold text-white/80 group-hover:text-[#13C636] transition-colors">QuantClaw</div>
              </div>
            </a>
            <a href="https://moneyclaw.com" target="_blank" rel="noopener noreferrer" className="group">
              <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4 hover:border-[#13C636]/50 transition-all">
                <div className="text-2xl mb-2">💰</div>
                <div className="text-sm font-semibold text-white/80 group-hover:text-[#13C636] transition-colors">MoneyClaw</div>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 px-6 py-12">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                <span className="text-2xl">📈</span>
                <span className="font-bold text-xl">
                  <span className="text-[#13C636]">Quant</span>Claw
                </span>
              </div>
              <p className="text-white/40 text-sm">
                Autonomous Financial Intelligence
              </p>
            </div>

            <div className="text-center md:text-right">
              <p className="text-white/30 text-sm mb-1">
                Part of the <a href="https://moneyclaw.com" className="text-[#C0E8FD] hover:underline">MoneyClaw</a> ecosystem
              </p>
              <p className="text-white/20 text-xs">
                {totalLoc.toLocaleString()} lines • {doneCount} modules • Built by AI
              </p>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-white/5 text-center text-white/20 text-xs">
            <p>Open source • Free forever • Self-evolving</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
