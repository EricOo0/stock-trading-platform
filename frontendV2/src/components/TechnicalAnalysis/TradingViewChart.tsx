import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CrosshairMode, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';
import type { StockData } from '../../types/stock';

interface TradingViewChartProps {
    data: StockData[];
    mainIndicator: 'MA' | 'BOLL' | 'NONE';
    subIndicator: 'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE';
}

const TradingViewChart: React.FC<TradingViewChartProps> = ({ data, mainIndicator, subIndicator }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const subChartContainerRef = useRef<HTMLDivElement>(null);
    
    // 保存图表实例以供清理
    const chartInstance = useRef<IChartApi | null>(null);
    const subChartInstance = useRef<IChartApi | null>(null);

    // 同步 Crosshair 的状态
    const isSyncing = useRef(false);

    useEffect(() => {
        if (!chartContainerRef.current || data.length === 0) return;

        // 1. 初始化主图表
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#0f172a' }, // slate-900
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#334155' },
                horzLines: { color: '#334155' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 400, // 主图高度
            timeScale: {
                timeVisible: true,
                secondsVisible: true,
                borderColor: '#475569',
            },
            rightPriceScale: {
                borderColor: '#475569',
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
        });
        chartInstance.current = chart;

        // 2. 添加 K 线 Series
        const candlestickSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#ef4444',
            downColor: '#22c55e',
            borderUpColor: '#ef4444',
            borderDownColor: '#22c55e',
            wickUpColor: '#ef4444',
            wickDownColor: '#22c55e',
        });

        // 转换数据格式
        // Lightweight Charts 需要 { time, open, high, low, close }
        // time 可以是 string 'yyyy-mm-dd' 或者 timestamp (number, seconds)
        const candleData = data.map(d => {
            const timeStr = d.timestamp || d.date;
            if (!timeStr) {
                console.error('Missing timestamp/date for data point:', d);
                return null;
            }
            return {
                time: (new Date(timeStr).getTime() / 1000) as Time,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close,
            };
        }).filter(item => item !== null) as { time: Time; open: number; high: number; low: number; close: number }[];
        
        // 必须按时间升序排序
        candleData.sort((a, b) => (a.time as number) - (b.time as number));
        candlestickSeries.setData(candleData);

        // 3. 添加主图指标 (MA / BOLL)
        if (mainIndicator === 'MA') {
            const ma5Series = chart.addSeries(LineSeries, { color: '#fbbf24', lineWidth: 1, title: 'MA5' });
            const ma10Series = chart.addSeries(LineSeries, { color: '#38bdf8', lineWidth: 1, title: 'MA10' });
            const ma20Series = chart.addSeries(LineSeries, { color: '#c084fc', lineWidth: 1, title: 'MA20' });
            const ma60Series = chart.addSeries(LineSeries, { color: '#22c55e', lineWidth: 1, title: 'MA60' });

            const getMaData = (key: keyof StockData) => data.map(d => {
                const timeStr = d.timestamp || d.date;
                return { 
                    time: (new Date(timeStr!).getTime() / 1000) as Time, 
                    value: (d[key] as number) || NaN 
                };
            }).filter(d => !isNaN(d.value) && !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number));

            ma5Series.setData(getMaData('ma5'));
            ma10Series.setData(getMaData('ma10'));
            ma20Series.setData(getMaData('ma20'));
            ma60Series.setData(getMaData('ma60'));
        } else if (mainIndicator === 'BOLL') {
            const upperSeries = chart.addSeries(LineSeries, { color: '#fbbf24', lineWidth: 1, lineStyle: 2, title: 'Upper' });
            const midSeries = chart.addSeries(LineSeries, { color: '#f8fafc', lineWidth: 1, title: 'Mid' });
            const lowerSeries = chart.addSeries(LineSeries, { color: '#c084fc', lineWidth: 1, lineStyle: 2, title: 'Lower' });

            const getBollData = (key: keyof StockData) => data.map(d => {
                const timeStr = d.timestamp || d.date;
                return { 
                    time: (new Date(timeStr!).getTime() / 1000) as Time, 
                    value: (d[key] as number) || NaN 
                };
            }).filter(d => !isNaN(d.value) && !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number));

            upperSeries.setData(getBollData('boll_upper'));
            midSeries.setData(getBollData('boll_mid'));
            lowerSeries.setData(getBollData('boll_lower'));
        }

        // 4. 初始化副图 (如果有)
        if (subChartContainerRef.current && subIndicator !== 'NONE') {
            const subChart = createChart(subChartContainerRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: '#0f172a' },
                    textColor: '#94a3b8',
                },
                grid: {
                    vertLines: { color: '#334155' },
                    horzLines: { color: '#334155' },
                },
                width: subChartContainerRef.current.clientWidth,
                height: 150, // 副图高度
                timeScale: {
                    visible: true, // 隐藏副图时间轴，共用主图的
                    timeVisible: true,
                    secondsVisible: true,
                },
                rightPriceScale: {
                    borderColor: '#475569',
                },
                crosshair: {
                    mode: CrosshairMode.Normal,
                },
            });
            subChartInstance.current = subChart;

            // 同步主副图的时间轴范围
            chart.timeScale().subscribeVisibleTimeRangeChange(range => {
                if (isSyncing.current || !range) return;
                isSyncing.current = true;
                subChart.timeScale().setVisibleRange(range);
                isSyncing.current = false;
            });

            subChart.timeScale().subscribeVisibleTimeRangeChange(range => {
                if (isSyncing.current || !range) return;
                isSyncing.current = true;
                chart.timeScale().setVisibleRange(range);
                isSyncing.current = false;
            });

            // 渲染副图指标
            if (subIndicator === 'VOL') {
                const volSeries = subChart.addSeries(HistogramSeries, {
                    priceFormat: { type: 'volume' },
                    priceScaleId: '', // Default
                });
                const volData = data.map(d => {
                    const timeStr = d.timestamp || d.date;
                    return {
                        time: (new Date(timeStr!).getTime() / 1000) as Time,
                        value: d.volume,
                        color: d.close >= d.open ? '#ef4444' : '#22c55e', // 涨红跌绿
                    };
                }).filter(d => !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number));
                volSeries.setData(volData);
            } else if (subIndicator === 'MACD') {
                const difSeries = subChart.addSeries(LineSeries, { color: '#fbbf24', lineWidth: 1, title: 'DIF' });
                const deaSeries = subChart.addSeries(LineSeries, { color: '#38bdf8', lineWidth: 1, title: 'DEA' });
                const barSeries = subChart.addSeries(HistogramSeries, { title: 'MACD' });

                const getMacdData = (key: keyof StockData, def = 0) => data.map(d => {
                    const timeStr = d.timestamp || d.date;
                    return { 
                        time: (new Date(timeStr!).getTime() / 1000) as Time, 
                        value: (d[key] as number) || def 
                    };
                }).filter(d => !isNaN(d.value) && !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number));

                difSeries.setData(getMacdData('macd_dif'));
                deaSeries.setData(getMacdData('macd_dea'));
                barSeries.setData(data.map(d => {
                    const timeStr = d.timestamp || d.date;
                    const val = d.macd_bar || 0;
                    return {
                        time: (new Date(timeStr!).getTime() / 1000) as Time,
                        value: val,
                        color: val >= 0 ? '#ef4444' : '#22c55e',
                    };
                }).filter(d => !isNaN(d.value) && !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number)));
            } else if (subIndicator === 'RSI') {
                const rsiSeries = subChart.addSeries(LineSeries, { color: '#c084fc', lineWidth: 1, title: 'RSI' });
                // 添加 30/70 参考线 (Lightweight charts 原生不支持 ReferenceLine，可以用 LineSeries 模拟)
                const ref70 = subChart.addSeries(LineSeries, { color: '#ef4444', lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false });
                const ref30 = subChart.addSeries(LineSeries, { color: '#22c55e', lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false });

                const validRsi = data.map(d => {
                    const timeStr = d.timestamp || d.date;
                    return { 
                        time: (new Date(timeStr!).getTime() / 1000) as Time, 
                        value: d.rsi14 || NaN 
                    };
                }).filter(d => !isNaN(d.value) && !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number));
                
                rsiSeries.setData(validRsi);
                
                if (validRsi.length > 0) {
                    ref70.setData(validRsi.map(d => ({ ...d, value: 70 })));
                    ref30.setData(validRsi.map(d => ({ ...d, value: 30 })));
                }
            } else if (subIndicator === 'KDJ') {
                const kSeries = subChart.addSeries(LineSeries, { color: '#fbbf24', lineWidth: 1, title: 'K' });
                const dSeries = subChart.addSeries(LineSeries, { color: '#38bdf8', lineWidth: 1, title: 'D' });
                const jSeries = subChart.addSeries(LineSeries, { color: '#c084fc', lineWidth: 1, title: 'J' });

                const getKdjData = (key: keyof StockData) => data.map(d => {
                    const timeStr = d.timestamp || d.date;
                    return { 
                        time: (new Date(timeStr!).getTime() / 1000) as Time, 
                        value: (d[key] as number) || 0 
                    };
                }).filter(d => !isNaN(d.value) && !isNaN(d.time as number)).sort((a, b) => (a.time as number) - (b.time as number));

                kSeries.setData(getKdjData('kdj_k'));
                dSeries.setData(getKdjData('kdj_d'));
                jSeries.setData(getKdjData('kdj_j'));
            }
        }

        // 响应式调整大小
        const handleResize = () => {
            if (chartContainerRef.current && chartInstance.current) {
                chartInstance.current.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
            if (subChartContainerRef.current && subChartInstance.current) {
                subChartInstance.current.applyOptions({ width: subChartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        // Fit Content
        chart.timeScale().fitContent();
        if (subChartInstance.current) subChartInstance.current.timeScale().fitContent();

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartInstance.current) {
                chartInstance.current.remove();
                chartInstance.current = null;
            }
            if (subChartInstance.current) {
                subChartInstance.current.remove();
                subChartInstance.current = null;
            }
        };
    }, [data, mainIndicator, subIndicator]); // 依赖项变化时重建图表

    return (
        <div className="flex flex-col gap-2 w-full h-[600px]">
            {/* 主图 */}
            <div ref={chartContainerRef} className="flex-1 rounded-lg border border-slate-800 overflow-hidden" />
            
            {/* 副图 */}
            {subIndicator !== 'NONE' && (
                <div ref={subChartContainerRef} className="h-[150px] rounded-lg border border-slate-800 overflow-hidden" />
            )}
        </div>
    );
};

export default TradingViewChart;
