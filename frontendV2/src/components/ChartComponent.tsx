import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, LineSeries } from 'lightweight-charts';
import type { IChartApi } from 'lightweight-charts';
import type { MacroDataPoint } from '../services/macroAPI';

interface ChartComponentProps {
    data: MacroDataPoint[];
    color?: string;
}

export const ChartComponent: React.FC<ChartComponentProps> = ({
    data,
    color = '#3b82f6'
}) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        console.log("ChartComponent mounting with data:", data.length);

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#334155' },
                horzLines: { color: '#334155' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                borderColor: '#475569',
            },
        });

        try {
            const lineSeries = chart.addSeries(LineSeries, {
                color: color,
                lineWidth: 2,
            });

            // Sort data by date just in case
            const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

            // Map data to lightweight-charts format and filter out nulls
            const chartData = sortedData
                .filter(item => item.value !== null && item.value !== undefined && !isNaN(item.value))
                .map(item => ({
                    time: item.date,
                    value: item.value,
                }));

            console.log("Chart data prepared:", chartData);

            lineSeries.setData(chartData);
            chart.timeScale().fitContent();

            chartRef.current = chart;

            const resizeObserver = new ResizeObserver(entries => {
                if (entries.length === 0 || !entries[0].target) return;
                const newRect = entries[0].contentRect;
                chart.applyOptions({ width: newRect.width, height: newRect.height });
            });

            resizeObserver.observe(chartContainerRef.current);

            return () => {
                resizeObserver.disconnect();
                chart.remove();
            };
        } catch (e) {
            console.error("Error initializing chart:", e);
        }
    }, [data, color]);

    return <div ref={chartContainerRef} className="w-full h-full" />;
};
