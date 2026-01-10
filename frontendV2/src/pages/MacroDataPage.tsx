import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, BarChart, Bar, Cell, LabelList, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { ArrowUp, ArrowDown, Globe, BarChart2, DollarSign, Bot, Loader } from 'lucide-react';
import { macroAPI } from '../services/macroAPI';
import type { MacroDataPoint } from '../services/macroAPI';
import { ChartComponent } from '../components/ChartComponent';
import MacroIndicatorCard from '../components/Macro/MacroIndicatorCard';

interface IndicatorConfig {
    id: string; // ID sent to backend
    name: string;
    region: 'Global' | 'CN';
    category: string;
    unit: string;
}

interface IndicatorData extends IndicatorConfig {
    history: MacroDataPoint[];
    latest?: MacroDataPoint;
}

interface IndicatorData extends IndicatorConfig {
    history: MacroDataPoint[];
    latest?: MacroDataPoint;
}

const INDICATORS_CONFIG: IndicatorConfig[] = [
    // China
    { id: 'CN_GDP', name: 'China GDP', region: 'CN', category: 'Growth', unit: '100M CNY' },
    { id: 'CN_CPI', name: 'China CPI', region: 'CN', category: 'Inflation', unit: 'Index' },
    { id: 'CN_PMI', name: 'China PMI', region: 'CN', category: 'Activity', unit: 'Index' },
    { id: 'CN_PPI', name: 'China PPI', region: 'CN', category: 'Inflation', unit: '%' },
    { id: 'CN_M2', name: 'China M2', region: 'CN', category: 'Monetary', unit: '100M CNY' },
    { id: 'CN_LPR', name: 'China LPR (1Y)', region: 'CN', category: 'Monetary', unit: '%' },

    // Global (US)
    { id: 'US10Y', name: 'US 10Y Yield', region: 'Global', category: 'Rates', unit: '%' },
    { id: 'VIX', name: 'VIX Index', region: 'Global', category: 'Volatility', unit: 'Index' },
    { id: 'DXY', name: 'Dollar Index', region: 'Global', category: 'Currency', unit: 'Index' },
    { id: 'US_CPI', name: 'US CPI', region: 'Global', category: 'Inflation', unit: 'Index' },
    { id: 'UNEMPLOYMENT', name: 'US Unemployment', region: 'Global', category: 'Labor', unit: '%' },
    { id: 'NONFARM', name: 'Non-Farm Payrolls', region: 'Global', category: 'Labor', unit: 'k' },
    { id: 'FED_FUNDS', name: 'Fed Funds Rate', region: 'Global', category: 'Monetary', unit: '%' },
];

const normalizeDate = (dateStr: string): string => {
    // 简单处理日期格式，确保 charts 能正确排序
    if (!dateStr) return '';

    // Handle "2006-第1季度" or "2025年第1-3季度" -> Convert to end of quarter
    if (dateStr.includes('季度')) {
        const yearMatch = dateStr.match(/(\d{4})/);
        // Match the LAST digit before 季度. e.g. "第1-3季度" -> 3, "第1季度" -> 1
        const qMatch = dateStr.match(/第.*?(\d)季度/);

        if (yearMatch && qMatch) {
            const year = yearMatch[1];
            const q = parseInt(qMatch[1]);
            // End of quarter dates: Q1=03-31, Q2=06-30, Q3=09-30, Q4=12-31
            const month = (q * 3).toString().padStart(2, '0');
            const day = (q === 1 || q === 4) ? '31' : '30';
            return `${year}-${month}-${day}`;
        }
    }

    if (dateStr.includes('年')) {
        // 粗略处理中文日期，实际项目中可能需要更复杂的 parsing
        return dateStr.replace('年', '-').replace('月份', '-01').replace('月', '-01');
    }
    return dateStr;
};

