import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import type { UTCTimestamp } from 'lightweight-charts';

interface KLineData {
  time: UTCTimestamp;
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
  const chartRef = useRef<any>(null);
  const [hasError, setHasError] = useState(false);

  console.log('TradingViewKLineChart received data:', data); // 调试信息

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      console.log('TradingViewKLineChart early return - no data or container');
      return;
    }

    if (hasError) {
      console.log('TradingViewKLineChart has error, not rendering');
      return;
    }

    let chart: any = null;
    let candlestickSeries: any = null;

    try {
      console.log('Creating TradingView chart with data length:', data.length);
      
      // 创建图表配置
      const chartOptions = {
        width: width,
        height: height,
        layout: {
          background: { color: '#ffffff' },
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

      console.log('Chart options:', chartOptions);

      // 创建图表
      chart = createChart(chartContainerRef.current, chartOptions);
      console.log('Chart created successfully');

      // 添加K线系列 - 使用正确的API
      const seriesOptions = {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
        wickVisible: true,
      };

      console.log('Series options:', seriesOptions);

      // 检查API方法是否存在
      if (typeof chart.addCandlestickSeries === 'function') {
        candlestickSeries = chart.addCandlestickSeries(seriesOptions);
      } else if (typeof (chart as any).addSeries === 'function') {
        // 降级处理：使用通用addSeries方法
        console.log('Using fallback addSeries method');
        candlestickSeries = (chart as any).addSeries('Candlestick', seriesOptions);
      } else {
        throw new Error('Neither addCandlestickSeries nor addSeries method found');
      }

      console.log('Candlestick series created successfully');

      // 设置数据
      candlestickSeries.setData(data);
      console.log('Data set successfully');
      
      // 自适应大小
      chart.timeScale().fitContent();
      console.log('Chart content fitted');

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
      console.log('Cleaning up TradingView chart');
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
        <span style={{ color: '#dc2626', fontSize: '14px' }}>高级图表加载失败</span>
        <span style={{ color: '#7f1d1d', fontSize: '12px' }}>请切换到简单图表模式</span>
      </div>
    );
  }

  return <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />;
};

export default TradingViewKLineChart;