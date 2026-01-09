import React, { useState, useEffect, useRef } from 'react';
import { Search, AlertCircle, Bot, ChevronDown, ChevronUp, Loader } from 'lucide-react';
import StockChart, { type StockData } from '../components/TechnicalAnalysis/StockChart';
import AnalysisPanel from '../components/TechnicalAnalysis/AnalysisPanel';
import IndicatorSelector from '../components/TechnicalAnalysis/IndicatorSelector';

const TechnicalAnalysisPage: React.FC = () => {
    const [symbol, setSymbol] = useState('');
    const [loading, setLoading] = useState(false);
    const [mode, setMode] = useState<'ANALYSIS' | 'REVIEW'>('ANALYSIS');
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<StockData[]>([]);
    const [period, setPeriod] = useState('1y');

    // AI Analysis State
    const [analyzing, setAnalyzing] = useState(false);
    const [aiSignal, setAiSignal] = useState<'BULLISH' | 'BEARISH' | 'NEUTRAL' | null>(null);
    const [aiSummary, setAiSummary] = useState<string>('');
    const [aiReasoning, setAiReasoning] = useState<string>('');
    const [aiContextExpanded, setAiContextExpanded] = useState(false);

    // 指标状态
    const [mainIndicator, setMainIndicator] = useState<'MA' | 'BOLL' | 'NONE'>('MA');
    const [subIndicator, setSubIndicator] = useState<'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE'>('VOL');

    const reasoningEndRef = useRef<HTMLDivElement>(null);

    const fetchAbortControllerRef = useRef<AbortController | null>(null);
    const aiAbortControllerRef = useRef<AbortController | null>(null);

    const fetchData = async () => {
        if (!symbol) return;

        // Cancel previous request
        if (fetchAbortControllerRef.current) {
            fetchAbortControllerRef.current.abort();
        }
        fetchAbortControllerRef.current = new AbortController();
        const signal = fetchAbortControllerRef.current.signal;

        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`http://localhost:8000/api/market/technical/${symbol}?period=${period}`, { signal });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const result = await response.json();
            if (result.status === 'success') {
                setData(result.data);
                // Trigger AI Analysis after data load
                fetchAIAnalysis();
            } else {
                setError(result.message || '获取数据失败');
            }
        } catch (err) {
            if (err instanceof Error && err.name === 'AbortError') {
                console.log('Fetch aborted');
                return;
            }
            const errorMessage = err instanceof Error ? err.message : '网络请求失败';
            console.error('Technical data fetch error:', err);
            setError(errorMessage);
        } finally {
            if (!signal.aborted) {
                setLoading(false);
            }
        }
    };

    const fetchAIAnalysis = async () => {
        // Cancel previous AI request
        if (aiAbortControllerRef.current) {
            aiAbortControllerRef.current.abort();
        }
        aiAbortControllerRef.current = new AbortController();
        const signal = aiAbortControllerRef.current.signal;

        setAnalyzing(true);
        setAiSignal(null);
        setAiSummary('');
        setAiReasoning('');

        try {
            const endpoint = mode === 'REVIEW' ? '/api/agent/review/analyze' : '/api/agent/technical/analyze';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    session_id: `${mode.toLowerCase()}-${Date.now()}`,
                    user_id: "user" // Add user_id for Review Agent
                }),
                signal
            });

            if (!response.body) return;
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let hasReceivedThoughts = false;
            let fullResponseText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                if (signal.aborted) break;

                buffer += decoder.decode(value, { stream: true });

                // Fix concatenated JSON objects if newline is missing
                // This is a robust fix for when the stream chunks arrive fused
                buffer = buffer.replace(/}{"type"/g, '}\n{"type"');

                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);

                        if (event.type === 'thought') {
                            hasReceivedThoughts = true;
                            setAiReasoning(prev => prev + event.content);
                            if (reasoningEndRef.current) {
                                reasoningEndRef.current.scrollIntoView({ behavior: 'smooth' });
                            }
                        }
                        else if (event.type === 'agent_response') {
                            // Accumulate the final answer text
                            fullResponseText += event.content;
                            // Optionally display it as it arrives if we haven't switched to summary yet
                            if (!hasReceivedThoughts) {
                                setAiReasoning(prev => prev + event.content);
                            }
                        }
                    } catch (e) {
                        // ignore partial line parse errors
                    }
                }
            }

            // Stream complete, try to parse the final JSON from fullResponseText
            if (fullResponseText) {
                try {
                    // Extract JSON block: find first '{' and last '}'
                    const firstOpen = fullResponseText.indexOf('{');
                    const lastClose = fullResponseText.lastIndexOf('}');

                    if (firstOpen !== -1 && lastClose !== -1 && lastClose > firstOpen) {
                        const jsonStr = fullResponseText.substring(firstOpen, lastClose + 1);
                        const result = JSON.parse(jsonStr);

                        setAiSignal(result.signal);
                        setAiSummary(result.summary);
                        // If we didn't receive thought stream, ensure the reasoning is set to the structured analysis
                        if (!hasReceivedThoughts) {
                            setAiReasoning(result.analysis);
                        }
                    } else {
                        // If no JSON found, just show the text
                        setAiSummary("Analysis Completed (Unstructured)");
                        if (!hasReceivedThoughts) setAiReasoning(fullResponseText);
                    }
                } catch (e) {
                    console.warn("Failed to parse final accumulated JSON", e);
                    setAiSummary("Analysis Parsing Failed");
                }
            }
        } catch (e) {
            if (e instanceof Error && e.name === 'AbortError') {
                console.log('AI Analysis aborted');
                return;
            }
            console.error("AI Analysis failed", e);
        } finally {
            if (!signal.aborted) {
                setAnalyzing(false);
            }
        }
    };

    useEffect(() => {
        fetchData();
        return () => {
            if (fetchAbortControllerRef.current) fetchAbortControllerRef.current.abort();
            if (aiAbortControllerRef.current) aiAbortControllerRef.current.abort();
        };
    }, []);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        fetchData();
    };

    // Render Logic for AI Card
    const renderAICard = () => {
        if (!aiSignal && !analyzing && !aiReasoning) return null; // Nothing yet

        const getSignalColor = () => {
            if (aiSignal === 'BULLISH') return 'text-red-400 border-red-500/30 bg-red-500/10';
            if (aiSignal === 'BEARISH') return 'text-green-400 border-green-500/30 bg-green-500/10';
            return 'text-slate-300 border-slate-600/30 bg-slate-700/30';
        };

        return (
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden mb-6 shadow-lg transition-all">
                {/* Header / Summary */}
                <div
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-700/50 transition-colors"
                    onClick={() => setAiContextExpanded(!aiContextExpanded)}
                >
                    <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg ${analyzing ? 'animate-pulse bg-blue-500/20 text-blue-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                            {analyzing ? <Loader className="animate-spin" size={24} /> : <Bot size={24} />}
                        </div>

                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <h3 className="font-bold text-white text-lg">AI Technical Insight</h3>
                                {aiSignal && (
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getSignalColor()}`}>
                                        {aiSignal}
                                    </span>
                                )}
                            </div>
                            <p className="text-slate-400 text-sm">
                                {analyzing && !aiSummary ? "Analyzing market structure & indicators..." : (aiSummary || "Analysis ready.")}
                            </p>
                        </div>
                    </div>

                    <div className="text-slate-500">
                        {aiContextExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </div>
                </div>

                {/* Expanded Content: Reasoning */}
                {(aiContextExpanded || analyzing) && (
                    <div className="border-t border-slate-700 bg-slate-900/50 p-4">
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Detailed Reasoning</h4>
                        <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed font-mono text-xs whitespace-pre-wrap">
                            {aiReasoning}
                            <div ref={reasoningEndRef} />
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="h-full flex flex-col bg-slate-900 text-white overflow-hidden">
            <header className="flex-none p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">技术面分析 (Technical Analysis)</h1>
                    <p className="text-slate-400">AI-Enhanced Technical Research Platform</p>
                </div>

                <div className="flex flex-col gap-4 items-end">
                    <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700 w-fit">
                        <button
                            onClick={() => setMode('ANALYSIS')}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                                mode === 'ANALYSIS' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                            }`}
                        >
                            实时分析
                        </button>
                        <button
                            onClick={() => setMode('REVIEW')}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                                mode === 'REVIEW' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                            }`}
                        >
                            每日复盘
                        </button>
                    </div>

                    <div className="flex items-center gap-4">
                        <form onSubmit={handleSearch} className="flex gap-2">
                        <div className="relative">
                            <input
                                type="text"
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                placeholder="Symbol (e.g. AAPL)"
                                className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 pl-10 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64 transition-all"
                            />
                            <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
                        </div>
                        <button
                            type="submit"
                            disabled={loading || analyzing}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Fetching...' : 'Analyze'}
                        </button>
                    </form>

                    <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
                        {['6mo', '1y', '2y', '5y'].map((p) => (
                            <button
                                key={p}
                                onClick={() => { setPeriod(p); setTimeout(fetchData, 0); }}
                                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${period === p ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-white'
                                    }`}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                </div>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3 text-red-400 animate-in fade-in">
                        <AlertCircle size={20} />
                        <span>{error}</span>
                    </div>
                )}

                {loading && !data.length ? (
                    <div className="animate-pulse space-y-6">
                        {/* Skeletons */}
                        <div className="h-32 bg-slate-800 rounded-xl border border-slate-700"></div>
                        <div className="h-[500px] bg-slate-800 rounded-xl border border-slate-700"></div>
                    </div>
                ) : !symbol ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500">
                        <Search size={48} className="mb-4 opacity-50" />
                        <h2 className="text-xl font-medium mb-2">Enter a stock symbol to start {mode === 'REVIEW' ? 'Review' : 'Analysis'}</h2>
                        <p>Search for any US/HK/CN stock code (e.g. AAPL, 00700, 600519)</p>
                    </div>
                ) : (
                    <>
                        {/* AI Analysis Panel */}
                        {renderAICard()}

                        {/* Legacy Panels (Modified to be simpler perhaps, or kept as is) */}
                        <AnalysisPanel data={data} />

                        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                            <div className="lg:col-span-3 space-y-4">
                                <StockChart
                                    data={data}
                                    mainIndicator={mainIndicator}
                                    subIndicator={subIndicator}
                                />
                            </div>

                            <div className="lg:col-span-1">
                                <IndicatorSelector
                                    mainIndicator={mainIndicator}
                                    subIndicator={subIndicator}
                                    onMainChange={setMainIndicator}
                                    onSubChange={setSubIndicator}
                                />

                                <div className="mt-6 bg-slate-800 p-4 rounded-lg border border-slate-700">
                                    <h3 className="text-white font-medium mb-2">Indicator Guide</h3>
                                    <div className="space-y-2 text-sm text-slate-400">
                                        <p><span className="text-yellow-400">MA</span>: Moving Average</p>
                                        <p><span className="text-purple-400">BOLL</span>: Bollinger Bands</p>
                                        <p><span className="text-blue-400">MACD</span>: Momentum Convergence Divergence</p>
                                        <p><span className="text-green-400">RSI</span>: Relative Strength Index</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default TechnicalAnalysisPage;
