'use client';

import { useTerminalStore } from '@/store/terminal-store';
import { services, categories } from '@/app/services';

export default function WelcomePanel() {
  const { addPanel, toggleCommandBar } = useTerminalStore();

  const handleQuickAction = (moduleId: string, ticker?: string) => {
    const service = services.find((s) => s.id === moduleId);
    if (!service) return;

    const panelId = `${moduleId}-${Date.now()}`;
    addPanel({
      id: panelId,
      type: 'data-module',
      title: ticker ? `${service.name} - ${ticker}` : service.name,
      x: 0,
      y: 0,
      w: 6,
      h: 6,
      props: {
        moduleId,
        ticker,
      },
    });
  };

  // Count sources from categories (rough approximation)
  const sourceCount = 194;
  const moduleCount = services.length;

  return (
    <div className="terminal-welcome" style={{ padding: '24px' }}>
      <div
        className="terminal-welcome-title"
        style={{
          fontSize: '24px',
          fontWeight: 700,
          color: '#00d4ff',
          marginBottom: '16px',
          letterSpacing: '2px',
        }}
      >
        QUANTCLAW DATA TERMINAL
      </div>

      <div style={{ fontSize: '11px', color: 'rgba(224, 232, 240, 0.7)', marginBottom: '24px' }}>
        Bloomberg-style financial intelligence platform powered by {moduleCount} data modules
      </div>

      <div
        className="terminal-welcome-stats"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          margin: '24px 0',
        }}
      >
        <div
          className="terminal-welcome-stat"
          style={{
            background: 'rgba(0, 212, 255, 0.05)',
            padding: '16px',
            borderLeft: '3px solid #00d4ff',
          }}
        >
          <div
            className="terminal-welcome-stat-label"
            style={{
              fontSize: '10px',
              color: 'rgba(224, 232, 240, 0.6)',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              marginBottom: '8px',
            }}
          >
            Data Modules
          </div>
          <div
            className="terminal-welcome-stat-value"
            style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#00d4ff',
            }}
          >
            {moduleCount}
          </div>
        </div>

        <div
          className="terminal-welcome-stat"
          style={{
            background: 'rgba(0, 255, 65, 0.05)',
            padding: '16px',
            borderLeft: '3px solid #00ff41',
          }}
        >
          <div
            className="terminal-welcome-stat-label"
            style={{
              fontSize: '10px',
              color: 'rgba(224, 232, 240, 0.6)',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              marginBottom: '8px',
            }}
          >
            Data Sources
          </div>
          <div
            className="terminal-welcome-stat-value"
            style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#00ff41',
            }}
          >
            {sourceCount}
          </div>
        </div>

        <div
          className="terminal-welcome-stat"
          style={{
            background: 'rgba(255, 215, 0, 0.05)',
            padding: '16px',
            borderLeft: '3px solid #ffd700',
          }}
        >
          <div
            className="terminal-welcome-stat-label"
            style={{
              fontSize: '10px',
              color: 'rgba(224, 232, 240, 0.6)',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              marginBottom: '8px',
            }}
          >
            Categories
          </div>
          <div
            className="terminal-welcome-stat-value"
            style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#ffd700',
            }}
          >
            {categories.length}
          </div>
        </div>
      </div>

      <div
        className="terminal-welcome-actions"
        style={{
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap',
          margin: '24px 0',
        }}
      >
        <button
          className="terminal-welcome-button"
          onClick={() => handleQuickAction('prices', 'AAPL')}
          style={{
            background: '#1a2340',
            border: '1px solid #00d4ff',
            color: '#00d4ff',
            padding: '10px 16px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '11px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            fontWeight: 600,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 212, 255, 0.2)';
            e.currentTarget.style.boxShadow = '0 0 10px rgba(0, 212, 255, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#1a2340';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          📊 AAPL Price
        </button>
        <button
          className="terminal-welcome-button"
          onClick={() => handleQuickAction('options', 'TSLA')}
          style={{
            background: '#1a2340',
            border: '1px solid #00d4ff',
            color: '#00d4ff',
            padding: '10px 16px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '11px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            fontWeight: 600,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 212, 255, 0.2)';
            e.currentTarget.style.boxShadow = '0 0 10px rgba(0, 212, 255, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#1a2340';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          📋 TSLA Options
        </button>
        <button
          className="terminal-welcome-button"
          onClick={() => handleQuickAction('congress-trades')}
          style={{
            background: '#1a2340',
            border: '1px solid #00d4ff',
            color: '#00d4ff',
            padding: '10px 16px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '11px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            fontWeight: 600,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 212, 255, 0.2)';
            e.currentTarget.style.boxShadow = '0 0 10px rgba(0, 212, 255, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#1a2340';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          🏛️ Congress Trades
        </button>
        <button
          className="terminal-welcome-button"
          onClick={() => toggleCommandBar()}
          style={{
            background: '#1a2340',
            border: '1px solid #00ff41',
            color: '#00ff41',
            padding: '10px 16px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '11px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            fontWeight: 600,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 255, 65, 0.2)';
            e.currentTarget.style.boxShadow = '0 0 10px rgba(0, 255, 65, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#1a2340';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          ⌨️ Open Command Bar
        </button>
      </div>

      <div
        className="terminal-welcome-shortcuts"
        style={{
          marginTop: '32px',
          paddingTop: '24px',
          borderTop: '1px solid #1a2340',
        }}
      >
        <div
          className="terminal-welcome-shortcuts-title"
          style={{
            fontSize: '12px',
            fontWeight: 600,
            color: '#00d4ff',
            marginBottom: '12px',
            textTransform: 'uppercase',
            letterSpacing: '1px',
          }}
        >
          Keyboard Shortcuts
        </div>
        <div className="terminal-shortcut-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '11px' }}>
          <span className="terminal-shortcut-key" style={{ color: '#00ff41', fontWeight: 600 }}>
            Ctrl+K or /
          </span>
          <span className="terminal-shortcut-desc" style={{ color: 'rgba(224, 232, 240, 0.7)' }}>
            Open command bar
          </span>
        </div>
        <div className="terminal-shortcut-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '11px' }}>
          <span className="terminal-shortcut-key" style={{ color: '#00ff41', fontWeight: 600 }}>
            Ctrl+N
          </span>
          <span className="terminal-shortcut-desc" style={{ color: 'rgba(224, 232, 240, 0.7)' }}>
            New panel
          </span>
        </div>
        <div className="terminal-shortcut-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '11px' }}>
          <span className="terminal-shortcut-key" style={{ color: '#00ff41', fontWeight: 600 }}>
            Ctrl+W
          </span>
          <span className="terminal-shortcut-desc" style={{ color: 'rgba(224, 232, 240, 0.7)' }}>
            Close active panel
          </span>
        </div>
        <div className="terminal-shortcut-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '11px' }}>
          <span className="terminal-shortcut-key" style={{ color: '#00ff41', fontWeight: 600 }}>
            Drag header
          </span>
          <span className="terminal-shortcut-desc" style={{ color: 'rgba(224, 232, 240, 0.7)' }}>
            Move panel
          </span>
        </div>
        <div className="terminal-shortcut-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '11px' }}>
          <span className="terminal-shortcut-key" style={{ color: '#00ff41', fontWeight: 600 }}>
            Drag corner
          </span>
          <span className="terminal-shortcut-desc" style={{ color: 'rgba(224, 232, 240, 0.7)' }}>
            Resize panel
          </span>
        </div>
      </div>
    </div>
  );
}
