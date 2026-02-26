'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi } from 'lightweight-charts';

interface ChartPanelProps {
  ticker: string;
}

interface PriceData {
  time: string;
  value: number;
}

export default function ChartPanel({ ticker }: ChartPanelProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f1629' },
        textColor: '#e0e8f0',
      },
      grid: {
        vertLines: { color: '#1a2340' },
        horzLines: { color: '#1a2340' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#00d4ff',
          width: 1,
          style: 2,
          labelBackgroundColor: '#00d4ff',
        },
        horzLine: {
          color: '#00d4ff',
          width: 1,
          style: 2,
          labelBackgroundColor: '#00d4ff',
        },
      },
      timeScale: {
        borderColor: '#1a2340',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: '#1a2340',
      },
    });

    const series = chart.addSeries({
      type: 'Area',
      lineColor: '#00d4ff',
      topColor: 'rgba(0, 212, 255, 0.4)',
      bottomColor: 'rgba(0, 212, 255, 0.0)',
      lineWidth: 2,
    } as any);

    chartRef.current = chart;
    seriesRef.current = series;

    // Fetch data
    fetch(`/api/v1/prices?ticker=${ticker}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
          setLoading(false);
          return;
        }

        // Transform data for lightweight-charts
        const chartData: PriceData[] = [];
        
        if (data.prices && Array.isArray(data.prices)) {
          data.prices.forEach((item: any) => {
            if (item.date && item.close) {
              chartData.push({
                time: item.date,
                value: parseFloat(item.close),
              });
            }
          });
        } else if (data.history && Array.isArray(data.history)) {
          data.history.forEach((item: any) => {
            if (item.date && item.close) {
              chartData.push({
                time: item.date,
                value: parseFloat(item.close),
              });
            }
          });
        }

        if (chartData.length > 0) {
          series.setData(chartData);
          chart.timeScale().fitContent();
          setLoading(false);
        } else {
          setError('No price data available');
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Chart fetch error:', err);
        setError('Failed to load chart data');
        setLoading(false);
      });

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [ticker]);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#e0e8f0',
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: '14px',
        }}
      >
        LOADING CHART...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#ff3366',
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: '14px',
        }}
      >
        {error}
      </div>
    );
  }

  return (
    <div
      ref={chartContainerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
      }}
    />
  );
}
