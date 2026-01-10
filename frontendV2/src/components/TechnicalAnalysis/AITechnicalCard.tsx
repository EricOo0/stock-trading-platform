import React, { useState } from 'react';
import {
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronDown,
    ChevronUp,
    Bot,
    Target,
    Shield,
    Zap,
    Info,
    Loader,
    AlertTriangle
} from 'lucide-react';

interface KeyLevels {
    support: number[];
    resistance: number[];
}

interface AITechnicalCardProps {
    signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | null;
    confidence: number;
    summary: string;
    reasoning: string;
    keyLevels?: KeyLevels;
    riskFactors?: string[];
    analyzing: boolean;
}

const AITechnicalCard: React.FC<AITechnicalCardProps> = ({
    signal,
    confidence,
    summary,
    reasoning,
    keyLevels,
    riskFactors,
    analyzing
}) => {
    const [expanded, setExpanded] = useState(false);

    if (!signal && !analyzing && !reasoning) return null;

    const score = Math.round((confidence || 0) * 100);

    // Color Logic
    const getStatusColor = () => {
        if (analyzing) return 'text-blue-400 border-blue-500/30 shadow-blue-500/10';
        if (signal === 'BULLISH') return 'text-emerald-400 border-emerald-500/30 shadow-emerald-500/10';
        if (signal === 'BEARISH') return 'text-rose-400 border-rose-500/30 shadow-rose-500/10';
        return 'text-slate-300 border-slate-600/30 shadow-slate-500/10';
    };

    const getBgColor = () => {
        if (analyzing) return 'bg-blue-500/5';
        if (signal === 'BULLISH') return 'bg-emerald-500/5';
        if (signal === 'BEARISH') return 'bg-rose-500/5';
        return 'bg-slate-700/20';
    };

    const getIcon = () => {
        if (analyzing) return <Bot className="animate-pulse" size={24} />;
        if (signal === 'BULLISH') return <TrendingUp size={24} />;
        if (signal === 'BEARISH') return <TrendingDown size={24} />;
        return <Minus size={24} />;
    };

    const formatLevel = (vals?: number[]) => vals && vals.length > 0 ? vals.join(', ') : '--';

    // Tooltip for Methodology
    const MethodologyTooltip = () => (
        <div className="group relative flex items-center">
            <Info size={14} className="text-slate-500 cursor-help hover:text-blue-400 transition-colors" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-slate-800 border border-slate-700 rounded-xl shadow-xl text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                <div className="font-bold text-slate-200 mb-1">AI Scoring Methodology</div>
                <p>Based on multi-model consensus analyzing:</p>
                <ul className="list-disc pl-3 mt-1 space-y-0.5 opacity-80">
                    <li>Trend Structure (Dow/Elliott)</li>
                    <li>Momentum (RSI/MACD)</li>
                    <li>Volume Analysis (OBV)</li>
                    <li>Key Levels (Support/Resistance)</li>
                </ul>
                <div className="absolute bottom-[-5px] left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-800 border-r border-b border-slate-700 transform rotate-45"></div>
            </div>
        </div>
    );

    return (
        <div className={`rounded-2xl border backdrop-blur-sm transition-all duration-500 overflow-hidden ${getStatusColor()} ${getBgColor()} shadow-lg`}>
            {/* Header / Dashboard */}
            <div className="p-5 flex flex-col md:flex-row md:items-center gap-6 relative">

                {/* 1. Score / Gauge Section */}
                <div className="flex items-center gap-4 min-w-[140px]">
                    <div className="relative w-16 h-16 flex items-center justify-center">
                        {analyzing ? (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <Bot className="text-blue-400 animate-bounce" size={28} />
                            </div>
                        ) : (
                            <>
                                <svg className="w-full h-full transform -rotate-90">
                                    <circle
                                        cx="32"
                                        cy="32"
                                        r="28"
                                        stroke="currentColor"
                                        strokeWidth="6"
                                        fill="transparent"
                                        className="text-slate-800"
                                    />
                                    <circle
                                        cx="32"
                                        cy="32"
                                        r="28"
                                        stroke="currentColor"
                                        strokeWidth="6"
                                        fill="transparent"
                                        strokeDasharray={175} // 2 * pi * 28 approx 175
                                        strokeDashoffset={175 - (175 * score) / 100}
                                        className={`transition-all duration-1000 ease-out ${getStatusColor()}`}
                                    />
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center font-bold text-lg">
                                    {score}<span className="text-[10px] opacity-70">%</span>
                                </div>
                            </>
                        )}
                    </div>
                    <div>
                        <div className="flex items-center gap-1.5 mb-0.5">
                            <div className="text-xs font-medium opacity-60 uppercase tracking-wider">Confidence</div>
                            <MethodologyTooltip />
                        </div>
                        <div className="font-bold text-lg tracking-tight">
                            {analyzing ? (
                                <span className="animate-pulse text-blue-400">Thinking...</span>
                            ) : (
                                signal || 'WAITING'
                            )}
                        </div>
                    </div>
                </div>

                {/* Separator */}
                <div className="hidden md:block w-px h-12 bg-white/10 mx-2"></div>

                {/* 2. Key Levels */}
                <div className="flex-1 grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-xs text-rose-300 font-medium uppercase">
                            <Shield size={12} /> 压力位 (Resistance)
                        </div>
                        <div className="font-mono text-sm">{keyLevels ? formatLevel(keyLevels.resistance) : '--'}</div>
                    </div>
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-xs text-emerald-300 font-medium uppercase">
                            <Target size={12} /> 支撑位 (Support)
                        </div>
                        <div className="font-mono text-sm">{keyLevels ? formatLevel(keyLevels.support) : '--'}</div>
                    </div>

                    {/* Summary Text (Spans 2 cols) */}
                    <div className="col-span-2 pt-2 border-t border-white/5">
                        <div className="flex items-center gap-2 text-xs opacity-70 mb-1">
                            <Zap size={12} /> AI Summary
                        </div>
                        <p className="text-sm font-medium leading-relaxed opacity-90">
                            {analyzing ? "Analyzing market structure..." : summary || "Waiting for signal..."}
                        </p>
                    </div>

                    {/* Risk Factors */}
                    {riskFactors && riskFactors.length > 0 && (
                        <div className="col-span-2 pt-2 border-t border-white/5">
                            <div className="flex items-start gap-2">
                                <AlertTriangle size={12} className="text-amber-400 mt-0.5 shrink-0" />
                                <div className="space-y-1">
                                    {riskFactors.map((risk, idx) => (
                                        <div key={idx} className="text-xs text-amber-200/80 leading-snug">
                                            • {risk}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Expand Button */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="absolute top-4 right-4 p-2 hover:bg-white/5 rounded-lg transition-colors"
                >
                    {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
            </div>

            {/* Expanded Detailed Reasoning */}
            <div className={`transition-all duration-500 ease-in-out bg-slate-900/40 border-t border-white/5 ${expanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}>
                <div className="p-5">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Detailed Logic</h4>
                    <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed font-mono text-xs whitespace-pre-wrap">
                        {reasoning}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AITechnicalCard;
