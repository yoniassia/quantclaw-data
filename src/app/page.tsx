"use client";
import { useState, useEffect, useCallback } from "react";
import { services, categories, Service, getApiEndpoint } from "./services";
import { phases, dataSources, ideaGeneration } from "./roadmap";
import { installSteps, mcpConfig, cliReference, apiEndpoints } from "./install";

type Tab = "dashboard" | "modules" | "roadmap" | "install";
const VALID_TABS: Tab[] = ["dashboard", "modules", "roadmap", "install"];

function ServiceCard({ s }: { s: Service }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="border border-white/10 rounded-xl p-5 hover:border-[#13C636]/50 transition-all cursor-pointer bg-white/[0.02] hover:bg-white/[0.05]"
      onClick={() => setOpen(!open)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{s.icon}</span>
          <h3 className="font-semibold text-lg">{s.name}</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded-full bg-white/10 text-white/60">Phase {s.phase}</span>
      </div>
      <p className="text-white/60 text-sm mb-3">{s.description}</p>
      {open && (
        <div className="mt-3 space-y-3 border-t border-white/10 pt-3">
          <div>
            <p className="text-xs text-[#13C636] font-mono mb-1">CLI Commands</p>
            {s.commands.map((c, i) => (
              <code key={i} className="block text-xs bg-black/40 rounded px-2 py-1 mb-1 text-white/80">
                python cli.py {c}
              </code>
            ))}
          </div>
          <div>
            <p className="text-xs text-[#FF6B6B] font-mono mb-1">REST API</p>
            <code className="block text-xs bg-black/40 rounded px-2 py-1 mb-1 text-white/80">
              GET https://data.quantclaw.org{getApiEndpoint(s)}
            </code>
          </div>
          <div>
            <p className="text-xs text-[#FFD700] font-mono mb-1">Web UI</p>
            <code className="block text-xs bg-black/40 rounded px-2 py-1 mb-1 text-white/80">
              https://data.quantclaw.org/#modules/{s.category}
            </code>
          </div>
          <div>
            <p className="text-xs text-[#C0E8FD] font-mono mb-1">MCP Tool</p>
            <pre className="text-xs bg-black/40 rounded px-3 py-2 text-white/80 overflow-x-auto">
{JSON.stringify({ name: s.mcpTool, description: s.description, inputSchema: { type: "object", properties: Object.fromEntries(s.params.split(", ").map(p => [p.replace("?","").replace("{}","").replace("[]",""), { type: "string" }])), required: s.params.split(", ").filter(p => !p.includes("?")).map(p => p.replace("{}","").replace("[]","")) }}, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

const doneCount = phases.filter(p => p.status === "done").length;
const totalLoc = phases.filter(p => p.loc).reduce((a, p) => a + (p.loc || 0), 0);
const roadmapCategories = [...new Set(phases.map(p => p.category))];

export default function Home() {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [roadmapFilter, setRoadmapFilter] = useState<string | null>(null);

  // Sync tab/category with URL hash for shareable links
  // Format: #tab or #tab/category
  const updateHash = useCallback((tab: Tab, category?: string | null) => {
    const hash = category ? `${tab}/${encodeURIComponent(category)}` : tab;
    window.history.replaceState(null, "", `#${hash}`);
  }, []);

  useEffect(() => {
    const parseHash = () => {
      const hash = window.location.hash.replace("#", "");
      if (!hash) return;
      const [tab, ...rest] = hash.split("/");
      const cat = rest.length ? decodeURIComponent(rest.join("/")) : null;
      if (VALID_TABS.includes(tab as Tab)) {
        setActiveTab(tab as Tab);
        if (tab === "modules" && cat) setActiveCategory(cat);
        if (tab === "roadmap" && cat) setRoadmapFilter(cat);
      }
    };
    parseHash();
    window.addEventListener("hashchange", parseHash);
    return () => window.removeEventListener("hashchange", parseHash);
  }, []);

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    updateHash(tab);
  };

  const handleCategoryChange = (cat: string | null) => {
    setActiveCategory(cat);
    updateHash("modules", cat);
  };

  const handleRoadmapFilter = (cat: string | null) => {
    setRoadmapFilter(cat);
    updateHash("roadmap", cat);
  };

  const filtered = services.filter(s => {
    if (activeCategory && s.category !== activeCategory) return false;
    if (search && !s.name.toLowerCase().includes(search.toLowerCase()) && !s.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const filteredPhases = roadmapFilter ? phases.filter(p => p.category === roadmapFilter) : phases;

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="border-b border-white/10 px-6 py-12 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="text-5xl">📈</span>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
              <span className="text-[#13C636]">Quant</span>Claw Data
            </h1>
          </div>
          <p className="text-lg text-white/60 mt-3 max-w-2xl mx-auto">
            The open financial intelligence platform. {phases.length} modules planned, {doneCount} built, {totalLoc.toLocaleString()} lines of code.
            <br /><span className="text-[#C0E8FD]">Free. Open. MCP-ready. Self-evolving.</span>
          </p>
          <div className="flex justify-center gap-8 mt-6 text-sm text-white/40">
            <div><span className="text-2xl text-[#13C636] font-bold">{doneCount}</span><br />Built</div>
            <div><span className="text-2xl text-[#C0E8FD] font-bold">{phases.length}</span><br />Planned</div>
            <div><span className="text-2xl text-[#FFD700] font-bold">{totalLoc.toLocaleString()}</span><br />Lines</div>
            <div><span className="text-2xl text-white/80 font-bold">{dataSources.length}</span><br />Sources</div>
            <div><span className="text-2xl text-[#FF6B6B] font-bold">$0</span><br />/month</div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="border-b border-white/10 px-6">
        <div className="max-w-6xl mx-auto flex gap-1">
          {(["dashboard", "modules", "install", "roadmap"] as const).map(tab => (
            <button key={tab} onClick={() => handleTabChange(tab)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition ${activeTab === tab ? "border-[#13C636] text-[#13C636]" : "border-transparent text-white/50 hover:text-white/80"}`}>
              {tab === "dashboard" ? "📊 Dashboard" : tab === "modules" ? "🔌 API Modules" : tab === "install" ? "⚡ Install & Use" : "🗺️ Roadmap"}
            </button>
          ))}
        </div>
      </nav>

      {/* Dashboard Tab */}
      {activeTab === "dashboard" && (
        <section className="px-6 py-8">
          <div className="max-w-6xl mx-auto space-y-8">
            {/* Data Sources Grid */}
            <div>
              <h2 className="text-2xl font-bold mb-4">📡 Data Sources</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {dataSources.map(ds => (
                  <div key={ds.name} className="border border-white/10 rounded-xl p-4 bg-white/[0.02]">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{ds.icon}</span>
                      <h3 className="font-semibold">{ds.name}</h3>
                      <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-[#13C636]/20 text-[#13C636]">● Active</span>
                    </div>
                    <p className="text-white/50 text-sm mb-2">{ds.desc}</p>
                    <div className="flex flex-wrap gap-1">
                      {ds.modules.map(m => (
                        <span key={m} className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-white/40 font-mono">{m}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Progress Bar */}
            <div>
              <h2 className="text-2xl font-bold mb-4">🏗️ Build Progress</h2>
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <div className="flex justify-between mb-2 text-sm">
                  <span className="text-white/60">Phase {doneCount} of {phases.length}</span>
                  <span className="text-[#13C636] font-bold">{Math.round(doneCount / phases.length * 100)}%</span>
                </div>
                <div className="h-4 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-[#13C636] to-[#C0E8FD] rounded-full transition-all" style={{ width: `${doneCount / phases.length * 100}%` }} />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
                  {roadmapCategories.map(cat => {
                    const catPhases = phases.filter(p => p.category === cat);
                    const catDone = catPhases.filter(p => p.status === "done").length;
                    return (
                      <div key={cat} className="text-center">
                        <div className="text-lg font-bold text-white/80">{catDone}/{catPhases.length}</div>
                        <div className="text-xs text-white/40">{cat}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* MCP Integration */}
            <div>
              <h2 className="text-2xl font-bold mb-4">🔌 MCP Integration</h2>
              <p className="text-white/60 mb-4">Add QuantClaw Data to any AI agent with a single config. Every module is a callable tool.</p>
              <pre className="bg-black/60 border border-white/10 rounded-xl p-5 text-sm overflow-x-auto text-white/80">
{JSON.stringify({ mcpServers: { "quantclaw-data": { command: "python", args: ["/path/to/financial-data-pipeline/mcp_server.py"], env: { CACHE_DIR: "/tmp/quantclaw-cache" }}}}, null, 2)}
              </pre>
              <p className="text-white/40 text-xs mt-3">HTTP API: <code className="text-[#13C636]">data.quantclaw.org/api/v1/&#123;tool&#125;?ticker=AAPL</code></p>
            </div>

            {/* How Ideas Are Generated */}
            <div>
              <h2 className="text-2xl font-bold mb-4">💡 {ideaGeneration.title}</h2>
              <p className="text-white/60 mb-4">QuantClaw Data is a self-evolving platform. After each phase, the AI build agent suggests new features — compounding innovation autonomously.</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {ideaGeneration.process.map((p, i) => (
                  <div key={i} className="border border-white/10 rounded-xl p-4 bg-white/[0.02]">
                    <div className="text-lg mb-1">{p.step}</div>
                    <p className="text-white/50 text-sm">{p.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Modules Tab */}
      {activeTab === "modules" && (
        <section className="px-6 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <input type="text" placeholder="Search modules..." value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:border-[#13C636] focus:outline-none" />
            </div>
            <div className="flex flex-wrap gap-2 mb-8">
              <button onClick={() => handleCategoryChange(null)}
                className={`px-4 py-2 rounded-full text-sm transition ${!activeCategory ? "bg-[#13C636] text-black font-semibold" : "bg-white/5 text-white/60 hover:bg-white/10"}`}>
                All ({services.length})
              </button>
              {categories.map(c => {
                const count = services.filter(s => s.category === c.id).length;
                if (!count) return null;
                return (
                  <button key={c.id} onClick={() => handleCategoryChange(activeCategory === c.id ? null : c.id)}
                    className={`px-4 py-2 rounded-full text-sm transition ${activeCategory === c.id ? "bg-[#13C636] text-black font-semibold" : "bg-white/5 text-white/60 hover:bg-white/10"}`}>
                    {c.icon} {c.name} ({count})
                  </button>
                );
              })}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map(s => <ServiceCard key={s.id} s={s} />)}
            </div>
          </div>
        </section>
      )}

      {/* Roadmap Tab */}
      {activeTab === "roadmap" && (
        <section className="px-6 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">🗺️ Full Roadmap — {phases.length} Phases</h2>
              <p className="text-white/60">Each phase is built autonomously by an AI agent every 30 minutes. After completing a phase, the agent suggests 3 new features — the roadmap grows itself.</p>
            </div>

            {/* Category Filter */}
            <div className="flex flex-wrap gap-2 mb-6">
              <button onClick={() => handleRoadmapFilter(null)}
                className={`px-3 py-1.5 rounded-full text-xs transition ${!roadmapFilter ? "bg-[#13C636] text-black font-semibold" : "bg-white/5 text-white/60 hover:bg-white/10"}`}>
                All ({phases.length})
              </button>
              {roadmapCategories.map(cat => (
                <button key={cat} onClick={() => handleRoadmapFilter(roadmapFilter === cat ? null : cat)}
                  className={`px-3 py-1.5 rounded-full text-xs transition ${roadmapFilter === cat ? "bg-[#13C636] text-black font-semibold" : "bg-white/5 text-white/60 hover:bg-white/10"}`}>
                  {cat} ({phases.filter(p => p.category === cat).length})
                </button>
              ))}
            </div>

            {/* Roadmap Timeline */}
            <div className="space-y-2">
              {filteredPhases.map(p => (
                <div key={p.id} className={`flex items-start gap-4 p-4 rounded-xl border transition ${
                  p.status === "done" ? "border-[#13C636]/30 bg-[#13C636]/5" :
                  p.status === "next" ? "border-[#FFD700]/50 bg-[#FFD700]/10 ring-1 ring-[#FFD700]/30" :
                  "border-white/5 bg-white/[0.01]"
                }`}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
                    p.status === "done" ? "bg-[#13C636] text-black" :
                    p.status === "next" ? "bg-[#FFD700] text-black animate-pulse" :
                    "bg-white/10 text-white/40"
                  }`}>
                    {p.status === "done" ? "✓" : p.id}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className={`font-semibold ${p.status === "done" ? "text-[#13C636]" : p.status === "next" ? "text-[#FFD700]" : "text-white/70"}`}>
                        Phase {p.id}: {p.name}
                      </h3>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40">{p.category}</span>
                      {p.loc && <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">{p.loc} LOC</span>}
                      {p.status === "next" && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFD700]/20 text-[#FFD700] font-bold">BUILDING NEXT</span>}
                    </div>
                    <p className="text-white/50 text-sm mt-1">{p.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Self-Evolution Explanation */}
            <div className="mt-8 p-6 rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.03] to-white/[0.01]">
              <h3 className="text-xl font-bold mb-3">🧬 Self-Evolving Architecture</h3>
              <p className="text-white/60 mb-4">QuantClaw Data grows autonomously. Here&apos;s how:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <span className="text-[#13C636] text-lg">1.</span>
                    <div>
                      <p className="font-medium">Cron triggers every 30 min</p>
                      <p className="text-white/40 text-sm">An isolated Sonnet agent spins up</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-[#13C636] text-lg">2.</span>
                    <div>
                      <p className="font-medium">Reads BUILD_QUEUE.md</p>
                      <p className="text-white/40 text-sm">Finds the next unchecked phase</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-[#13C636] text-lg">3.</span>
                    <div>
                      <p className="font-medium">Builds the module</p>
                      <p className="text-white/40 text-sm">Writes Python, tests it, integrates with CLI</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <span className="text-[#C0E8FD] text-lg">4.</span>
                    <div>
                      <p className="font-medium">Marks phase complete</p>
                      <p className="text-white/40 text-sm">Updates BUILD_QUEUE.md, increments counter</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-[#C0E8FD] text-lg">5.</span>
                    <div>
                      <p className="font-medium">Suggests 3 new features</p>
                      <p className="text-white/40 text-sm">Based on what it just built — compounding ideas</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-[#C0E8FD] text-lg">6.</span>
                    <div>
                      <p className="font-medium">Announces to team</p>
                      <p className="text-white/40 text-sm">Posts summary to WhatsApp monitoring group</p>
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-white/40 text-sm mt-4 italic">Cost per phase: ~$0.15 (Sonnet) | Build time: ~5 min | The roadmap started at 24 phases and has grown to {phases.length}+ autonomously.</p>
            </div>
          </div>
        </section>
      )}

      {/* Install & Use Tab */}
      {activeTab === "install" && (
        <section className="px-6 py-8">
          <div className="max-w-6xl mx-auto space-y-10">

            {/* Hero Install Banner */}
            <div className="text-center bg-gradient-to-r from-[#13C636]/10 to-[#C0E8FD]/10 rounded-2xl p-8 border border-[#13C636]/30">
              <h2 className="text-3xl font-bold mb-3">⚡ Get Started in 60 Seconds</h2>
              <p className="text-white/60 text-lg mb-6">Full financial intelligence platform — {doneCount} modules, 100+ CLI commands, REST API, MCP-ready</p>
              <div className="inline-flex gap-4">
                <a href="https://github.com/yoniassia/quantclaw-data" target="_blank" className="px-6 py-3 bg-[#13C636] text-black font-bold rounded-lg hover:bg-[#13C636]/80 transition">
                  ⬇️ Download from GitHub
                </a>
                <a href="#cli-ref" onClick={(e) => { e.preventDefault(); document.getElementById('cli-ref')?.scrollIntoView({ behavior: 'smooth' }); }} className="px-6 py-3 border border-white/20 text-white rounded-lg hover:bg-white/5 transition">
                  📖 CLI Reference
                </a>
              </div>
            </div>

            {/* Quick Install */}
            <div>
              <h3 className="text-2xl font-bold mb-6">🔧 Installation</h3>
              <div className="space-y-4">
                {installSteps.map((s) => (
                  <div key={s.step} className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="w-8 h-8 rounded-full bg-[#13C636] text-black font-bold flex items-center justify-center text-sm">{s.step}</span>
                      <h4 className="font-semibold text-lg">{s.title}</h4>
                    </div>
                    <pre className="bg-black/60 rounded-lg p-4 text-sm text-[#13C636] font-mono overflow-x-auto whitespace-pre-wrap">{s.code}</pre>
                  </div>
                ))}
              </div>
            </div>

            {/* MCP Configuration */}
            <div>
              <h3 className="text-2xl font-bold mb-4">🤖 MCP Server (for AI Agents)</h3>
              <p className="text-white/60 mb-4">{mcpConfig.description}</p>
              <pre className="bg-black/60 rounded-lg p-4 text-sm text-[#C0E8FD] font-mono overflow-x-auto whitespace-pre-wrap">{mcpConfig.config}</pre>
              <p className="text-white/40 text-sm mt-3">Or use the REST API directly: <code className="text-[#13C636]">{mcpConfig.apiBase}/[tool]?symbol=AAPL</code></p>
            </div>

            {/* REST API Endpoints */}
            <div>
              <h3 className="text-2xl font-bold mb-4">🌐 REST API Endpoints</h3>
              <p className="text-white/60 mb-4">All endpoints return JSON. Base URL: <code className="text-[#13C636]">{mcpConfig.apiBase}</code></p>
              <div className="grid gap-2">
                {apiEndpoints.map((ep, i) => (
                  <div key={i} className="flex items-center gap-3 bg-white/[0.02] rounded-lg px-4 py-2 hover:bg-white/[0.05] transition group">
                    <span className="text-xs px-2 py-0.5 rounded bg-[#13C636]/20 text-[#13C636] font-mono">GET</span>
                    <code className="text-xs text-[#C0E8FD] font-mono flex-1 truncate">{ep.path}</code>
                    <span className="text-xs text-white/40">{ep.description}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Full CLI Reference */}
            <div id="cli-ref">
              <h3 className="text-2xl font-bold mb-2">📖 Complete CLI Reference</h3>
              <p className="text-white/60 mb-6">All {cliReference.reduce((a, c) => a + c.commands.length, 0)}+ commands — copy and run</p>
              <div className="space-y-6">
                {cliReference.map((cat) => (
                  <div key={cat.category} className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-white/10 bg-white/[0.03]">
                      <h4 className="font-semibold">{cat.category}</h4>
                    </div>
                    <div className="divide-y divide-white/5">
                      {cat.commands.map((c, i) => (
                        <div key={i} className="flex items-center px-5 py-2.5 hover:bg-white/[0.03] transition group cursor-pointer"
                          onClick={() => { navigator.clipboard.writeText(`python cli.py ${c.cmd}`); setCopiedCmd(c.cmd); setTimeout(() => setCopiedCmd(null), 2000); }}>
                          <code className="text-sm text-[#13C636] font-mono flex-1">python cli.py {c.cmd}</code>
                          <span className="text-xs text-white/40 mr-3">{c.description}</span>
                          <span className="text-xs text-white/20 group-hover:text-[#13C636] transition">
                            {copiedCmd === c.cmd ? "✅ copied" : "📋"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* DSL Quick Reference */}
            <div>
              <h3 className="text-2xl font-bold mb-4">🔤 Alert DSL Quick Reference</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
                  <h4 className="font-semibold text-[#13C636] mb-3">Operators</h4>
                  <div className="space-y-1 text-sm font-mono">
                    <p className="text-white/60"><span className="text-white">AND / OR</span> — Logical</p>
                    <p className="text-white/60"><span className="text-white">&gt; &lt; &gt;= &lt;= == !=</span> — Comparison</p>
                    <p className="text-white/60"><span className="text-white">crosses_above / crosses_below</span> — Crossover</p>
                  </div>
                </div>
                <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
                  <h4 className="font-semibold text-[#C0E8FD] mb-3">Indicators</h4>
                  <div className="space-y-1 text-sm font-mono">
                    <p className="text-white/60"><span className="text-white">price, volume, rsi</span> — Basic</p>
                    <p className="text-white/60"><span className="text-white">sma(20), ema(12), macd</span> — Moving averages</p>
                    <p className="text-white/60"><span className="text-white">change_pct(5d), atr, obv</span> — Advanced</p>
                  </div>
                </div>
                <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5 md:col-span-2">
                  <h4 className="font-semibold text-[#FFD700] mb-3">Examples</h4>
                  <div className="space-y-2 text-sm font-mono">
                    <p><span className="text-[#13C636]">python cli.py dsl-eval AAPL</span> <span className="text-white">&quot;price &gt; 200 AND rsi &lt; 30&quot;</span></p>
                    <p><span className="text-[#13C636]">python cli.py dsl-eval TSLA</span> <span className="text-white">&quot;sma(20) crosses_above sma(50)&quot;</span></p>
                    <p><span className="text-[#13C636]">python cli.py dsl-scan</span> <span className="text-white">&quot;rsi &lt; 25 AND volume &gt; 10M&quot; --universe SP500</span></p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="border-t border-white/10 px-6 py-8 text-center text-white/30 text-sm mt-8">
        <p>Built by <span className="text-[#13C636]">QuantClaw</span> — Autonomous Financial Intelligence</p>
        <p className="mt-1">Part of the <a href="https://moneyclaw.com" className="text-[#C0E8FD] hover:underline">MoneyClaw</a> ecosystem • {totalLoc.toLocaleString()} lines of code • {doneCount} modules live</p>
      </footer>
    </div>
  );
}
