'use client';

import { useEffect, useState } from 'react';
import { useTerminalStore } from '@/store/terminal-store';
import TerminalGrid from '@/components/terminal/TerminalGrid';
import CommandBar from '@/components/terminal/CommandBar';
import TickerPanel from '@/components/panels/TickerPanel';

export const dynamic = 'force-dynamic';

function PresetButtons() {
  const { loadPreset } = useTerminalStore();
  const presets = ['DEFAULT', 'TRADING', 'RESEARCH', 'OVERVIEW'];

  return (
    <div
      style={{
        display: 'flex',
        gap: '8px',
        alignItems: 'center',
      }}
    >
      {presets.map((preset) => (
        <button
          key={preset}
          onClick={() => loadPreset(preset)}
          style={{
            padding: '6px 12px',
            background: 'transparent',
            border: '1px solid #1a2340',
            borderRadius: '4px',
            color: '#e0e8f0',
            fontSize: '10px',
            fontWeight: 600,
            letterSpacing: '0.5px',
            cursor: 'pointer',
            fontFamily: 'IBM Plex Mono, monospace',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#00d4ff';
            e.currentTarget.style.background = 'rgba(0, 212, 255, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#1a2340';
            e.currentTarget.style.background = 'transparent';
          }}
        >
          {preset}
        </button>
      ))}
    </div>
  );
}

export default function HomePage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const { commandBarOpen, toggleCommandBar, activePanel, removePanel } = useTerminalStore();

  // Update clock every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or / - Open command bar
      if ((e.ctrlKey && e.key === 'k') || e.key === '/') {
        if (!commandBarOpen) {
          e.preventDefault();
          toggleCommandBar();
        }
      }
      
      // Ctrl+N - New panel (open command bar)
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        if (!commandBarOpen) {
          toggleCommandBar();
        }
      }
      
      // Ctrl+W - Close active panel
      if (e.ctrlKey && e.key === 'w') {
        e.preventDefault();
        if (activePanel) {
          removePanel(activePanel);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandBarOpen, toggleCommandBar, activePanel, removePanel]);

  return (
    <div
      className="terminal-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        background: '#0a0e27',
        overflow: 'hidden',
      }}
    >
      {/* Top Bar */}
      <div
        className="terminal-topbar"
        style={{
          background: '#0f1629',
          borderBottom: '2px solid #1a2340',
          padding: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '50px',
          zIndex: 100,
        }}
      >
        <div
          className="terminal-brand"
          style={{
            fontSize: '16px',
            fontWeight: 700,
            letterSpacing: '1px',
            color: '#00d4ff',
            textTransform: 'uppercase',
          }}
        >
          QUANTCLAW DATA
        </div>
        
        <PresetButtons />

        <div
          className="terminal-status"
          style={{
            display: 'flex',
            gap: '20px',
            alignItems: 'center',
            fontSize: '11px',
          }}
        >
          <div
            className="terminal-live-indicator"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: '#00ff41',
            }}
          >
            <div
              className="terminal-live-dot"
              style={{
                width: '8px',
                height: '8px',
                background: '#00ff41',
                borderRadius: '50%',
                animation: 'pulse 2s infinite',
              }}
            />
            LIVE
          </div>
          <div
            className="terminal-clock"
            style={{
              color: '#e0e8f0',
              fontWeight: 500,
            }}
          >
            {currentTime.toLocaleTimeString('en-US', { hour12: false })}
          </div>
        </div>
      </div>

      {/* Ticker Marquee */}
      <TickerPanel />

      {/* Terminal Grid */}
      <TerminalGrid />

      {/* Command Bar Overlay */}
      <CommandBar isOpen={commandBarOpen} onClose={toggleCommandBar} />
    </div>
  );
}
