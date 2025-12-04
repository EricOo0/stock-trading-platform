import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import type { HistoryItem } from '../../types/financial';

interface TrendChartProps {
    data: HistoryItem[];
    title: string;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, title }) => {
    // Sort data by date ascending for the chart
    const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return (
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4 w-full h-[300px]">
            <h3 className="text-gray-300 text-sm font-medium mb-4">{title}</h3>
            <div className="w-full h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={sortedData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis
                            dataKey="date"
                            stroke="#9CA3AF"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="#9CA3AF"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            unit="%"
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                borderColor: '#374151',
                                borderRadius: '0.5rem',
                                color: '#F3F4F6'
                            }}
                            itemStyle={{ color: '#F3F4F6' }}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="roe"
                            name="ROE"
                            stroke="#8B5CF6"
                            strokeWidth={2}
                            dot={{ r: 4, fill: '#8B5CF6' }}
                            activeDot={{ r: 6 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="gross_margin"
                            name="Gross Margin"
                            stroke="#10B981"
                            strokeWidth={2}
                            dot={{ r: 4, fill: '#10B981' }}
                            activeDot={{ r: 6 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="net_margin"
                            name="Net Margin"
                            stroke="#3B82F6"
                            strokeWidth={2}
                            dot={{ r: 4, fill: '#3B82F6' }}
                            activeDot={{ r: 6 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default TrendChart;
