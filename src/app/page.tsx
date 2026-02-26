"use client";
import { useState, useEffect, useRef } from "react";
import { services, categories } from "./services";
import { phases, dataSources } from "./roadmap";
import { mcpConfig } from "./install";

const doneCount = phases.filter(p => p.status === "done").length;
const totalLoc = phases.filter(p => p.loc).reduce((a, p) => a + (p.loc || 0), 0);

interface TerminalLine {
  type: "input" | "output" | "error" | "info";
  content: string;
  timestamp?: Date;
}

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [chatMode, setChatMode] = useState(false);
  const [terminalHistory, setTerminalHistory] = useState<TerminalLine[]>([
    {
      type: "info",
      content: `QuantClaw Data Terminal v1.0
${doneCount} modules • ${dataSources.length} data sources • ${totalLoc.toLocaleString()} lines of code

Type 'help' for available commands, or try:
  prices AAPL          - Get real-time stock price
  congress-trades      - Recent congressional trades
  options TSLA         - Options chain with Greeks
  clear                - Clear terminal output`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Scroll to bottom on new output
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalHistory]);

  // Generate suggestions based on input
  useEffect(() => {
    if (input.trim().length > 0) {
      const builtInCommands = ["help", "sources", "modules", "clear"];
      const serviceCommands = services.map(s => s.id.replace(/_/g, "-"));
      const allCommands = [...builtInCommands, ...serviceCommands];
      
      const matches = allCommands
        .filter(cmd => cmd.toLowerCase().includes(input.toLowerCase().split(" ")[0]))
        .slice(0, 5);
      setSuggestions(matches);
    } else {
      setSuggestions([]);
    }
  }, [input]);

  const executeCommand = async (cmd: string) => {
    if (!cmd.trim()) return;

    // Add input to history
    setTerminalHistory(prev => [...prev, { type: "input", content: cmd, timestamp: new Date() }]);
    setInput("");
    setSuggestions([]);

    const parts = cmd.trim().split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    // Built-in commands
    if (command === "clear") {
      setTerminalHistory([]);
      return;
    }

    if (command === "help") {
      const helpText = `Available Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Built-in:
  help              - Show this help message
  sources           - List all ${dataSources.length} data sources
  modules           - List module categories and counts
  clear             - Clear terminal output

Data Commands (examples):
  prices AAPL       - Real-time stock price
  options TSLA      - Options chain with Greeks
  congress-trades   - Congressional trading disclosures
  crypto BTC        - Cryptocurrency data
  news NVDA         - News sentiment analysis
  technicals SPY    - Technical indicators
  macro GDP         - Macroeconomic indicators
  insider-trades AAPL - Insider trading activity

Total: ${services.length} data modules available
Use <command> --help for specific command details`;
      
      setTerminalHistory(prev => [...prev, { type: "output", content: helpText }]);
      return;
    }

    if (command === "sources") {
      const sourcesList = dataSources.map((ds, i) => 
        `${(i + 1).toString().padStart(3, " ")}. ${ds.icon} ${ds.name.padEnd(40)} ${ds.modules.length} modules`
      ).join("\n");
      
      setTerminalHistory(prev => [...prev, { 
        type: "output", 
        content: `Data Sources (${dataSources.length} total):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n${sourcesList}`
      }]);
      return;
    }

    if (command === "modules") {
      const categoryStats = [...new Set(services.map(s => s.category))]
        .map(cat => {
          const catServices = services.filter(s => s.category === cat);
          const categoryInfo = categories.find(c => c.id === cat);
          return `${categoryInfo?.icon || "📦"} ${cat.padEnd(25)} ${catServices.length.toString().padStart(3)} modules`;
        })
        .join("\n");
      
      setTerminalHistory(prev => [...prev, { 
        type: "output", 
        content: `Module Categories:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n${categoryStats}\n\nTotal: ${services.length} modules`
      }]);
      return;
    }

    // Try to execute as API command
    const normalizedCmd = command.replace(/-/g, "_");
    const service = services.find(s => s.id === normalizedCmd || s.id.replace(/_/g, "-") === command);

    if (service) {
      setLoading(true);
      try {
        // Build API endpoint
        const endpoint = `/api/v1/${command}`;
        const ticker = args[0] || "";
        const url = ticker ? `${endpoint}?ticker=${ticker}` : endpoint;

        const response = await fetch(url);
        const data = await response.json();

        if (response.ok) {
          const formatted = JSON.stringify(data, null, 2);
          setTerminalHistory(prev => [...prev, { 
            type: "output", 
            content: chatMode 
              ? formatChatResponse(service, data, ticker)
              : formatted
          }]);
        } else {
          setTerminalHistory(prev => [...prev, { 
            type: "error", 
            content: `Error: ${data.error || "API request failed"}`
          }]);
        }
      } catch (error) {
        setTerminalHistory(prev => [...prev, { 
          type: "error", 
          content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`
        }]);
      } finally {
        setLoading(false);
      }
      return;
    }

    // Unknown command
    setTerminalHistory(prev => [...prev, { 
      type: "error", 
      content: `Unknown command: ${command}\nType 'help' for available commands`
    }]);
  };

  const formatChatResponse = (service: any, data: any, ticker: string): string => {
    // Format response as natural language card
    const title = ticker 
      ? `${service.icon} ${service.name} - ${ticker.toUpperCase()}`
      : `${service.icon} ${service.name}`;
    
    return `${title}\n${"━".repeat(60)}\n${JSON.stringify(data, null, 2)}`;
  };

  const quickActions = [
    "prices AAPL",
    "options TSLA", 
    "monte-carlo SPY",
    "congress-trades",
    "crypto BTC",
    "macro GDP",
    "treasury-curve",
    "insider-trades NVDA"
  ];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(text);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const curlExample = `curl -X GET "https://data.quantclaw.org/api/v1/prices?ticker=AAPL"`;

  return (
    <div className="min-h-screen bg-[#0a0a1a] text-[#00ff41] font-mono">
      {/* CRT Scanline effect */}
      <div className="fixed inset-0 pointer-events-none opacity-5">
        <div className="h-full w-full" style={{
          backgroundImage: "repeating-linear-gradient(0deg, rgba(0,255,65,0.03) 0px, transparent 1px, transparent 2px, rgba(0,255,65,0.03) 3px)",
        }} />
      </div>

      {/* Stats Bar */}
      <div className="sticky top-0 z-50 bg-[#0a0a1a]/95 border-b border-[#00ff41]/20 backdrop-blur-sm">
        <div className="max-w-[1800px] mx-auto px-4 py-2 flex items-center justify-between text-xs">
          <div className="flex items-center gap-6">
            <span className="text-[#C0E8FD]">⚡ QUANTCLAW DATA</span>
            <span>{doneCount} modules</span>
            <span>·</span>
            <span>{dataSources.length} sources</span>
            <span>·</span>
            <span>{totalLoc.toLocaleString()} lines</span>
            <span>·</span>
            <span className="text-[#FFD700]">$0/month</span>
            <span>·</span>
            <span className="text-white/60">No signup required</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#13C636] animate-pulse" />
            <span className="text-white/60">LIVE</span>
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className="max-w-[1800px] mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          
          {/* Left Panel - Marketing Hero */}
          <div className="space-y-6">
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl font-bold leading-tight">
                <span className="text-[#13C636]">AI Agents</span> That Build
                <br />
                <span className="text-white">Their Own Arsenal</span>
              </h1>
              
              <p className="text-lg text-white/60 leading-relaxed">
                From fragmented APIs and Excel chaos to AI-orchestrated market intelligence.
                <br />
                <span className="text-[#C0E8FD]">{doneCount} self-built modules. {dataSources.length} data sources. Zero API keys.</span>
              </p>

              <div className="flex flex-col sm:flex-row gap-3">
                <a 
                  href="https://data.quantclaw.org" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 bg-[#13C636] text-black font-bold rounded hover:bg-[#13C636]/80 transition-all text-center"
                >
                  Launch Dashboard →
                </a>
                <a 
                  href="https://github.com/quantclaw/data" 
                  className="px-6 py-3 border border-white/20 text-white font-bold rounded hover:bg-white/5 transition-all text-center"
                >
                  View on GitHub
                </a>
              </div>
            </div>

            {/* Feature Highlights */}
            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="bg-white/[0.02] border border-[#13C636]/30 rounded p-4">
                <div className="text-2xl mb-2">🤖</div>
                <div className="font-bold text-sm text-white mb-1">Self-Evolving</div>
                <div className="text-xs text-white/50">AI builds new modules every 30 minutes</div>
              </div>
              <div className="bg-white/[0.02] border border-[#C0E8FD]/30 rounded p-4">
                <div className="text-2xl mb-2">⚡</div>
                <div className="font-bold text-sm text-white mb-1">{services.length}+ Commands</div>
                <div className="text-xs text-white/50">CLI + REST API + MCP ready</div>
              </div>
              <div className="bg-white/[0.02] border border-[#FFD700]/30 rounded p-4">
                <div className="text-2xl mb-2">🔓</div>
                <div className="font-bold text-sm text-white mb-1">Zero Setup</div>
                <div className="text-xs text-white/50">No API keys, no rate limits</div>
              </div>
              <div className="bg-white/[0.02] border border-white/30 rounded p-4">
                <div className="text-2xl mb-2">📊</div>
                <div className="font-bold text-sm text-white mb-1">Real-Time Data</div>
                <div className="text-xs text-white/50">Live prices, options, sentiment</div>
              </div>
            </div>

            {/* Data Sources Preview */}
            <div className="bg-black/40 border border-white/10 rounded p-4">
              <h3 className="text-sm font-bold text-white mb-3">
                {dataSources.length} Data Sources Integrated
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {dataSources.slice(0, 8).map(ds => (
                  <div key={ds.name} className="flex items-center gap-2 text-white/60">
                    <span>{ds.icon}</span>
                    <span className="truncate">{ds.name}</span>
                  </div>
                ))}
              </div>
              <div className="mt-2 text-xs text-[#13C636]">
                + {dataSources.length - 8} more sources
              </div>
            </div>
          </div>

          {/* Right Panel - Interactive Terminal */}
          <div className="space-y-4">
            
            {/* Terminal/Chat Mode Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-white/60">
                <span>█</span>
                <span>{chatMode ? "CHAT MODE" : "TERMINAL MODE"}</span>
              </div>
              <button
                onClick={() => setChatMode(!chatMode)}
                className="px-3 py-1 text-xs border border-white/20 rounded hover:bg-white/5 transition-all"
              >
                {chatMode ? "Switch to Terminal" : "Switch to Chat"}
              </button>
            </div>

            {/* Terminal Window */}
            <div className="bg-black border border-[#13C636]/50 rounded-lg overflow-hidden shadow-lg shadow-[#13C636]/20">
              
              {/* Terminal Header */}
              <div className="bg-[#13C636]/10 border-b border-[#13C636]/30 px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#FF6B6B]" />
                    <div className="w-3 h-3 rounded-full bg-[#FFD700]" />
                    <div className="w-3 h-3 rounded-full bg-[#13C636]" />
                  </div>
                  <span className="text-xs text-white/60 ml-2">
                    {chatMode ? "chat@quantclaw" : "quantclaw@terminal"}
                  </span>
                </div>
                <div className="text-xs text-white/40">
                  {new Date().toLocaleTimeString()}
                </div>
              </div>

              {/* Terminal Output */}
              <div 
                ref={terminalRef}
                className="h-[500px] overflow-y-auto p-4 space-y-2 text-sm"
                onClick={() => inputRef.current?.focus()}
              >
                {terminalHistory.map((line, i) => (
                  <div key={i} className={
                    line.type === "input" ? "text-white" :
                    line.type === "error" ? "text-[#FF6B6B]" :
                    line.type === "info" ? "text-[#C0E8FD]" :
                    "text-[#00ff41]"
                  }>
                    {line.type === "input" && (
                      <span className="text-[#13C636]">quantclaw&gt; </span>
                    )}
                    <span className="whitespace-pre-wrap">{line.content}</span>
                  </div>
                ))}
                
                {loading && (
                  <div className="text-[#C0E8FD]">
                    <span className="animate-pulse">Fetching data...</span>
                  </div>
                )}

                {/* Input Line */}
                {!loading && (
                  <div className="flex items-center gap-2">
                    <span className="text-[#13C636]">quantclaw&gt;</span>
                    <input
                      ref={inputRef}
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          executeCommand(input);
                        } else if (e.key === "Tab" && suggestions.length > 0) {
                          e.preventDefault();
                          setInput(suggestions[0]);
                        }
                      }}
                      className="flex-1 bg-transparent outline-none text-white caret-[#13C636]"
                      placeholder={chatMode ? "Ask anything about markets..." : "Type a command..."}
                      autoFocus
                    />
                    <span className="text-[#13C636] animate-pulse">█</span>
                  </div>
                )}

                {/* Suggestions */}
                {suggestions.length > 0 && !loading && (
                  <div className="text-xs text-white/40 pl-14">
                    Suggestions: {suggestions.join(", ")}
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <div className="text-xs text-white/60 mb-2">Quick Actions:</div>
              <div className="flex flex-wrap gap-2">
                {quickActions.map((cmd) => (
                  <button
                    key={cmd}
                    onClick={() => executeCommand(cmd)}
                    className="px-3 py-1 text-xs bg-white/5 border border-white/10 rounded hover:bg-white/10 hover:border-[#13C636]/50 transition-all"
                  >
                    {cmd}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* AI/Claw Access Section */}
        <div className="mt-12 grid md:grid-cols-2 gap-6">
          
          {/* MCP Config */}
          <div className="bg-black/60 border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white">MCP Configuration</h3>
              <button
                onClick={() => copyToClipboard(mcpConfig.config)}
                className="text-xs px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-white/60 hover:text-[#13C636] transition-all"
              >
                {copiedCmd === mcpConfig.config ? "✅ Copied" : "📋 Copy"}
              </button>
            </div>
            <pre className="text-xs text-[#C0E8FD] overflow-x-auto whitespace-pre-wrap">
{mcpConfig.config}
            </pre>
            <p className="text-xs text-white/40 mt-3">
              Add to claude_desktop_config.json to use all {services.length} modules as AI tools
            </p>
          </div>

          {/* REST API */}
          <div className="bg-black/60 border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white">REST API</h3>
              <button
                onClick={() => copyToClipboard(curlExample)}
                className="text-xs px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-white/60 hover:text-[#13C636] transition-all"
              >
                {copiedCmd === curlExample ? "✅ Copied" : "📋 Copy"}
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-white/40 mb-1">Endpoint Format:</div>
                <code className="text-xs text-[#C0E8FD] block">
                  GET https://data.quantclaw.org/api/v1/{"{tool}"}?ticker=SYMBOL
                </code>
              </div>
              <div>
                <div className="text-xs text-white/40 mb-1">Example (curl):</div>
                <code className="text-xs text-[#C0E8FD] block break-all">
                  {curlExample}
                </code>
              </div>
              <div>
                <a 
                  href="https://data.quantclaw.org/llms.txt"
                  className="text-xs text-[#13C636] hover:underline"
                >
                  View llms.txt →
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Links */}
        <footer className="mt-12 pt-8 border-t border-white/10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-6 text-sm">
              <a href="https://data.quantclaw.org" target="_blank" rel="noopener noreferrer" className="text-[#C0E8FD] hover:underline">
                Dashboard
              </a>
              <span className="text-white/20">·</span>
              <a href="https://terminal.quantclaw.org" target="_blank" rel="noopener noreferrer" className="text-[#C0E8FD] hover:underline">
                TerminalX
              </a>
              <span className="text-white/20">·</span>
              <a href="https://moneyclaw.com" target="_blank" rel="noopener noreferrer" className="text-[#C0E8FD] hover:underline">
                MoneyClaw
              </a>
              <span className="text-white/20">·</span>
              <a href="https://github.com/quantclaw/data" className="text-[#C0E8FD] hover:underline">
                GitHub
              </a>
            </div>
            
            <div className="text-xs text-white/40">
              <span className="text-[#13C636]">QuantClaw</span> · {totalLoc.toLocaleString()} lines · Built by AI
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
