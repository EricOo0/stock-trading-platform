import React from 'react';

interface IndicatorSelectorProps {
    mainIndicator: 'MA' | 'BOLL' | 'NONE';
    subIndicator: 'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE';
    onMainChange: (indicator: 'MA' | 'BOLL' | 'NONE') => void;
    onSubChange: (indicator: 'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE') => void;
}

const IndicatorSelector: React.FC<IndicatorSelectorProps> = ({
    mainIndicator,
    subIndicator,
    onMainChange,
    onSubChange,
}) => {
    return (
        <div className="flex flex-col gap-6 p-5 bg-slate-800 rounded-lg border border-slate-700">
            {/* 主图指标 */}
            <div className="flex flex-col gap-3">
                <span className="text-slate-400 text-sm font-medium">主图指标 (Main)</span>
                <div className="flex flex-wrap gap-2">
                    {(['MA', 'BOLL', 'NONE'] as const).map((ind) => (
                        <button
                            key={ind}
                            onClick={() => onMainChange(ind)}
                            className={`flex-1 min-w-[60px] px-3 py-2 rounded text-sm font-medium transition-all ${mainIndicator === ind
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
                                }`}
                        >
                            {ind === 'NONE' ? '无' : ind}
                        </button>
                    ))}
                </div>
            </div>

            {/* 副图指标 */}
            <div className="flex flex-col gap-3">
                <span className="text-slate-400 text-sm font-medium">副图指标 (Sub)</span>
                <div className="grid grid-cols-2 gap-2">
                    {(['VOL', 'MACD', 'RSI', 'KDJ', 'NONE'] as const).map((ind) => (
                        <button
                            key={ind}
                            onClick={() => onSubChange(ind)}
                            className={`px-3 py-2 rounded text-sm font-medium transition-all ${subIndicator === ind
                                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
                                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
                                }`}
                        >
                            {ind === 'NONE' ? '无' : ind === 'VOL' ? '成交量' : ind}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default IndicatorSelector;
