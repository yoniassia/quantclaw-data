'use client';

import { useState, useEffect } from 'react';
import type { JSX } from 'react';

interface DataModulePanelProps {
  moduleId: string;
  ticker?: string;
}

export default function DataModulePanel({ moduleId, ticker }: DataModulePanelProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = `/api/v1/${moduleId.replace(/_/g, '-')}${ticker ? `?ticker=${ticker}` : ''}`;
      const response = await fetch(endpoint);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setData(result);
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [moduleId, ticker]);

  if (loading) {
    return (
      <div className="terminal-loading" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px', color: '#00d4ff', fontSize: '11px' }}>
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="terminal-error" style={{ padding: '16px', background: 'rgba(255, 51, 102, 0.1)', borderLeft: '3px solid #ff3366', color: '#ff3366', fontSize: '11px' }}>
        ERROR: {error}
      </div>
    );
  }

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      {lastUpdated && (
        <div style={{ fontSize: '10px', color: 'rgba(224, 232, 240, 0.5)', marginBottom: '12px' }}>
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
      {renderData(data)}
    </div>
  );
}

function renderData(data: any): JSX.Element {
  if (data === null || data === undefined) {
    return <div style={{ color: 'rgba(224, 232, 240, 0.5)', fontSize: '11px' }}>No data</div>;
  }

  // Handle arrays - render as table
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <div style={{ color: 'rgba(224, 232, 240, 0.5)', fontSize: '11px' }}>Empty array</div>;
    }

    // If array of primitives, render as list
    if (typeof data[0] !== 'object') {
      return (
        <div>
          {data.map((item, i) => (
            <div key={i} style={{ padding: '4px 0', fontSize: '11px', color: '#e0e8f0' }}>
              {String(item)}
            </div>
          ))}
        </div>
      );
    }

    // Array of objects - render as table
    const keys = Object.keys(data[0]);
    return (
      <table className="terminal-data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
        <thead>
          <tr>
            {keys.map((key) => (
              <th
                key={key}
                style={{
                  textAlign: 'left',
                  padding: '8px',
                  borderBottom: '1px solid #1a2340',
                  fontWeight: 600,
                  color: '#00d4ff',
                  textTransform: 'uppercase',
                  fontSize: '10px',
                  letterSpacing: '0.5px',
                }}
              >
                {key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {keys.map((key) => (
                <td
                  key={key}
                  style={{
                    padding: '6px 8px',
                    borderBottom: '1px solid rgba(26, 35, 64, 0.5)',
                    color: '#e0e8f0',
                  }}
                >
                  {renderValue(row[key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  // Handle objects - render as key-value pairs
  if (typeof data === 'object') {
    const entries = Object.entries(data);
    return (
      <div className="terminal-kv-table" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', fontSize: '11px' }}>
        {entries.map(([key, value]) => (
          <div key={key} style={{ display: 'contents' }}>
            <div className="terminal-kv-key" style={{ color: '#00d4ff', fontWeight: 600, textTransform: 'uppercase', fontSize: '10px' }}>
              {key}:
            </div>
            <div className="terminal-kv-value" style={{ color: '#e0e8f0' }}>
              {renderValue(value)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Primitives
  return <div style={{ fontSize: '11px', color: '#e0e8f0' }}>{String(data)}</div>;
}

function renderValue(value: any): string {
  if (value === null || value === undefined) {
    return '-';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === 'boolean') {
    return value ? 'YES' : 'NO';
  }
  if (typeof value === 'number') {
    // Format numbers with appropriate precision
    if (Math.abs(value) > 1000) {
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return value.toString();
  }
  return String(value);
}
