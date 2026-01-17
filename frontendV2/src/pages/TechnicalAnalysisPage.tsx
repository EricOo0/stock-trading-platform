import React, { useState, useEffect, useRef } from 'react';
import { Search, AlertCircle, Bot, Loader } from 'lucide-react';
// import StockChart, { type StockData } from '../components/TechnicalAnalysis/StockChart';
import TradingViewChart from '../components/TechnicalAnalysis/TradingViewChart';
import { type StockData } from '../types/stock';
import AnalysisPanel from '../components/TechnicalAnalysis/AnalysisPanel';
import IndicatorSelector from '../components/TechnicalAnalysis/IndicatorSelector';
import AITechnicalCard from '../components/TechnicalAnalysis/AITechnicalCard';


interface TechnicalAnalysisResult {
    signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | null;
    confidence: number;
    summary: string;
    reasoning: string;
    keyLevels?: { support: number[], resistance: number[] };
    riskFactors: string[];
}

interface TechnicalAnalysisProps {
    sharedSymbol?: string;
    searchTrigger?: number;
    isActive?: boolean;
}

const TechnicalAnalysisPage: React.FC<TechnicalAnalysisProps> = ({ sharedSymbol }) => {

    const [symbol, setSymbol] = useState<string>('');
    const [loading, setLoading] = useState(false);
    // const [mode, setMode] = useState<'ANALYSIS' | 'REVIEW'>('ANALYSIS'); // Removed Review mode
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<StockData[]>([]);
    const [period, setPeriod] = useState('1y');

    useEffect(() => {
        if (sharedSymbol) {
            setSymbol(sharedSymbol);
        }
    }, [sharedSymbol]);

    // AI Analysis State
    const [analyzing, setAnalyzing] = useState(false);

    // Separate Data States for Modes
    const [technicalData, setTechnicalData] = useState<TechnicalAnalysisResult | null>(null);
    // const [aiContextExpanded, setAiContextExpanded] = useState(false);


    // Legacy mapping for backwards compatibility in JSX (optional, or just update JSX)
    // We will update JSX to use technicalData directly.

    // 指标状态
    const [mainIndicator, setMainIndicator] = useState<'MA' | 'BOLL' | 'NONE'>('MA');
    const [subIndicator, setSubIndicator] = useState<'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE'>('VOL');

    const reasoningEndRef = useRef<HTMLDivElement>(null);

    const fetchAbortControllerRef = useRef<AbortController | null>(null);
    const aiAbortControllerRef = useRef<AbortController | null>(null);

    const fetchStockData = async () => {
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
                // fetchAIAnalysis(); // Removed: Manual trigger only per user request
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

        // Clear ONLY the current mode's data to indicate fresh start, or keep previous while loading?
        // Usually clearing is better to show "Thinking..." state correctly.
        // Clear ONLY the current mode's data to indicate fresh start, or keep previous while loading?
        // Usually clearing is better to show "Thinking..." state correctly.
        setTechnicalData(null);

        try {
            const endpoint = '/api/agent/technical/analyze';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    session_id: `analysis-${Date.now()}`
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
                            const content = event.content;
                            setTechnicalData(prev => ({
                                signal: prev?.signal || null,
                                confidence: prev?.confidence || 0,
                                summary: prev?.summary || '',
                                reasoning: (prev?.reasoning || '') + content,
                                keyLevels: prev?.keyLevels,
                                riskFactors: prev?.riskFactors || []
                            }));

                            if (reasoningEndRef.current) {
                                reasoningEndRef.current.scrollIntoView({ behavior: 'smooth' });
                            }
                        }
                        else if (event.type === 'agent_response') {
                            // Accumulate the final answer text
                            fullResponseText += event.content;
                            // Also stream to UI for visibility
                            if (!hasReceivedThoughts) {
                                const content = event.content;
                                setTechnicalData(prev => ({
                                    signal: prev?.signal || null,
                                    confidence: prev?.confidence || 0,
                                    summary: prev?.summary || '',
                                    reasoning: (prev?.reasoning || '') + content,
                                    keyLevels: prev?.keyLevels,
                                    riskFactors: prev?.riskFactors || []
                                }));
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

                        setTechnicalData({
                            signal: result.signal,
                            confidence: result.confidence || 0,
                            summary: result.summary,
                            reasoning: (!hasReceivedThoughts && result.analysis) ? result.analysis : (technicalData?.reasoning || ''),
                            keyLevels: result.key_levels,
                            riskFactors: result.risk_factors || []
                        });

                        // If we didn't receive thought stream, ensure the reasoning is set to the structured analysis
                        if (!hasReceivedThoughts && result.analysis) {
                            // Already handled in setTechnicalData above
                        }

                    } else {
                        // No JSON found
                        setTechnicalData(prev => ({
                            ...(prev as TechnicalAnalysisResult),
                            summary: "Analysis Completed (Unstructured)",
                            reasoning: fullResponseText
                        }));
                    }
                } catch (e) {
                    console.warn("Failed to parse final accumulated JSON", e);
                    setTechnicalData(prev => ({ ...(prev as TechnicalAnalysisResult), summary: "Analysis Parsing Failed" }));
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
        if (symbol) {
            fetchStockData();
        }
        return () => {
            if (fetchAbortControllerRef.current) fetchAbortControllerRef.current.abort();
            if (aiAbortControllerRef.current) aiAbortControllerRef.current.abort();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [symbol, period]);



    // Render Logic for AI Card
    // Replaced by AITechnicalCard component
    // const renderAICard = () => ... (removed)

    return (
        <div className="h-full flex flex-col bg-slate-900 text-white overflow-hidden">
            <header className="flex-none p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">技术面分析 (Technical Analysis)</h1>
                    <p className="text-slate-400">AI-Enhanced Technical Research Platform</p>
                </div>

                <div className="flex flex-col gap-4 items-end">
                    <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700 w-fit">
                        <div className="px-3 py-1.5 rounded-md text-sm font-medium bg-indigo-600 text-white shadow-lg">
                            实时分析
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-4">
                            {symbol ? (
                                <div className="px-4 py-2 bg-slate-800 rounded-lg text-slate-300 text-sm border border-slate-700 font-mono font-bold tracking-wider">
                                    {symbol}
                                </div>
                            ) : (
                                <div className="text-slate-500 text-sm italic">请在顶部输入代码</div>
                            )}

                            <button
                                onClick={() => fetchAIAnalysis()}
                                disabled={loading || analyzing || !symbol}
                                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                {loading ? <Loader className="animate-spin" size={16} /> : <Bot size={18} />}
                                {loading ? '获取数据中...' : '开始 AI 分析'}
                            </button>
                        </div>

                        <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
                            {['6mo', '1y', '2y', '5y'].map((p) => (
                                <button
                                    key={p}
                                    onClick={() => { setPeriod(p); setTimeout(fetchStockData, 0); }}
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
                        <h2 className="text-xl font-medium mb-2">Enter a stock symbol to start Analysis</h2>
                        <p>Search for any US/HK/CN stock code (e.g. AAPL, 00700, 600519)</p>
                    </div>
                ) : (
                    <>
                        {/* AI Analysis Panel */}
                        <AITechnicalCard
                            signal={technicalData?.signal || null}
                            confidence={technicalData?.confidence || 0}
                            summary={technicalData?.summary || ''}
                            reasoning={technicalData?.reasoning || ''}
                            keyLevels={technicalData?.keyLevels}
                            riskFactors={technicalData?.riskFactors}
                            analyzing={analyzing}
                        />

                        {/* Legacy Panels (Modified to be simpler perhaps, or kept as is) */}
                        <AnalysisPanel data={data} />

                        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                            <div className="lg:col-span-3 space-y-4">
                                <TradingViewChart
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
