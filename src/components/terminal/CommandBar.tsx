'use client';

import { useState, useEffect, useRef } from 'react';
import { useTerminalStore } from '@/store/terminal-store';
import { services } from '@/app/services';

interface CommandBarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandBar({ isOpen, onClose }: CommandBarProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addPanel, addToHistory, commandHistory } = useTerminalStore();

  // Filter services based on query
  const filteredServices = services.filter((service) => {
    const searchText = query.toLowerCase();
    return (
      service.name.toLowerCase().includes(searchText) ||
      service.id.toLowerCase().includes(searchText) ||
      service.description.toLowerCase().includes(searchText) ||
      service.category.toLowerCase().includes(searchText)
    );
  }).slice(0, 10);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, filteredServices.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredServices[selectedIndex]) {
          executeCommand(filteredServices[selectedIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredServices, selectedIndex]);

  const executeCommand = (service: typeof services[0]) => {
    // Parse command for ticker if present
    const parts = query.split(' ');
    const ticker = parts.length > 1 ? parts[1].toUpperCase() : undefined;

    // Generate unique ID
    const panelId = `${service.id}-${Date.now()}`;

    // Create new panel
    const newPanel = {
      id: panelId,
      type: 'data-module' as const,
      title: ticker ? `${service.name} - ${ticker}` : service.name,
      x: 0,
      y: 0,
      w: 6,
      h: 6,
      props: {
        moduleId: service.id,
        ticker,
      },
    };

    addPanel(newPanel);
    addToHistory(`${service.id}${ticker ? ` ${ticker}` : ''}`);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="terminal-command-bar"
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(10, 14, 39, 0.95)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '120px',
      }}
    >
      <div
        className="terminal-command-input-container"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '600px',
          background: '#0f1629',
          border: '2px solid #00d4ff',
          borderRadius: '4px',
          padding: '16px',
          boxShadow: '0 4px 20px rgba(0, 212, 255, 0.2)',
        }}
      >
        <input
          ref={inputRef}
          type="text"
          className="terminal-command-input"
          placeholder="Type a module name or ticker... (e.g., prices AAPL)"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelectedIndex(0);
          }}
          style={{
            width: '100%',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#e0e8f0',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '14px',
            padding: '8px 0',
            caretColor: '#00ff41',
          }}
        />

        {query && (
          <div className="terminal-command-results" style={{ marginTop: '16px', maxHeight: '400px', overflowY: 'auto' }}>
            {filteredServices.length > 0 ? (
              filteredServices.map((service, index) => (
                <div
                  key={service.id}
                  className={`terminal-command-result-item ${index === selectedIndex ? 'selected' : ''}`}
                  onClick={() => executeCommand(service)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  style={{
                    padding: '10px 12px',
                    cursor: 'pointer',
                    borderLeft: '3px solid transparent',
                    transition: 'all 0.2s',
                    background: index === selectedIndex ? 'rgba(0, 212, 255, 0.1)' : 'transparent',
                    borderLeftColor: index === selectedIndex ? '#00d4ff' : 'transparent',
                  }}
                >
                  <div className="terminal-command-result-title" style={{ fontSize: '12px', fontWeight: 600, color: '#e0e8f0', marginBottom: '4px' }}>
                    {service.name}
                  </div>
                  <div className="terminal-command-result-desc" style={{ fontSize: '10px', color: 'rgba(224, 232, 240, 0.6)' }}>
                    {service.description}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(224, 232, 240, 0.5)', fontSize: '11px' }}>
                No modules found for "{query}"
              </div>
            )}
          </div>
        )}

        {!query && commandHistory.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <div style={{ fontSize: '10px', color: 'rgba(224, 232, 240, 0.5)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Recent Commands
            </div>
            {commandHistory.slice(0, 5).map((cmd, index) => (
              <div
                key={index}
                style={{
                  padding: '6px 12px',
                  fontSize: '11px',
                  color: '#00d4ff',
                  cursor: 'pointer',
                  borderLeft: '3px solid transparent',
                  transition: 'all 0.2s',
                }}
                onClick={() => setQuery(cmd)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(0, 212, 255, 0.1)';
                  e.currentTarget.style.borderLeftColor = '#00d4ff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.borderLeftColor = 'transparent';
                }}
              >
                {cmd}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
