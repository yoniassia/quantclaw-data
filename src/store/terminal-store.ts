import { create } from 'zustand';

// Define Layout type locally since react-grid-layout types are tricky
export interface LayoutItem {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
  static?: boolean;
}

export type Layout = LayoutItem[];

export interface PanelConfig {
  id: string;
  type: 'welcome' | 'data-module' | 'ticker' | 'watchlist' | 'chart' | 'heatmap' | 'news' | 'module-browser' | 'status';
  title: string;
  x: number;
  y: number;
  w: number;
  h: number;
  props?: {
    moduleId?: string;
    ticker?: string;
  };
}

interface SavedLayout {
  name: string;
  layout: Layout;
  panels: PanelConfig[];
}

interface TerminalStore {
  panels: PanelConfig[];
  activePanel: string | null;
  layout: Layout;
  commandBarOpen: boolean;
  commandHistory: string[];
  savedLayouts: SavedLayout[];
  
  addPanel: (panel: PanelConfig) => void;
  removePanel: (id: string) => void;
  setActivePanel: (id: string | null) => void;
  updateLayout: (layout: Layout) => void;
  toggleCommandBar: () => void;
  addToHistory: (command: string) => void;
  saveLayout: (name: string) => void;
  loadLayout: (name: string) => void;
  loadPreset: (name: string) => void;
  initializeDefaultLayout: () => void;
}

const DEFAULT_PANELS: PanelConfig[] = [
  {
    id: 'welcome-1',
    type: 'welcome',
    title: 'Welcome',
    x: 0,
    y: 0,
    w: 6,
    h: 6,
  },
  {
    id: 'treasury-1',
    type: 'data-module',
    title: 'Treasury Curve',
    x: 6,
    y: 0,
    w: 6,
    h: 6,
    props: {
      moduleId: 'treasury-curve',
    },
  },
  {
    id: 'prices-1',
    type: 'data-module',
    title: 'AAPL Price',
    x: 0,
    y: 6,
    w: 6,
    h: 6,
    props: {
      moduleId: 'prices',
      ticker: 'AAPL',
    },
  },
  {
    id: 'congress-1',
    type: 'data-module',
    title: 'Congress Trades',
    x: 6,
    y: 6,
    w: 6,
    h: 6,
    props: {
      moduleId: 'congress-trades',
    },
  },
];

const DEFAULT_LAYOUT: Layout = DEFAULT_PANELS.map((p) => ({
  i: p.id,
  x: p.x,
  y: p.y,
  w: p.w,
  h: p.h,
  minW: 3,
  minH: 4,
}));

