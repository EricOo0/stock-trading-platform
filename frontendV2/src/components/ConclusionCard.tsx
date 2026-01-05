import React from 'react';
import { ArrowUp, ArrowDown, Minus, CheckCircle } from 'lucide-react';

export interface ConclusionData {
    ticker: string;
    sentiment: string;
    trend: 'up' | 'down' | 'neutral';
    title: string;
    summary: string;
}

interface ConclusionCardProps {
    data: ConclusionData;
}

const ConclusionCard: React.FC<ConclusionCardProps> = ({ data }) => {
    const isUp = data.trend === 'up';
    const isDown = data.trend === 'down';

    // Gradient logic based on trend? Request showed Green, assuming "Good News" / "Clear Upside".
    // Let's stick to the green theme for positive, maybe red for negative if needed, but the image showed green.
    // For now, let's implement the Green style as requested.

    return (
        <div className="w-full bg-gradient-to-br from-emerald-400 to-teal-500 rounded-3xl p-6 text-white shadow-xl transform transition-all hover:scale-[1.01] duration-300 mb-6 animate-in slide-in-from-top-4 fade-in">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4 opacity-90">
                <CheckCircle className="text-white" size={20} />
                <span className="text-sm font-semibold tracking-wide uppercase">结论展示 (Conclusion)</span>
            </div>

            {/* Main Title & Trend */}
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                    <h2 className="text-4xl font-bold tracking-tight">
                        {data.ticker}: {data.title}
                    </h2>
                </div>
                <div>
                    {isUp && <ArrowUp size={48} className="text-white" />}
                    {isDown && <ArrowDown size={48} className="text-white" />}
                    {!isUp && !isDown && <Minus size={48} className="text-white" />}
                </div>
            </div>

            {/* Sub-label */}
            <div className="mb-6">
                <p className="text-lg font-medium opacity-90">
                    市场情绪分析: <span className="font-bold text-white text-xl">{data.sentiment}</span>
                </p>
            </div>

            {/* Summary */}
            <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm border border-white/10 text-sm leading-relaxed opacity-95">
                {data.summary}
            </div>

            {/* Wave Decoration (CSS based or SVG) */}
            <div className="absolute bottom-0 right-0 opacity-10 pointer-events-none">
                <svg width="300" height="100" viewBox="0 0 300 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M0 50C100 50 150 0 300 0V100H0V50Z" fill="white" />
                </svg>
            </div>
        </div>
    );
};

export default ConclusionCard;
