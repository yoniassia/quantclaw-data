'use client';

import { ReactNode } from 'react';
import { useTerminalStore } from '@/store/terminal-store';

interface PanelProps {
  id: string;
  title: string;
  children: ReactNode;
  onRefresh?: () => void;
}

export default function Panel({ id, title, children, onRefresh }: PanelProps) {
  const { activePanel, setActivePanel, removePanel } = useTerminalStore();
  const isActive = activePanel === id;

  return (
    <div
      className={`terminal-panel ${isActive ? 'active' : ''}`}
      onClick={() => setActivePanel(id)}
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <div className="terminal-panel-header">
        <div className="terminal-panel-title">{title}</div>
        <div className="terminal-panel-actions">
          {onRefresh && (
            <button
              className="terminal-panel-button"
              onClick={(e) => {
                e.stopPropagation();
                onRefresh();
              }}
              title="Refresh"
            >
              ↻
            </button>
          )}
          <button
            className="terminal-panel-button"
            onClick={(e) => {
              e.stopPropagation();
              removePanel(id);
            }}
            title="Close"
          >
            ✕
          </button>
        </div>
      </div>
      <div className="terminal-panel-content">{children}</div>
    </div>
  );
}
