/**
 * 财务指标卡片组件
 * 用于显示单个类别的财务指标
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface MetricItemProps {
    label: string;
    value: number | null | undefined;
    unit?: string;
    trend?: 'up' | 'down' | 'neutral';
    format?: 'number' | 'percent' | 'currency';
}

const MetricItem: React.FC<MetricItemProps> = ({
    label,
    value,
    unit = '',
    trend,
    format = 'number'
}) => {
    const getTrendIcon = () => {
        if (!trend) return null;
        if (trend === 'up') return <TrendingUp className="text-green-500" size={16} />;
        if (trend === 'down') return <TrendingDown className="text-red-500" size={16} />;
        return <Minus className="text-gray-400" size={16} />;
    };

    const formatValue = (val: number) => {
        if (format === 'percent') return `${val.toFixed(2)}%`;
        if (format === 'currency') return `¥${(val / 100000000).toFixed(2)}亿`;
        return val.toFixed(2);
    };

    const displayValue = value !== null && value !== undefined ? formatValue(value) : 'N/A';

    return (
        <div className="flex justify-between items-center py-2">
            <span className="text-sm text-gray-600">{label}</span>
            <div className="flex items-center gap-2">
                <span className="text-base font-semibold text-gray-900 font-mono">
                    {displayValue}{unit}
                </span>
                {getTrendIcon()}
            </div>
        </div>
    );
};

interface IndicatorCardProps {
    title: string;
    icon: LucideIcon;
    iconColor: string;
    iconBgColor: string;
    metrics: MetricItemProps[];
    borderColor?: string;
}

export const IndicatorCard: React.FC<IndicatorCardProps> = ({
    title,
    icon: Icon,
    iconColor,
    iconBgColor,
    metrics,
    borderColor = 'border-gray-200'
}) => {
    return (
        <div className={`bg-white rounded-xl shadow-sm border ${borderColor} p-6 hover:shadow-md transition-all duration-300`}>
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-100">
                <div className={`w-12 h-12 ${iconBgColor} rounded-lg flex items-center justify-center`}>
                    <Icon className={iconColor} size={24} />
                </div>
                <h3 className="text-lg font-bold text-gray-900">{title}</h3>
            </div>

            <div className="space-y-1">
                {metrics.map((metric, index) => (
                    <MetricItem key={index} {...metric} />
                ))}
            </div>
        </div>
    );
};
