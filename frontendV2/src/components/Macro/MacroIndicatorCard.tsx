import React, { useState } from 'react';
import {
    Activity,
    TrendingUp,
    TrendingDown,
    Minus,
    AlertTriangle,
    Zap,
    ChevronDown,
    ChevronUp,
    Bot,
    Target
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// 类型定义
interface KeyMetric {
    name: string;
    value: string;
    trend: 'UP' | 'NEUTRAL' | 'DOWN';
}

interface KeyFactors {
    positive: string[];
    negative: string[];
}

interface MacroIndicatorCardProps {
    macroHealthScore?: number;
    macroHealthLabel?: string;
    keyMetrics?: KeyMetric[];
    signal?: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | null;
    confidence?: number;
    marketCycle?: string;
    marketImplication?: string;
    riskWarning?: string;
    strategy?: string;
    summary?: string;
    analysis?: string;
    keyFactors?: KeyFactors;
    analyzing?: boolean;
}

const MacroIndicatorCard: React.FC<MacroIndicatorCardProps> = ({
    macroHealthScore = 50,
    macroHealthLabel = '中性',
    keyMetrics = [],
    signal,
    confidence = 0,
    marketCycle = '',
    marketImplication = '',
    riskWarning = '',
    strategy = '',
    summary = '',
    analysis = '',
    keyFactors,
    analyzing = false
}) => {
    const [expanded, setExpanded] = useState(false);

    // 健康度颜色计算
    const getHealthColor = (score: number) => {
        if (score >= 70) return 'text-emerald-400';
        if (score >= 50) return 'text-yellow-400';
        if (score >= 30) return 'text-orange-400';
        return 'text-red-400';
    };

    const getHealthGradient = (score: number) => {
        if (score >= 70) return 'from-emerald-500 to-emerald-400';
        if (score >= 50) return 'from-yellow-500 to-yellow-400';
        if (score >= 30) return 'from-orange-500 to-orange-400';
        return 'from-red-500 to-red-400';
    };

    // 趋势图标
    const getTrendIcon = (trend: 'UP' | 'NEUTRAL' | 'DOWN') => {
        switch (trend) {
            case 'UP':
                return <TrendingUp size={12} className="text-emerald-400" />;
            case 'DOWN':
                return <TrendingDown size={12} className="text-red-400" />;
            default:
                return <Minus size={12} className="text-gray-400" />;
        }
    };

    // 信号颜色
    const getSignalColor = () => {
        switch (signal) {
            case 'BULLISH':
                return 'border-emerald-500/50 bg-emerald-500/5';
            case 'BEARISH':
                return 'border-red-500/50 bg-red-500/5';
            default:
                return 'border-slate-600 bg-slate-800/50';
        }
    };

    // SVG 仪表盘
    const renderGauge = () => {
        // 半圆仪表盘：0分在左边(180°)，100分在右边(0°)
        // 角度范围：180° → 0° (从左到右)
        const angle = 180 - (macroHealthScore / 100) * 180; // 180 to 0 degrees
        const radians = (angle * Math.PI) / 180;
        const needleLength = 32;
        const centerX = 50;
        const centerY = 50;
        const needleX = centerX + needleLength * Math.cos(radians);
        const needleY = centerY - needleLength * Math.sin(radians); // Y轴向上为负

        return (
            <svg viewBox="0 0 100 60" className="w-32 h-20">
                {/* 背景弧 */}
                <path
                    d="M 10 50 A 40 40 0 0 1 90 50"
                    fill="none"
                    stroke="#334155"
                    strokeWidth="8"
                    strokeLinecap="round"
                />
                {/* 渐变弧 */}
                <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#ef4444" />
                        <stop offset="33%" stopColor="#f59e0b" />
                        <stop offset="66%" stopColor="#eab308" />
                        <stop offset="100%" stopColor="#22c55e" />
                    </linearGradient>
                </defs>
                <path
                    d="M 10 50 A 40 40 0 0 1 90 50"
                    fill="none"
                    stroke="url(#gaugeGradient)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(macroHealthScore / 100) * 126} 126`}
                />
                {/* 指针 */}
                <line
                    x1={centerX}
                    y1={centerY}
                    x2={needleX}
                    y2={needleY}
                    stroke="white"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                />
                <circle cx={centerX} cy={centerY} r="4" fill="white" />
            </svg>
        );
    };

    // 加载状态
    if (analyzing && !summary) {
        return (
            <div className={`rounded-2xl border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-6`}>
                <div className="flex items-center gap-3">
                    <Bot className="text-cyan-400 animate-pulse" size={24} />
                    <div>
                        <div className="text-white font-medium">宏观分析中...</div>
                        <div className="text-slate-400 text-sm">正在评估全球经济环境</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={`rounded-2xl border ${getSignalColor()} backdrop-blur-sm transition-all duration-500 shadow-lg`}>
            {/* 顶部区域 */}
            <div className="p-5 flex flex-col md:flex-row md:items-start gap-6">
                {/* 健康度仪表盘 */}
                <div className="flex flex-col items-center gap-1">
                    {renderGauge()}
                    <div className={`text-2xl font-bold ${getHealthColor(macroHealthScore)}`}>
                        {macroHealthScore}
                    </div>
                    <div className={`text-xs font-medium px-2 py-0.5 rounded-full bg-gradient-to-r ${getHealthGradient(macroHealthScore)} text-white`}>
                        {macroHealthLabel}
                    </div>
                    <div className="text-slate-500 text-xs mt-1">宏观健康度</div>
                </div>

                {/* 核心指标网格 */}
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-3">
                        <Activity size={14} className="text-cyan-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wider">核心指标</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        {keyMetrics.slice(0, 6).map((metric, idx) => (
                            <div key={idx} className="bg-slate-800/60 rounded-lg px-3 py-2 border border-slate-700/50">
                                <div className="text-slate-400 text-xs">{metric.name}</div>
                                <div className="flex items-center justify-between mt-1">
                                    <span className="text-white font-medium text-sm">{metric.value}</span>
                                    {getTrendIcon(metric.trend)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 市场含义 */}
                <div className="md:max-w-[200px]">
                    <div className="flex items-center gap-2 mb-2">
                        <Target size={14} className="text-amber-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wider">市场含义</span>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                        {marketImplication || 'Waiting for analysis...'}
                    </p>
                    {riskWarning && (
                        <div className="flex items-start gap-1.5 mt-3 text-amber-300/80 text-xs">
                            <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                            <span>⚠️ {riskWarning}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* 策略建议栏 */}
            {strategy && (
                <div className="bg-slate-900/60 border-t border-b border-slate-700/50 px-5 py-3">
                    <div className="flex items-center gap-2">
                        <Zap size={14} className="text-yellow-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wider">AI 策略建议</span>
                    </div>
                    <p className="text-white text-sm mt-1">{strategy}</p>
                </div>
            )}

            {/* 经济周期标签 */}
            <div className="px-5 py-3 flex flex-wrap items-center gap-3 border-b border-slate-700/50">
                {marketCycle && (
                    <span className="px-2 py-1 bg-indigo-500/20 text-indigo-300 text-xs rounded-full border border-indigo-500/30">
                        {marketCycle}
                    </span>
                )}
                {signal && (
                    <span className={`px-2 py-1 text-xs rounded-full border ${signal === 'BULLISH'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                        : signal === 'BEARISH'
                            ? 'bg-red-500/20 text-red-300 border-red-500/30'
                            : 'bg-slate-500/20 text-slate-300 border-slate-500/30'
                        }`}>
                        {signal === 'BULLISH' ? '看多' : signal === 'BEARISH' ? '看空' : '中性'} ({Math.round(confidence * 100)}%)
                    </span>
                )}
                {keyFactors && (
                    <>
                        {keyFactors.positive?.slice(0, 2).map((p, i) => (
                            <span key={`pos-${i}`} className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded-full border border-emerald-500/20">
                                +{p}
                            </span>
                        ))}
                        {keyFactors.negative?.slice(0, 2).map((n, i) => (
                            <span key={`neg-${i}`} className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded-full border border-red-500/20">
                                -{n}
                            </span>
                        ))}
                    </>
                )}
            </div>

            {/* 详细分析 */}
            {(summary || analysis) && (
                <div className="px-5 py-4">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-3"
                    >
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        <span className="text-xs uppercase tracking-wider">详细分析</span>
                    </button>

                    {!expanded && summary && (
                        <p className="text-slate-300 text-sm">{summary}</p>
                    )}

                    {expanded && analysis && (
                        <div className="prose prose-sm prose-invert max-w-none text-slate-300">
                            <ReactMarkdown>{analysis}</ReactMarkdown>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default MacroIndicatorCard;
