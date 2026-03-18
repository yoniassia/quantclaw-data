'use client';

import { useEffect, useState, useCallback } from 'react';
import { useDCCStore, Module, DCCView, ModuleDetail } from '@/store/dcc-store';

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div style={{
      background: 'var(--terminal-panel-bg)',
      border: '1px solid var(--terminal-panel-border)',
      padding: '14px 16px',
      flex: '1 1 160px',
      minWidth: 140,
    }}>
      <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.5)', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: color ?? 'var(--terminal-blue)' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function TierBar({ tiers }: { tiers: { bronze: number; silver: number; gold: number; platinum: number; none: number } }) {
  const total = tiers.bronze + tiers.silver + tiers.gold + tiers.platinum + tiers.none;
  if (total === 0) return null;
  const segments = [
    { key: 'platinum', count: tiers.platinum, color: '#a855f7' },
    { key: 'gold', count: tiers.gold, color: '#ffd700' },
    { key: 'silver', count: tiers.silver, color: '#94a3b8' },
    { key: 'bronze', count: tiers.bronze, color: '#cd7f32' },
    { key: 'none', count: tiers.none, color: '#374151' },
  ];
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', height: 8, borderRadius: 4, overflow: 'hidden', marginBottom: 8 }}>
        {segments.map(s => s.count > 0 && (
          <div key={s.key} style={{ width: `${(s.count / total) * 100}%`, background: s.color }} title={`${s.key}: ${s.count}`} />
        ))}
      </div>
      <div style={{ display: 'flex', gap: 16, fontSize: 10, flexWrap: 'wrap' }}>
        {segments.map(s => s.count > 0 && (
          <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: s.color }} />
            <span style={{ color: 'rgba(224,232,240,0.6)', textTransform: 'capitalize' }}>{s.key}</span>
            <span style={{ color: 'var(--terminal-text)', fontWeight: 600 }}>{s.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const TIER_COLORS: Record<string, string> = {
  gold: '#ffd700', platinum: '#a855f7', silver: '#94a3b8', bronze: '#cd7f32', none: '#374151',
};

const CADENCE_ORDER = ['realtime', '1min', '5min', '15min', '1h', '4h', 'daily', 'weekly', 'monthly', 'quarterly'];

function ModuleHeatmap({ modules }: { modules: Module[] }) {
  const grouped = new Map<string, Module[]>();
  for (const m of modules) {
    const key = m.cadence;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(m);
  }

  const sortedKeys = [...grouped.keys()].sort((a, b) => {
    const ai = CADENCE_ORDER.indexOf(a);
    const bi = CADENCE_ORDER.indexOf(b);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {sortedKeys.map(cadence => {
        const mods = grouped.get(cadence)!;
        return (
          <div key={cadence}>
            <div style={{ fontSize: 10, color: 'var(--terminal-blue)', fontWeight: 600, letterSpacing: 1, marginBottom: 6, textTransform: 'uppercase' }}>
              {cadence} <span style={{ color: 'rgba(224,232,240,0.4)', fontWeight: 400 }}>({mods.length})</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              {mods.map(m => {
                const hasError = m.consecutive_failures > 0;
                const bg = hasError ? 'var(--terminal-red)' : (TIER_COLORS[m.current_tier] ?? '#374151');
                return (
                  <div
                    key={m.id}
                    title={`${m.name}\nTier: ${m.current_tier}\nQuality: ${m.quality_score}\nErrors: ${m.error_count}${hasError ? '\n⚠ FAILING' : ''}`}
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: 1,
                      background: bg,
                      opacity: m.is_active ? (hasError ? 1 : 0.85) : 0.3,
                      cursor: 'pointer',
                      transition: 'transform 0.1s',
                    }}
                    onMouseEnter={(e) => { (e.target as HTMLElement).style.transform = 'scale(2.5)'; }}
                    onMouseLeave={(e) => { (e.target as HTMLElement).style.transform = 'scale(1)'; }}
                  />
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PipelineFeed() {
  const { recentRuns } = useDCCStore();
  const statusColors: Record<string, string> = {
    success: 'var(--terminal-green)',
    failed: 'var(--terminal-red)',
    running: 'var(--terminal-blue)',
    retrying: 'var(--terminal-yellow)',
    queued: 'rgba(224,232,240,0.4)',
  };

  return (
    <div style={{ maxHeight: 400, overflow: 'auto' }}>
      {recentRuns.length === 0 && (
        <div style={{ color: 'rgba(224,232,240,0.4)', fontSize: 11, padding: 16 }}>No recent pipeline runs</div>
      )}
      {recentRuns.map(run => (
        <div key={run.id} style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '6px 0',
          borderBottom: '1px solid rgba(26,35,64,0.5)',
          fontSize: 11,
        }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: statusColors[run.status] ?? 'rgba(224,232,240,0.4)',
            flexShrink: 0,
          }} />
          <div style={{ flex: 1, color: 'var(--terminal-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {run.module_name}
          </div>
          <div style={{ color: 'rgba(224,232,240,0.4)', fontSize: 10, flexShrink: 0 }}>
            {run.tier_target}
          </div>
          <div style={{ color: statusColors[run.status], fontWeight: 600, fontSize: 10, flexShrink: 0, width: 55, textAlign: 'right' }}>
            {run.status.toUpperCase()}
          </div>
          {run.duration_ms != null && (
            <div style={{ color: 'rgba(224,232,240,0.4)', fontSize: 10, flexShrink: 0, width: 55, textAlign: 'right' }}>
              {run.duration_ms < 1000 ? `${run.duration_ms}ms` : `${(run.duration_ms / 1000).toFixed(1)}s`}
            </div>
          )}
          <div style={{ color: 'rgba(224,232,240,0.3)', fontSize: 9, flexShrink: 0, width: 60, textAlign: 'right' }}>
            {run.started_at ? new Date(run.started_at).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }) : ''}
          </div>
        </div>
      ))}
    </div>
  );
}

function AlertsFeed() {
  const { alerts, resolveAlert } = useDCCStore();
  const sevColors: Record<string, string> = {
    critical: 'var(--terminal-red)',
    warning: 'var(--terminal-yellow)',
    info: 'var(--terminal-blue)',
  };

  return (
    <div style={{ maxHeight: 300, overflow: 'auto' }}>
      {alerts.length === 0 && (
        <div style={{ color: 'var(--terminal-green)', fontSize: 11, padding: 16 }}>✓ No active alerts</div>
      )}
      {alerts.map(alert => (
        <div key={alert.id} style={{
          padding: '8px 0',
          borderBottom: '1px solid rgba(26,35,64,0.5)',
          borderLeft: `3px solid ${sevColors[alert.severity] ?? 'rgba(224,232,240,0.4)'}`,
          paddingLeft: 10,
          marginBottom: 4,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 9, fontWeight: 700, color: sevColors[alert.severity], textTransform: 'uppercase' }}>
                {alert.severity}
              </span>
              {alert.module_name && (
                <span style={{ fontSize: 10, color: 'var(--terminal-blue)' }}>{alert.module_name}</span>
              )}
            </div>
            <button
              onClick={() => resolveAlert(alert.id)}
              style={{
                background: 'transparent',
                border: '1px solid rgba(224,232,240,0.2)',
                color: 'rgba(224,232,240,0.5)',
                fontSize: 9,
                padding: '2px 8px',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              RESOLVE
            </button>
          </div>
          <div style={{ fontSize: 11, color: 'var(--terminal-text)', marginTop: 4 }}>{alert.message}</div>
          <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.3)', marginTop: 4 }}>
            {alert.category && <span>{alert.category} · </span>}
            {new Date(alert.created_at).toLocaleString('en-US', { hour12: false })}
          </div>
        </div>
      ))}
    </div>
  );
}

function CadenceChart({ cadence }: { cadence: { cadence: string; count: number }[] }) {
  const maxCount = Math.max(...cadence.map(c => c.count), 1);
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 80 }}>
      {cadence.map(c => (
        <div key={c.cadence} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
          <div style={{ fontSize: 9, color: 'var(--terminal-text)', fontWeight: 600, marginBottom: 4 }}>{c.count}</div>
          <div style={{
            width: '100%',
            maxWidth: 32,
            height: `${(c.count / maxCount) * 60}px`,
            background: 'var(--terminal-blue)',
            borderRadius: '2px 2px 0 0',
            opacity: 0.7,
          }} />
          <div style={{ fontSize: 8, color: 'rgba(224,232,240,0.4)', marginTop: 4, textTransform: 'uppercase' }}>
            {c.cadence.slice(0, 5)}
          </div>
        </div>
      ))}
    </div>
  );
}

function Panel({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div style={{
      background: 'var(--terminal-panel-bg)',
      border: '1px solid var(--terminal-panel-border)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid var(--terminal-panel-border)',
      }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 1.5, textTransform: 'uppercase' }}>
          {title}
        </div>
        {action}
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
        {children}
      </div>
    </div>
  );
}

function MissionControl() {
  const { stats, modules, recentRuns, alerts, fetchStats, fetchModules, fetchRecentRuns, fetchAlerts, setView } = useDCCStore();
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const refresh = useCallback(async () => {
    await Promise.all([fetchStats(), fetchModules({ limit: '1000' }), fetchRecentRuns(), fetchAlerts()]);
    setLastRefresh(new Date());
  }, [fetchStats, fetchModules, fetchRecentRuns, fetchAlerts]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  if (!stats) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--terminal-blue)' }}>Loading...</div>;
  }

  const successRate = stats.pipeline.totalRuns > 0
    ? ((stats.pipeline.success / stats.pipeline.totalRuns) * 100).toFixed(1)
    : '0';

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16, height: '100%' }}>
      {/* Top bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>MISSION CONTROL</div>
          <div style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)', marginTop: 2 }}>
            QuantClaw Data — 970+ Module Pipeline
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--terminal-green)', animation: 'pulse 2s infinite' }} />
            <span style={{ fontSize: 10, color: 'var(--terminal-green)' }}>LIVE</span>
          </div>
          <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.3)' }}>
            Updated {lastRefresh.toLocaleTimeString('en-US', { hour12: false })}
          </div>
          <button
            onClick={refresh}
            style={{
              background: 'transparent', border: '1px solid var(--terminal-panel-border)',
              color: 'var(--terminal-text)', cursor: 'pointer', padding: '4px 10px',
              fontFamily: 'inherit', fontSize: 10,
            }}
          >
            ↻ REFRESH
          </button>
        </div>
      </div>

      {/* Hero stats strip */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <StatCard label="Total Modules" value={stats.modules.total} sub={`${stats.modules.active} active`} />
        <StatCard label="Gold+" value={stats.modules.tiers.gold + stats.modules.tiers.platinum} sub={`${((stats.modules.tiers.gold + stats.modules.tiers.platinum) / stats.modules.total * 100).toFixed(0)}% of total`} color="var(--terminal-yellow)" />
        <StatCard label="Pipeline Runs" value={stats.pipeline.totalRuns} sub={`${stats.pipeline.todayRuns} today`} />
        <StatCard label="Success Rate" value={`${successRate}%`} sub={`${stats.pipeline.failed} failed total`} color={+successRate > 90 ? 'var(--terminal-green)' : 'var(--terminal-yellow)'} />
        <StatCard label="Active Alerts" value={stats.alerts.unresolved} sub={stats.alerts.critical > 0 ? `${stats.alerts.critical} critical!` : 'All clear'} color={stats.alerts.critical > 0 ? 'var(--terminal-red)' : 'var(--terminal-green)'} />
        <StatCard label="Freshness" value={`${stats.freshness.onSchedule}`} sub={stats.freshness.overdue > 0 ? `${stats.freshness.overdue} overdue` : 'All on schedule'} color={stats.freshness.overdue > 0 ? 'var(--terminal-yellow)' : 'var(--terminal-green)'} />
      </div>

      {/* Tier distribution bar */}
      <div style={{ background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)', padding: 14 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 4 }}>
          QUALITY TIER DISTRIBUTION
        </div>
        <TierBar tiers={stats.modules.tiers} />
      </div>

      {/* Main grid: Heatmap + Pipeline + Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, flex: 1, minHeight: 0 }}>
        {/* Module Heatmap */}
        <Panel
          title="Module Health Map"
          action={
            <button onClick={() => setView('module-explorer')} style={{
              background: 'transparent', border: 'none', color: 'rgba(224,232,240,0.5)',
              cursor: 'pointer', fontSize: 9, fontFamily: 'inherit',
            }}>
              EXPLORE →
            </button>
          }
        >
          <ModuleHeatmap modules={modules} />
        </Panel>

        {/* Right column: Pipeline + Alerts stacked */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0 }}>
          <Panel
            title="Pipeline Activity"
            action={
              <button onClick={() => setView('pipeline')} style={{
                background: 'transparent', border: 'none', color: 'rgba(224,232,240,0.5)',
                cursor: 'pointer', fontSize: 9, fontFamily: 'inherit',
              }}>
                DETAILS →
              </button>
            }
          >
            <PipelineFeed />
          </Panel>

          <Panel
            title={`Alerts (${alerts.length})`}
            action={
              <button onClick={() => setView('alerts')} style={{
                background: 'transparent', border: 'none', color: 'rgba(224,232,240,0.5)',
                cursor: 'pointer', fontSize: 9, fontFamily: 'inherit',
              }}>
                VIEW ALL →
              </button>
            }
          >
            <AlertsFeed />
          </Panel>
        </div>
      </div>

      {/* Cadence chart */}
      <Panel title="Cadence Distribution">
        <CadenceChart cadence={stats.cadence} />
      </Panel>
    </div>
  );
}

function ModuleDetailPanel({ moduleId }: { moduleId: number }) {
  const { moduleDetail, fetchModuleDetail } = useDCCStore();
  const [tab, setTab] = useState<'overview' | 'runs' | 'quality'>('overview');

  useEffect(() => { fetchModuleDetail(moduleId); }, [moduleId, fetchModuleDetail]);

  if (!moduleDetail) return <div style={{ padding: 16, color: 'var(--terminal-blue)', fontSize: 11 }}>Loading...</div>;

  const { module: mod, runs, qualityChecks, tags } = moduleDetail;

  const statusColors: Record<string, string> = {
    success: 'var(--terminal-green)', failed: 'var(--terminal-red)', running: 'var(--terminal-blue)',
    retrying: 'var(--terminal-yellow)', queued: 'rgba(224,232,240,0.4)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--terminal-panel-border)' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--terminal-blue)', marginBottom: 4 }}>{mod.name}</div>
        {tags.length > 0 && (
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 6 }}>
            {tags.map((t, i) => (
              <span key={i} style={{ fontSize: 9, padding: '1px 6px', background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 2, color: 'var(--terminal-blue)' }}>
                {t.label}
              </span>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid var(--terminal-panel-border)' }}>
        {(['overview', 'runs', 'quality'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            flex: 1, padding: '6px 8px', background: tab === t ? 'rgba(0,212,255,0.1)' : 'transparent',
            border: 'none', borderBottom: tab === t ? '2px solid var(--terminal-blue)' : '2px solid transparent',
            color: tab === t ? 'var(--terminal-blue)' : 'rgba(224,232,240,0.5)',
            cursor: 'pointer', fontFamily: 'inherit', fontSize: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase',
          }}>{t}</button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
        {tab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', fontSize: 11 }}>
            {[
              ['TIER', mod.current_tier, TIER_COLORS[mod.current_tier]],
              ['QUALITY', `${mod.quality_score}/100`, mod.quality_score >= 80 ? 'var(--terminal-green)' : mod.quality_score >= 50 ? 'var(--terminal-yellow)' : 'var(--terminal-red)'],
              ['CADENCE', mod.cadence],
              ['GRANULARITY', mod.granularity],
              ['ACTIVE', mod.is_active ? 'Yes' : 'No', mod.is_active ? 'var(--terminal-green)' : 'var(--terminal-red)'],
              ['TOTAL RUNS', String(mod.run_count)],
              ['ERRORS', String(mod.error_count), mod.error_count > 0 ? 'var(--terminal-red)' : undefined],
              ['CONSEC FAIL', String(mod.consecutive_failures), mod.consecutive_failures > 0 ? 'var(--terminal-red)' : undefined],
              ['AVG DURATION', mod.avg_duration_ms != null ? `${(mod.avg_duration_ms / 1000).toFixed(1)}s` : '—'],
              ['LAST RUN', mod.last_run_at ? new Date(mod.last_run_at).toLocaleString('en-US', { hour12: false }) : '—'],
              ['LAST SUCCESS', mod.last_success_at ? new Date(mod.last_success_at).toLocaleString('en-US', { hour12: false }) : '—'],
              ['NEXT RUN', mod.next_run_at ? new Date(mod.next_run_at).toLocaleString('en-US', { hour12: false }) : '—'],
              ['SOURCE', mod.source_file ?? '—'],
            ].map(([label, val, color]) => (
              <>
                <span key={`k-${label}`} style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>{label}</span>
                <span key={`v-${label}`} style={{ color: (color as string) ?? 'var(--terminal-text)', fontWeight: color ? 600 : 400, textTransform: label === 'TIER' ? 'uppercase' : 'none', fontSize: label === 'SOURCE' ? 10 : 11, wordBreak: 'break-all' }}>{val}</span>
              </>
            ))}
          </div>
        )}
        {tab === 'runs' && (
          <div>
            {runs.length === 0 ? (
              <div style={{ color: 'rgba(224,232,240,0.4)', fontSize: 11 }}>No runs recorded</div>
            ) : runs.map((run: ModuleDetail['runs'][0]) => (
              <div key={run.id} style={{
                padding: '6px 0', borderBottom: '1px solid rgba(26,35,64,0.5)',
                display: 'flex', alignItems: 'center', gap: 8, fontSize: 11,
              }}>
                <span style={{ color: statusColors[run.status], fontWeight: 700, fontSize: 10, width: 55 }}>{run.status.toUpperCase()}</span>
                <span style={{ color: 'rgba(224,232,240,0.5)', fontSize: 10 }}>{run.tier_target}</span>
                <span style={{ color: 'rgba(224,232,240,0.4)', fontSize: 10 }}>
                  {run.duration_ms != null ? (run.duration_ms < 1000 ? `${run.duration_ms}ms` : `${(run.duration_ms / 1000).toFixed(1)}s`) : '—'}
                </span>
                <span style={{ color: 'rgba(224,232,240,0.5)', fontSize: 10 }}>{run.rows_out} rows</span>
                <span style={{ marginLeft: 'auto', color: 'rgba(224,232,240,0.3)', fontSize: 9 }}>
                  {new Date(run.started_at).toLocaleString('en-US', { hour12: false, month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        )}
        {tab === 'quality' && (
          <div>
            {qualityChecks.length === 0 ? (
              <div style={{ color: 'rgba(224,232,240,0.4)', fontSize: 11 }}>No quality checks recorded</div>
            ) : qualityChecks.map((qc: ModuleDetail['qualityChecks'][0]) => (
              <div key={qc.id} style={{
                padding: '6px 0', borderBottom: '1px solid rgba(26,35,64,0.5)',
                display: 'flex', alignItems: 'center', gap: 8, fontSize: 11,
              }}>
                <span style={{ color: qc.passed ? 'var(--terminal-green)' : 'var(--terminal-red)', fontWeight: 700, fontSize: 10 }}>
                  {qc.passed ? '✓' : '✗'}
                </span>
                <span style={{ color: 'var(--terminal-text)' }}>{qc.check_type}</span>
                <span style={{ color: qc.score >= 80 ? 'var(--terminal-green)' : qc.score >= 50 ? 'var(--terminal-yellow)' : 'var(--terminal-red)' }}>{qc.score}</span>
                <span style={{ marginLeft: 'auto', color: 'rgba(224,232,240,0.3)', fontSize: 9 }}>
                  {new Date(qc.checked_at).toLocaleString('en-US', { hour12: false, month: 'short', day: 'numeric' })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ModuleExplorer() {
  const { modules, modulesTotal, fetchModules, setSelectedModule, selectedModuleId, fetchModuleDetail } = useDCCStore();
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [cadenceFilter, setCadenceFilter] = useState('');

  useEffect(() => {
    const params: Record<string, string> = { limit: '200' };
    if (search) params.search = search;
    if (tierFilter) params.tier = tierFilter;
    if (cadenceFilter) params.cadence = cadenceFilter;
    fetchModules(params);
  }, [search, tierFilter, cadenceFilter, fetchModules]);

  const handleSelect = (id: number) => {
    setSelectedModule(id);
    fetchModuleDetail(id);
  };

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>MODULE EXPLORER</div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <input
          placeholder="Search modules..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
            color: 'var(--terminal-text)', padding: '6px 12px', fontSize: 11,
            fontFamily: 'inherit', flex: '1 1 200px', outline: 'none',
          }}
        />
        <select value={tierFilter} onChange={e => setTierFilter(e.target.value)} style={{
          background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
          color: 'var(--terminal-text)', padding: '6px 12px', fontSize: 11, fontFamily: 'inherit',
        }}>
          <option value="">All Tiers</option>
          <option value="platinum">Platinum</option>
          <option value="gold">Gold</option>
          <option value="silver">Silver</option>
          <option value="bronze">Bronze</option>
          <option value="none">None</option>
        </select>
        <select value={cadenceFilter} onChange={e => setCadenceFilter(e.target.value)} style={{
          background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
          color: 'var(--terminal-text)', padding: '6px 12px', fontSize: 11, fontFamily: 'inherit',
        }}>
          <option value="">All Cadences</option>
          {CADENCE_ORDER.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <div style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)', alignSelf: 'center' }}>{modulesTotal} results</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, minHeight: 0 }}>
        <div style={{ flex: 2, overflow: 'auto', background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
            <thead>
              <tr style={{ position: 'sticky', top: 0, background: 'var(--terminal-panel-bg)', zIndex: 1 }}>
                {['Module', 'Cadence', 'Tier', 'Quality', 'Runs', 'Errors', 'Last Run'].map(h => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '8px', borderBottom: '1px solid var(--terminal-panel-border)',
                    color: 'var(--terminal-blue)', fontSize: 9, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {modules.map(m => (
                <tr key={m.id} onClick={() => handleSelect(m.id)} style={{
                  cursor: 'pointer', background: selectedModuleId === m.id ? 'rgba(0,212,255,0.08)' : 'transparent',
                }}>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'var(--terminal-text)', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.name}</td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.6)' }}>{m.cadence}</td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>
                    <span style={{ color: TIER_COLORS[m.current_tier] ?? '#374151', fontWeight: 600, textTransform: 'uppercase', fontSize: 10 }}>{m.current_tier}</span>
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: m.quality_score >= 80 ? 'var(--terminal-green)' : m.quality_score >= 50 ? 'var(--terminal-yellow)' : 'var(--terminal-red)' }}>{m.quality_score}</td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.6)' }}>{m.run_count}</td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: m.error_count > 0 ? 'var(--terminal-red)' : 'rgba(224,232,240,0.4)' }}>
                    {m.error_count}{m.consecutive_failures > 0 && <span style={{ color: 'var(--terminal-red)' }}> ⚠</span>}
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.4)', fontSize: 10 }}>
                    {m.last_run_at ? new Date(m.last_run_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selectedModuleId && (
          <div style={{ flex: 1, background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <ModuleDetailPanel moduleId={selectedModuleId} />
          </div>
        )}
      </div>
    </div>
  );
}

function ThroughputChart() {
  const { throughput, fetchThroughput } = useDCCStore();

  useEffect(() => { fetchThroughput(); }, [fetchThroughput]);

  if (!throughput || throughput.daily.length === 0) return null;

  const days = [...throughput.daily].reverse().slice(-14);
  const maxVal = Math.max(...days.map(d => d.total), 1);

  return (
    <Panel title="Daily Pipeline Throughput (14d)">
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 100 }}>
        {days.map((d, i) => {
          const successH = (d.success / maxVal) * 80;
          const failedH = (d.failed / maxVal) * 80;
          return (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
              <div style={{ fontSize: 8, color: 'rgba(224,232,240,0.5)', marginBottom: 2 }}>{d.total}</div>
              <div style={{ display: 'flex', flexDirection: 'column', width: '100%', maxWidth: 24 }}>
                {d.failed > 0 && <div style={{ height: failedH, background: 'var(--terminal-red)', borderRadius: '2px 2px 0 0', opacity: 0.8 }} />}
                <div style={{ height: successH, background: 'var(--terminal-green)', borderRadius: d.failed > 0 ? 0 : '2px 2px 0 0', opacity: 0.6 }} />
              </div>
              <div style={{ fontSize: 7, color: 'rgba(224,232,240,0.3)', marginTop: 2 }}>
                {new Date(d.day).toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' })}
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 9 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 8, height: 8, background: 'var(--terminal-green)', opacity: 0.6, borderRadius: 2 }} />
          <span style={{ color: 'rgba(224,232,240,0.5)' }}>Success</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 8, height: 8, background: 'var(--terminal-red)', opacity: 0.8, borderRadius: 2 }} />
          <span style={{ color: 'rgba(224,232,240,0.5)' }}>Failed</span>
        </div>
      </div>
    </Panel>
  );
}

function PipelineMonitor() {
  const { recentRuns, fetchRecentRuns } = useDCCStore();

  useEffect(() => { fetchRecentRuns(); }, [fetchRecentRuns]);

  const statusColors: Record<string, string> = {
    success: 'var(--terminal-green)', failed: 'var(--terminal-red)', running: 'var(--terminal-blue)',
    retrying: 'var(--terminal-yellow)', queued: 'rgba(224,232,240,0.4)',
  };

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>PIPELINE MONITOR</div>

      <ThroughputChart />

      <div style={{ flex: 1, overflow: 'auto', background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead>
            <tr style={{ position: 'sticky', top: 0, background: 'var(--terminal-panel-bg)', zIndex: 1 }}>
              {['Status', 'Module', 'Target', 'Started', 'Duration', 'Rows In', 'Rows Out', 'Errors', 'Retry'].map(h => (
                <th key={h} style={{
                  textAlign: 'left', padding: '8px', borderBottom: '1px solid var(--terminal-panel-border)',
                  color: 'var(--terminal-blue)', fontSize: 9, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {recentRuns.map(run => (
              <tr key={run.id}>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>
                  <span style={{ color: statusColors[run.status], fontWeight: 700, fontSize: 10, textTransform: 'uppercase' }}>{run.status}</span>
                </td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.module_name}</td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.6)' }}>{run.tier_target}</td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.5)', fontSize: 10 }}>
                  {new Date(run.started_at).toLocaleString('en-US', { hour12: false, month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.5)' }}>
                  {run.duration_ms != null ? (run.duration_ms < 1000 ? `${run.duration_ms}ms` : `${(run.duration_ms / 1000).toFixed(1)}s`) : '—'}
                </td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>{run.rows_in}</td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>{run.rows_out}</td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: run.rows_failed > 0 ? 'var(--terminal-red)' : 'rgba(224,232,240,0.4)' }}>{run.rows_failed}</td>
                <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>{run.retry_attempt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface QualityOverview {
  overall: { avgQuality: number; totalChecks: number; passed: number; failed: number };
  checkTypes: { checkType: string; total: number; passed: number; avgScore: number }[];
  tierTrend: { day: string; gold: number; silver: number; bronze: number }[];
  worstModules: Module[];
}

function QualityConsole() {
  const { stats, fetchStats } = useDCCStore();
  const [qualityData, setQualityData] = useState<QualityOverview | null>(null);

  useEffect(() => {
    fetchStats();
    fetch('/api/dcc/quality/overview').then(r => r.json()).then(setQualityData).catch(() => {});
  }, [fetchStats]);

  if (!stats) return <div style={{ padding: 16, color: 'var(--terminal-blue)' }}>Loading...</div>;

  const passRate = qualityData && qualityData.overall.totalChecks > 0
    ? ((qualityData.overall.passed / qualityData.overall.totalChecks) * 100).toFixed(1)
    : '—';

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>QUALITY CONSOLE</div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <StatCard label="Gold+ Modules" value={stats.modules.tiers.gold + stats.modules.tiers.platinum} color="var(--terminal-yellow)" />
        <StatCard label="Bronze" value={stats.modules.tiers.bronze} color="#cd7f32" />
        <StatCard label="Avg Quality" value={qualityData?.overall.avgQuality ?? '—'} color="var(--terminal-blue)" />
        <StatCard label="Check Pass Rate" value={`${passRate}%`} color={+passRate > 80 ? 'var(--terminal-green)' : 'var(--terminal-yellow)'} />
        <StatCard label="Total Checks" value={qualityData?.overall.totalChecks ?? 0} />
      </div>

      <Panel title="Tier Distribution">
        <TierBar tiers={stats.modules.tiers} />
      </Panel>

      {qualityData && qualityData.checkTypes.length > 0 && (
        <Panel title="Quality Check Breakdown">
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {qualityData.checkTypes.map(ct => {
              const passP = ct.total > 0 ? ((ct.passed / ct.total) * 100).toFixed(0) : '0';
              return (
                <div key={ct.checkType} style={{
                  background: 'rgba(0,212,255,0.05)', border: '1px solid var(--terminal-panel-border)',
                  padding: '10px 14px', flex: '1 1 140px', minWidth: 120,
                }}>
                  <div style={{ fontSize: 10, color: 'var(--terminal-blue)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                    {ct.checkType}
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: ct.avgScore >= 80 ? 'var(--terminal-green)' : ct.avgScore >= 50 ? 'var(--terminal-yellow)' : 'var(--terminal-red)' }}>
                    {ct.avgScore}
                  </div>
                  <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.4)', marginTop: 4 }}>
                    {passP}% pass ({ct.passed}/{ct.total})
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      <Panel title="Worst 20 Modules (by Quality Score)">
        <div style={{ maxHeight: 400, overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
            <thead>
              <tr>
                {['Module', 'Cadence', 'Tier', 'Quality', 'Errors', 'Consec Fail'].map(h => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid var(--terminal-panel-border)',
                    color: 'var(--terminal-blue)', fontSize: 9, fontWeight: 700, letterSpacing: 1,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(qualityData?.worstModules ?? []).map((m: Module) => (
                <tr key={m.id}>
                  <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.name}</td>
                  <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.5)', fontSize: 10 }}>{m.cadence}</td>
                  <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: TIER_COLORS[m.current_tier], fontWeight: 600, textTransform: 'uppercase', fontSize: 10 }}>{m.current_tier}</td>
                  <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: m.quality_score < 30 ? 'var(--terminal-red)' : 'var(--terminal-yellow)' }}>{m.quality_score}</td>
                  <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: m.error_count > 0 ? 'var(--terminal-red)' : 'rgba(224,232,240,0.4)' }}>{m.error_count}</td>
                  <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: m.consecutive_failures > 0 ? 'var(--terminal-red)' : 'rgba(224,232,240,0.4)' }}>{m.consecutive_failures}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function AlertCenter() {
  const { alerts, fetchAlerts, resolveAlert } = useDCCStore();
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved'>('active');

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const sevColors: Record<string, string> = {
    critical: 'var(--terminal-red)', warning: 'var(--terminal-yellow)', info: 'var(--terminal-blue)',
  };

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>ALERT CENTER</div>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['active', 'all'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              background: filter === f ? 'rgba(0,212,255,0.15)' : 'transparent',
              border: '1px solid var(--terminal-panel-border)',
              color: filter === f ? 'var(--terminal-blue)' : 'rgba(224,232,240,0.5)',
              padding: '4px 12px', fontSize: 10, fontFamily: 'inherit', cursor: 'pointer', textTransform: 'uppercase',
            }}>{f}</button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--terminal-green)' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>✓</div>
            <div style={{ fontSize: 12 }}>No active alerts</div>
          </div>
        ) : (
          alerts.map(alert => (
            <div key={alert.id} style={{
              background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
              borderLeft: `3px solid ${sevColors[alert.severity]}`, padding: 14, marginBottom: 8,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: sevColors[alert.severity], textTransform: 'uppercase', letterSpacing: 1 }}>{alert.severity}</span>
                  {alert.category && <span style={{ fontSize: 9, color: 'rgba(224,232,240,0.5)', padding: '1px 6px', border: '1px solid rgba(224,232,240,0.2)', borderRadius: 2 }}>{alert.category}</span>}
                </div>
                <button onClick={() => resolveAlert(alert.id)} style={{
                  background: 'transparent', border: '1px solid var(--terminal-green)', color: 'var(--terminal-green)',
                  padding: '3px 10px', fontSize: 9, fontFamily: 'inherit', cursor: 'pointer', letterSpacing: 1,
                }}>RESOLVE</button>
              </div>
              <div style={{ fontSize: 11, color: 'var(--terminal-text)', marginBottom: 6 }}>{alert.message}</div>
              <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.3)', display: 'flex', gap: 12 }}>
                {alert.module_name && <span>Module: {alert.module_name}</span>}
                <span>{new Date(alert.created_at).toLocaleString('en-US', { hour12: false })}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

interface SourceData {
  sources: { sourceUrl: string; moduleCount: number; lastSuccess: string | null; lastRun: string | null; totalRuns: number; successRuns: number; failedRuns: number; avgDuration: number; uptime: number }[];
  cadenceConfig: { cadence: string; count: number; nextRuns: number }[];
  symbolUniverse: { total: number; active: number; assetClasses: number };
  assetClasses: { assetClass: string; count: number }[];
}

interface HealthData {
  database: { version: string; size: string; connections: number };
  tables: { name: string; rows: number; size: string }[];
  activity: { lastHour: number; lastDay: number };
}

function SourceHealth() {
  const [data, setData] = useState<SourceData | null>(null);

  useEffect(() => {
    fetch('/api/dcc/sources').then(r => r.json()).then(setData).catch(() => {});
  }, []);

  if (!data) return <div style={{ padding: 16, color: 'var(--terminal-blue)' }}>Loading...</div>;

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>SOURCE HEALTH</div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <StatCard label="Data Sources" value={data.sources.length} />
        <StatCard label="Symbol Universe" value={data.symbolUniverse.active} sub={`${data.symbolUniverse.assetClasses} asset classes`} />
      </div>

      <Panel title="Data Sources">
        <div style={{ overflow: 'auto', maxHeight: 400 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
            <thead>
              <tr>
                {['Source', 'Modules', 'Uptime %', 'Runs', 'Failed', 'Avg Duration', 'Last Success'].map(h => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid var(--terminal-panel-border)',
                    color: 'var(--terminal-blue)', fontSize: 9, fontWeight: 700, letterSpacing: 1,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.sources.map((s, i) => {
                const domain = s.sourceUrl === 'local' ? 'local' : (() => { try { return new URL(s.sourceUrl).hostname; } catch { return s.sourceUrl; } })();
                return (
                  <tr key={i}>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={s.sourceUrl}>{domain}</td>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', fontWeight: 600 }}>{s.moduleCount}</td>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: s.uptime >= 95 ? 'var(--terminal-green)' : s.uptime >= 80 ? 'var(--terminal-yellow)' : 'var(--terminal-red)' }}>{s.uptime}%</td>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>{s.totalRuns}</td>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: s.failedRuns > 0 ? 'var(--terminal-red)' : 'rgba(224,232,240,0.4)' }}>{s.failedRuns}</td>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.5)' }}>
                      {s.avgDuration < 1000 ? `${s.avgDuration}ms` : `${(s.avgDuration / 1000).toFixed(1)}s`}
                    </td>
                    <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.4)', fontSize: 10 }}>
                      {s.lastSuccess ? new Date(s.lastSuccess).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Panel title="Cadence Configuration">
          {data.cadenceConfig.map(c => (
            <div key={c.cadence} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(26,35,64,0.3)', fontSize: 11 }}>
              <span style={{ color: 'var(--terminal-text)', textTransform: 'uppercase', fontWeight: 600 }}>{c.cadence}</span>
              <span style={{ color: 'rgba(224,232,240,0.6)' }}>{c.count} modules · {c.nextRuns} scheduled</span>
            </div>
          ))}
        </Panel>

        <Panel title="Asset Classes">
          {data.assetClasses.map(a => (
            <div key={a.assetClass} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(26,35,64,0.3)', fontSize: 11 }}>
              <span style={{ color: 'var(--terminal-text)' }}>{a.assetClass}</span>
              <span style={{ color: 'var(--terminal-blue)', fontWeight: 600 }}>{a.count}</span>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}

function Configuration() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const { stats } = useDCCStore();

  useEffect(() => {
    fetch('/api/dcc/config/health').then(r => r.json()).then(setHealth).catch(() => {});
  }, []);

  if (!health) return <div style={{ padding: 16, color: 'var(--terminal-blue)' }}>Loading...</div>;

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>CONFIGURATION</div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <StatCard label="Database" value={health.database.version} sub={health.database.size} />
        <StatCard label="Connections" value={health.database.connections} />
        <StatCard label="Runs (Last Hour)" value={health.activity.lastHour} />
        <StatCard label="Runs (Last Day)" value={health.activity.lastDay} />
      </div>

      <Panel title="Table Statistics">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead>
            <tr>
              {['Table', 'Rows', 'Size'].map(h => (
                <th key={h} style={{
                  textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid var(--terminal-panel-border)',
                  color: 'var(--terminal-blue)', fontSize: 9, fontWeight: 700, letterSpacing: 1,
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {health.tables.map(t => (
              <tr key={t.name}>
                <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', fontWeight: 600 }}>{t.name}</td>
                <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)' }}>{t.rows.toLocaleString()}</td>
                <td style={{ padding: '4px 8px', borderBottom: '1px solid rgba(26,35,64,0.5)', color: 'rgba(224,232,240,0.6)' }}>{t.size}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <Panel title="System Info">
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 16px', fontSize: 11 }}>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>APP</span>
          <span>QuantClaw Data v1.0</span>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>PORT</span>
          <span>3055</span>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>FRAMEWORK</span>
          <span>Next.js 15 + TypeScript</span>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>DB ENGINE</span>
          <span>{health.database.version}</span>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>DB SIZE</span>
          <span>{health.database.size}</span>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>MODULES</span>
          <span>{stats?.modules.total ?? '—'}</span>
          <span style={{ color: 'var(--terminal-blue)', fontSize: 10, fontWeight: 600 }}>URL</span>
          <span>data.quantclaw.org/dcc</span>
        </div>
      </Panel>
    </div>
  );
}

export default function DCCPage() {
  const { view } = useDCCStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
      const viewMap: Record<string, DCCView> = {
        '1': 'mission-control', '2': 'module-explorer', '3': 'pipeline',
        '4': 'quality', '5': 'alerts', '6': 'sources', '7': 'config',
      };
      if (viewMap[e.key]) {
        useDCCStore.getState().setView(viewMap[e.key]);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  switch (view) {
    case 'mission-control': return <MissionControl />;
    case 'module-explorer': return <ModuleExplorer />;
    case 'pipeline': return <PipelineMonitor />;
    case 'quality': return <QualityConsole />;
    case 'alerts': return <AlertCenter />;
    case 'sources': return <SourceHealth />;
    case 'config': return <Configuration />;
    default: return <MissionControl />;
  }
}
