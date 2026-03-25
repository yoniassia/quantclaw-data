'use client';

import { useEffect, useState, useCallback, useRef, lazy, Suspense } from 'react';
import { useDCCStore, Module, DCCView, ModuleDetail } from '@/store/dcc-store';

const NLQueryView = lazy(() => import('./nl-query-view'));

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

// --------------- Instrument View (SAPI) ---------------

interface SapiMeta {
  instrument_id: number; symbol: string; display_name: string; exchange: string;
  asset_class: string; industry: string; sector: string; umbrella_sector: string;
  market_cap_class: string; ceo: string; city: string; country: string;
  isin: string; cusip: string; figi: string; ipo_date: string; founded_year: number;
  is_tradable: boolean; is_buy_enabled: boolean; is_delisted: boolean; logo_url: string;
}

interface SapiPrices {
  current_rate: number; closing_price: number; daily_change_pct: number;
  weekly_change_pct: number; monthly_change_pct: number; three_month_pct: number;
  six_month_pct: number; one_year_pct: number; two_year_pct: number; ytd_pct: number;
  ma_5d: number; ma_10d: number; ma_50d: number; ma_200d: number;
  ma_10w: number; ma_30w: number; week_52_high: number; week_52_low: number;
  year_5_high: number; year_5_low: number; market_cap_usd: number;
}

interface SapiFundamentals {
  pe_ratio: number; price_to_book: number; price_to_sales: number;
  price_to_cashflow: number; price_to_fcf: number; peg_ratio: number;
  ev: number; ev_to_ebitda: number; ev_to_sales: number;
  gross_margin: number; operating_margin: number; pretax_margin: number; net_margin: number;
  roe: number; roa: number; roic: number;
  debt_to_equity: number; current_ratio: number; quick_ratio: number;
  leverage_ratio: number; interest_coverage: number;
  revenue_per_share: number; book_value_ps: number; cashflow_ps: number;
  eps_basic: number; eps_diluted: number; dividend_ps: number; dividend_yield: number;
  rev_growth_1y: number; rev_growth_3y: number; rev_growth_5y: number;
  income_growth_1y: number; income_growth_3y: number; income_growth_5y: number;
  eps_growth_1y: number; eps_growth_5y: number;
  shares_outstanding: number; employees: number;
}

interface SapiAnalysts {
  consensus: string; target_price: number; target_upside_pct: number;
  total_analysts: number; buy_count: number; hold_count: number; sell_count: number;
  target_high: number; target_low: number;
  estimated_eps: number; annual_eps_est: number; quarterly_eps_est: number;
  next_earnings_date: string; earnings_quarter: string;
}

interface SapiSocial {
  popularity_uniques: number; popularity_7d: number; popularity_14d: number; popularity_30d: number;
  traders_7d_change: number; traders_14d_change: number; traders_30d_change: number;
  buy_holding_pct: number; sell_holding_pct: number; holding_pct: number; institutional_pct: number;
}

interface SapiEsg {
  esg_total: number; esg_environment: number; esg_social: number; esg_governance: number;
  normalized_score: number; gc_total: number; gc_environment: number; gc_anti_corruption: number;
  human_rights: number; labour_rights: number;
}

interface SapiBetas { beta_12m: number; beta_24m: number; beta_36m: number; beta_60m: number; }

interface SapiInstrumentData {
  meta: SapiMeta | null;
  prices: SapiPrices | null;
  fundamentals: SapiFundamentals | null;
  analysts: SapiAnalysts | null;
  social: SapiSocial | null;
  esg: SapiEsg | null;
  betas: SapiBetas | null;
  factorScores: Record<string, unknown> | null;
  trendSignals: Record<string, unknown> | null;
  rankings: Record<string, unknown> | null;
}

interface SapiListItem {
  instrument_id: number; symbol: string; display_name: string; exchange: string;
  umbrella_sector: string; market_cap_class: string; logo_url: string;
  current_rate: number; daily_change_pct: number; weekly_change_pct: number;
  ytd_pct: number; market_cap_usd: number; pe_ratio: number; roe: number;
  net_margin: number; rev_growth_1y: number; consensus: string; target_upside_pct: number;
}

type InstrumentTab = 'overview' | 'technicals' | 'fundamentals' | 'analysts' | 'social' | 'esg' | 'risk';

function fmtNum(val: number | null | undefined, decimals = 2): string {
  if (val == null || isNaN(val)) return '—';
  return val.toFixed(decimals);
}

function fmtPct(val: number | null | undefined, decimals = 2): string {
  if (val == null || isNaN(val)) return '—';
  return `${val >= 0 ? '+' : ''}${val.toFixed(decimals)}%`;
}

function fmtMcap(val: number | null | undefined): string {
  if (val == null) return '—';
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(0)}M`;
  return `$${val.toLocaleString()}`;
}

function fmtBigNum(val: number | null | undefined): string {
  if (val == null) return '—';
  if (val >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  if (val >= 1e3) return `${(val / 1e3).toFixed(0)}K`;
  return val.toLocaleString();
}

function pctColor(val: number | null | undefined): string {
  if (val == null) return 'rgba(224,232,240,0.5)';
  return val >= 0 ? 'var(--terminal-green)' : 'var(--terminal-red)';
}

function scoreColor(score: number): string {
  if (score >= 80) return '#00d26a';
  if (score >= 60) return '#fbbf24';
  if (score >= 40) return '#f97316';
  return '#ef4444';
}

function MetricCell({ label, value, color, sub }: { label: string; value: string; color?: string; sub?: string }) {
  return (
    <div style={{ padding: '8px 0', borderBottom: '1px solid rgba(26,35,64,0.25)' }}>
      <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.45)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color: color || 'var(--terminal-text)', fontVariantNumeric: 'tabular-nums' }}>{value}</div>
      {sub && <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.35)', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function MetricGrid({ children }: { children: React.ReactNode }) {
  return <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0 20px' }}>{children}</div>;
}

function SectionPanel({ title, color, children }: { title: string; color?: string; children: React.ReactNode }) {
  return (
    <div style={{ background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)', marginBottom: 10, overflow: 'hidden' }}>
      <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--terminal-panel-border)' }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: color || 'var(--terminal-blue)', letterSpacing: 1.5, textTransform: 'uppercase' }}>{title}</span>
      </div>
      <div style={{ padding: '8px 16px 12px' }}>{children}</div>
    </div>
  );
}

function HorizontalBar({ value, max, color, height = 6 }: { value: number; max: number; color: string; height?: number }) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div style={{ height, background: 'rgba(224,232,240,0.06)', borderRadius: height / 2, overflow: 'hidden', width: '100%' }}>
      <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: height / 2, transition: 'width 0.4s ease' }} />
    </div>
  );
}

function RangeBar({ current, low, high, label }: { current: number; low: number; high: number; label?: string }) {
  const range = high - low;
  const pct = range > 0 ? Math.min(100, Math.max(0, ((current - low) / range) * 100)) : 50;
  return (
    <div style={{ marginBottom: 10 }}>
      {label && <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.45)', marginBottom: 4, letterSpacing: 0.5 }}>{label}</div>}
      <div style={{ position: 'relative', height: 8, background: 'linear-gradient(to right, var(--terminal-red), var(--terminal-yellow), var(--terminal-green))', borderRadius: 4, opacity: 0.4 }}>
        <div style={{
          position: 'absolute', top: -3, left: `${pct}%`, transform: 'translateX(-50%)',
          width: 14, height: 14, borderRadius: '50%', background: 'var(--terminal-blue)', border: '2px solid var(--terminal-panel-bg)',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'rgba(224,232,240,0.4)', marginTop: 4 }}>
        <span>${fmtNum(low, 0)}</span>
        <span style={{ color: 'var(--terminal-text)', fontWeight: 600 }}>${fmtNum(current, 2)}</span>
        <span>${fmtNum(high, 0)}</span>
      </div>
    </div>
  );
}

function ConsensusDonut({ buy, hold, sell }: { buy: number; hold: number; sell: number }) {
  const total = buy + hold + sell;
  if (total === 0) return null;
  const buyPct = (buy / total) * 100;
  const holdPct = (hold / total) * 100;
  const buyDeg = (buyPct / 100) * 360;
  const holdDeg = (holdPct / 100) * 360;
  const bg = `conic-gradient(#00d26a 0deg ${buyDeg}deg, #fbbf24 ${buyDeg}deg ${buyDeg + holdDeg}deg, #ef4444 ${buyDeg + holdDeg}deg 360deg)`;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ width: 80, height: 80, borderRadius: '50%', background: bg, position: 'relative' }}>
        <div style={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
          width: 50, height: 50, borderRadius: '50%', background: 'var(--terminal-panel-bg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: 'var(--terminal-text)',
        }}>
          {total}
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: '#00d26a' }} />
          <span style={{ color: 'var(--terminal-text)' }}>Buy {buy}</span>
          <span style={{ color: 'rgba(224,232,240,0.4)', fontSize: 10 }}>({buyPct.toFixed(0)}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: '#fbbf24' }} />
          <span style={{ color: 'var(--terminal-text)' }}>Hold {hold}</span>
          <span style={{ color: 'rgba(224,232,240,0.4)', fontSize: 10 }}>({holdPct.toFixed(0)}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: '#ef4444' }} />
          <span style={{ color: 'var(--terminal-text)' }}>Sell {sell}</span>
          <span style={{ color: 'rgba(224,232,240,0.4)', fontSize: 10 }}>({((sell / total) * 100).toFixed(0)}%)</span>
        </div>
      </div>
    </div>
  );
}

