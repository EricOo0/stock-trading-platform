/**
 * 财务指标趋势图表组件
 * 使用 Recharts 显示多指标折线图
 */

import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import type { HistoricalDataPoint } from '../../types/financial';

interface TrendChartProps {
    data: HistoricalDataPoint[];
    height?: number;
}

export const TrendChart: React.FC<TrendChartProps> = ({ data, height = 400 }) => {
    if (!data || data.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-gray-400">
                <div className="text-center">
                    <p className="text-sm">暂无历史数据</p>
                </div>
            </div>
        );
    }

    // 反转数据以按时间正序显示
    const chartData = [...data].reverse();

    return (
        <ResponsiveContainer width="100%" height={height}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    stroke="#9ca3af"
                />
                <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 12 }}
                    stroke="#9ca3af"
                    label={{ value: '百分比 (%)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                />
                <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                    stroke="#9ca3af"
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '12px'
                    }}
                />
                <Legend
                    wrapperStyle={{ fontSize: '12px' }}
                    iconType="line"
                />

                <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="roe"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    name="ROE"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                />
                <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="gross_margin"
                    stroke="#10B981"
                    strokeWidth={2}
                    name="毛利率"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                />
                <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="net_margin"
                    stroke="#8B5CF6"
                    strokeWidth={2}
                    name="净利率"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                />
                <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="asset_liability_ratio"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    name="资产负债率"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
};
