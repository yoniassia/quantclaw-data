'use client';

import { useEffect } from 'react';
import { Responsive } from 'react-grid-layout';
import { useTerminalStore, Layout, LayoutItem } from '@/store/terminal-store';
import Panel from './Panel';
import {
  WelcomePanel,
  DataModulePanel,
  TickerPanel,
  WatchlistPanel,
  ChartPanel,
  HeatmapPanel,
  NewsPanel,
  ModuleBrowserPanel,
  StatusPanel,
} from '../panels';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

// @ts-ignore - WidthProvider is available at runtime
const ResponsiveGridLayout = Responsive as any;

export default function TerminalGrid() {
  const { panels, layout, updateLayout, initializeDefaultLayout } = useTerminalStore();

  // Initialize default layout on mount
  useEffect(() => {
    initializeDefaultLayout();
  }, [initializeDefaultLayout]);

  const handleLayoutChange = (newLayout: LayoutItem[]) => {
    updateLayout(newLayout);
  };

  const renderPanel = (panel: any) => {
    switch (panel.type) {
      case 'welcome':
        return <WelcomePanel />;
      case 'data-module':
        return (
          <DataModulePanel
            moduleId={panel.props?.moduleId || ''}
            ticker={panel.props?.ticker}
          />
        );
      case 'ticker':
        return <TickerPanel />;
      case 'watchlist':
        return <WatchlistPanel id={panel.id} />;
      case 'chart':
        return <ChartPanel ticker={panel.props?.ticker || 'AAPL'} />;
      case 'heatmap':
        return <HeatmapPanel id={panel.id} />;
      case 'news':
        return <NewsPanel id={panel.id} ticker={panel.props?.ticker} />;
      case 'module-browser':
        return <ModuleBrowserPanel />;
      case 'status':
        return <StatusPanel />;
      default:
        return <div style={{ color: '#ff3366', padding: '20px' }}>Unknown panel type: {panel.type}</div>;
    }
  };

  return (
    <div className="terminal-grid-container" style={{ flex: 1, overflow: 'hidden', padding: '8px' }}>
      <ResponsiveGridLayout
        className="react-grid-layout"
        layouts={{ lg: layout, md: layout, sm: layout }}
        breakpoints={{ lg: 1200, md: 996, sm: 768 }}
        cols={{ lg: 12, md: 8, sm: 4 }}
        rowHeight={40}
        compactType="vertical"
        margin={[8, 8]}
        containerPadding={[0, 0]}
        onLayoutChange={handleLayoutChange}
        isDraggable={true}
        isResizable={true}
        draggableHandle=".terminal-panel-header"
      >
        {panels.map((panel) => (
          <div key={panel.id} style={{ overflow: 'hidden' }}>
            <Panel id={panel.id} title={panel.title}>
              {renderPanel(panel)}
            </Panel>
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  );
}
