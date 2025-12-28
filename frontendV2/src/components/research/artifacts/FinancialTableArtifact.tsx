import React from 'react';

interface FinancialTableArtifactProps {
    data: {
        symbol: string;
        currency?: string;
        metrics: Record<string, string | number>[]; // Array of objects
    };
}

export const FinancialTableArtifact: React.FC<FinancialTableArtifactProps> = ({ data }) => {
    const { metrics } = data;
    
    if (!metrics || metrics.length === 0) {
        return <div className="text-gray-500 text-sm p-4">No financial data available.</div>;
    }

    // Extract keys dynamically from the first item, filtering out 'date' to put it first
    const firstItem = metrics[0];
    const keys = Object.keys(firstItem).filter(k => k !== 'date');
    const columns = ['date', ...keys];

    // Format header names (e.g. "gross_profit" -> "Gross Profit")
    const formatHeader = (key: string) => {
        return key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    };

    // Format cell values
    const formatValue = (key: string, value: string | number) => {
        if (typeof value === 'number') {
            // Large numbers format
            if (Math.abs(value) >= 1e9) return (value / 1e9).toFixed(2) + 'B';
            if (Math.abs(value) >= 1e6) return (value / 1e6).toFixed(2) + 'M';
            return value.toLocaleString();
        }
        return value;
    };

    return (
        <div className="overflow-x-auto w-full border border-gray-200 rounded-lg shadow-sm bg-white my-2">
            <table className="w-full text-sm text-left text-gray-700">
                <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-200">
                    <tr>
                        {columns.map(col => (
                            <th key={col} className="px-4 py-2 font-medium whitespace-nowrap">
                                {formatHeader(col)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {metrics.map((row, idx) => (
                        <tr key={idx} className="bg-white border-b border-gray-100 hover:bg-gray-50 last:border-0">
                            {columns.map(col => (
                                <td key={col} className="px-4 py-2 whitespace-nowrap">
                                    {formatValue(col, row[col])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
