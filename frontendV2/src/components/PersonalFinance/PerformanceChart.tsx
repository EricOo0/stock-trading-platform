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

export interface PerformanceData {
    date: string;
    nav_user: number | null;
    nav_ai: number | null;
    nav_sh: number;
    nav_sz: number;
}

interface Props {
    data: PerformanceData[];
    height?: number;
}

export const PerformanceChart: React.FC<Props> = ({ data, height = 400 }) => {
    if (!data || data.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-gray-400 bg-white rounded-lg border border-gray-100">
                <div className="text-center">
                    <p className="text-sm">暂无业绩走势数据</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">业绩走势对比</h3>
            <ResponsiveContainer width="100%" height={height}>
                <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                    <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        axisLine={{ stroke: '#e5e7eb' }}
                        tickLine={false}
                    />
                    <YAxis 
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        axisLine={false}
                        tickLine={false}
                        domain={['auto', 'auto']}
                        tickFormatter={(value) => `${((value - 1) * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                            fontSize: '12px'
                        }}
                        itemStyle={{ padding: '2px 0' }}
                        formatter={(value: number) => [`${((value - 1) * 100).toFixed(2)}%`, '']}
                    />
                    <Legend 
                        verticalAlign="top" 
                        height={36}
                        iconType="circle"
                        wrapperStyle={{ fontSize: '12px', color: '#4b5563' }}
                    />
                    
                    {/* User: Red/Primary */}
                    <Line
                        type="monotone"
                        dataKey="nav_user"
                        name="我的组合"
                        stroke="#ef4444" // red-500
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />
                    
                    {/* AI: Blue/Accent */}
                    <Line
                        type="monotone"
                        dataKey="nav_ai"
                        name="AI推荐"
                        stroke="#3b82f6" // blue-500
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />
                    
                    {/* SH Index: Orange/Dashed */}
                    <Line
                        type="monotone"
                        dataKey="nav_sh"
                        name="上证指数"
                        stroke="#f97316" // orange-500
                        strokeDasharray="5 5"
                        strokeWidth={1.5}
                        dot={false}
                        activeDot={{ r: 4 }}
                    />
                    
                    {/* SZ Index: Cyan/Dotted */}
                    <Line
                        type="monotone"
                        dataKey="nav_sz"
                        name="深证成指"
                        stroke="#06b6d4" // cyan-500
                        strokeDasharray="3 3"
                        strokeWidth={1.5}
                        dot={false}
                        activeDot={{ r: 4 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
