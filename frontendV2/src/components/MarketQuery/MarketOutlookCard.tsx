import React, { useState } from 'react';
import { Bot, RefreshCw, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { marketService } from '../../services/marketService';

interface MarketOutlookCardProps {
    className?: string;
}

const MarketOutlookCard: React.FC<MarketOutlookCardProps> = ({ className }) => {
    const [status, setStatus] = useState<'idle' | 'loading' | 'streaming' | 'done'>('idle');
    const [content, setContent] = useState('');

    const handleAnalysis = async () => {
        if (status === 'loading' || status === 'streaming') return;
        
        setStatus('loading');
        setContent('');
        
        try {
            await marketService.fetchMarketOutlook((chunk) => {
                setStatus('streaming');
                setContent(prev => prev + chunk);
            });
            setStatus('done');
        } catch (e) {
            console.error(e);
            setStatus('idle'); // Allow retry
        }
    };

    return (
        <div className={`rounded-2xl border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-6 ${className} flex flex-col h-full`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                        <Bot size={20} className="text-white" />
                    </div>
                    <div>
                        <h3 className="text-white font-bold text-lg">AI 市场全景前瞻</h3>
                        <p className="text-slate-400 text-xs">基于资金流向的深度逻辑分析</p>
                    </div>
                </div>
                
                <button 
                    onClick={handleAnalysis}
                    disabled={status === 'loading' || status === 'streaming'}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2
                        ${status === 'loading' || status === 'streaming' 
                            ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                            : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30'
                        }`}
                >
                    {status === 'loading' || status === 'streaming' ? (
                        <>
                            <RefreshCw size={16} className="animate-spin" />
                            分析中...
                        </>
                    ) : (
                        <>
                            <Bot size={16} />
                            开始挖掘
                        </>
                    )}
                </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto min-h-[300px] bg-slate-900/50 rounded-xl border border-slate-700/50 p-4">
                {status === 'idle' && !content ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-3">
                        <Bot size={48} className="opacity-20" />
                        <p className="text-sm">点击上方按钮，AI 将为您：</p>
                        <ul className="text-xs space-y-2 text-slate-400">
                            <li className="flex items-center gap-2"><ChevronRight size={12} /> 分析热门板块轮动逻辑</li>
                            <li className="flex items-center gap-2"><ChevronRight size={12} /> 识别潜在的资金避险方向</li>
                            <li className="flex items-center gap-2"><ChevronRight size={12} /> 推荐值得关注的细分领域</li>
                        </ul>
                    </div>
                ) : (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                        {status === 'streaming' && (
                            <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse align-middle"></span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MarketOutlookCard;
