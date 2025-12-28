import React, { useMemo } from 'react';

interface WordData {
    text: string;
    value: number;
    sentiment: 'positive' | 'negative' | 'neutral';
}

interface WordCloudArtifactProps {
    data: {
        status: string;
        data: {
            words: WordData[];
            summary: string;
            source_url?: string;
        };
    };
    title: string;
}

// Custom Word Cloud Implementation for better React 19 compatibility
export const WordCloudArtifact: React.FC<WordCloudArtifactProps> = ({ data, title }) => {
    if (!data || !data.data || !data.data.words || data.data.words.length === 0) {
        return <div className="text-gray-500 italic p-4 text-center">No word cloud data available.</div>;
    }

    const { words, summary, source_url } = data.data;

    // Layout algorithm: Simple spiral placement
    const placedWords = useMemo(() => {
        const sortedWords = [...words].sort((a, b) => b.value - a.value);
        const maxVal = Math.max(...words.map(w => w.value), 1);
        const minVal = Math.min(...words.map(w => w.value));

        const result: any[] = [];
        const occupied: { x: number, y: number, w: number, h: number }[] = [];

        // Constants for layout
        const width = 600;
        const height = 400;
        const centerX = width / 2;
        const centerY = height / 2;

        sortedWords.forEach((word, index) => {
            // Calculate size
            const fontSize = 14 + ((word.value - minVal) / (maxVal - minVal || 1)) * 34;
            // Estimated dimensions (rough but functional)
            const w = word.text.length * fontSize * 0.7 + 20;
            const h = fontSize + 10;

            let angle = 0;
            let radius = 0;
            let x = centerX;
            let y = centerY;
            let found = false;

            // Spiral out until a spot is found
            while (!found && radius < 300) {
                x = centerX + radius * Math.cos(angle) - w / 2;
                y = centerY + radius * Math.sin(angle) - h / 2;

                const hasOverlap = occupied.some(rect => (
                    x < rect.x + rect.w &&
                    x + w > rect.x &&
                    y < rect.y + rect.h &&
                    y + h > rect.y
                ));

                if (!hasOverlap) {
                    found = true;
                    occupied.push({ x, y, w, h });
                    result.push({
                        ...word,
                        x,
                        y,
                        fontSize,
                        rotate: index % 5 === 0 ? (index % 2 === 0 ? 15 : -15) : 0
                    });
                }

                angle += 0.4;
                radius += 0.5;
            }
        });

        return result;
    }, [words]);

    const getSentimentColor = (sentiment: string) => {
        switch (sentiment) {
            case 'positive': return 'fill-emerald-400 drop-shadow-[0_0_3px_rgba(52,211,153,0.5)]';
            case 'negative': return 'fill-rose-400 drop-shadow-[0_0_3px_rgba(251,113,133,0.5)]';
            default: return 'fill-cyan-400 drop-shadow-[0_0_3px_rgba(34,211,238,0.5)]';
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#0f172a] rounded-xl border border-slate-800 overflow-hidden shadow-2xl min-h-[450px]">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]"></span>
                    {title}
                </h3>
                {source_url && (
                    <a href={source_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-cyan-400 hover:text-cyan-300 transition-colors">
                        Source Link
                    </a>
                )}
            </div>

            {/* SVG Canvas */}
            <div className="flex-1 relative bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-[#0f172a] flex items-center justify-center p-4">
                <svg 
                    viewBox="0 0 600 400" 
                    className="w-full h-full max-h-[400px]"
                    preserveAspectRatio="xMidYMid meet"
                >
                    {placedWords.map((word, idx) => (
                        <text
                            key={idx}
                            x={word.x + word.fontSize * 0.35} // Adjust for text anchor
                            y={word.y + word.fontSize}
                            fontSize={word.fontSize}
                            className={`font-bold transition-all duration-500 cursor-default hover:opacity-100 ${getSentimentColor(word.sentiment)}`}
                            style={{ 
                                opacity: 0.8,
                                transform: `rotate(${word.rotate}deg)`,
                                transformOrigin: `${word.x + 20}px ${word.y + 10}px`
                            }}
                        >
                            {word.text}
                            <title>Weight: {word.value} ({word.sentiment})</title>
                        </text>
                    ))}
                </svg>
            </div>

            {/* Summary Footer */}
            {summary && (
                <div className="px-5 py-4 bg-slate-900/80 border-t border-slate-800 text-xs text-slate-400 leading-relaxed italic backdrop-blur-sm">
                    <span className="text-cyan-500 mr-2">✦</span>
                    {summary}
                </div>
            )}
        </div>
    );
};
