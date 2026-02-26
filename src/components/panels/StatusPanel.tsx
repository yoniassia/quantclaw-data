'use client';

import { useEffect, useState } from 'react';
import { services } from '@/app/services';

interface EndpointHealth {
  endpoint: string;
  status: 'healthy' | 'unhealthy' | 'checking';
  responseTime?: number;
}

export default function StatusPanel() {
  const [endpointHealth, setEndpointHealth] = useState<EndpointHealth[]>([]);
  const [uptime, setUptime] = useState(0);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const checkEndpoints = async () => {
    // Select 3 random endpoints to test
    const randomEndpoints = services
      .filter((s) => s.phase <= 4) // Only check phase 1-4 endpoints
      .sort(() => Math.random() - 0.5)
      .slice(0, 3)
      .map((s) => {
        if (s.apiEndpoint) return s.apiEndpoint;
        const base = `/api/v1/${s.id.replace(/_/g, '-')}`;
        return base;
      });

    const healthChecks: EndpointHealth[] = randomEndpoints.map((endpoint) => ({
      endpoint,
      status: 'checking',
    }));

    setEndpointHealth(healthChecks);

    // Test each endpoint
    const results = await Promise.all(
      randomEndpoints.map(async (endpoint) => {
        const startTime = Date.now();
        try {
          const response = await fetch(endpoint, { signal: AbortSignal.timeout(5000) });
          const responseTime = Date.now() - startTime;
          
          return {
            endpoint,
            status: response.ok ? ('healthy' as const) : ('unhealthy' as const),
            responseTime,
          };
        } catch (error) {
          return {
            endpoint,
            status: 'unhealthy' as const,
          };
        }
      })
    );

    setEndpointHealth(results);
    setLastChecked(new Date());
  };

  useEffect(() => {
    // Initial check
    checkEndpoints();

    // Auto-refresh every 30s
    const interval = setInterval(() => {
      checkEndpoints();
      setUptime((prev) => prev + 30);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const healthyCount = endpointHealth.filter((e) => e.status === 'healthy').length;
  const totalCount = endpointHealth.length;
  const overallHealth = totalCount > 0 ? (healthyCount / totalCount) * 100 : 0;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'auto',
        background: '#0a0e27',
        padding: '16px',
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: '12px',
        color: '#e0e8f0',
      }}
    >
      {/* Header */}
      <div
        style={{
          marginBottom: '20px',
          paddingBottom: '12px',
          borderBottom: '1px solid #1a2340',
        }}
      >
        <div style={{ fontSize: '16px', fontWeight: 700, color: '#00d4ff', marginBottom: '8px' }}>
          SYSTEM STATUS
        </div>
        <div style={{ fontSize: '10px', color: '#768390' }}>
          Last checked: {lastChecked.toLocaleTimeString()}
        </div>
      </div>

      {/* Overall Health */}
      <div
        style={{
          marginBottom: '20px',
          padding: '12px',
          background: '#0f1629',
          border: '1px solid #1a2340',
          borderRadius: '4px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <div
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: overallHealth === 100 ? '#00ff41' : overallHealth >= 50 ? '#ffc107' : '#ff3366',
              boxShadow: `0 0 8px ${overallHealth === 100 ? '#00ff41' : overallHealth >= 50 ? '#ffc107' : '#ff3366'}`,
            }}
          />
          <span style={{ fontWeight: 600 }}>OVERALL HEALTH</span>
        </div>
        <div style={{ fontSize: '24px', fontWeight: 700, color: '#00d4ff' }}>
          {overallHealth.toFixed(0)}%
        </div>
      </div>

      {/* Module Count */}
      <div
        style={{
          marginBottom: '20px',
          padding: '12px',
          background: '#0f1629',
          border: '1px solid #1a2340',
          borderRadius: '4px',
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>MODULE COUNT</div>
        <div style={{ fontSize: '24px', fontWeight: 700, color: '#00d4ff' }}>
          {services.length}
        </div>
        <div style={{ fontSize: '10px', color: '#768390', marginTop: '4px' }}>
          Total data modules available
        </div>
      </div>

      {/* Uptime */}
      <div
        style={{
          marginBottom: '20px',
          padding: '12px',
          background: '#0f1629',
          border: '1px solid #1a2340',
          borderRadius: '4px',
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>SESSION UPTIME</div>
        <div style={{ fontSize: '20px', fontWeight: 700, color: '#00ff41' }}>
          {formatUptime(uptime)}
        </div>
      </div>

      {/* API Health Checks */}
      <div
        style={{
          marginBottom: '20px',
          padding: '12px',
          background: '#0f1629',
          border: '1px solid #1a2340',
          borderRadius: '4px',
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: '12px' }}>API HEALTH</div>
        {endpointHealth.map((check, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px',
              padding: '8px',
              background: '#0a0e27',
              borderRadius: '3px',
            }}
          >
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background:
                  check.status === 'healthy'
                    ? '#00ff41'
                    : check.status === 'unhealthy'
                    ? '#ff3366'
                    : '#ffc107',
              }}
            />
            <div style={{ flex: 1, fontSize: '10px', color: '#768390' }}>
              {check.endpoint}
            </div>
            {check.responseTime && (
              <div style={{ fontSize: '10px', color: '#00d4ff' }}>
                {check.responseTime}ms
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Version */}
      <div
        style={{
          padding: '12px',
          background: '#0f1629',
          border: '1px solid #1a2340',
          borderRadius: '4px',
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>VERSION</div>
        <div style={{ fontSize: '14px', color: '#00d4ff' }}>v1.0.0-beta</div>
        <div style={{ fontSize: '10px', color: '#768390', marginTop: '4px' }}>
          QuantClaw Data Terminal
        </div>
      </div>
    </div>
  );
}
