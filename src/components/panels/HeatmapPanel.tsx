'use client';

import { useState, useEffect } from 'react';
import Panel from '@/components/terminal/Panel';
import { categories, services } from '@/app/services';

interface HeatmapPanelProps {
  id: string;
  onOpenModule?: (moduleId: string) => void;
}

export default function HeatmapPanel({ id, onOpenModule }: HeatmapPanelProps) {
  const [categoryStats, setCategoryStats] = useState<Map<string, { count: number; freshness: number }>>(new Map());

  useEffect(() => {
    const stats = new Map();
    categories.forEach(cat => {
      const moduleCount = services.filter(s => s.category === cat.id).length;
      const freshness = Math.random() * 0.5 + 0.5;
      stats.set(cat.id, { count: moduleCount, freshness });
    });
    setCategoryStats(stats);
  }, []);

  const getColorIntensity = (freshness: number) => {
    const intensity = Math.floor(freshness * 255);
    return `rgb(0, ${intensity}, ${Math.floor(intensity * 0.26)})`;
  };

  const getCellStyle = (categoryId: string) => {
    const stats = categoryStats.get(categoryId);
    if (!stats) return {};
    return {
      backgroundColor: getColorIntensity(stats.freshness),
      opacity: 0.7 + (stats.freshness * 0.3),
    };
  };

  return (
    <Panel id={id} title="Market Heatmap">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', padding: '16px', height: '100%', overflow: 'auto', fontFamily: "'JetBrains Mono', monospace" }}>
        {categories.map((cat) => {
          const stats = categoryStats.get(cat.id);
          const moduleCount = stats?.count || 0;
          const freshness = stats?.freshness || 0;
          return (
            <div key={cat.id} onClick={() => { const firstModule = services.find(s => s.category === cat.id); if (firstModule && onOpenModule) { onOpenModule(firstModule.id); } }} style={{ ...getCellStyle(cat.id), border: '1px solid #1a2340', borderRadius: '4px', padding: '16px', cursor: 'pointer', transition: 'all 0.2s', minHeight: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }} onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.05)'; e.currentTarget.style.borderColor = '#00d4ff'; }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.borderColor = '#1a2340'; }}>
              <div><div style={{ fontSize: '28px', marginBottom: '8px' }}>{cat.icon}</div><div style={{ fontSize: '13px', fontWeight: 'bold', color: '#e0e8f0', marginBottom: '4px' }}>{cat.name}</div></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}><div style={{ fontSize: '11px', color: '#a0b0c0' }}>{moduleCount} modules</div><div style={{ fontSize: '10px', color: freshness > 0.7 ? '#00ff41' : freshness > 0.4 ? '#ffd700' : '#ff3366', fontWeight: 'bold' }}>{Math.round(freshness * 100)}%</div></div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
