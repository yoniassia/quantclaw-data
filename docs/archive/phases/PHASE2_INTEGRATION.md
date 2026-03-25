# Phase 2 Integration Guide

## Overview
Phase 2 has created 6 advanced panel types for the Bloomberg Terminal redesign. This guide explains how to integrate them into the existing Phase 1 architecture.

## Files Created

### Panel Components
- `src/components/panels/ChartPanel.tsx` - Interactive candlestick charts
- `src/components/panels/HeatmapPanel.tsx` - Category heatmap
- `src/components/panels/NewsPanel.tsx` - News feed with sentiment
- `src/components/panels/WatchlistPanel.tsx` - Multi-ticker watchlist
- `src/components/panels/ModuleBrowserPanel.tsx` - Browse all 402+ modules
- `src/components/panels/StatusPanel.tsx` - System status dashboard

### Support Files
- `src/components/panels/index.ts` - Barrel export
- `src/components/panels/panel-registry.tsx` - Panel metadata and helpers

## Integration Steps

### 1. Update Store Types

Edit `src/store/terminal-store.ts`:

```typescript
export interface PanelConfig {
  id: string;
  type: 'welcome' | 'data-module' | 'ticker' | 'chart' | 'watchlist' | 'news' | 'heatmap' | 'module-browser' | 'status';
  title: string;
  x: number;
  y: number;
  w: number;
  h: number;
  props?: {
    moduleId?: string;
    ticker?: string;
    onOpenModule?: (moduleId: string) => void;
    onOpenChart?: (ticker: string) => void;
  };
}
```

### 2. Update TerminalGrid

Edit `src/components/terminal/TerminalGrid.tsx`:

Add imports:
```typescript
import { renderPanel } from '../panels/panel-registry';
import ChartPanel from '../panels/ChartPanel';
import WatchlistPanel from '../panels/WatchlistPanel';
import NewsPanel from '../panels/NewsPanel';
import HeatmapPanel from '../panels/HeatmapPanel';
import ModuleBrowserPanel from '../panels/ModuleBrowserPanel';
import StatusPanel from '../panels/StatusPanel';
```

Update the panel rendering section:
```typescript
{panels.map((panel) => (
  <div key={panel.id} style={{ overflow: 'hidden' }}>
    {panel.type === 'welcome' && (
      <Panel id={panel.id} title={panel.title}>
        <WelcomePanel />
      </Panel>
    )}
    {panel.type === 'data-module' && (
      <Panel id={panel.id} title={panel.title}>
        <DataModulePanel
          moduleId={panel.props?.moduleId || ''}
          ticker={panel.props?.ticker}
        />
      </Panel>
    )}
    {panel.type === 'chart' && (
      <ChartPanel
        id={panel.id}
        ticker={panel.props?.ticker || 'AAPL'}
      />
    )}
    {panel.type === 'watchlist' && (
      <WatchlistPanel
        id={panel.id}
        onOpenChart={(ticker) => {
          // Create new chart panel
          const { addPanel } = useTerminalStore.getState();
          addPanel({
            id: `chart-${ticker}-${Date.now()}`,
            type: 'chart',
            title: `Chart • ${ticker}`,
            x: 0,
            y: 0,
            w: 8,
            h: 8,
            props: { ticker },
          });
        }}
      />
    )}
    {panel.type === 'news' && (
      <NewsPanel
        id={panel.id}
        ticker={panel.props?.ticker}
      />
    )}
    {panel.type === 'heatmap' && (
      <HeatmapPanel
        id={panel.id}
        onOpenModule={(moduleId) => {
          // Create new data-module panel
          const { addPanel } = useTerminalStore.getState();
          addPanel({
            id: `module-${moduleId}-${Date.now()}`,
            type: 'data-module',
            title: moduleId,
            x: 0,
            y: 0,
            w: 6,
            h: 6,
            props: { moduleId },
          });
        }}
      />
    )}
    {panel.type === 'module-browser' && (
      <ModuleBrowserPanel
        id={panel.id}
        onOpenModule={(moduleId) => {
          const { addPanel } = useTerminalStore.getState();
          addPanel({
            id: `module-${moduleId}-${Date.now()}`,
            type: 'data-module',
            title: moduleId,
            x: 0,
            y: 0,
            w: 6,
            h: 6,
            props: { moduleId },
          });
        }}
      />
    )}
    {panel.type === 'status' && (
      <StatusPanel id={panel.id} />
    )}
  </div>
))}
```