function EsgRadar({ esg }: { esg: SapiEsg }) {
  const items = [
    { label: 'Environmental', value: esg.esg_environment, color: '#10b981' },
    { label: 'Social', value: esg.esg_social, color: '#3b82f6' },
    { label: 'Governance', value: esg.esg_governance, color: '#8b5cf6' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {items.map(item => (
        <div key={item.label}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 4 }}>
            <span style={{ color: 'rgba(224,232,240,0.6)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 1 }}>{item.label}</span>
            <span style={{ color: item.color, fontWeight: 700 }}>{fmtNum(item.value, 1)}</span>
          </div>
          <HorizontalBar value={item.value ?? 0} max={100} color={item.color} height={8} />
        </div>
      ))}
    </div>
  );
}

function InstrumentOverviewTab({ data }: { data: SapiInstrumentData }) {
  const { meta, prices, fundamentals, analysts, social, esg, betas } = data;
  if (!meta) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Hero card */}
      <div style={{ background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)', padding: 20 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16 }}>
          {meta.logo_url && (
            <img src={meta.logo_url} alt={meta.symbol} style={{ width: 48, height: 48, borderRadius: 8, objectFit: 'cover', background: '#1a2340' }} onError={e => (e.currentTarget.style.display = 'none')} />
          )}
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 2 }}>
              <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 1 }}>{meta.symbol}</span>
              <span style={{ fontSize: 14, color: 'var(--terminal-text)' }}>{meta.display_name}</span>
              {meta.is_tradable && <span style={{ fontSize: 8, padding: '2px 6px', background: 'rgba(0,210,106,0.15)', border: '1px solid rgba(0,210,106,0.3)', color: '#00d26a', borderRadius: 2, fontWeight: 600 }}>TRADABLE</span>}
            </div>
            <div style={{ display: 'flex', gap: 12, fontSize: 10, color: 'rgba(224,232,240,0.5)', flexWrap: 'wrap' }}>
              {meta.umbrella_sector && <span>{meta.umbrella_sector}</span>}
              {meta.exchange && <span>• {meta.exchange}</span>}
              {meta.market_cap_class && <span>• {meta.market_cap_class}</span>}
              {meta.country && <span>• {meta.country}</span>}
              {meta.ceo && <span>• CEO: {meta.ceo}</span>}
            </div>
          </div>
          {prices && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--terminal-text)', fontVariantNumeric: 'tabular-nums' }}>${fmtNum(prices.current_rate)}</div>
              <div style={{ fontSize: 15, fontWeight: 600, color: pctColor(prices.daily_change_pct) }}>
                {fmtPct(prices.daily_change_pct)} today
              </div>
            </div>
          )}
        </div>

        {prices && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '4px 16px' }}>
            {[
              ['1W', prices.weekly_change_pct],
              ['1M', prices.monthly_change_pct],
              ['3M', prices.three_month_pct],
              ['6M', prices.six_month_pct],
              ['YTD', prices.ytd_pct],
              ['1Y', prices.one_year_pct],
              ['2Y', prices.two_year_pct],
            ].map(([label, val]) => (
              <div key={label as string} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(26,35,64,0.2)' }}>
                <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.45)' }}>{label as string}</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: pctColor(val as number), fontVariantNumeric: 'tabular-nums' }}>{fmtPct(val as number)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 52W Range */}
      {prices && prices.week_52_high && (
        <SectionPanel title="52-Week Range" color="#22d3ee">
          <RangeBar current={prices.current_rate} low={prices.week_52_low} high={prices.week_52_high} />
          {prices.year_5_high && (
            <>
              <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.4)', marginTop: 8, marginBottom: 4 }}>5-Year Range</div>
              <RangeBar current={prices.current_rate} low={prices.year_5_low} high={prices.year_5_high} />
            </>
          )}
        </SectionPanel>
      )}

      {/* Key metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {/* Valuation snapshot */}
        {fundamentals && (
          <SectionPanel title="Valuation" color="#8b5cf6">
            <MetricGrid>
              <MetricCell label="P/E" value={fmtNum(fundamentals.pe_ratio)} />
              <MetricCell label="PEG" value={fmtNum(fundamentals.peg_ratio)} />
              <MetricCell label="P/B" value={fmtNum(fundamentals.price_to_book)} />
              <MetricCell label="EV/EBITDA" value={fmtNum(fundamentals.ev_to_ebitda)} />
              <MetricCell label="MCap" value={fmtMcap(prices?.market_cap_usd)} />
              <MetricCell label="Dividend" value={fundamentals.dividend_yield ? `${(fundamentals.dividend_yield * 100).toFixed(2)}%` : '—'} />
            </MetricGrid>
          </SectionPanel>
        )}

        {/* Analyst snapshot */}
        {analysts && (
          <SectionPanel title="Analysts" color="#06b6d4">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
              <div style={{
                fontSize: 16, fontWeight: 700, padding: '4px 14px', borderRadius: 4,
                background: analysts.consensus === 'Buy' ? 'rgba(0,210,106,0.15)' : analysts.consensus === 'Sell' ? 'rgba(239,68,68,0.15)' : 'rgba(251,191,36,0.15)',
                color: analysts.consensus === 'Buy' ? '#00d26a' : analysts.consensus === 'Sell' ? '#ef4444' : '#fbbf24',
                border: `1px solid ${analysts.consensus === 'Buy' ? 'rgba(0,210,106,0.3)' : analysts.consensus === 'Sell' ? 'rgba(239,68,68,0.3)' : 'rgba(251,191,36,0.3)'}`,
              }}>
                {analysts.consensus?.toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 12, color: 'var(--terminal-text)' }}>Target ${fmtNum(analysts.target_price, 0)}</div>
                <div style={{ fontSize: 11, color: pctColor(analysts.target_upside_pct) }}>{fmtPct(analysts.target_upside_pct)} upside</div>
              </div>
            </div>
            <ConsensusDonut buy={analysts.buy_count} hold={analysts.hold_count} sell={analysts.sell_count} />
          </SectionPanel>
        )}
      </div>

      {/* Bottom row: Social + ESG mini */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {social && (
          <SectionPanel title="eToro Social" color="#f97316">
            <MetricGrid>
              <MetricCell label="Traders 30d Chg" value={fmtPct(social.traders_30d_change)} color={pctColor(social.traders_30d_change)} />
              <MetricCell label="Buy Holding" value={`${fmtNum(social.buy_holding_pct, 0)}%`} />
              <MetricCell label="Institutional" value={`${fmtNum(social.institutional_pct, 1)}%`} />
              <MetricCell label="Popularity" value={String(social.popularity_uniques ?? '—')} />
            </MetricGrid>
          </SectionPanel>
        )}

        {esg && (
          <SectionPanel title="ESG Score" color="#10b981">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 60, height: 60, borderRadius: '50%',
                border: `4px solid ${scoreColor(esg.esg_total)}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, fontWeight: 700, color: scoreColor(esg.esg_total),
              }}>
                {fmtNum(esg.esg_total, 0)}
              </div>
              <div style={{ flex: 1 }}>
                <EsgRadar esg={esg} />
              </div>
            </div>
          </SectionPanel>
        )}
      </div>

      {/* Identifiers */}
      <SectionPanel title="Identifiers" color="rgba(224,232,240,0.4)">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0 20px', fontSize: 11 }}>
          <MetricCell label="eToro ID" value={String(meta.instrument_id)} />
          {meta.isin && <MetricCell label="ISIN" value={meta.isin} />}
          {meta.cusip && <MetricCell label="CUSIP" value={meta.cusip} />}
          {meta.figi && <MetricCell label="FIGI" value={meta.figi} />}
          {meta.ipo_date && <MetricCell label="IPO Date" value={meta.ipo_date} />}
          {meta.founded_year && <MetricCell label="Founded" value={String(meta.founded_year)} />}
        </div>
      </SectionPanel>
    </div>
  );
}

function InstrumentTechnicalsTab({ data }: { data: SapiInstrumentData }) {
  const { prices, betas } = data;
  if (!prices) return <div style={{ padding: 20, color: 'rgba(224,232,240,0.4)' }}>No price data available</div>;

  const maData = [
    { label: '5D MA', value: prices.ma_5d, above: prices.current_rate >= (prices.ma_5d ?? 0) },
    { label: '10D MA', value: prices.ma_10d, above: prices.current_rate >= (prices.ma_10d ?? 0) },
    { label: '50D MA', value: prices.ma_50d, above: prices.current_rate >= (prices.ma_50d ?? 0) },
    { label: '200D MA', value: prices.ma_200d, above: prices.current_rate >= (prices.ma_200d ?? 0) },
    { label: '10W MA', value: prices.ma_10w, above: prices.current_rate >= (prices.ma_10w ?? 0) },
    { label: '30W MA', value: prices.ma_30w, above: prices.current_rate >= (prices.ma_30w ?? 0) },
  ];

  const goldenCross = prices.ma_50d && prices.ma_200d && prices.ma_50d > prices.ma_200d;
  const deathCross = prices.ma_50d && prices.ma_200d && prices.ma_50d < prices.ma_200d;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <SectionPanel title="Moving Average Stack" color="#3b82f6">
        <div style={{ marginBottom: 12 }}>
          {goldenCross && (
            <span style={{ fontSize: 10, padding: '3px 10px', background: 'rgba(0,210,106,0.15)', border: '1px solid rgba(0,210,106,0.3)', color: '#00d26a', borderRadius: 3, fontWeight: 600, marginRight: 8 }}>
              ✦ GOLDEN CROSS
            </span>
          )}
          {deathCross && (
            <span style={{ fontSize: 10, padding: '3px 10px', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', borderRadius: 3, fontWeight: 600, marginRight: 8 }}>
              ✦ DEATH CROSS
            </span>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {maData.filter(m => m.value != null).map(ma => {
            const diff = prices.current_rate && ma.value ? ((prices.current_rate - ma.value) / ma.value * 100) : 0;
            return (
              <div key={ma.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.5)', width: 60, fontWeight: 600 }}>{ma.label}</span>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <HorizontalBar
                    value={Math.min(prices.current_rate, ma.value ?? 0)}
                    max={Math.max(prices.current_rate, ma.value ?? 0) * 1.05}
                    color={ma.above ? '#00d26a' : '#ef4444'}
                    height={6}
                  />
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--terminal-text)', width: 65, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>${fmtNum(ma.value)}</span>
                <span style={{ fontSize: 10, fontWeight: 600, color: ma.above ? '#00d26a' : '#ef4444', width: 55, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                  {fmtPct(diff, 1)}
                </span>
              </div>
            );
          })}
        </div>
      </SectionPanel>

      <SectionPanel title="Price Performance" color="#22d3ee">
        <MetricGrid>
          <MetricCell label="Day" value={fmtPct(prices.daily_change_pct)} color={pctColor(prices.daily_change_pct)} />
          <MetricCell label="Week" value={fmtPct(prices.weekly_change_pct)} color={pctColor(prices.weekly_change_pct)} />
          <MetricCell label="Month" value={fmtPct(prices.monthly_change_pct)} color={pctColor(prices.monthly_change_pct)} />
          <MetricCell label="3 Month" value={fmtPct(prices.three_month_pct)} color={pctColor(prices.three_month_pct)} />
          <MetricCell label="6 Month" value={fmtPct(prices.six_month_pct)} color={pctColor(prices.six_month_pct)} />
          <MetricCell label="YTD" value={fmtPct(prices.ytd_pct)} color={pctColor(prices.ytd_pct)} />
          <MetricCell label="1 Year" value={fmtPct(prices.one_year_pct)} color={pctColor(prices.one_year_pct)} />
          <MetricCell label="2 Year" value={fmtPct(prices.two_year_pct)} color={pctColor(prices.two_year_pct)} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Price Levels" color="#a855f7">
        <MetricGrid>
          <MetricCell label="Current" value={`$${fmtNum(prices.current_rate)}`} />
          <MetricCell label="Prev Close" value={`$${fmtNum(prices.closing_price)}`} />
          <MetricCell label="52W High" value={`$${fmtNum(prices.week_52_high)}`} />
          <MetricCell label="52W Low" value={`$${fmtNum(prices.week_52_low)}`} />
          <MetricCell label="5Y High" value={prices.year_5_high ? `$${fmtNum(prices.year_5_high)}` : '—'} />
          <MetricCell label="5Y Low" value={prices.year_5_low ? `$${fmtNum(prices.year_5_low)}` : '—'} />
          <MetricCell label="Market Cap" value={fmtMcap(prices.market_cap_usd)} />
        </MetricGrid>
      </SectionPanel>

      {betas && (
        <SectionPanel title="Beta (Volatility)" color="#f59e0b">
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {[
              ['12M', betas.beta_12m],
              ['24M', betas.beta_24m],
              ['36M', betas.beta_36m],
              ['60M', betas.beta_60m],
            ].filter(([, v]) => v != null).map(([label, val]) => (
              <div key={label as string} style={{ flex: '1 1 80px', textAlign: 'center', padding: 12, background: 'rgba(245,158,11,0.06)', borderRadius: 6 }}>
                <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.45)', letterSpacing: 1, marginBottom: 4 }}>{label as string}</div>
                <div style={{
                  fontSize: 22, fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                  color: (val as number) > 1.5 ? '#ef4444' : (val as number) > 1 ? '#fbbf24' : '#00d26a',
                }}>
                  {fmtNum(val as number, 2)}
                </div>
              </div>
            ))}
          </div>
        </SectionPanel>
      )}
    </div>
  );
}

function InstrumentFundamentalsTab({ data }: { data: SapiInstrumentData }) {
  const f = data.fundamentals;
  if (!f) return <div style={{ padding: 20, color: 'rgba(224,232,240,0.4)' }}>No fundamentals data available</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <SectionPanel title="Valuation Multiples" color="#8b5cf6">
        <MetricGrid>
          <MetricCell label="P/E (TTM)" value={fmtNum(f.pe_ratio)} />
          <MetricCell label="PEG Ratio" value={fmtNum(f.peg_ratio)} />
          <MetricCell label="P/B" value={fmtNum(f.price_to_book)} />
          <MetricCell label="P/S" value={fmtNum(f.price_to_sales)} />
          <MetricCell label="P/CF" value={fmtNum(f.price_to_cashflow)} />
          <MetricCell label="P/FCF" value={fmtNum(f.price_to_fcf)} />
          <MetricCell label="EV/EBITDA" value={fmtNum(f.ev_to_ebitda)} />
          <MetricCell label="EV/Sales" value={fmtNum(f.ev_to_sales)} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Profitability" color="#10b981">
        <MetricGrid>
          <MetricCell label="Gross Margin" value={`${fmtNum(f.gross_margin, 1)}%`} color={f.gross_margin > 40 ? '#00d26a' : f.gross_margin > 20 ? '#fbbf24' : '#ef4444'} />
          <MetricCell label="Operating Margin" value={`${fmtNum(f.operating_margin, 1)}%`} color={f.operating_margin > 20 ? '#00d26a' : f.operating_margin > 10 ? '#fbbf24' : '#ef4444'} />
          <MetricCell label="Pretax Margin" value={f.pretax_margin ? `${fmtNum(f.pretax_margin, 1)}%` : '—'} />
          <MetricCell label="Net Margin" value={`${fmtNum(f.net_margin, 1)}%`} color={f.net_margin > 15 ? '#00d26a' : f.net_margin > 5 ? '#fbbf24' : '#ef4444'} />
          <MetricCell label="ROE" value={`${fmtNum(f.roe, 1)}%`} color={f.roe > 20 ? '#00d26a' : f.roe > 10 ? '#fbbf24' : '#ef4444'} />
          <MetricCell label="ROA" value={`${fmtNum(f.roa, 1)}%`} />
          <MetricCell label="ROIC" value={f.roic ? `${fmtNum(f.roic * 100, 1)}%` : '—'} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Growth Rates" color="#06b6d4">
        <MetricGrid>
          <MetricCell label="Revenue 1Y" value={`${fmtNum(f.rev_growth_1y, 1)}%`} color={pctColor(f.rev_growth_1y)} />
          <MetricCell label="Revenue 3Y" value={f.rev_growth_3y ? `${fmtNum(f.rev_growth_3y, 1)}%` : '—'} color={pctColor(f.rev_growth_3y)} />
          <MetricCell label="Revenue 5Y" value={f.rev_growth_5y ? `${fmtNum(f.rev_growth_5y, 1)}%` : '—'} color={pctColor(f.rev_growth_5y)} />
          <MetricCell label="Income 1Y" value={f.income_growth_1y ? `${fmtNum(f.income_growth_1y, 1)}%` : '—'} color={pctColor(f.income_growth_1y)} />
          <MetricCell label="Income 3Y" value={f.income_growth_3y ? `${fmtNum(f.income_growth_3y, 1)}%` : '—'} color={pctColor(f.income_growth_3y)} />
          <MetricCell label="Income 5Y" value={f.income_growth_5y ? `${fmtNum(f.income_growth_5y, 1)}%` : '—'} color={pctColor(f.income_growth_5y)} />
          <MetricCell label="EPS 1Y" value={f.eps_growth_1y ? `${fmtNum(f.eps_growth_1y, 1)}%` : '—'} color={pctColor(f.eps_growth_1y)} />
          <MetricCell label="EPS 5Y" value={f.eps_growth_5y ? `${fmtNum(f.eps_growth_5y, 1)}%` : '—'} color={pctColor(f.eps_growth_5y)} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Balance Sheet & Risk" color="#f97316">
        <MetricGrid>
          <MetricCell label="D/E Ratio" value={fmtNum(f.debt_to_equity)} color={f.debt_to_equity > 100 ? '#ef4444' : f.debt_to_equity > 50 ? '#fbbf24' : '#00d26a'} />
          <MetricCell label="Current Ratio" value={fmtNum(f.current_ratio)} color={f.current_ratio >= 1.5 ? '#00d26a' : f.current_ratio >= 1 ? '#fbbf24' : '#ef4444'} />
          <MetricCell label="Quick Ratio" value={fmtNum(f.quick_ratio)} />
          <MetricCell label="Leverage" value={f.leverage_ratio ? `${fmtNum(f.leverage_ratio, 1)}x` : '—'} />
          <MetricCell label="Interest Coverage" value={f.interest_coverage ? `${fmtNum(f.interest_coverage, 1)}x` : '—'} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Per Share Data" color="#ec4899">
        <MetricGrid>
          <MetricCell label="EPS (Basic)" value={`$${fmtNum(f.eps_basic)}`} />
          <MetricCell label="EPS (Diluted)" value={`$${fmtNum(f.eps_diluted)}`} />
          <MetricCell label="Revenue/Share" value={`$${fmtNum(f.revenue_per_share)}`} />
          <MetricCell label="Book Value/Share" value={`$${fmtNum(f.book_value_ps)}`} />
          <MetricCell label="Cash Flow/Share" value={`$${fmtNum(f.cashflow_ps)}`} />
          <MetricCell label="Dividend/Share" value={f.dividend_ps ? `$${fmtNum(f.dividend_ps)}` : '—'} />
          <MetricCell label="Div Yield" value={f.dividend_yield ? `${(f.dividend_yield * 100).toFixed(2)}%` : '—'} />
          <MetricCell label="Shares Out" value={fmtBigNum(f.shares_outstanding)} />
          <MetricCell label="Employees" value={f.employees ? fmtBigNum(f.employees) : '—'} />
        </MetricGrid>
      </SectionPanel>
    </div>
  );
}

function InstrumentAnalystsTab({ data }: { data: SapiInstrumentData }) {
  const a = data.analysts;
  if (!a) return <div style={{ padding: 20, color: 'rgba(224,232,240,0.4)' }}>No analyst data available</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <SectionPanel title="Analyst Consensus" color="#06b6d4">
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <ConsensusDonut buy={a.buy_count} hold={a.hold_count} sell={a.sell_count} />
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{
              fontSize: 28, fontWeight: 700, marginBottom: 8,
              color: a.consensus === 'Buy' ? '#00d26a' : a.consensus === 'Sell' ? '#ef4444' : '#fbbf24',
            }}>
              {a.consensus?.toUpperCase()}
            </div>
            <div style={{ fontSize: 11, color: 'rgba(224,232,240,0.5)', marginBottom: 4 }}>{a.total_analysts} analysts covering</div>
          </div>
        </div>
      </SectionPanel>

      <SectionPanel title="Price Target" color="#8b5cf6">
        {a.target_high && a.target_low && (
          <RangeBar
            current={data.prices?.current_rate ?? 0}
            low={a.target_low}
            high={a.target_high}
            label="Current price within analyst target range"
          />
        )}
        <MetricGrid>
          <MetricCell label="Mean Target" value={`$${fmtNum(a.target_price, 0)}`} />
          <MetricCell label="Upside" value={fmtPct(a.target_upside_pct)} color={pctColor(a.target_upside_pct)} />
          <MetricCell label="Target High" value={a.target_high ? `$${fmtNum(a.target_high, 0)}` : '—'} />
          <MetricCell label="Target Low" value={a.target_low ? `$${fmtNum(a.target_low, 0)}` : '—'} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Earnings" color="#f59e0b">
        <MetricGrid>
          <MetricCell label="Est EPS" value={a.estimated_eps ? `$${fmtNum(a.estimated_eps)}` : '—'} />
          <MetricCell label="Annual EPS Est" value={a.annual_eps_est ? `$${fmtNum(a.annual_eps_est)}` : '—'} />
          <MetricCell label="Quarterly EPS Est" value={a.quarterly_eps_est ? `$${fmtNum(a.quarterly_eps_est)}` : '—'} />
          <MetricCell label="Next Earnings" value={a.next_earnings_date || '—'} color="#f59e0b" />
          <MetricCell label="Quarter" value={a.earnings_quarter || '—'} />
        </MetricGrid>
      </SectionPanel>
    </div>
  );
}

function InstrumentSocialTab({ data }: { data: SapiInstrumentData }) {
  const s = data.social;
  if (!s) return <div style={{ padding: 20, color: 'rgba(224,232,240,0.4)' }}>No social data available</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <SectionPanel title="eToro Trader Sentiment" color="#f97316">
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          {[
            { label: '7D Change', value: s.traders_7d_change },
            { label: '14D Change', value: s.traders_14d_change },
            { label: '30D Change', value: s.traders_30d_change },
          ].map(item => (
            <div key={item.label} style={{ flex: 1, textAlign: 'center', padding: 12, background: 'rgba(249,115,22,0.06)', borderRadius: 6, border: '1px solid rgba(249,115,22,0.15)' }}>
              <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.45)', letterSpacing: 1, marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: pctColor(item.value), fontVariantNumeric: 'tabular-nums' }}>
                {fmtPct(item.value, 1)}
              </div>
            </div>
          ))}
        </div>
      </SectionPanel>

      <SectionPanel title="Position Breakdown" color="#3b82f6">
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 6 }}>
            <span style={{ color: '#00d26a', fontWeight: 600 }}>BUY {fmtNum(s.buy_holding_pct, 0)}%</span>
            <span style={{ color: '#ef4444', fontWeight: 600 }}>SELL {fmtNum(s.sell_holding_pct, 0)}%</span>
          </div>
          <div style={{ display: 'flex', height: 12, borderRadius: 6, overflow: 'hidden' }}>
            <div style={{ width: `${s.buy_holding_pct}%`, background: '#00d26a', transition: 'width 0.4s' }} />
            <div style={{ width: `${s.sell_holding_pct}%`, background: '#ef4444', transition: 'width 0.4s' }} />
          </div>
        </div>

        <MetricGrid>
          <MetricCell label="Popularity Rank" value={String(s.popularity_uniques ?? '—')} />
          <MetricCell label="Popularity 7D" value={String(s.popularity_7d ?? '—')} />
          <MetricCell label="Popularity 14D" value={String(s.popularity_14d ?? '—')} />
          <MetricCell label="Popularity 30D" value={String(s.popularity_30d ?? '—')} />
          <MetricCell label="Holding %" value={`${fmtNum(s.holding_pct, 1)}%`} />
          <MetricCell label="Institutional %" value={`${fmtNum(s.institutional_pct, 1)}%`} />
        </MetricGrid>
      </SectionPanel>
    </div>
  );
}

function InstrumentEsgTab({ data }: { data: SapiInstrumentData }) {
  const e = data.esg;
  if (!e) return <div style={{ padding: 20, color: 'rgba(224,232,240,0.4)' }}>No ESG data available</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <SectionPanel title="ESG Overview" color="#10b981">
        <div style={{ display: 'flex', gap: 24, alignItems: 'center', marginBottom: 16 }}>
          <div style={{
            width: 100, height: 100, borderRadius: '50%',
            border: `5px solid ${scoreColor(e.esg_total)}`,
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: scoreColor(e.esg_total) }}>{fmtNum(e.esg_total, 0)}</div>
            <div style={{ fontSize: 8, color: 'rgba(224,232,240,0.4)', letterSpacing: 1 }}>ESG TOTAL</div>
          </div>
          <div style={{ flex: 1 }}>
            <EsgRadar esg={e} />
          </div>
        </div>
      </SectionPanel>

      <SectionPanel title="Arabesque Scores" color="#14b8a6">
        <MetricGrid>
          <MetricCell label="ESG Total" value={fmtNum(e.esg_total, 1)} color={scoreColor(e.esg_total)} />
          <MetricCell label="Environment" value={fmtNum(e.esg_environment, 1)} color="#10b981" />
          <MetricCell label="Social" value={fmtNum(e.esg_social, 1)} color="#3b82f6" />
          <MetricCell label="Governance" value={fmtNum(e.esg_governance, 1)} color="#8b5cf6" />
          <MetricCell label="Normalized" value={String(e.normalized_score ?? '—')} />
        </MetricGrid>
      </SectionPanel>

      <SectionPanel title="Global Compact" color="#06b6d4">
        <MetricGrid>
          <MetricCell label="GC Total" value={fmtNum(e.gc_total, 1)} />
          <MetricCell label="GC Environment" value={fmtNum(e.gc_environment, 1)} />
          <MetricCell label="Anti-Corruption" value={fmtNum(e.gc_anti_corruption, 1)} />
          <MetricCell label="Human Rights" value={fmtNum(e.human_rights, 1)} />
          <MetricCell label="Labour Rights" value={fmtNum(e.labour_rights, 1)} />
        </MetricGrid>
      </SectionPanel>
    </div>
  );
}

function InstrumentRiskTab({ data }: { data: SapiInstrumentData }) {
  const { betas, fundamentals, prices } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {betas && (
        <SectionPanel title="Beta (Market Sensitivity)" color="#f59e0b">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
            {[
              ['12 Month', betas.beta_12m],
              ['24 Month', betas.beta_24m],
              ['36 Month', betas.beta_36m],
              ['60 Month', betas.beta_60m],
            ].filter(([, v]) => v != null).map(([label, val]) => (
              <div key={label as string} style={{ textAlign: 'center', padding: 16, background: 'rgba(245,158,11,0.06)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.15)' }}>
                <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.45)', letterSpacing: 1, marginBottom: 6 }}>{label as string}</div>
                <div style={{
                  fontSize: 28, fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                  color: (val as number) > 1.5 ? '#ef4444' : (val as number) > 1 ? '#fbbf24' : '#00d26a',
                }}>
                  {fmtNum(val as number)}
                </div>
                <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.35)', marginTop: 4 }}>
                  {(val as number) > 1.5 ? 'High volatility' : (val as number) > 1 ? 'Above market' : (val as number) > 0.5 ? 'Below market' : 'Low volatility'}
                </div>
              </div>
            ))}
          </div>
        </SectionPanel>
      )}

      {fundamentals && (
        <SectionPanel title="Financial Health" color="#ef4444">
          <MetricGrid>
            <MetricCell label="Debt/Equity" value={fmtNum(fundamentals.debt_to_equity)} color={fundamentals.debt_to_equity > 100 ? '#ef4444' : fundamentals.debt_to_equity > 50 ? '#fbbf24' : '#00d26a'} />
            <MetricCell label="Current Ratio" value={fmtNum(fundamentals.current_ratio)} color={fundamentals.current_ratio >= 1.5 ? '#00d26a' : fundamentals.current_ratio >= 1 ? '#fbbf24' : '#ef4444'} />
            <MetricCell label="Quick Ratio" value={fmtNum(fundamentals.quick_ratio)} color={fundamentals.quick_ratio >= 1 ? '#00d26a' : '#fbbf24'} />
            <MetricCell label="Leverage" value={fundamentals.leverage_ratio ? `${fmtNum(fundamentals.leverage_ratio, 1)}x` : '—'} />
            <MetricCell label="Interest Cov." value={fundamentals.interest_coverage ? `${fmtNum(fundamentals.interest_coverage, 1)}x` : '—'} />
          </MetricGrid>
        </SectionPanel>
      )}

      {prices && (
        <SectionPanel title="Drawdown Analysis" color="#a855f7">
          <MetricGrid>
            <MetricCell label="From 52W High" value={prices.week_52_high ? `${fmtNum(((prices.current_rate - prices.week_52_high) / prices.week_52_high) * 100, 1)}%` : '—'} color="#ef4444" />
            <MetricCell label="From 5Y High" value={prices.year_5_high ? `${fmtNum(((prices.current_rate - prices.year_5_high) / prices.year_5_high) * 100, 1)}%` : '—'} color="#ef4444" />
            <MetricCell label="Above 52W Low" value={prices.week_52_low ? `+${fmtNum(((prices.current_rate - prices.week_52_low) / prices.week_52_low) * 100, 1)}%` : '—'} color="#00d26a" />
          </MetricGrid>
        </SectionPanel>
      )}
    </div>
  );
}

function InstrumentView() {
  const [search, setSearch] = useState('');
  const [instruments, setInstruments] = useState<SapiListItem[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [instrumentData, setInstrumentData] = useState<SapiInstrumentData | null>(null);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [tab, setTab] = useState<InstrumentTab>('overview');
  const [sectorFilter, setSectorFilter] = useState('');
  const searchRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const loadList = useCallback(async (s: string, sector: string) => {
    setListLoading(true);
    try {
      const params = new URLSearchParams({ limit: '200' });
      if (s) params.set('search', s);
      if (sector) params.set('sector', sector);
      const res = await fetch(`/api/dcc/sapi/instruments?${params}`);
      const data = await res.json();
      setInstruments(data.instruments ?? []);
      setTotal(data.total ?? 0);
    } catch { /* ignore */ }
    setListLoading(false);
  }, []);

  useEffect(() => { loadList('', ''); }, [loadList]);

  const handleSearch = (val: string) => {
    setSearch(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => loadList(val, sectorFilter), 300);
  };

  const handleSectorChange = (val: string) => {
    setSectorFilter(val);
    loadList(search, val);
  };

  const loadInstrument = useCallback(async (sym: string) => {
    setSelectedSymbol(sym);
    setInstrumentData(null);
    setLoading(true);
    setTab('overview');
    try {
      const res = await fetch(`/api/dcc/sapi/instrument/${sym}`);
      if (res.ok) setInstrumentData(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  const tabs: { key: InstrumentTab; label: string; icon: string }[] = [
    { key: 'overview', label: 'Overview', icon: '◉' },
    { key: 'technicals', label: 'Technicals', icon: '〰' },
    { key: 'fundamentals', label: 'Fundamentals', icon: '◆' },
    { key: 'analysts', label: 'Analysts', icon: '◎' },
    { key: 'social', label: 'Social', icon: '👥' },
    { key: 'esg', label: 'ESG', icon: '🌱' },
    { key: 'risk', label: 'Risk', icon: '⚡' },
  ];

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 2 }}>INSTRUMENT EXPLORER</div>
          <div style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)', marginTop: 2 }}>eToro SAPI — {total.toLocaleString()} instruments • 130+ data points each</div>
        </div>
      </div>

      {/* Search + filter */}
      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ position: 'relative', flex: '1 1 300px' }}>
          <input
            ref={searchRef}
            value={search}
            onChange={e => handleSearch(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && search.trim()) loadInstrument(search.trim().toUpperCase());
            }}
            placeholder="Search symbol or company..."
            style={{
              width: '100%', background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
              color: 'var(--terminal-text)', padding: '8px 12px 8px 32px', fontSize: 11,
              fontFamily: 'inherit', outline: 'none',
            }}
          />
          <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'rgba(224,232,240,0.3)', fontSize: 13 }}>⌕</span>
        </div>
        <select
          value={sectorFilter}
          onChange={e => handleSectorChange(e.target.value)}
          style={{
            background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
            color: 'var(--terminal-text)', padding: '8px 12px', fontSize: 11, fontFamily: 'inherit',
          }}
        >
          <option value="">All Sectors</option>
          {['Information Technology', 'Financials', 'Healthcare', 'Consumer Discretionary', 'Communication Services', 'Industrials', 'Consumer Staples', 'Energy', 'Utilities', 'Real Estate', 'Materials'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <div style={{ alignSelf: 'center', fontSize: 10, color: 'rgba(224,232,240,0.4)' }}>
          {instruments.length} / {total.toLocaleString()}
        </div>
      </div>

      {/* Main: List + Detail */}
      <div style={{ display: 'flex', gap: 12, flex: 1, minHeight: 0 }}>
        {/* Left: Instrument list */}
        <div style={{
          width: 360, minWidth: 360, overflow: 'auto',
          background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
            <thead>
              <tr style={{ position: 'sticky', top: 0, background: 'var(--terminal-panel-bg)', zIndex: 1 }}>
                {['Symbol', 'Price', 'Day', 'YTD', 'MCap', 'P/E'].map(h => (
                  <th key={h} style={{
                    textAlign: h === 'Symbol' ? 'left' : 'right', padding: '7px 8px',
                    borderBottom: '1px solid var(--terminal-panel-border)',
                    color: 'var(--terminal-blue)', fontSize: 9, fontWeight: 700, letterSpacing: 1,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {listLoading && instruments.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: 20, textAlign: 'center', color: 'var(--terminal-blue)', fontSize: 11 }}>Loading...</td></tr>
              ) : instruments.map(inst => (
                <tr
                  key={inst.instrument_id}
                  onClick={() => loadInstrument(inst.symbol)}
                  style={{
                    cursor: 'pointer',
                    background: selectedSymbol === inst.symbol ? 'rgba(0,212,255,0.08)' : 'transparent',
                    borderLeft: selectedSymbol === inst.symbol ? '3px solid var(--terminal-blue)' : '3px solid transparent',
                  }}
                >
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.3)' }}>
                    <div style={{ fontWeight: 600, color: selectedSymbol === inst.symbol ? 'var(--terminal-blue)' : 'var(--terminal-text)' }}>{inst.symbol}</div>
                    <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.4)', maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inst.display_name}</div>
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.3)', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                    {inst.current_rate ? `$${fmtNum(inst.current_rate)}` : '—'}
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.3)', textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: pctColor(inst.daily_change_pct), fontWeight: 600, fontSize: 10 }}>
                    {fmtPct(inst.daily_change_pct, 1)}
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.3)', textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: pctColor(inst.ytd_pct), fontSize: 10 }}>
                    {fmtPct(inst.ytd_pct, 1)}
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.3)', textAlign: 'right', fontSize: 10, color: 'rgba(224,232,240,0.5)' }}>
                    {fmtMcap(inst.market_cap_usd)}
                  </td>
                  <td style={{ padding: '5px 8px', borderBottom: '1px solid rgba(26,35,64,0.3)', textAlign: 'right', fontSize: 10, color: 'rgba(224,232,240,0.6)' }}>
                    {inst.pe_ratio ? fmtNum(inst.pe_ratio, 1) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right: Detail panel */}
        <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          {!selectedSymbol && !loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'rgba(224,232,240,0.3)', fontSize: 13 }}>
              Select an instrument from the list or search above
            </div>
          )}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--terminal-blue)', fontSize: 12 }}>
              Loading {selectedSymbol}...
            </div>
          )}

          {instrumentData && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
              {/* Tab bar */}
              <div style={{ display: 'flex', borderBottom: '1px solid var(--terminal-panel-border)', background: 'var(--terminal-panel-bg)', flexShrink: 0 }}>
                {tabs.map(t => (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    style={{
                      padding: '8px 14px', background: tab === t.key ? 'rgba(0,212,255,0.1)' : 'transparent',
                      border: 'none', borderBottom: tab === t.key ? '2px solid var(--terminal-blue)' : '2px solid transparent',
                      color: tab === t.key ? 'var(--terminal-blue)' : 'rgba(224,232,240,0.5)',
                      cursor: 'pointer', fontFamily: 'inherit', fontSize: 10, fontWeight: 600,
                      letterSpacing: 0.5, display: 'flex', alignItems: 'center', gap: 5,
                    }}
                  >
                    <span style={{ fontSize: 12 }}>{t.icon}</span>
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
                {tab === 'overview' && <InstrumentOverviewTab data={instrumentData} />}
                {tab === 'technicals' && <InstrumentTechnicalsTab data={instrumentData} />}
                {tab === 'fundamentals' && <InstrumentFundamentalsTab data={instrumentData} />}
                {tab === 'analysts' && <InstrumentAnalystsTab data={instrumentData} />}
                {tab === 'social' && <InstrumentSocialTab data={instrumentData} />}
                {tab === 'esg' && <InstrumentEsgTab data={instrumentData} />}
                {tab === 'risk' && <InstrumentRiskTab data={instrumentData} />}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --------------- Symbol View ---------------

interface PlatinumRecord {
  ticker: string;
  generated_at: string;
  tier: string;
  version: string;
  profile: { name: string; sector: string; industry: string; market_cap: number; employees: number; country: string; exchange: string } | null;
  price: { current: number; previous_close: number; change_pct: number; day_high: number; day_low: number; volume: number; avg_volume: number } | null;
  technicals: Record<string, number | null> | null;
  valuation: Record<string, number | null> | null;
  fundamentals: Record<string, number | null> | null;
  dividend: Record<string, number | string | null> | null;
  estimate_revisions: Record<string, unknown> | null;
  analyst_targets: { mean_target: number | null; median_target: number | null; high_target: number | null; low_target: number | null; upside_pct: number | null; num_analysts: number | null; assessment: { rating: string; color: string } | null } | null;
  earnings_quality: Record<string, unknown> | null;
  earnings_surprises: Record<string, unknown> | null;
  composite: { composite_score: number; component_scores: Record<string, number>; weights_used: Record<string, number>; coverage: number; max_coverage: number } | null;
  _meta: { elapsed_seconds: number; sections_populated: number; total_sections: number } | null;
}

interface DashboardItem {
  ticker: string;
  name: string;
  sector: string;
  market_cap: number;
  price: number;
  change_pct: number;
  composite_score: number;
  rating: string | null;
  gf_score: number | null;
  pe_forward: number | null;
  rsi_14: number | null;
  profit_margin: number | null;
  analyst_upside: number | null;
  beat_rate: number | null;
  generated_at: string;
}

type TreeNode = { label: string; children: TreeNode[]; symbols: DashboardItem[] };

function buildTree(items: DashboardItem[]): TreeNode[] {
  const sectorMap = new Map<string, Map<string, DashboardItem[]>>();
  for (const item of items) {
    const sector = item.sector || 'Other';
    if (!sectorMap.has(sector)) sectorMap.set(sector, new Map());
    const industryMap = sectorMap.get(sector)!;
    const industry = 'All';
    if (!industryMap.has(industry)) industryMap.set(industry, []);
    industryMap.get(industry)!.push(item);
  }

  return [...sectorMap.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([sector, industryMap]) => ({
      label: sector,
      children: [],
      symbols: [...industryMap.values()].flat().sort((a, b) => (b.composite_score ?? 0) - (a.composite_score ?? 0)),
    }));
}

function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const color = score >= 80 ? '#00d26a' : score >= 60 ? '#fbbf24' : score >= 40 ? '#f97316' : '#ef4444';

  return (
    <svg width={size} height={size} style={{ display: 'block' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(224,232,240,0.08)" strokeWidth={8} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={8} strokeLinecap="round"
        strokeDasharray={`${pct * circ} ${circ}`}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
      <text x={size / 2} y={size / 2 - 6} textAnchor="middle" fill={color} fontSize={size * 0.28} fontWeight={700} fontFamily="inherit">
        {score.toFixed(1)}
      </text>
      <text x={size / 2} y={size / 2 + 14} textAnchor="middle" fill="rgba(224,232,240,0.5)" fontSize={10} fontFamily="inherit">
        PLATINUM
      </text>
    </svg>
  );
}

function ComponentBar({ label, score, weight }: { label: string; score: number; weight: number }) {
  const color = score >= 80 ? 'var(--terminal-green)' : score >= 60 ? '#fbbf24' : score >= 40 ? '#f97316' : 'var(--terminal-red)';
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 4 }}>
        <span style={{ color: 'var(--terminal-text)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 1 }}>{label}</span>
        <span style={{ color, fontWeight: 700 }}>{score.toFixed(1)} <span style={{ color: 'rgba(224,232,240,0.3)', fontWeight: 400 }}>({(weight * 100).toFixed(0)}%)</span></span>
      </div>
      <div style={{ height: 6, background: 'rgba(224,232,240,0.06)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.min(100, score)}%`, background: color, borderRadius: 3, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
}

function DataSection({ title, data, color }: { title: string; data: Record<string, unknown> | null; color?: string }) {
  const [open, setOpen] = useState(true);
  if (!data) return null;
  const entries = Object.entries(data).filter(([, v]) => v != null && v !== '' && typeof v !== 'object');

  if (entries.length === 0) return null;

  const fmt = (key: string, val: unknown): string => {
    if (val == null) return '—';
    if (typeof val === 'number') {
      if (key.includes('margin') || key.includes('growth') || key.includes('roe') || key.includes('roa') || key.includes('yield') || key.includes('payout') || key.includes('pct') || key.includes('percent'))
        return `${(val * (Math.abs(val) < 5 ? 100 : 1)).toFixed(2)}%`;
      if (key.includes('cap') || key.includes('revenue') || key.includes('flow') || key.includes('volume'))
        return val >= 1e12 ? `$${(val / 1e12).toFixed(2)}T` : val >= 1e9 ? `$${(val / 1e9).toFixed(2)}B` : val >= 1e6 ? `$${(val / 1e6).toFixed(1)}M` : val.toLocaleString();
      return val.toFixed(2);
    }
    return String(val);
  };

  const labelMap: Record<string, string> = {
    pe_trailing: 'P/E (TTM)', pe_forward: 'P/E (Fwd)', peg_ratio: 'PEG', pb_ratio: 'P/B', ps_ratio: 'P/S',
    ev_ebitda: 'EV/EBITDA', ev_revenue: 'EV/Revenue', price_to_fcf: 'P/FCF',
    sma_20: 'SMA 20', sma_50: 'SMA 50', sma_200: 'SMA 200', rsi_14: 'RSI 14',
    price_vs_sma20: 'vs SMA20', price_vs_sma50: 'vs SMA50',
    high_52w: '52W High', low_52w: '52W Low', pct_from_52w_high: 'From 52W High',
    revenue_growth: 'Rev Growth', gross_margin: 'Gross Margin', operating_margin: 'Op Margin', profit_margin: 'Profit Margin',
    debt_to_equity: 'D/E', current_ratio: 'Current Ratio', free_cash_flow: 'FCF',
    eps_trailing: 'EPS (TTM)', eps_forward: 'EPS (Fwd)',
    mean_target: 'Mean Target', median_target: 'Median Target', upside_pct: 'Upside %',
    beat_rate: 'Beat Rate', avg_surprise_pct: 'Avg Surprise', consecutive_beats: 'Consec Beats',
    accruals_ratio: 'Accruals Ratio', beneish_m_score: 'Beneish M', altman_z_score: 'Altman Z',
    change_pct: 'Change %', day_high: 'Day High', day_low: 'Day Low', avg_volume: 'Avg Volume',
    previous_close: 'Prev Close', current: 'Price', num_analysts: '# Analysts', ex_date: 'Ex-Date',
  };

  return (
    <div style={{ background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)', marginBottom: 8, overflow: 'hidden' }}>
      <button onClick={() => setOpen(!open)} style={{
        width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '10px 14px', background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'inherit',
      }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: color ?? 'var(--terminal-blue)', letterSpacing: 1.5, textTransform: 'uppercase' }}>{title}</span>
        <span style={{ color: 'rgba(224,232,240,0.4)', fontSize: 12 }}>{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div style={{ padding: '0 14px 12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '6px 20px' }}>
          {entries.map(([key, val]) => (
            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '3px 0', borderBottom: '1px solid rgba(26,35,64,0.3)' }}>
              <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.5)' }}>{labelMap[key] ?? key.replace(/_/g, ' ')}</span>
              <span style={{ fontSize: 11, color: 'var(--terminal-text)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                {fmt(key, val)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SymbolView() {
  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState<DashboardItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [allSymbols, setAllSymbols] = useState<DashboardItem[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [symbolData, setSymbolData] = useState<PlatinumRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());
  const searchRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const [highlightIdx, setHighlightIdx] = useState(-1);

  useEffect(() => {
    fetch('/api/v1/platinum/dashboard?sort=composite_score&limit=200')
      .then(r => r.json())
      .then(d => {
        const items: DashboardItem[] = d.data ?? [];
        setAllSymbols(items);
        setTreeData(buildTree(items));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!search.trim()) { setSuggestions([]); return; }
    const q = search.toUpperCase();
    const filtered = allSymbols.filter(s =>
      s.ticker.includes(q) || (s.name && s.name.toUpperCase().includes(q))
    ).slice(0, 12);
    setSuggestions(filtered);
    setHighlightIdx(-1);
  }, [search, allSymbols]);

  const loadSymbol = useCallback(async (ticker: string) => {
    setSelectedSymbol(ticker);
    setSymbolData(null);
    setLoading(true);
    setShowSuggestions(false);
    setSearch('');
    try {
      const res = await fetch(`/api/v1/platinum/${ticker}?mode=full`);
      const data = await res.json();
      setSymbolData(data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  const handleSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIdx(prev => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIdx(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightIdx >= 0 && suggestions[highlightIdx]) {
        loadSymbol(suggestions[highlightIdx].ticker);
      } else if (search.trim()) {
        loadSymbol(search.trim().toUpperCase());
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node) && e.target !== searchRef.current) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const toggleSector = (sector: string) => {
    setExpandedSectors(prev => {
      const next = new Set(prev);
      if (next.has(sector)) next.delete(sector); else next.add(sector);
      return next;
    });
  };

  const scoreColor = (s: number) => s >= 80 ? 'var(--terminal-green)' : s >= 60 ? '#fbbf24' : s >= 40 ? '#f97316' : 'var(--terminal-red)';

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#a855f7', letterSpacing: 2 }}>SYMBOL VIEW</div>
          <div style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)', marginTop: 2 }}>Platinum Enriched Records — {allSymbols.length} symbols</div>
        </div>
      </div>

      {/* Search with autocomplete */}
      <div style={{ position: 'relative', maxWidth: 500 }}>
        <input
          ref={searchRef}
          value={search}
          onChange={e => { setSearch(e.target.value); setShowSuggestions(true); }}
          onFocus={() => { if (suggestions.length > 0) setShowSuggestions(true); }}
          onKeyDown={handleSearchKey}
          placeholder="Search symbol or company name..."
          style={{
            width: '100%', background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
            color: 'var(--terminal-text)', padding: '10px 14px 10px 36px', fontSize: 12,
            fontFamily: 'inherit', outline: 'none', letterSpacing: 0.5,
          }}
        />
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'rgba(224,232,240,0.3)', fontSize: 14 }}>⌕</span>

        {showSuggestions && suggestions.length > 0 && (
          <div ref={suggestionsRef} style={{
            position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
            background: '#0f1117', border: '1px solid var(--terminal-panel-border)', borderTop: 'none',
            maxHeight: 320, overflow: 'auto', boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          }}>
            {suggestions.map((s, i) => (
              <div
                key={s.ticker}
                onClick={() => loadSymbol(s.ticker)}
                onMouseEnter={() => setHighlightIdx(i)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 14px', cursor: 'pointer',
                  background: i === highlightIdx ? 'rgba(168,85,247,0.12)' : 'transparent',
                  borderBottom: '1px solid rgba(26,35,64,0.3)',
                }}
              >
                <div>
                  <span style={{ color: '#a855f7', fontWeight: 700, marginRight: 8, fontSize: 12 }}>{s.ticker}</span>
                  <span style={{ color: 'rgba(224,232,240,0.6)', fontSize: 11 }}>{s.name}</span>
                </div>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)' }}>{s.sector}</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: scoreColor(s.composite_score) }}>{s.composite_score?.toFixed(1) ?? '—'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Main area: Tree + Detail */}
      <div style={{ display: 'flex', gap: 12, flex: 1, minHeight: 0 }}>
        {/* Left: Tree */}
        <div style={{
          width: 280, minWidth: 280, overflow: 'auto',
          background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
        }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--terminal-panel-border)', fontSize: 10, fontWeight: 700, color: 'var(--terminal-blue)', letterSpacing: 1.5 }}>
            ASSET CLASS TREE
          </div>
          {treeData.map(sector => (
            <div key={sector.label}>
              <button
                onClick={() => toggleSector(sector.label)}
                style={{
                  width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 14px', background: expandedSectors.has(sector.label) ? 'rgba(168,85,247,0.06)' : 'transparent',
                  border: 'none', borderBottom: '1px solid rgba(26,35,64,0.3)',
                  cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left',
                }}
              >
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--terminal-text)' }}>
                  {expandedSectors.has(sector.label) ? '▾' : '▸'} {sector.label}
                </span>
                <span style={{ fontSize: 9, color: 'rgba(224,232,240,0.4)' }}>{sector.symbols.length}</span>
              </button>
              {expandedSectors.has(sector.label) && sector.symbols.map(sym => (
                <button
                  key={sym.ticker}
                  onClick={() => loadSymbol(sym.ticker)}
                  style={{
                    width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '5px 14px 5px 28px',
                    background: selectedSymbol === sym.ticker ? 'rgba(168,85,247,0.12)' : 'transparent',
                    borderLeft: selectedSymbol === sym.ticker ? '3px solid #a855f7' : '3px solid transparent',
                    border: 'none', borderBottom: '1px solid rgba(26,35,64,0.15)',
                    cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left',
                  }}
                >
                  <div>
                    <span style={{ fontSize: 10, fontWeight: 600, color: selectedSymbol === sym.ticker ? '#a855f7' : 'var(--terminal-text)', marginRight: 6 }}>{sym.ticker}</span>
                    <span style={{ fontSize: 9, color: 'rgba(224,232,240,0.4)' }}>{sym.name?.slice(0, 20)}</span>
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: scoreColor(sym.composite_score), fontVariantNumeric: 'tabular-nums' }}>
                    {sym.composite_score?.toFixed(1) ?? '—'}
                  </span>
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Right: Detail */}
        <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 0 }}>
          {!selectedSymbol && !loading && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%',
              color: 'rgba(224,232,240,0.3)', fontSize: 13,
            }}>
              Select a symbol from the tree or search above
            </div>
          )}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#a855f7', fontSize: 12 }}>
              Loading {selectedSymbol}...
            </div>
          )}

          {symbolData && !loading && (
            <div>
              {/* Hero: Score + Profile */}
              <div style={{
                display: 'flex', gap: 24, alignItems: 'center',
                background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)',
                padding: 20, marginBottom: 8,
              }}>
                <ScoreRing score={symbolData.composite?.composite_score ?? 0} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
                    <span style={{ fontSize: 22, fontWeight: 700, color: '#a855f7', letterSpacing: 1 }}>{symbolData.ticker}</span>
                    <span style={{ fontSize: 13, color: 'var(--terminal-text)' }}>{symbolData.profile?.name}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 10, color: 'rgba(224,232,240,0.5)', marginBottom: 12, flexWrap: 'wrap' }}>
                    {symbolData.profile?.sector && <span>{symbolData.profile.sector}</span>}
                    {symbolData.profile?.industry && <span>• {symbolData.profile.industry}</span>}
                    {symbolData.profile?.exchange && <span>• {symbolData.profile.exchange}</span>}
                    {symbolData.profile?.country && <span>• {symbolData.profile.country}</span>}
                    {symbolData.profile?.market_cap && (
                      <span>• MCap {symbolData.profile.market_cap >= 1e12 ? `$${(symbolData.profile.market_cap / 1e12).toFixed(2)}T` : `$${(symbolData.profile.market_cap / 1e9).toFixed(1)}B`}</span>
                    )}
                  </div>

                  {/* Price strip */}
                  {symbolData.price && (
                    <div style={{ display: 'flex', gap: 20, alignItems: 'baseline' }}>
                      <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--terminal-text)' }}>${symbolData.price.current?.toFixed(2)}</span>
                      <span style={{
                        fontSize: 13, fontWeight: 600,
                        color: (symbolData.price.change_pct ?? 0) >= 0 ? 'var(--terminal-green)' : 'var(--terminal-red)',
                      }}>
                        {(symbolData.price.change_pct ?? 0) >= 0 ? '+' : ''}{symbolData.price.change_pct?.toFixed(2)}%
                      </span>
                      <span style={{ fontSize: 10, color: 'rgba(224,232,240,0.4)' }}>
                        Vol {symbolData.price.volume != null ? (symbolData.price.volume >= 1e6 ? `${(symbolData.price.volume / 1e6).toFixed(1)}M` : symbolData.price.volume.toLocaleString()) : '—'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Analyst target */}
                {symbolData.analyst_targets?.assessment && (
                  <div style={{ textAlign: 'right', minWidth: 120 }}>
                    <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.5)', letterSpacing: 1, marginBottom: 4 }}>ANALYST</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: symbolData.analyst_targets.assessment.color === 'green' ? 'var(--terminal-green)' : symbolData.analyst_targets.assessment.color === 'red' ? 'var(--terminal-red)' : '#fbbf24' }}>
                      {symbolData.analyst_targets.assessment.rating?.split(' - ')[0]}
                    </div>
                    {symbolData.analyst_targets.mean_target != null && (
                      <div style={{ fontSize: 11, color: 'rgba(224,232,240,0.5)', marginTop: 4 }}>
                        Target ${symbolData.analyst_targets.mean_target.toFixed(0)} ({symbolData.analyst_targets.upside_pct?.toFixed(1)}%)
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Score breakdown */}
              {symbolData.composite && (
                <div style={{ background: 'var(--terminal-panel-bg)', border: '1px solid var(--terminal-panel-border)', padding: '14px 16px', marginBottom: 8 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#a855f7', letterSpacing: 1.5, marginBottom: 12 }}>SCORE COMPOSITION</div>
                  {Object.entries(symbolData.composite.component_scores).map(([key, score]) => (
                    <ComponentBar key={key} label={key} score={score} weight={symbolData.composite!.weights_used[key] ?? 0} />
                  ))}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'rgba(224,232,240,0.4)', marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(26,35,64,0.3)' }}>
                    <span>Coverage: {symbolData.composite.coverage}/{symbolData.composite.max_coverage} sources</span>
                    <span>Generated: {new Date(symbolData.generated_at).toLocaleString('en-US', { hour12: false })}</span>
                  </div>
                </div>
              )}

              {/* Data sections */}
              <DataSection title="Price & Trading" data={symbolData.price} color="#22d3ee" />
              <DataSection title="Technicals" data={symbolData.technicals} color="#3b82f6" />
              <DataSection title="Valuation" data={symbolData.valuation} color="#8b5cf6" />
              <DataSection title="Fundamentals" data={symbolData.fundamentals} color="#10b981" />
              <DataSection title="Dividend" data={symbolData.dividend as Record<string, unknown> | null} color="#f59e0b" />
              <DataSection title="Analyst Targets" data={symbolData.analyst_targets ? { mean_target: symbolData.analyst_targets.mean_target, median_target: symbolData.analyst_targets.median_target, upside_pct: symbolData.analyst_targets.upside_pct, num_analysts: symbolData.analyst_targets.num_analysts } : null} color="#06b6d4" />
              <DataSection title="Earnings Quality" data={symbolData.earnings_quality as Record<string, unknown> | null} color="#ec4899" />
              <DataSection title="Earnings Surprises" data={symbolData.earnings_surprises as Record<string, unknown> | null} color="#f97316" />
              <DataSection title="Estimate Revisions" data={symbolData.estimate_revisions as Record<string, unknown> | null} color="#14b8a6" />

              {symbolData._meta && (
                <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.3)', padding: '8px 0', textAlign: 'right' }}>
                  {symbolData._meta.sections_populated}/{symbolData._meta.total_sections} sections • {symbolData._meta.elapsed_seconds?.toFixed(1)}s
                </div>
              )}
            </div>
          )}
        </div>
      </div>
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
        '4': 'quality', '5': 'alerts', '6': 'sources', '7': 'config', '8': 'symbol-view', '9': 'instrument-view', '0': 'nl-query',
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
    case 'symbol-view': return <SymbolView />;
    case 'instrument-view': return <InstrumentView />;
    case 'nl-query': return <Suspense fallback={<div style={{ padding: 40, color: 'var(--terminal-text)' }}>Loading NL Query...</div>}><NLQueryView /></Suspense>;
    default: return <MissionControl />;
  }
}
