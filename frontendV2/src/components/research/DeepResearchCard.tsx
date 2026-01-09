import React from 'react';

export interface DeepResearchProps {
    signals: {
        condition: string;
        result: string;
    }[];
    analysis: string;
    outlook: {
        score: number; // 0-100
        label: 'Extreme Caution' | 'Caution' | 'Neutral' | 'Optimism' | 'Extreme Optimism';
    };
    references: {
        id: string;
        title: string;
        source: string;
        url?: string;
    }[];
}

export const DeepResearchCard: React.FC<DeepResearchProps> = ({ signals, analysis, outlook, references }) => {
    // Outlook segments configuration
    const segments = [
        { label: 'Extreme Caution', color: 'bg-emerald-500', activeColor: 'bg-emerald-400', range: [0, 20] },
        { label: 'Caution', color: 'bg-teal-500', activeColor: 'bg-teal-400', range: [21, 40] },
        { label: 'Neutral', color: 'bg-yellow-500', activeColor: 'bg-yellow-400', range: [41, 60] },
        { label: 'Optimism', color: 'bg-orange-500', activeColor: 'bg-orange-400', range: [61, 80] },
        { label: 'Extreme Optimism', color: 'bg-red-500', activeColor: 'bg-red-400', range: [81, 100] },
    ];

    // Find active segment index
    const activeSegmentIndex = segments.findIndex(seg =>
        outlook.score >= seg.range[0] && outlook.score <= seg.range[1]
    );

    return (
        <div className="w-full max-w-md mx-auto bg-gray-900/90 backdrop-blur-xl border border-gray-700/50 rounded-2xl overflow-hidden shadow-2xl text-gray-200 font-sans">
            {/* Header / Signals Section */}
            <div className="p-5 bg-gradient-to-b from-gray-800/50 to-transparent">
                <div className="flex items-center gap-2 mb-3 text-gray-400 text-xs font-semibold uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    Key Signals
                </div>

                <div className="space-y-2">
                    {signals.map((signal, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-gray-800/50 border border-gray-700 rounded-lg p-3 group hover:border-blue-500/30 transition-colors">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-gray-300">{signal.condition}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-gray-500 text-xs text-bold">=</span>
                                <span className="text-sm font-bold text-blue-400">{signal.result}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Analysis Text */}
            <div className="px-5 py-2">
                <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">Trend Analysis</h3>
                <p className="text-sm leading-relaxed text-gray-300">
                    {analysis}
                </p>
            </div>

            {/* Market Outlook Meter */}
            <div className="p-5">
                <h3 className="text-xs font-bold text-gray-500 uppercase mb-4 text-center">Market Outlook</h3>

                <div className="relative pt-6 pb-2">
                    {/* Meter Segments */}
                    <div className="flex gap-1 h-2 rounded-full overflow-hidden bg-gray-800">
                        {segments.map((seg, idx) => {
                            const isActive = idx === activeSegmentIndex;
                            return (
                                <div
                                    key={idx}
                                    className={`flex-1 transition-all duration-500 ${isActive ? seg.activeColor + ' shadow-[0_0_10px_rgba(255,255,255,0.3)]' : 'bg-gray-700 opacity-30'}`}
                                />
                            );
                        })}
                    </div>

                    {/* Active Label & Indicator */}
                    <div
                        className="absolute top-0 transition-all duration-500 flex flex-col items-center transform -translate-x-1/2"
                        style={{
                            left: `${segments.reduce((acc, _, idx) => idx < activeSegmentIndex ? acc + 20 : acc, 10)}%`
                            // Simplified positioning logic: 5 segments = 20% each. Center of active segment.
                            // Better logic: (activeSegmentIndex * 20) + 10 + '%'
                        }}
                    >
                        {/* Determine exact left position based on score if needed, but segment based is cleaner visually for this stepped UI */}
                    </div>
                </div>

                <div className="flex justify-between items-center mt-3">
                    {segments.map((seg, idx) => (
                        <div key={idx} className={`text-[9px] font-bold uppercase transition-colors duration-300 ${idx === activeSegmentIndex ? 'text-white scale-110' : 'text-gray-600'}`}>
                            {seg.label.split(' ')[0]} <br /> {seg.label.split(' ')[1]}
                        </div>
                    ))}
                </div>

                {/* Big Score Display */}
                <div className="mt-4 text-center">
                    <span className={`text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-yellow-400 to-red-500`}>
                        {outlook.score}%
                    </span>
                    <div className="text-xs text-gray-400 mt-1 uppercase tracking-widest">{outlook.label}</div>
                </div>
            </div>

            {/* References */}
            <div className="bg-gray-950/50 p-5 border-t border-gray-800">
                <div className="flex items-center gap-2 mb-3 cursor-pointer group">
                    <h3 className="text-xs font-bold text-gray-500 uppercase group-hover:text-gray-300 transition-colors">Reference Sources</h3>
                    <span className="text-[10px] text-gray-600 group-hover:text-gray-400">▼</span>
                </div>
                <div className="space-y-3">
                    {references.map((ref) => (
                        <a key={ref.id} href={ref.url} target="_blank" rel="noopener noreferrer" className="flex items-start gap-3 group hover:bg-gray-800/30 p-2 -mx-2 rounded transition-colors">
                            <div className="mt-0.5 w-4 h-4 rounded-sm bg-blue-500/20 text-blue-400 flex items-center justify-center text-[8px] font-bold flex-shrink-0">
                                S
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="text-xs text-gray-300 truncate group-hover:text-blue-300 transition-colors">{ref.title}</div>
                                <div className="text-[10px] text-gray-600 mt-0.5">{ref.source}</div>
                            </div>
                        </a>
                    ))}
                </div>
            </div>
        </div>
    );
};