export const useTerminalStore = create<TerminalStore>((set, get) => ({
  panels: [],
  activePanel: null,
  layout: [],
  commandBarOpen: false,
  commandHistory: [],
  savedLayouts: [],

  initializeDefaultLayout: () => {
    // Load from localStorage if available
    if (typeof window !== 'undefined') {
      const savedState = localStorage.getItem('quantclaw-terminal-state');
      if (savedState) {
        try {
          const { panels, layout } = JSON.parse(savedState);
          set({ panels, layout });
          return;
        } catch (e) {
          console.error('Failed to load saved state:', e);
        }
      }
    }
    
    // Otherwise use defaults
    set({
      panels: DEFAULT_PANELS,
      layout: DEFAULT_LAYOUT,
    });
  },

  addPanel: (panel) => {
    set((state) => {
      const newPanels = [...state.panels, panel];
      const newLayout = [
        ...state.layout,
        {
          i: panel.id,
          x: panel.x,
          y: panel.y,
          w: panel.w,
          h: panel.h,
          minW: 3,
          minH: 4,
        },
      ];
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          'quantclaw-terminal-state',
          JSON.stringify({ panels: newPanels, layout: newLayout })
        );
      }
      
      return {
        panels: newPanels,
        layout: newLayout,
        activePanel: panel.id,
      };
    });
  },

  removePanel: (id) => {
    set((state) => {
      const newPanels = state.panels.filter((p) => p.id !== id);
      const newLayout = state.layout.filter((l) => l.i !== id);
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          'quantclaw-terminal-state',
          JSON.stringify({ panels: newPanels, layout: newLayout })
        );
      }
      
      return {
        panels: newPanels,
        layout: newLayout,
        activePanel: state.activePanel === id ? null : state.activePanel,
      };
    });
  },

  setActivePanel: (id) => {
    set({ activePanel: id });
  },

  updateLayout: (layout) => {
    set((state) => {
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          'quantclaw-terminal-state',
          JSON.stringify({ panels: state.panels, layout })
        );
      }
      
      return { layout };
    });
  },

  toggleCommandBar: () => {
    set((state) => ({ commandBarOpen: !state.commandBarOpen }));
  },

  addToHistory: (command) => {
    set((state) => {
      const newHistory = [command, ...state.commandHistory.slice(0, 49)];
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('quantclaw-command-history', JSON.stringify(newHistory));
      }
      
      return { commandHistory: newHistory };
    });
  },

  saveLayout: (name) => {
    set((state) => {
      const newSavedLayouts = [
        ...state.savedLayouts.filter((l) => l.name !== name),
        {
          name,
          layout: state.layout,
          panels: state.panels,
        },
      ];
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('quantclaw-saved-layouts', JSON.stringify(newSavedLayouts));
      }
      
      return { savedLayouts: newSavedLayouts };
    });
  },

  loadLayout: (name) => {
    const state = get();
    const savedLayout = state.savedLayouts.find((l) => l.name === name);
    if (savedLayout) {
      set({
        panels: savedLayout.panels,
        layout: savedLayout.layout,
      });
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          'quantclaw-terminal-state',
          JSON.stringify({ panels: savedLayout.panels, layout: savedLayout.layout })
        );
      }
    }
  },

  loadPreset: (name) => {
    const presets: Record<string, { panels: PanelConfig[], layout: Layout }> = {
      default: {
        panels: [
          { id: 'welcome-1', type: 'welcome', title: 'Welcome', x: 0, y: 0, w: 6, h: 6 },
          { id: 'watchlist-1', type: 'watchlist', title: 'Watchlist', x: 6, y: 0, w: 6, h: 6 },
          { id: 'treasury-1', type: 'data-module', title: 'Treasury Curve', x: 0, y: 6, w: 6, h: 6, props: { moduleId: 'treasury-curve' } },
          { id: 'congress-1', type: 'data-module', title: 'Congress Trades', x: 6, y: 6, w: 6, h: 6, props: { moduleId: 'congress_trades' } },
        ],
        layout: [
          { i: 'welcome-1', x: 0, y: 0, w: 6, h: 6, minW: 3, minH: 4 },
          { i: 'watchlist-1', x: 6, y: 0, w: 6, h: 6, minW: 3, minH: 4 },
          { i: 'treasury-1', x: 0, y: 6, w: 6, h: 6, minW: 3, minH: 4 },
          { i: 'congress-1', x: 6, y: 6, w: 6, h: 6, minW: 3, minH: 4 },
        ],
      },
      trading: {
        panels: [
          { id: 'watchlist-1', type: 'watchlist', title: 'Watchlist', x: 0, y: 0, w: 4, h: 12 },
          { id: 'chart-1', type: 'chart', title: 'AAPL Chart', x: 4, y: 0, w: 8, h: 8, props: { ticker: 'AAPL' } },
          { id: 'options-1', type: 'data-module', title: 'Options', x: 4, y: 8, w: 4, h: 4, props: { moduleId: 'options' } },
          { id: 'news-1', type: 'news', title: 'Market News', x: 8, y: 8, w: 4, h: 4 },
        ],
        layout: [
          { i: 'watchlist-1', x: 0, y: 0, w: 4, h: 12, minW: 3, minH: 4 },
          { i: 'chart-1', x: 4, y: 0, w: 8, h: 8, minW: 4, minH: 6 },
          { i: 'options-1', x: 4, y: 8, w: 4, h: 4, minW: 3, minH: 4 },
          { i: 'news-1', x: 8, y: 8, w: 4, h: 4, minW: 3, minH: 4 },
        ],
      },
      research: {
        panels: [
          { id: 'modules-1', type: 'module-browser', title: 'Module Browser', x: 0, y: 0, w: 4, h: 12 },
          { id: 'macro-1', type: 'data-module', title: 'Macro Indicators', x: 4, y: 0, w: 4, h: 6, props: { moduleId: 'macro' } },
          { id: 'heatmap-1', type: 'heatmap', title: 'Market Heatmap', x: 8, y: 0, w: 4, h: 6 },
          { id: 'status-1', type: 'status', title: 'System Status', x: 4, y: 6, w: 8, h: 6 },
        ],
        layout: [
          { i: 'modules-1', x: 0, y: 0, w: 4, h: 12, minW: 3, minH: 4 },
          { i: 'macro-1', x: 4, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
          { i: 'heatmap-1', x: 8, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
          { i: 'status-1', x: 4, y: 6, w: 8, h: 6, minW: 3, minH: 4 },
        ],
      },
      overview: {
        panels: [
          { id: 'watchlist-1', type: 'watchlist', title: 'Watchlist', x: 0, y: 0, w: 4, h: 6 },
          { id: 'heatmap-1', type: 'heatmap', title: 'Market Heatmap', x: 4, y: 0, w: 4, h: 6 },
          { id: 'news-1', type: 'news', title: 'Market News', x: 8, y: 0, w: 4, h: 6 },
          { id: 'status-1', type: 'status', title: 'System Status', x: 0, y: 6, w: 12, h: 6 },
        ],
        layout: [
          { i: 'watchlist-1', x: 0, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
          { i: 'heatmap-1', x: 4, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
          { i: 'news-1', x: 8, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
          { i: 'status-1', x: 0, y: 6, w: 12, h: 6, minW: 3, minH: 4 },
        ],
      },
    };

    const preset = presets[name.toLowerCase()];
    if (preset) {
      set({
        panels: preset.panels,
        layout: preset.layout,
      });

      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          'quantclaw-terminal-state',
          JSON.stringify({ panels: preset.panels, layout: preset.layout })
        );
      }
    }
  },
}));
