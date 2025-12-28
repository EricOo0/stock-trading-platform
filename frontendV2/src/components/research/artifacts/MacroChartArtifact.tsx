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

interface MacroChartArtifactProps {
    data: {
        indicator?: string;
        // Backend might return raw list or object wrapper. Assuming list of objects based on tool implementation.
        // But artifact payload wrapper puts the tool return value into `data`.
        // If tools returns List, `data` is List.
        // Let's robustly handle if `data` IS the list or contains the list.
        [key: string]: any; 
    };
    title?: string;
}

export const MacroChartArtifact: React.FC<MacroChartArtifactProps> = ({ data, title }) => {
    // Normalize data: it might be an array directly or an object with 'data' field
    const chartData = Array.isArray(data) ? data : (data.data || []);
    
    // Find the value key (not 'date')
    const dataKeys = chartData.length > 0 ? Object.keys(chartData[0]).filter(k => k !== 'date' && k !== 'value') : [];
    // If explicit 'value' key exists, use it. Otherwise use the first non-date key.
    const hasValueKey = chartData.length > 0 && 'value' in chartData[0];
    const yKey = hasValueKey ? 'value' : (dataKeys[0] || 'value');

    if (chartData.length === 0) {
        return <div className="text-gray-500 p-4">No chart data available.</div>;
    }

    return (
        <div className="w-full h-64 bg-white border border-gray-200 rounded-lg p-2 my-2 shadow-sm">
            <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase text-center">{title || "Macro Trend"}</h4>
            <ResponsiveContainer width="100%" height="90%">
                <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis 
                        dataKey="date" 
                        fontSize={10} 
                        tickFormatter={(val) => val ? val.substring(0, 7) : ''} 
                        minTickGap={30}
                    />
                    <YAxis fontSize={10} domain={['auto', 'auto']} width={40} />
                    <Tooltip 
                        contentStyle={{ fontSize: '12px', borderRadius: '4px' }}
                        labelStyle={{ color: '#666' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '10px' }}/>
                    <Line 
                        type="monotone" 
                        dataKey={yKey} 
                        stroke="#8884d8" 
                        strokeWidth={2} 
                        dot={false}
                        activeDot={{ r: 4 }} 
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