const fetchIndicator = async (config: IndicatorConfig): Promise<IndicatorData | null> => {
    try {
        const rawData = await macroAPI.getHistoricalData(config.id);
        // console.log(`[MacroPage] Fetched ${config.id}`, rawData); 

        let historyList: MacroDataPoint[] = [];

        if (Array.isArray(rawData)) {
            // AkShare returns direct array
            historyList = rawData;
        } else if (rawData && typeof rawData === 'object' && Array.isArray(rawData.data)) {
            // Fred returns wrapper object { indicator, data: [...] }
            historyList = rawData.data;
        } else {
            console.error(`[MacroPage] Invalid data format for ${config.id}`, rawData);
            return null;
        }

        const history = historyList.map((item: MacroDataPoint) => ({
            ...item,
            date: normalizeDate(item.date)
        })).sort((a: MacroDataPoint, b: MacroDataPoint) => new Date(a.date).getTime() - new Date(b.date).getTime());

        return {
            ...config,
            history,
            latest: history[history.length - 1],
        };
    } catch (e) {
        console.error(`[MacroPage] Failed to fetch/process ${config.name} (${config.id})`, e);
        return null; // Return null on failure to filter out later
    }
};

const MacroDataPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'CN' | 'Global'>('CN');
    const [indicators, setIndicators] = useState<IndicatorData[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIndicator, setSelectedIndicator] = useState<IndicatorData | null>(null);
    const [fedProbData, setFedProbData] = useState<any>(null);

    // AI Analysis State
    const [analyzing, setAnalyzing] = useState(false);
    const [macroData, setMacroData] = useState<{
        macroHealthScore?: number;
        macroHealthLabel?: string;
        keyMetrics?: Array<{ name: string; value: string; trend: 'UP' | 'NEUTRAL' | 'DOWN' }>;
        signal?: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | null;
        confidence?: number;
        marketCycle?: string;
        marketImplication?: string;
        riskWarning?: string;
        strategy?: string;
        summary?: string;
        analysis?: string;
        keyFactors?: { positive: string[]; negative: string[] };
    }>({});

    // const reasoningEndRef = React.useRef<HTMLDivElement>(null);  // Removed, unused
    const aiAbortControllerRef = React.useRef<AbortController | null>(null);

    const fetchAIAnalysis = async () => {
        if (aiAbortControllerRef.current) aiAbortControllerRef.current.abort();
        aiAbortControllerRef.current = new AbortController();
        const signal = aiAbortControllerRef.current.signal;

        setAnalyzing(true);
        setMacroData({});

        try {
            const response = await fetch('/api/agent/macro/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: `macro-${Date.now()}` }),
                signal
            });

            if (!response.body) return;
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                if (signal.aborted) break;

                buffer += decoder.decode(value, { stream: true });
                // console.log("Buffer update:", buffer.length);
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    // console.log("Processing line:", line);
                    try {
                        const event = JSON.parse(line);
                        // console.log("Parsed event:", event);
                        if (event.type === 'agent_response') {
                            const newContent = event.content;
                            fullText += newContent;
                            // Do not display raw JSON stream
                            // Only display if we detect it's NOT JSON (unlikely with current prompt) 
                            // or if we implement a stream parser later.
                        } else if (event.type === 'error') {
                            console.error("Agent returned error:", event.content);
                            setMacroData(prev => ({ ...prev, analysis: (prev.analysis || '') + `\n[Error: ${event.content}]` }));
                        }
                    } catch (e) { }
                }
            }

            // Final Parsing to extract structured data if available
            try {
                // Remove markdown code blocks if present
                let cleanText = fullText.replace(/```json/g, '').replace(/```/g, '').trim();

                // Find JSON block
                const jsonMatch = cleanText.match(/\{[\s\S]*\}/);
                const jsonStr = jsonMatch ? jsonMatch[0] : cleanText;

                const result = JSON.parse(jsonStr);
                console.log("[MacroPage] Parsed AI result:", result);

                setMacroData({
                    macroHealthScore: result.macro_health_score ?? 50,
                    macroHealthLabel: result.macro_health_label || '中性',
                    keyMetrics: result.key_metrics || [],
                    signal: result.signal || null,
                    confidence: result.confidence ?? 0,
                    marketCycle: result.market_cycle || '',
                    marketImplication: result.market_implication || result.summary || '分析已完成',
                    riskWarning: result.risk_warning || '',
                    strategy: result.strategy || '',
                    summary: result.summary || '',
                    analysis: result.analysis || '',
                    keyFactors: result.key_factors || { positive: [], negative: [] }
                });
            } catch (e) {
                console.warn("Macro JSON parse failed:", e, "fullText:", fullText.slice(0, 500));
                // Fallback: use raw text as analysis
                setMacroData(prev => ({
                    ...prev,
                    macroHealthScore: 50,
                    macroHealthLabel: '分析完成',
                    marketImplication: '请查看详细分析',
                    analysis: fullText
                }));
            }

        } catch (e) {
            if (e instanceof Error && e.name === 'AbortError') return;
            console.error(e);
            setMacroData(prev => ({ ...prev, analysis: prev.analysis + "\n[Analysis interrupted or failed]" }));
        } finally {
            if (!signal.aborted) setAnalyzing(false);
        }
    };



    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            const promises = INDICATORS_CONFIG.map(cfg => fetchIndicator(cfg));

            // Fetch Fed Probability parallel
            const fedProbPromise = macroAPI.getFedImpliedProbability();

            const [results, fedProb] = await Promise.all([
                Promise.all(promises),
                fedProbPromise
            ]);

            const validResults = results.filter((r): r is IndicatorData => r !== null);
            setIndicators(validResults);

            if (fedProb) {
                setFedProbData(fedProb);
            }

            // Set default selected indicator based on active tab
            const defaultForTab = validResults.find(r => r.region === activeTab);
            if (defaultForTab) setSelectedIndicator(defaultForTab);

            setLoading(false);

            // AI Analysis is now manual - no auto-trigger
            // fetchAIAnalysis();
        };
        loadData();

        return () => {
            if (aiAbortControllerRef.current) aiAbortControllerRef.current.abort();
        };
    }, []); // Run once on mount

    // Filter indicators for current tab
    const currentIndicators = indicators.filter(i => i.region === activeTab);

    // Auto-select first indicator when switching tabs if current selection is not in new tab
    useEffect(() => {
        if (selectedIndicator && selectedIndicator.region !== activeTab) {
            const firstInTab = currentIndicators[0];
            if (firstInTab) setSelectedIndicator(firstInTab);
        } else if (!selectedIndicator && currentIndicators.length > 0) {
            setSelectedIndicator(currentIndicators[0]);
        }
    }, [activeTab, indicators]);


    if (loading) {
        return <div className="p-10 text-center text-slate-400">Loading Macro Data...</div>;
    }

    return (
        <div className="h-full flex flex-col bg-slate-900 text-white p-6 overflow-hidden">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Globe className="text-blue-500" />
                    Macroeconomic Data
                </h1>

                {/* Tabs */}
                <div className="flex gap-2 bg-slate-800 p-1 rounded-lg">
                    {(['CN', 'Global'] as const).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === tab
                                ? 'bg-blue-600 text-white shadow'
                                : 'text-slate-400 hover:text-white hover:bg-slate-700'
                                }`}
                        >
                            {tab === 'CN' ? 'China Domestic' : 'Global Market'}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex flex-col gap-6 h-[calc(100vh-140px)] overflow-y-auto">

                {/* AI Analysis Section */}
                <div className="flex items-start gap-4 shrink-0">
                    {/* AI Trigger Button */}
                    <button
                        onClick={fetchAIAnalysis}
                        disabled={analyzing}
                        className={`flex items-center gap-2 px-5 py-3 rounded-xl font-medium transition-all shrink-0 ${analyzing
                            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 shadow-lg hover:shadow-cyan-500/25'
                            }`}
                    >
                        {analyzing ? (
                            <Loader className="animate-spin" size={18} />
                        ) : (
                            <Bot size={18} />
                        )}
                        {analyzing ? '分析中...' : '开始 AI 分析'}
                    </button>

                    {/* AI Analysis Card */}
                    <div className="flex-1">
                        <MacroIndicatorCard
                            macroHealthScore={macroData.macroHealthScore}
                            macroHealthLabel={macroData.macroHealthLabel}
                            keyMetrics={macroData.keyMetrics}
                            signal={macroData.signal}
                            confidence={macroData.confidence}
                            marketCycle={macroData.marketCycle}
                            marketImplication={macroData.marketImplication}
                            riskWarning={macroData.riskWarning}
                            strategy={macroData.strategy}
                            summary={macroData.summary}
                            analysis={macroData.analysis}
                            keyFactors={macroData.keyFactors}
                            analyzing={analyzing}
                        />
                    </div>
                </div>

                {/* Top Section: Data Table & Fed Watch (Global Only) */}
                <div className="min-h-[280px] flex gap-6 shrink-0">
                    {/* Data Table */}
                    <div className={`bg-slate-800 rounded-xl border border-slate-700 flex flex-col overflow-hidden ${activeTab === 'Global' ? 'w-2/3' : 'w-full'}`}>
                        <div className="overflow-y-auto flex-1">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-900/50 sticky top-0 backdrop-blur-sm z-10">
                                    <tr>
                                        <th className="p-3 text-left text-slate-400 font-medium">Indicator</th>
                                        <th className="p-3 text-left text-slate-400 font-medium">Category</th>
                                        <th className="p-3 text-right text-slate-400 font-medium">Latest Value</th>
                                        <th className="p-3 text-right text-slate-400 font-medium">Date</th>
                                        <th className="p-3 text-right text-slate-400 font-medium">Trend</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentIndicators.map((item) => (
                                        <tr
                                            key={item.id}
                                            onClick={() => setSelectedIndicator(item)}
                                            className={`
                                            cursor-pointer border-b border-slate-700/50 hover:bg-slate-700/50 transition-colors
                                            ${selectedIndicator?.id === item.id ? 'bg-blue-500/10 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'}
                                        `}
                                        >
                                            <td className="p-3 font-medium text-slate-200">{item.name}</td>
                                            <td className="p-3 text-slate-500">{item.category}</td>
                                            <td className="p-3 text-right font-mono font-bold text-slate-200">
                                                {item.latest?.value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                <span className="text-xs text-slate-500 ml-1">{item.unit}</span>
                                            </td>
                                            <td className="p-3 text-right text-slate-500 tabular-nums">
                                                {item.latest?.date}
                                            </td>
                                            <td className="p-3 text-right">
                                                {item.history.length > 1 && (
                                                    (() => {
                                                        const curr = item.latest?.value || 0;
                                                        const prev = item.history[item.history.length - 2].value;
                                                        const diff = curr - prev;
                                                        const color = diff > 0 ? 'text-red-400' : diff < 0 ? 'text-green-400' : 'text-slate-400';
                                                        return (
                                                            <div className={`flex items-center justify-end gap-1 ${color}`}>
                                                                {diff > 0 ? <ArrowUp size={14} /> : diff < 0 ? <ArrowDown size={14} /> : null}
                                                                {Math.abs(diff).toFixed(2)}
                                                            </div>
                                                        );
                                                    })()
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Fed Watch Card - Only for Global Tab */}
                    {activeTab === 'Global' && fedProbData && (
                        <div className="w-1/3 bg-slate-800 rounded-xl border border-slate-700 p-4 flex flex-col">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                    <DollarSign size={18} className="text-green-400" />
                                    Fed Watch
                                </h3>
                                <div className="text-xs text-slate-400">
                                    Implied: <span className="text-white font-mono">{fedProbData.implied_rate}%</span>
                                </div>
                            </div>

                            <div className="flex-1 min-h-0">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={fedProbData.data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} vertical={false} />
                                        <XAxis dataKey="bin" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                                        <YAxis hide />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                            cursor={{ fill: '#334155', opacity: 0.2 }}
                                        />
                                        <Bar dataKey="prob" radius={[4, 4, 0, 0]}>
                                            {fedProbData.data.map((entry: any, index: number) => (
                                                <Cell key={`cell-${index}`} fill={entry.is_current ? '#3b82f6' : '#64748b'} />
                                            ))}
                                            <LabelList dataKey="prob" position="top" formatter={(val: any) => `${val}%`} fill="#e2e8f0" fontSize={12} />
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="mt-2 text-center text-xs text-slate-500">
                                Current Target: {fedProbData.current_target_rate}%
                            </div>
                        </div>
                    )}
                </div>

                {/* Bottom Section: Chart */}
                <div className="min-h-[400px] bg-slate-800 rounded-xl border border-slate-700 p-6 flex flex-col shrink-0">
                    {selectedIndicator ? (
                        <>
                            <div className="mb-4 flex items-center gap-3">
                                <div className="p-2 bg-slate-700 rounded-lg">
                                    <BarChart2 size={20} className="text-blue-400" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">{selectedIndicator.name} Trend</h2>
                                    <p className="text-xs text-slate-400">Historical data analysis over the past year</p>
                                </div>
                            </div>

                            <div className="flex-1 min-h-0">
                                <ChartComponent data={selectedIndicator.history} />
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-slate-500">
                            Select an indicator to view trend
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default MacroDataPage;
