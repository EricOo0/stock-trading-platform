import React, { useState, useRef } from 'react';
import { Bot, RefreshCw, Zap, TrendingUp, TrendingDown, Minus, Target, AlertTriangle, Lightbulb, Rocket, RotateCcw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { marketService } from '../../services/marketService';

interface MarketAnalysisCardProps {
    className?: string;
}

interface SectorPick {
    name: string;
    reason: string;
    top_stocks: string[];
}

interface AnalysisResult {
    market_sentiment_score: number;
    market_signal: 'Bullish' | 'Bearish' | 'Neutral' | 'Volatile';
    core_thesis: string;
    confidence_score: number;
    key_catalysts: string[];
    sector_picks: SectorPick[];
    hot_sectors_analysis: string;
    strategy_suggestion: string;
    detailed_report: string;
}

const MarketAnalysisCard: React.FC<MarketAnalysisCardProps> = ({ className }) => {
    const [status, setStatus] = useState<'idle' | 'loading' | 'analyzing' | 'done'>('idle');
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [streamBuffer, setStreamBuffer] = useState('');
    
    // UI State
    const [expanded, setExpanded] = useState(false);

    const handleAnalysis = async () => {
        if (status === 'loading' || status === 'analyzing') return;
        
        setStatus('loading');
        setStreamBuffer('');
        setResult(null);
        
        try {
            setStatus('analyzing');
            await marketService.fetchMarketOutlook((chunk) => {
                setStreamBuffer(prev => prev + chunk);
            });
            setStatus('done');
        } catch (e) {
            console.error(e);
            setStatus('idle');
        }
    };

    React.useEffect(() => {
        if (streamBuffer && status === 'done') {
            try {
                let jsonStr = streamBuffer;
                if (streamBuffer.includes('```json')) {
                    jsonStr = streamBuffer.split('```json')[1].split('```')[0];
                }
                const parsed = JSON.parse(jsonStr);
                setResult(parsed);
            } catch (e) {
                console.warn("Failed to parse analysis result:", e);
                setResult({
                    market_sentiment_score: 50,
                    market_signal: 'Neutral',
                    core_thesis: "解析失败，请查看详细报告。",
                    confidence_score: 0,
                    key_catalysts: [],
                    sector_picks: [],
                    hot_sectors_analysis: "",
                    strategy_suggestion: "",
                    detailed_report: streamBuffer
                });
            }
        }
    }, [streamBuffer, status]);

    const getSignalColor = (signal: string) => {
        switch (signal) {
            case 'Bullish': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
            case 'Bearish': return 'text-red-400 bg-red-500/10 border-red-500/20';
            case 'Volatile': return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
            default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 70) return 'text-emerald-400';
        if (score <= 30) return 'text-red-400';
        return 'text-yellow-400';
    };

    if (status === 'idle') {
        return (
            <div className={`w-full bg-slate-800/30 border border-slate-700/30 rounded-2xl p-8 flex flex-col items-center justify-center text-center space-y-6 ${className}`}>
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center ring-1 ring-white/10">
                    <Bot size={32} className="text-indigo-400" />
                </div>
                <div className="max-w-md">
                    <h3 className="text-xl font-bold text-white mb-2">AI 市场全景深度分析</h3>
                    <p className="text-slate-400">结合资金流向、舆情热度与宏观数据，生成专业的市场研判报告与操作建议。</p>
                </div>
                <button
                    onClick={handleAnalysis}
                    className="group relative px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-indigo-500/25 overflow-hidden"
                >
                    <span className="relative z-10 flex items-center gap-2">
                        <Zap size={18} className="group-hover:text-yellow-300 transition-colors" />
                        开始智能分析
                    </span>
                    <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                </button>
            </div>
        );
    }

    if (status === 'loading' || status === 'analyzing') {
        return (
            <div className={`w-full bg-slate-800/30 border border-slate-700/30 rounded-2xl p-8 min-h-[400px] flex flex-col items-center justify-center space-y-6 ${className}`}>
                <div className="relative">
                    <div className="w-16 h-16 rounded-full border-4 border-slate-700 border-t-indigo-500 animate-spin" />
                    <Bot size={24} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-400" />
                </div>
                <div className="text-center space-y-2">
                    <h3 className="text-lg font-medium text-white animate-pulse">正在深度扫描市场...</h3>
                    <p className="text-sm text-slate-500">
                        {status === 'loading' ? '连接决策大脑' : '分析资金流向与舆情数据'}
                    </p>
                </div>
                <div className="w-64 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 animate-progress origin-left" />
                </div>
            </div>
        );
    }

    if (!result) return null;

    return (
        <div className={`w-full space-y-6 ${className}`}>
            <div className="flex justify-end px-2">
                <button 
                    onClick={handleAnalysis}
                    className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors bg-slate-800/50 hover:bg-slate-700/50 px-3 py-1.5 rounded-lg border border-slate-700/50"
                >
                    <RotateCcw size={12} />
                    重新分析
                </button>
            </div>

            {/* 核心指标卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                {/* 左侧：情绪仪表盘与核心观点 */}
                <div className="md:col-span-4 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 flex flex-col">
                    <div className="flex items-center justify-between mb-6">
                        <span className="text-sm text-slate-400 font-medium uppercase tracking-wider">市场情绪</span>
                        <div className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getSignalColor(result.market_signal)}`}>
                            {result.market_signal.toUpperCase()}
                        </div>
                    </div>
                    
                    <div className="flex-1 flex flex-col items-center justify-center py-4">
                        <div className={`text-5xl font-bold mb-2 ${getScoreColor(result.market_sentiment_score)}`}>
                            {result.market_sentiment_score}
                        </div>
                        <div className="text-sm text-slate-500">Sentiment Score</div>
                    </div>

                    <div className="mt-6 pt-6 border-t border-slate-700/50">
                        <div className="flex items-start gap-3">
                            <Target className="text-indigo-400 shrink-0 mt-1" size={18} />
                            <div>
                                <h4 className="text-sm font-medium text-slate-300 mb-1">核心观点</h4>
                                <p className="text-white text-sm leading-relaxed font-medium">
                                    {result.core_thesis}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 右侧：催化剂与建议 */}
                <div className="md:col-span-8 grid grid-cols-1 gap-6">
                    {/* 关键催化剂 */}
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                        <h4 className="text-sm text-slate-400 font-medium uppercase tracking-wider mb-4 flex items-center gap-2">
                            <TrendingUp size={16} /> 关键驱动因素
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            {result.key_catalysts.map((cat, idx) => (
                                <div key={idx} className="bg-slate-700/30 rounded-lg p-3 text-sm text-slate-200 border border-slate-700/30 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                                    {cat}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        {/* 重点关注板块推荐 */}
                        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                            <h4 className="text-sm text-slate-400 font-medium uppercase tracking-wider mb-3 flex items-center gap-2">
                                <Rocket size={16} className="text-pink-400" /> 重点关注 (Sector Picks)
                            </h4>
                            <div className="space-y-3">
                                {result.sector_picks?.map((pick, idx) => (
                                    <div key={idx} className="bg-slate-900/40 rounded-lg p-3 border border-slate-700/30">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-white font-bold text-sm">{pick.name}</span>
                                            <div className="flex gap-1">
                                                {pick.top_stocks.map((stock, i) => (
                                                    <span key={i} className="text-[10px] bg-slate-700 px-1.5 py-0.5 rounded text-slate-300">{stock}</span>
                                                ))}
                                            </div>
                                        </div>
                                        <p className="text-xs text-slate-400 leading-tight">{pick.reason}</p>
                                    </div>
                                ))}
                                {(!result.sector_picks || result.sector_picks.length === 0) && (
                                    <p className="text-sm text-slate-500">暂无重点推荐</p>
                                )}
                            </div>
                        </div>

                        {/* 策略建议 */}
                        <div className="bg-gradient-to-br from-indigo-900/40 to-slate-800/50 backdrop-blur-sm border border-indigo-500/20 rounded-2xl p-6 flex flex-col">
                            <h4 className="text-sm text-indigo-300 font-medium uppercase tracking-wider mb-3 flex items-center gap-2">
                                <Lightbulb size={16} /> 操作建议
                            </h4>
                            <p className="text-sm text-white font-medium leading-relaxed mb-4 flex-1">
                                {result.strategy_suggestion}
                            </p>
                            <div className="text-xs text-slate-500 border-t border-slate-700/30 pt-3">
                                <span className="font-semibold text-slate-400">板块点评:</span> {result.hot_sectors_analysis}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 详细报告折叠区域 */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                <button 
                    onClick={() => setExpanded(!expanded)}
                    className="w-full flex items-center justify-between p-4 text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors"
                >
                    <span className="text-sm font-medium flex items-center gap-2">
                        <Bot size={16} /> 查看完整分析报告
                    </span>
                    <span className="text-xs bg-slate-800 px-2 py-1 rounded">Markdown</span>
                </button>
                
                {expanded && (
                    <div className="p-6 border-t border-slate-800 prose prose-invert prose-sm max-w-none bg-slate-950/30">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {result.detailed_report}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MarketAnalysisCard;
