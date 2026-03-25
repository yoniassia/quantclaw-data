'use client';

import { useDCCStore, DCCView } from '@/store/dcc-store';

const NAV_ITEMS: { key: DCCView; label: string; icon: string; shortcut: string }[] = [
  { key: 'mission-control', label: 'MISSION CTRL', icon: '◉', shortcut: '1' },
  { key: 'module-explorer', label: 'MODULES', icon: '☰', shortcut: '2' },
  { key: 'pipeline', label: 'PIPELINE', icon: '▶', shortcut: '3' },
  { key: 'quality', label: 'QUALITY', icon: '◆', shortcut: '4' },
  { key: 'alerts', label: 'ALERTS', icon: '⚠', shortcut: '5' },
  { key: 'sources', label: 'SOURCES', icon: '⊕', shortcut: '6' },
  { key: 'config', label: 'CONFIG', icon: '⚙', shortcut: '7' },
  { key: 'symbol-view', label: 'SYMBOL', icon: '◈', shortcut: '8' },
  { key: 'instrument-view', label: 'INSTRUMENTS', icon: '📊', shortcut: '9' },
  { key: 'nl-query', label: 'NL QUERY', icon: '💬', shortcut: '0' },
];

export default function DCCLayout({ children }: { children: React.ReactNode }) {
  const { view, setView } = useDCCStore();

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <nav style={{
        width: 180,
        minWidth: 180,
        background: 'var(--terminal-panel-bg)',
        borderRight: '1px solid var(--terminal-panel-border)',
        display: 'flex',
        flexDirection: 'column',
        paddingTop: 16,
      }}>
        <div style={{
          padding: '0 16px 20px',
          fontSize: 14,
          fontWeight: 700,
          color: 'var(--terminal-blue)',
          letterSpacing: 2,
          borderBottom: '1px solid var(--terminal-panel-border)',
          marginBottom: 8,
        }}>
          DCC
          <div style={{ fontSize: 9, color: 'rgba(224,232,240,0.5)', letterSpacing: 1, marginTop: 4, fontWeight: 400 }}>
            DATA CONTROL CENTRE
          </div>
        </div>

        {NAV_ITEMS.map(item => (
          <button
            key={item.key}
            onClick={() => setView(item.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 16px',
              background: view === item.key ? 'rgba(0,212,255,0.1)' : 'transparent',
              border: 'none',
              borderLeft: view === item.key ? '3px solid var(--terminal-blue)' : '3px solid transparent',
              color: view === item.key ? 'var(--terminal-blue)' : 'var(--terminal-text)',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: 11,
              fontWeight: view === item.key ? 600 : 400,
              letterSpacing: 1,
              textAlign: 'left',
              transition: 'all 0.15s',
            }}
          >
            <span style={{ fontSize: 13 }}>{item.icon}</span>
            <span>{item.label}</span>
            <span style={{
              marginLeft: 'auto',
              fontSize: 9,
              opacity: 0.4,
              fontWeight: 400,
            }}>{item.shortcut}</span>
          </button>
        ))}

        <div style={{ flex: 1 }} />
        <div style={{
          padding: '12px 16px',
          fontSize: 9,
          color: 'rgba(224,232,240,0.3)',
          borderTop: '1px solid var(--terminal-panel-border)',
        }}>
          QUANTCLAW DATA v1.0
        </div>
      </nav>

      <main style={{ flex: 1, overflow: 'auto', background: 'var(--terminal-bg)' }}>
        {children}
      </main>
    </div>
  );
}
