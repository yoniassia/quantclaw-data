'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

interface DisplayHint {
  type: 'table' | 'bar_chart' | 'line_chart' | 'area_chart' | 'pie_chart' | 'number' | 'text';
  xAxis?: string;
  yAxis?: string | string[];
  title?: string;
}

interface QueryResult {
  answer: string;
  sql: string;
  data: Record<string, unknown>[];
  fields: { name: string; dataTypeID: number }[];
  rowCount: number;
  truncated: boolean;
  displayHint: DisplayHint;
  conversationId: string;
  error?: string;
}

interface ConversationMeta {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turnCount: number;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  data?: Record<string, unknown>[];
  fields?: { name: string; dataTypeID: number }[];
  rowCount?: number;
  truncated?: boolean;
  displayHint?: DisplayHint;
  error?: string;
  loading?: boolean;
}

const CHART_COLORS = ['#00d4ff', '#a855f7', '#ffd700', '#22c55e', '#ef4444', '#f97316', '#06b6d4', '#8b5cf6', '#ec4899', '#84cc16'];

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'number') {
    if (Math.abs(val) >= 1e9) return (val / 1e9).toFixed(2) + 'B';
    if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(2) + 'M';
    if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(1) + 'K';
    if (Number.isInteger(val)) return val.toLocaleString();
    return val.toFixed(4);
  }
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}

