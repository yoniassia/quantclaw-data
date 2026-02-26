'use client';

import { useState, useMemo } from 'react';
import { services, categories, Service } from '@/app/services';
import { useTerminalStore } from '@/store/terminal-store';

export default function ModuleBrowserPanel() {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(categories.map((c) => c.id))
  );
  const { addPanel } = useTerminalStore();

  const filteredServices = useMemo(() => {
    const query = searchQuery.toLowerCase();
    if (!query) return services;
    
    return services.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.description.toLowerCase().includes(query) ||
        s.id.toLowerCase().includes(query) ||
        s.category.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  const groupedServices = useMemo(() => {
    const groups: Record<string, Service[]> = {};
    categories.forEach((cat) => {
      groups[cat.id] = filteredServices.filter((s) => s.category === cat.id);
    });
    return groups;
  }, [filteredServices]);

  const toggleCategory = (catId: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(catId)) {
        next.delete(catId);
      } else {
        next.add(catId);
      }
      return next;
    });
  };

  const handleModuleClick = (service: Service) => {
    const newPanel = {
      id: `module-${service.id}-${Date.now()}`,
      type: 'data-module' as const,
      title: service.name,
      x: 0,
      y: 0,
      w: 6,
      h: 6,
      props: {
        moduleId: service.id,
      },
    };
    addPanel(newPanel);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
        background: '#0a0e27',
        fontFamily: 'IBM Plex Mono, monospace',
      }}
    >
      {/* Search Bar */}
      <div
        style={{
          padding: '12px',
          borderBottom: '1px solid #1a2340',
        }}
      >
        <input
          type="text"
          placeholder="SEARCH MODULES..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 12px',
            background: '#0f1629',
            border: '1px solid #1a2340',
            borderRadius: '4px',
            color: '#e0e8f0',
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize: '12px',
            outline: 'none',
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#00d4ff';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#1a2340';
          }}
        />
      </div>

      {/* Module List */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px',
        }}
      >
        {categories.map((category) => {
          const catServices = groupedServices[category.id];
          if (catServices.length === 0) return null;

          const isExpanded = expandedCategories.has(category.id);

          return (
            <div key={category.id} style={{ marginBottom: '8px' }}>
              {/* Category Header */}
              <div
                onClick={() => toggleCategory(category.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px',
                  background: '#0f1629',
                  border: '1px solid #1a2340',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: category.color,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#1a2340';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#0f1629';
                }}
              >
                <span>{isExpanded ? '▼' : '▶'}</span>
                <span>{category.icon}</span>
                <span>{category.name}</span>
                <span style={{ marginLeft: 'auto', color: '#768390' }}>
                  ({catServices.length})
                </span>
              </div>

              {/* Module Items */}
              {isExpanded && (
                <div style={{ marginTop: '4px', paddingLeft: '12px' }}>
                  {catServices.map((service) => (
                    <div
                      key={service.id}
                      onClick={() => handleModuleClick(service)}
                      style={{
                        padding: '8px',
                        background: '#0f1629',
                        border: '1px solid #1a2340',
                        borderRadius: '4px',
                        marginBottom: '4px',
                        cursor: 'pointer',
                        fontSize: '11px',
                        color: '#e0e8f0',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#1a2340';
                        e.currentTarget.style.borderColor = '#00d4ff';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#0f1629';
                        e.currentTarget.style.borderColor = '#1a2340';
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          marginBottom: '4px',
                        }}
                      >
                        <span>{service.icon}</span>
                        <span style={{ fontWeight: 600 }}>{service.name}</span>
                        <span
                          style={{
                            marginLeft: 'auto',
                            fontSize: '9px',
                            color: '#768390',
                            background: '#0a0e27',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          PHASE {service.phase}
                        </span>
                      </div>
                      <div
                        style={{
                          fontSize: '10px',
                          color: '#768390',
                          lineHeight: 1.4,
                        }}
                      >
                        {service.description}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Stats */}
      <div
        style={{
          padding: '8px 12px',
          borderTop: '1px solid #1a2340',
          fontSize: '10px',
          color: '#768390',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <span>TOTAL MODULES: {services.length}</span>
        <span>SHOWING: {filteredServices.length}</span>
      </div>
    </div>
  );
}
