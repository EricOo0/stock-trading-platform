import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts';
import type { Time, IChartApi } from 'lightweight-charts';

interface KLineData {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface TradingViewKLineChartProps {
  data: KLineData[];
  width?: number;
  height?: number;
  onError?: (error: Error) => void;
}

const TradingViewKLineChart: React.FC<TradingViewKLineChartProps> = ({
  data,
  width = 800,
  height = 400,
  onError
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      return;
    }

    if (hasError) {
      return;
    }

    let chart: IChartApi | null = null;

    try {
      // 创建图表配置
      const chartOptions = {
        width: width,
        height: height,
        layout: {
          background: { type: ColorType.Solid, color: '#ffffff' },
          textColor: '#333',
          fontSize: 12,
        },
        grid: {
          vertLines: { color: '#e0e0e0', style: 1 },
          horzLines: { color: '#e0e0e0', style: 1 },
        },
        crosshair: {
          mode: 0, // Normal
          vertLine: {
            color: '#555',
            labelBackgroundColor: '#555',
          },
          horzLine: {
            color: '#555',
            labelBackgroundColor: '#555',
          },
        },
        rightPriceScale: {
          borderColor: '#e0e0e0',
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
        timeScale: {
          borderColor: '#e0e0e0',
          timeVisible: true,
          secondsVisible: false,
          rightOffset: 5,
          barSpacing: 6,
        },
      };

      // 创建图表
      chart = createChart(chartContainerRef.current, chartOptions);

      // 添加K线系列 - 使用 v5 API
      const candlestickSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
        wickVisible: true,
      });

      // 验证和过滤数据
      const validData = data.filter(item => {
        return (
          item &&
          item.time &&
          typeof item.open === 'number' && !isNaN(item.open) &&
          typeof item.high === 'number' && !isNaN(item.high) &&
          typeof item.low === 'number' && !isNaN(item.low) &&
          typeof item.close === 'number' && !isNaN(item.close)
        );
      });

      if (validData.length === 0) {
        console.warn('TradingViewKLineChart: No valid data to render');
        setHasError(true);
        return;
      }

      // 设置数据
      candlestickSeries.setData(validData);

      // 自适应大小
      chart.timeScale().fitContent();

      // 保存图表引用
      chartRef.current = chart;

    } catch (error) {
      console.error('Error creating TradingView chart:', error);
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
        try {
          chartRef.current.remove();
          chartRef.current = null;
        } catch (error) {
          console.error('Error removing chart:', error);
        }
      }
    };
  }, [data, width, height, hasError, onError]);

  // 如果没有数据，显示占位符
  if (!data || data.length === 0) {
    return (
      <div style={{
        width,
        height,
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
        <span style={{ color: '#dc2626', fontSize: '14px' }}>高级图表加载失败</span>
        <span style={{ color: '#7f1d1d', fontSize: '12px' }}>请切换到简单图表模式</span>
      </div>
    );
  }

  return <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />;
};

export default TradingViewKLineChart;