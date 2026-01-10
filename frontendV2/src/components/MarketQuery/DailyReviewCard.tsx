import React, { useState } from 'react';
import {
    Clock,
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronDown,
    ChevronUp,
    Bot,
    Zap,
    Calendar,
    ArrowRight
} from 'lucide-react';

interface KeyEvent {
    time: string;
    description: string;
    impact: 'Positive' | 'Negative' | 'Neutral';
}

interface TomorrowPrediction {
    trend: 'UP' | 'DOWN' | 'SIDEWAYS';
    probability: number;
    reason: string;
}

interface DailyReviewCardProps {
    sentimentScore: number;
    sentimentLabel: string;
    keyEvents: KeyEvent[];
    tomorrowPrediction?: TomorrowPrediction;
    strategy: string;
    summary: string;
    analysis: string; // The full markdown content
    analyzing: boolean;
}

const DailyReviewCard: React.FC<DailyReviewCardProps> = ({
    sentimentScore,
    sentimentLabel,
    keyEvents,
    tomorrowPrediction,
    strategy,
    summary,
    analysis,
    analyzing
}) => {
    const [expanded, setExpanded] = useState(false);

    if (!sentimentLabel && !analyzing && !analysis) return null;

    // Helper for Sentiment Color
    const getSentimentColor = () => {
        if (analyzing) return 'text-blue-400';
        if (sentimentScore >= 60) return 'text-rose-400'; // Euphoria/Optimism (Red in CN market usually implies up/heat, but standard sentiment: Green=Good? In stocks: Red=Up=Good Sentiment? Let's use generic Emotional colors)
        // Actually, let's use:
        // High Score (Euphoria) -> Red/Orange (Overheating? or just Up?)
        // Low Score (Panic) -> Green (Oversold?) or Cold Blue?
        // Let's stick to: High=Red (Warm), Low=Green (Cool/Panic drop) or vice versa depending on market convention.
        // A-shares: Red=Up. Let's assume High Score = Bullish/Euphoria = Red.
        if (sentimentScore <= 40) return 'text-emerald-400'; // Panic
        return 'text-amber-400'; // Neutral
    };

    const getBgColor = () => {
        if (analyzing) return 'bg-blue-500/5';
        if (sentimentScore >= 60) return 'bg-rose-500/5';
        if (sentimentScore <= 40) return 'bg-emerald-500/5';
        return 'bg-amber-500/5';
    };

    const getTrendIcon = (trend?: string) => {
        if (!trend) return <Minus size={16} />;
        if (trend === 'UP') return <TrendingUp size={16} className="text-rose-500" />;
        if (trend === 'DOWN') return <TrendingDown size={16} className="text-emerald-500" />;
        return <ArrowRight size={16} className="text-amber-500" />;
    };

    return (
        <div className={`rounded-2xl border backdrop-blur-sm transition-all duration-500 overflow-hidden text-slate-200 border-slate-700/50 shadow-lg ${getBgColor()}`}>

            {/* Main Header Area */}
            <div className="p-5 flex flex-col lg:flex-row lg:items-start gap-6 relative">

                {/* 1. Intraday Sentiment Gauge */}
                <div className="flex flex-col items-center gap-2 min-w-[120px]">
                    <div className="relative w-20 h-12 flex items-end justify-center overflow-hidden">
                        {/* Half Circle Gauge Background */}
                        <div className="absolute top-0 w-20 h-20 rounded-full border-[6px] border-slate-800 box-border"></div>

                        {analyzing ? (
                            <Bot className="mb-1 text-blue-400 animate-bounce" size={24} />
                        ) : (
                            // Gauge Needle logic simplifed for brevity, or css rotate
                            <div className="absolute top-0 w-20 h-20 rounded-full border-[6px] border-transparent border-t-slate-800 border-l-slate-800 transform rotate-45 origin-center transition-all duration-1000"
                                style={{
                                    borderColor: 'transparent',
                                    borderTopColor: sentimentScore > 50 ? '#fb7185' : '#34d399', // Simple color switch
                                    transform: `rotate(${(sentimentScore / 100) * 180 - 135}deg)` // -135 to +45 deg range for top half? 
                                    // CSS gauge is tricky without SVG. Let's use SVG.
                                }}></div>
                        )}
                        {!analyzing && (
                            <svg className="w-20 h-10 overflow-visible">
                                <path d="M 0 40 A 40 40 0 0 1 80 40" fill="none" stroke="#1e293b" strokeWidth="6" />
                                <path d="M 0 40 A 40 40 0 0 1 80 40" fill="none" stroke={sentimentScore >= 50 ? '#f43f5e' : '#10b981'} strokeWidth="6"
                                    strokeDasharray="125" strokeDashoffset={125 - (125 * sentimentScore / 100)}
                                    className="transition-all duration-1000 ease-out" />
                            </svg>
                        )}
                    </div>
                    <div className="text-center">
                        <div className={`font-bold text-lg ${getSentimentColor()}`}>
                            {analyzing ? "Thinking..." : (sentimentLabel || "Neutral")}
                        </div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Daily Sentiment</div>
                    </div>
                </div>

                {/* Separator */}
                <div className="hidden lg:block w-px h-24 bg-white/5 mx-2"></div>

                {/* 2. Key Events Timeline */}
                <div className="flex-1 flex flex-col gap-3 min-w-[200px]">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase">
                        <Clock size={12} /> Key Moments
                    </div>
                    <div className="space-y-2">
                        {keyEvents && keyEvents.length > 0 ? keyEvents.map((evt, idx) => (
                            <div key={idx} className="flex items-start gap-3 text-xs group">
                                <span className="font-mono text-slate-400 bg-slate-800/50 px-1.5 py-0.5 rounded border border-slate-700/50 group-hover:border-blue-500/30 transition-colors">
                                    {evt.time}
                                </span>
                                <span className={`flex-1 ${evt.impact === 'Positive' ? 'text-rose-200' : evt.impact === 'Negative' ? 'text-emerald-200' : 'text-slate-300'}`}>
                                    {evt.description}
                                </span>
                            </div>
                        )) : (
                            <div className="text-xs text-slate-600 italic">No key events identified yet.</div>
                        )}
                    </div>
                </div>

                {/* 3. Tomorrow's Outlook */}
                <div className="flex-1 border-l border-white/5 pl-6 min-w-[200px]">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase mb-3">
                        <Calendar size={12} /> Tomorrow's Script
                    </div>
                    {analyzing ? (
                        <div className="space-y-2">
                            <div className="h-4 w-24 bg-slate-800 animate-pulse rounded"></div>
                            <div className="h-2 w-32 bg-slate-800 animate-pulse rounded"></div>
                        </div>
                    ) : tomorrowPrediction ? (
                        <div>
                            <div className="flex items-center gap-2 mb-2">
                                <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700">
                                    {getTrendIcon(tomorrowPrediction.trend)}
                                </div>
                                <div>
                                    <div className="font-bold text-sm text-slate-200">
                                        {tomorrowPrediction.trend === 'UP' ? 'Bullish' : tomorrowPrediction.trend === 'DOWN' ? 'Bearish' : 'Sideways'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Probability: {tomorrowPrediction.probability}%</div>
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 leading-snug">
                                {tomorrowPrediction.reason}
                            </p>
                        </div>
                    ) : (
                        <div className="text-xs text-slate-600">Waiting for prediction...</div>
                    )}
                </div>

                {/* Expand Button */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="absolute top-4 right-4 p-2 hover:bg-white/5 rounded-lg transition-colors text-slate-500 hover:text-white"
                >
                    {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
            </div>

            {/* Bottom: Strategy & Summary */}
            <div className="px-5 pb-4">
                <div className="bg-slate-900/40 rounded-lg p-3 border border-white/5 flex items-start gap-3">
                    <Zap size={16} className="text-amber-400 mt-0.5 shrink-0" />
                    <div className="text-sm">
                        <span className="font-bold text-amber-100 block mb-0.5">Strategy Focus</span>
                        <span className="text-slate-300 opacity-90 text-xs leading-relaxed">{strategy || "Analyzing strategy..."}</span>
                    </div>
                </div>
            </div>

            {/* Expanded Content: Detailed Analysis */}
            <div className={`transition-all duration-500 ease-in-out bg-slate-900/60 border-t border-white/5 ${expanded ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'}`}>
                <div className="p-5 overflow-auto max-h-[500px] custom-scrollbar">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Comprehensive Review</h4>
                    <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed font-mono text-xs whitespace-pre-wrap">
                        {analysis}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DailyReviewCard;