### 3. Update CommandBar

Edit `src/components/terminal/CommandBar.tsx`:

Add imports:
```typescript
import { getSearchablePanelTypes, PANEL_TYPES } from '../panels/panel-registry';
```

Extend the search to include panel types:
```typescript
const panelTypes = getSearchablePanelTypes();

const filteredCommands = [
  ...panelTypes.filter((pt) => {
    const searchText = query.toLowerCase();
    return (
      pt.name.toLowerCase().includes(searchText) ||
      pt.description.toLowerCase().includes(searchText) ||
      pt.category.toLowerCase().includes(searchText)
    );
  }).map(pt => ({ ...pt, isPanelType: true })),
  ...services.filter((service) => {
    const searchText = query.toLowerCase();
    return (
      service.name.toLowerCase().includes(searchText) ||
      service.id.toLowerCase().includes(searchText) ||
      service.description.toLowerCase().includes(searchText) ||
      service.category.toLowerCase().includes(searchText)
    );
  }),
].slice(0, 10);
```

Update executeCommand to handle panel types:
```typescript
const executeCommand = (item: any) => {
  if (item.isPanelType) {
    const panelType = PANEL_TYPES[item.id];
    const parts = query.split(' ');
    const ticker = parts.length > 1 ? parts[1].toUpperCase() : undefined;
    
    const panelId = `${item.id}-${Date.now()}`;
    
    const newPanel = {
      id: panelId,
      type: item.id as any,
      title: ticker && panelType.requiresTicker
        ? `${panelType.name} • ${ticker}`
        : panelType.name,
      x: 0,
      y: 0,
      w: panelType.defaultSize.w,
      h: panelType.defaultSize.h,
      props: ticker ? { ticker } : {},
    };
    
    addPanel(newPanel);
    addToHistory(`${item.id}${ticker ? ` ${ticker}` : ''}`);
    onClose();
  } else {
    // Existing service logic
    // ... (keep existing code)
  }
};
```

### 4. Add Default Panels (Optional)

Update DEFAULT_PANELS in `terminal-store.ts` to include some Phase 2 panels:

```typescript
const DEFAULT_PANELS: PanelConfig[] = [
  {
    id: 'watchlist-1',
    type: 'watchlist',
    title: 'Watchlist',
    x: 0,
    y: 0,
    w: 6,
    h: 8,
  },
  {
    id: 'chart-1',
    type: 'chart',
    title: 'Chart • AAPL',
    x: 6,
    y: 0,
    w: 6,
    h: 8,
    props: { ticker: 'AAPL' },
  },
  {
    id: 'news-1',
    type: 'news',
    title: 'News Feed',
    x: 0,
    y: 8,
    w: 6,
    h: 6,
  },
  {
    id: 'status-1',
    type: 'status',
    title: 'System Status',
    x: 6,
    y: 8,
    w: 6,
    h: 6,
  },
];
```

## Dependencies

The ChartPanel requires `lightweight-charts`:

```bash
npm install lightweight-charts
```

## Testing Commands

Once integrated, test these commands in the command bar (Ctrl+K):

- `watchlist` - Open watchlist panel
- `chart AAPL` - Open chart for AAPL
- `news TSLA` - Open news feed for TSLA
- `heatmap` - Open category heatmap
- `module-browser` - Open module browser
- `status` - Open system status panel

## Notes

- All panels use inline styles (no Tailwind dependencies)
- Colors follow Bloomberg terminal theme
- Font: 'JetBrains Mono', monospace
- All panels work with the Panel wrapper from Phase 1
- Panels auto-refresh where appropriate
- API endpoints gracefully fall back to simulated data
