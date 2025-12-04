import React from 'react';

interface IndicatorCardProps {
    title: string;
    value: string | number | null;
    subValue?: string | number | null;
    subLabel?: string;
    trend?: 'up' | 'down' | 'neutral';
    tooltip?: string;
    className?: string;
}

const IndicatorCard: React.FC<IndicatorCardProps> = ({
    title,
    value,
    subValue,
    subLabel,
    trend,
    tooltip,
    className = '',
}) => {
    const formatValue = (val: string | number | null) => {
        if (val === null || val === undefined) return 'N/A';
        return val;
    };

    const getTrendColor = (t?: 'up' | 'down' | 'neutral') => {
        if (t === 'up') return 'text-green-500';
        if (t === 'down') return 'text-red-500';
        return 'text-gray-400';
    };

    return (
        <div className={`bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4 hover:border-blue-500/30 transition-all duration-300 ${className}`}>
            <div className="flex justify-between items-start mb-2">
                <h3 className="text-gray-400 text-sm font-medium" title={tooltip}>
                    {title}
                </h3>
                {trend && (
                    <span className={`text-xs px-2 py-0.5 rounded-full bg-opacity-10 ${getTrendColor(trend).replace('text-', 'bg-')} ${getTrendColor(trend)}`}>
                        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '-'}
                    </span>
                )}
            </div>

            <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">
                    {formatValue(value)}
                </span>
                {subValue && (
                    <span className="text-xs text-gray-500">
                        {subValue} {subLabel}
                    </span>
                )}
            </div>
        </div>
    );
};

export default IndicatorCard;
