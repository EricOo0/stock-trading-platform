
import React from 'react';
import { Activity, BarChart3, Clock } from 'lucide-react';

interface RealTimeDataProps {
    symbol?: string;
    price?: number;
    change?: number;
    changePercent?: number;
    high?: number;
    low?: number;
    open?: number;
    volume?: number; // 成交量
    turnover?: number; // 成交额
    turnoverRate?: number; // 换手率
    pe?: number; // 市盈率
    pb?: number; // 市净率
    marketCap?: number; // 市值
    amplitude?: number; // 振幅
}

const RealTimeDataPanel: React.FC<RealTimeDataProps> = ({
    symbol,
    price,
    change,
    changePercent,
    high,
    low,
    open,
    volume,
    turnover,
    turnoverRate,
    pe,
    // pb, 
    // marketCap,
    amplitude,
}) => {
    // Helper to format or show placeholder
    const formatVal = (val: number | undefined, suffix = '') => {
        if (val === undefined || val === null) return '--';
        return val + suffix;
    };

    // Use standard colors: Red=Up, Green=Down for Chinese context or if requested.
    // User image shows Green for negative.
    const getChangeColor = (val: number | undefined) => {
        if (val === undefined) return 'text-slate-200';
        return val >= 0 ? 'text-red-400' : 'text-green-400';
    };

    return (
        <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 rounded-xl p-6 h-full flex flex-col gap-6 shadow-xl">
            {/* Header Section */}
            <div>
                <h2 className="text-slate-400 text-sm font-medium flex items-center gap-2">
                    <Activity size={16} />
                    数据总览 (Real-time Data)
                </h2>
                <div className="mt-2 text-4xl font-bold text-white tracking-wider flex items-baseline gap-2">
                    {formatVal(price)}
                    <span className={`text-lg font-medium ${getChangeColor(change)}`}>
                        {change !== undefined && change >= 0 ? '+' : ''}{formatVal(change)} ({changePercent !== undefined ? changePercent : '--'}%)
                    </span>
                </div>
                <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                    <Clock size={12} />
                    <span>Data time: {price ? new Date().toLocaleTimeString() : '--:--:--'}</span>
                </div>
            </div>

            {/* Grid Stats */}
            <div className="grid grid-cols-2 gap-y-6 gap-x-4">
                <StatItem label="最高 (High)" value={formatVal(high)} />
                <StatItem label="最低 (Low)" value={formatVal(low)} />
                <StatItem label="今开 (Open)" value={formatVal(open)} />
                <StatItem label="换手率 (Turnover Rate)" value={formatVal(turnoverRate, '%')} />

                <StatItem label="成交量 (Vol)" value={formatVal(volume, 'M')} />
                <StatItem label="成交额 (Amt)" value={formatVal(turnover, 'B')} />

                <StatItem label="市盈率 (PE)" value={formatVal(pe)} />
                <StatItem label="振幅 (Amplitude)" value={formatVal(amplitude, '%')} />
            </div>

            {/* News Snippet or Extra Info */}
            <div className="mt-auto border-t border-slate-700/50 pt-4">
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                    <BarChart3 size={16} className="text-blue-400" />
                    Latest News
                </h3>
                <div className="space-y-3">
                    {symbol ? (
                        <>
                            <NewsItem
                                title={`${symbol} - Market movement analysis and updates...`}
                                time="2 hours ago"
                            />
                            <NewsItem
                                title="Sector performance report: Technology leads gains..."
                                time="5 hours ago"
                            />
                        </>
                    ) : (
                        <div className="text-slate-500 text-sm italic">Search a symbol to see news</div>
                    )}
                </div>
            </div>
        </div>
    );
};

const StatItem = ({ label, value }: { label: string, value: string | number }) => (
    <div className="flex flex-col gap-1">
        <span className="text-slate-500 text-xs">{label}</span>
        <span className="text-slate-200 font-mono font-medium">{value}</span>
    </div>
);

const NewsItem = ({ title, time }: { title: string, time: string }) => (
    <div className="group cursor-pointer">
        <p className="text-slate-300 text-sm line-clamp-2 group-hover:text-blue-400 transition-colors">
            {title}
        </p>
        <span className="text-slate-600 text-xs">{time}</span>
    </div>
);

export default RealTimeDataPanel;
