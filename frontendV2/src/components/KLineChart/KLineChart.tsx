import React, { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries } from 'lightweight-charts';
import type { UTCTimestamp } from 'lightweight-charts';

interface KLineData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface KLineChartProps {
  data: KLineData[];
  width?: number;
  height?: number;
  onError?: (error: Error) => void;
}

const KLineChart: React.FC<KLineChartProps> = ({ data, width = 800, height = 400, onError }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const [hasError, setHasError] = useState(false);

  console.log('KLineChart received data:', data); // 调试信息

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      console.log('KLineChart early return - no data or container'); // 调试信息
      return;
    }

    if (hasError) {
      console.log('KLineChart has error, not rendering');
      return;
    }

    let chart: any = null;

    try {
      console.log('Creating chart with data length:', data.length); // 调试信息

      // 创建图表
      chart = createChart(chartContainerRef.current, {
        width: width,
        height: height,
        layout: {
          background: { color: '#ffffff' },
          textColor: '#333',
        },
        grid: {
          vertLines: { color: '#e0e0e0' },
          horzLines: { color: '#e0e0e0' },
        },
        crosshair: {
          mode: 0, // CrosshairMode.Normal
        },
        rightPriceScale: {
          borderColor: '#e0e0e0',
        },
        timeScale: {
          borderColor: '#e0e0e0',
          timeVisible: true,
          secondsVisible: false,
        },
      });

      // 添加K线系列 - 使用更通用的API
      const candlestickSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      // 设置数据
      candlestickSeries.setData(data);
      console.log('KLineChart data set successfully'); // 调试信息

      // 自适应大小
      chart.timeScale().fitContent();

      // 保存图表引用
      chartRef.current = chart;

    } catch (error) {
      console.error('Error creating chart:', error);
      setHasError(true);
      if (onError) {
        onError(error instanceof Error ? error : new Error('Unknown chart error'));
      }

      // 清理
      if (chart) {
        try {
          chart.remove();
        } catch (cleanupError) {
          console.error('Error cleaning up chart:', cleanupError);
        }
      }
    }

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data, width, height, hasError, onError]);

  // 如果没有数据，显示一个占位符
  if (!data || data.length === 0) {
    return (
      <div style={{
        width: width,
        height: height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        border: '1px solid #ddd',
        borderRadius: '4px'
      }}>
        <span style={{ color: '#666' }}>暂无数据</span>
      </div>
    );
  }

  // 如果有错误，显示错误信息
  if (hasError) {
    return (
      <div style={{
        width: width,
        height: height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: '4px',
        flexDirection: 'column',
        gap: '8px'
      }}>
        <span style={{ color: '#dc2626', fontSize: '14px' }}>图表加载失败</span>
        <span style={{ color: '#7f1d1d', fontSize: '12px' }}>请检查控制台错误信息</span>
      </div>
    );
  }

  return <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />;
};

export default KLineChart;