function DataTable({ data, fields }: { data: Record<string, unknown>[]; fields: { name: string }[] }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const columnHelper = createColumnHelper<Record<string, unknown>>();

  const columns = useMemo(() => {
    if (!fields.length) return [];
    return fields.map(f =>
      columnHelper.accessor(row => row[f.name], {
        id: f.name,
        header: f.name,
        cell: info => formatValue(info.getValue()),
        sortingFn: (a, b, colId) => {
          const av = a.getValue(colId);
          const bv = b.getValue(colId);
          if (av === null || av === undefined) return 1;
          if (bv === null || bv === undefined) return -1;
          if (typeof av === 'number' && typeof bv === 'number') return av - bv;
          return String(av).localeCompare(String(bv));
        },
      })
    );
  }, [fields]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, globalFilter },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div>
      <input
        type="text"
        placeholder="Filter results..."
        value={globalFilter}
        onChange={e => setGlobalFilter(e.target.value)}
        style={{
          width: '100%',
          padding: '8px 12px',
          marginBottom: 8,
          background: 'rgba(0,0,0,0.3)',
          border: '1px solid var(--terminal-panel-border)',
          color: 'var(--terminal-text)',
          fontFamily: 'inherit',
          fontSize: 12,
          outline: 'none',
        }}
      />
      <div style={{ overflowX: 'auto', maxHeight: 500 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => (
                  <th
                    key={h.id}
                    onClick={h.column.getToggleSortingHandler()}
                    style={{
                      padding: '8px 10px',
                      textAlign: 'left',
                      background: 'rgba(0,212,255,0.08)',
                      color: 'var(--terminal-blue)',
                      cursor: 'pointer',
                      userSelect: 'none',
                      borderBottom: '1px solid var(--terminal-panel-border)',
                      fontSize: 10,
                      letterSpacing: 1,
                      textTransform: 'uppercase',
                      whiteSpace: 'nowrap',
                      position: 'sticky',
                      top: 0,
                    }}
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {{ asc: ' ▲', desc: ' ▼' }[h.column.getIsSorted() as string] ?? ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    style={{
                      padding: '6px 10px',
                      whiteSpace: 'nowrap',
                      color: 'var(--terminal-text)',
                      maxWidth: 300,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DataChart({ data, hint }: { data: Record<string, unknown>[]; hint: DisplayHint }) {
  const xKey = hint.xAxis || (data[0] ? Object.keys(data[0])[0] : '');
  const yKeys = hint.yAxis
    ? (Array.isArray(hint.yAxis) ? hint.yAxis : [hint.yAxis])
    : (data[0] ? Object.keys(data[0]).filter(k => k !== xKey).slice(0, 5) : []);

  const chartData = data.map(row => {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(row)) {
      out[k] = typeof v === 'string' && !isNaN(Number(v)) ? Number(v) : v;
    }
    return out;
  });

  const commonProps = {
    data: chartData,
    margin: { top: 10, right: 30, left: 10, bottom: 10 },
  };

  if (hint.type === 'pie_chart') {
    return (
      <div>
        {hint.title && <div style={{ color: 'var(--terminal-blue)', fontSize: 12, marginBottom: 8, fontWeight: 600 }}>{hint.title}</div>}
        <ResponsiveContainer width="100%" height={350}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey={yKeys[0]}
              nameKey={xKey}
              cx="50%"
              cy="50%"
              outerRadius={120}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(0,212,255,0.3)', color: '#e0e8f0' }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  const ChartComp = hint.type === 'area_chart' ? AreaChart : hint.type === 'bar_chart' ? BarChart : LineChart;
  const DataComp = hint.type === 'area_chart' ? Area : hint.type === 'bar_chart' ? Bar : Line;

  return (
    <div>
      {hint.title && <div style={{ color: 'var(--terminal-blue)', fontSize: 12, marginBottom: 8, fontWeight: 600 }}>{hint.title}</div>}
      <ResponsiveContainer width="100%" height={350}>
        <ChartComp {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey={xKey}
            tick={{ fill: 'rgba(224,232,240,0.5)', fontSize: 10 }}
            tickLine={false}
          />
          <YAxis tick={{ fill: 'rgba(224,232,240,0.5)', fontSize: 10 }} tickLine={false} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(0,212,255,0.3)', color: '#e0e8f0', fontSize: 12 }} />
          <Legend />
          {yKeys.map((key, i) => {
            const color = CHART_COLORS[i % CHART_COLORS.length];
            const props: Record<string, unknown> = {
              key,
              dataKey: key,
              stroke: color,
              fill: color,
              name: key,
            };
            if (hint.type === 'area_chart') props.fillOpacity = 0.2;
            if (hint.type === 'bar_chart') props.fillOpacity = 0.8;
            if (hint.type === 'line_chart') {
              props.dot = false;
              props.strokeWidth = 2;
            }
            return <DataComp {...props} />;
          })}
        </ChartComp>
      </ResponsiveContainer>
    </div>
  );
}

function ResultDisplay({ msg }: { msg: ChatMessage }) {
  const [showSql, setShowSql] = useState(false);
  const [viewMode, setViewMode] = useState<'auto' | 'table' | 'chart'>('auto');

  const isChartHint = msg.displayHint && ['bar_chart', 'line_chart', 'area_chart', 'pie_chart'].includes(msg.displayHint.type);
  const hasData = msg.data && msg.data.length > 0;
  const fields = msg.fields || [];

  const exportCSV = useCallback(() => {
    if (!msg.data || !fields.length) return;
    const headers = fields.map(f => f.name).join(',');
    const rows = msg.data.map(row => fields.map(f => {
      const v = row[f.name];
      const s = v === null || v === undefined ? '' : String(v);
      return s.includes(',') ? `"${s}"` : s;
    }).join(','));
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [msg.data, fields]);

  const actualView = viewMode === 'auto' ? (isChartHint ? 'chart' : 'table') : viewMode;

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ color: 'var(--terminal-text)', fontSize: 13, marginBottom: 8, lineHeight: 1.5 }}>
        {msg.content}
      </div>

      {msg.error && (
        <div style={{ padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: 12, marginBottom: 8 }}>
          {msg.error}
        </div>
      )}

      {hasData && (
        <>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.5)' }}>
              {msg.rowCount} row{msg.rowCount !== 1 ? 's' : ''}{msg.truncated ? ' (truncated)' : ''}
            </span>
            <div style={{ flex: 1 }} />
            {isChartHint && (
              <>
                <button onClick={() => setViewMode(viewMode === 'table' ? 'auto' : 'table')} style={toggleBtnStyle(actualView === 'table')}>
                  Table
                </button>
                <button onClick={() => setViewMode(viewMode === 'chart' ? 'auto' : 'chart')} style={toggleBtnStyle(actualView === 'chart')}>
                  Chart
                </button>
              </>
            )}
            <button onClick={exportCSV} style={actionBtnStyle}>
              ↓ CSV
            </button>
            <button onClick={() => setShowSql(!showSql)} style={actionBtnStyle}>
              {showSql ? 'Hide' : 'Show'} SQL
            </button>
          </div>

          {actualView === 'chart' && msg.displayHint ? (
            <DataChart data={msg.data!} hint={msg.displayHint} />
          ) : (
            <DataTable data={msg.data!} fields={fields} />
          )}
        </>
      )}

      {!hasData && msg.displayHint?.type === 'number' && msg.data && (
        <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--terminal-blue)', padding: '16px 0' }}>
          {msg.data.length ? formatValue(Object.values(msg.data[0])[0]) : '0'}
        </div>
      )}

      {showSql && msg.sql && (
        <pre style={{
          marginTop: 8,
          padding: 12,
          background: 'rgba(0,0,0,0.4)',
          border: '1px solid var(--terminal-panel-border)',
          color: '#94a3b8',
          fontSize: 11,
          overflow: 'auto',
          maxHeight: 200,
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
        }}>
          {msg.sql}
        </pre>
      )}
    </div>
  );
}

const toggleBtnStyle = (active: boolean): React.CSSProperties => ({
  padding: '3px 10px',
  fontSize: 10,
  background: active ? 'rgba(0,212,255,0.15)' : 'transparent',
  border: `1px solid ${active ? 'var(--terminal-blue)' : 'var(--terminal-panel-border)'}`,
  color: active ? 'var(--terminal-blue)' : 'rgba(224,232,240,0.5)',
  cursor: 'pointer',
  fontFamily: 'inherit',
});

const actionBtnStyle: React.CSSProperties = {
  padding: '3px 10px',
  fontSize: 10,
  background: 'transparent',
  border: '1px solid var(--terminal-panel-border)',
  color: 'rgba(224,232,240,0.5)',
  cursor: 'pointer',
  fontFamily: 'inherit',
};

const SUGGESTED_QUERIES = [
  'Show me the top 10 stocks by GF score',
  'Which stocks had the most insider buying in the last 30 days?',
  'What modules failed in the last 24 hours?',
  'Show the sector distribution of stocks in our universe',
  'List undervalued stocks where price_to_gf < 0.8',
  'How many data points were ingested per module today?',
];

export default function NLQueryView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationMeta[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const res = await fetch('/api/dcc/nl-query/conversations');
      const data = await res.json();
      setConversations(data.conversations || []);
    } catch {}
  };

  const loadConversation = async (id: string) => {
    try {
      const res = await fetch(`/api/dcc/nl-query/conversations?id=${id}`);
      const data = await res.json();
      const msgs: ChatMessage[] = (data.turns || []).map((t: { role: string; content: string; sql?: string; displayHint?: string }) => ({
        role: t.role,
        content: t.content,
        sql: t.sql,
        displayHint: t.displayHint ? JSON.parse(t.displayHint) : undefined,
      }));
      setMessages(msgs);
      setConversationId(id);
      setShowHistory(false);
    } catch {}
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
    setInput('');
    inputRef.current?.focus();
  };

  const submitQuery = async (question?: string) => {
    const q = (question || input).trim();
    if (!q || loading) return;

    setInput('');
    const userMsg: ChatMessage = { role: 'user', content: q };
    const loadingMsg: ChatMessage = { role: 'assistant', content: 'Analyzing your question and generating SQL...', loading: true };
    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setLoading(true);

    try {
      const res = await fetch('/api/dcc/nl-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, conversationId }),
      });
      const result: QueryResult = await res.json();

      if (!conversationId) setConversationId(result.conversationId);

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: result.answer,
        sql: result.sql,
        data: result.data,
        fields: result.fields,
        rowCount: result.rowCount,
        truncated: result.truncated,
        displayHint: result.displayHint,
        error: result.error,
      };

      setMessages(prev => [...prev.slice(0, -1), assistantMsg]);
      fetchConversations();
    } catch (err) {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`, error: String(err) },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuery();
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Sidebar */}
      <div style={{
        width: showHistory ? 280 : 0,
        minWidth: showHistory ? 280 : 0,
        overflow: 'hidden',
        transition: 'width 0.2s, min-width 0.2s',
        borderRight: showHistory ? '1px solid var(--terminal-panel-border)' : 'none',
        background: 'var(--terminal-panel-bg)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--terminal-panel-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--terminal-blue)', fontWeight: 600, letterSpacing: 1 }}>HISTORY</span>
          <button onClick={newConversation} style={{ ...actionBtnStyle, color: 'var(--terminal-blue)', borderColor: 'var(--terminal-blue)' }}>
            + New
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
          {conversations.map(c => (
            <button
              key={c.id}
              onClick={() => loadConversation(c.id)}
              style={{
                display: 'block',
                width: '100%',
                padding: '8px 16px',
                background: c.id === conversationId ? 'rgba(0,212,255,0.08)' : 'transparent',
                border: 'none',
                borderLeft: c.id === conversationId ? '2px solid var(--terminal-blue)' : '2px solid transparent',
                color: 'var(--terminal-text)',
                textAlign: 'left',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontSize: 11,
              }}
            >
              <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</div>
              <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.3)', marginTop: 2 }}>
                {new Date(c.updatedAt).toLocaleDateString()} · {c.turnCount} turns
              </div>
            </button>
          ))}
          {conversations.length === 0 && (
            <div style={{ padding: 16, fontSize: 11, color: 'rgba(224,232,240,0.3)', textAlign: 'center' }}>No conversations yet</div>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{
          padding: '10px 20px',
          borderBottom: '1px solid var(--terminal-panel-border)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <button onClick={() => setShowHistory(!showHistory)} style={{ ...actionBtnStyle, fontSize: 14, padding: '2px 8px' }}>
            ☰
          </button>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--terminal-blue)', letterSpacing: 1 }}>
            NL QUERY
          </span>
          <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)' }}>
            Ask questions about your financial data in plain English
          </span>
          <div style={{ flex: 1 }} />
          <button onClick={newConversation} style={actionBtnStyle}>
            New Chat
          </button>
        </div>

        {/* Messages area */}
        <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px' }}>
          {messages.length === 0 ? (
            <div style={{ maxWidth: 700, margin: '40px auto' }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--terminal-blue)', marginBottom: 8 }}>
                Query your data with natural language
              </div>
              <div style={{ fontSize: 12, color: 'rgba(224,232,240,0.5)', marginBottom: 24, lineHeight: 1.6 }}>
                Ask questions about financial data, module status, rankings, insider trades, and more.
                Results are returned as interactive tables or charts.
              </div>
              <div style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)', letterSpacing: 1, marginBottom: 12, textTransform: 'uppercase' }}>
                Suggested queries
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {SUGGESTED_QUERIES.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(q); submitQuery(q); }}
                    style={{
                      padding: '8px 14px',
                      background: 'rgba(0,212,255,0.05)',
                      border: '1px solid rgba(0,212,255,0.15)',
                      color: 'var(--terminal-text)',
                      cursor: 'pointer',
                      fontFamily: 'inherit',
                      fontSize: 11,
                      transition: 'all 0.15s',
                      textAlign: 'left',
                    }}
                    onMouseOver={e => {
                      (e.target as HTMLButtonElement).style.borderColor = 'var(--terminal-blue)';
                      (e.target as HTMLButtonElement).style.background = 'rgba(0,212,255,0.1)';
                    }}
                    onMouseOut={e => {
                      (e.target as HTMLButtonElement).style.borderColor = 'rgba(0,212,255,0.15)';
                      (e.target as HTMLButtonElement).style.background = 'rgba(0,212,255,0.05)';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  marginBottom: 16,
                  padding: msg.role === 'user' ? '10px 16px' : '12px 16px',
                  background: msg.role === 'user' ? 'rgba(0,212,255,0.05)' : 'transparent',
                  borderLeft: msg.role === 'user' ? '3px solid var(--terminal-blue)' : '3px solid rgba(168,85,247,0.4)',
                  maxWidth: '100%',
                }}
              >
                <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.4)', marginBottom: 4, letterSpacing: 1, textTransform: 'uppercase' }}>
                  {msg.role === 'user' ? 'YOU' : 'DCC'}
                </div>
                {msg.role === 'user' ? (
                  <div style={{ color: 'var(--terminal-text)', fontSize: 13 }}>{msg.content}</div>
                ) : msg.loading ? (
                  <div style={{ color: 'rgba(224,232,240,0.5)', fontSize: 12, fontStyle: 'italic' }}>
                    ⏳ {msg.content}
                  </div>
                ) : (
                  <ResultDisplay msg={msg} />
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div style={{
          padding: '12px 20px',
          borderTop: '1px solid var(--terminal-panel-border)',
          background: 'var(--terminal-panel-bg)',
        }}>
          <div style={{ display: 'flex', gap: 8, maxWidth: '100%' }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your data... (Enter to send, Shift+Enter for newline)"
              rows={2}
              style={{
                flex: 1,
                padding: '10px 14px',
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid var(--terminal-panel-border)',
                color: 'var(--terminal-text)',
                fontFamily: 'inherit',
                fontSize: 13,
                resize: 'none',
                outline: 'none',
              }}
              onFocus={e => { e.target.style.borderColor = 'var(--terminal-blue)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--terminal-panel-border)'; }}
            />
            <button
              onClick={() => submitQuery()}
              disabled={loading || !input.trim()}
              style={{
                padding: '10px 20px',
                background: loading || !input.trim() ? 'rgba(0,212,255,0.1)' : 'rgba(0,212,255,0.2)',
                border: `1px solid ${loading || !input.trim() ? 'var(--terminal-panel-border)' : 'var(--terminal-blue)'}`,
                color: loading || !input.trim() ? 'rgba(224,232,240,0.3)' : 'var(--terminal-blue)',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
                fontSize: 12,
                fontWeight: 600,
                letterSpacing: 1,
                alignSelf: 'stretch',
              }}
            >
              {loading ? '...' : 'QUERY'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
