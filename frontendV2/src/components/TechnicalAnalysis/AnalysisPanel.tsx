import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { StockData } from './StockChart';

interface AnalysisPanelProps {
    data: StockData[];
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ data }) => {
    if (!data || data.length === 0) return null;

    const latest = data[data.length - 1];
    
    // 简单的趋势判断
    const hasMa20 = latest.ma20 !== null && latest.ma20 !== undefined;
    const isBullish = hasMa20 ? latest.close > (latest.ma20 as number) : false;
    
    const rsi = latest.rsi14 ?? 50;

    // 支撑压力位 (简单估算)
    const last20 = data.slice(-20);
    const high20 = last20.length > 0 ? Math.max(...last20.map(d => d.high)) : 0;
    const low20 = last20.length > 0 ? Math.min(...last20.map(d => d.low)) : 0;

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {/* 趋势信号 */}
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex items-center justify-between">
                <div>
                    <p className="text-slate-400 text-sm">趋势信号 (Trend)</p>
                    <p className={`text-xl font-bold flex items-center gap-2 ${hasMa20 ? (isBullish ? 'text-red-500' : 'text-green-500') : 'text-slate-400'}`}>
                        {hasMa20 ? (isBullish ? <TrendingUp size={24} /> : <TrendingDown size={24} />) : <Minus size={24} />}
                        {hasMa20 ? (isBullish ? '看多 (Bullish)' : '看空 (Bearish)') : '中性 (Neutral)'}
                    </p>
                </div>
            </div>

            {/* RSI 指标 */}
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                <p className="text-slate-400 text-sm">RSI (14)</p>
                <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">{rsi.toFixed(2)}</span>
                    <span className={`text-sm mb-1 ${rsi > 70 ? 'text-red-400' : rsi < 30 ? 'text-green-400' : 'text-slate-400'}`}>
                        {rsi > 70 ? '超买' : rsi < 30 ? '超卖' : '中性'}
                    </span>
                </div>
            </div>

            {/* 压力位 */}
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                <p className="text-slate-400 text-sm">压力位 (Resistance)</p>
                <p className="text-2xl font-bold text-red-400">{high20.toFixed(2)}</p>
                <p className="text-xs text-slate-500">近20日最高</p>
            </div>

            {/* 支撑位 */}
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                <p className="text-slate-400 text-sm">支撑位 (Support)</p>
                <p className="text-2xl font-bold text-green-400">{low20.toFixed(2)}</p>
                <p className="text-xs text-slate-500">近20日最低</p>
            </div>
        </div>
    );
};

export default AnalysisPanel;
