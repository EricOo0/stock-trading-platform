import React, { useEffect, useState } from 'react';
import { macroAPI } from '../services/macroAPI';
import type { MacroDataPoint } from '../services/macroAPI';
import { ArrowUp, ArrowDown, Activity, Globe } from 'lucide-react';
import { ChartComponent } from '../components/ChartComponent';
import { FedWatchTable } from '../components/FedWatchTable';

interface IndicatorConfig {
    id: string;
    name: string;
    region: 'US' | 'CN' | 'Global';
    category: 'Growth' | 'Inflation' | 'Employment' | 'Monetary' | 'Market';
    unit?: string;
}

interface IndicatorData extends IndicatorConfig {
    unit: string;
    history: MacroDataPoint[];
    latest?: MacroDataPoint;
}

const INDICATORS_CONFIG: IndicatorConfig[] = [
    { id: 'GDP', name: 'US GDP', region: 'US', category: 'Growth' },
    { id: 'CPI', name: 'US CPI', region: 'US', category: 'Inflation' },
    { id: 'UNEMPLOYMENT_RATE', name: 'US Unemployment', region: 'US', category: 'Employment' },
    { id: 'NONFARM_PAYROLLS', name: 'Non-Farm Payrolls', region: 'US', category: 'Employment' },
    { id: 'FED_FUNDS_RATE', name: 'Fed Funds Rate', region: 'US', category: 'Monetary' },
    { id: 'FED_FUNDS_FUTURES', name: 'Implied Fed Rate (Calculated)', region: 'US', category: 'Monetary' },
    { id: 'US10Y', name: 'US 10Y Yield', region: 'US', category: 'Market' },
    { id: 'VIX', name: 'VIX Index', region: 'Global', category: 'Market' },
    { id: 'GDP', name: 'China GDP', region: 'CN', category: 'Growth' }, // Note: ID conflict handling needed in API or here
    { id: 'CPI', name: 'China CPI', region: 'CN', category: 'Inflation' },
];

const normalizeDate = (dateStr: string): string | null => {
    // Standard YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;

    // 2025年10月份 -> 2025-10-01
    const monthMatch = dateStr.match(/^(\d{4})年(\d{1,2})月份$/);
    if (monthMatch) {
        const year = monthMatch[1];
        const month = monthMatch[2].padStart(2, '0');
        return `${year}-${month}-01`;
    }

    // 2025年第1-3季度 -> 2025-09-30 (End of Q3)
    // 2025年第3季度 -> 2025-09-30
    const quarterMatch = dateStr.match(/^(\d{4})年第(\d)(?:-(\d))?季度$/);
    if (quarterMatch) {
        const year = parseInt(quarterMatch[1]);
        const startQ = parseInt(quarterMatch[2]);
        const endQ = quarterMatch[3] ? parseInt(quarterMatch[3]) : startQ;
        
        // Map quarter end month: Q1->3, Q2->6, Q3->9, Q4->12
        const monthIdx = endQ * 3; // 1-based month index
        // Get last day of that month
        const lastDayDate = new Date(year, monthIdx, 0);
        const monthStr = monthIdx.toString().padStart(2, '0');
        const dayStr = lastDayDate.getDate().toString().padStart(2, '0');
        return `${year}-${monthStr}-${dayStr}`;
    }

    // Try basic parsing as fallback
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
         return d.toISOString().split('T')[0];
    }

    return null;
};

// Helper to map config to API calls
const fetchIndicator = async (config: IndicatorConfig) => {
    // For China data, we might need a different ID or handle it in the API
    // The API currently uses the same ID for US and China (e.g. GDP) but different services?
    // Wait, my MacroDataSkill.get_historical_data uses the indicator name to route.
    // FRED has 'GDP', AkShare has 'GDP'.
    // I need to disambiguate in the API or Skill.
    // In MacroDataSkill.get_historical_data:
    // if indicator in FRED -> FRED
    // if indicator in Yahoo -> Yahoo
    // if indicator in ['GDP', 'CPI', 'PMI'] -> AkShare
    // This is ambiguous! 'GDP' is in both FRED and AkShare (conceptually).
    // But FRED keys are 'GDP', 'CPI'. AkShare keys are 'GDP', 'CPI'.
    // The current implementation checks FRED first. So 'GDP' will go to FRED.
    // I need to fix this in the Skill or use distinct names like 'CN_GDP'.

    let apiId = config.id;
    if (config.region === 'CN') {
        // I need to update the skill to accept CN_GDP etc. or pass a region.
        // For now, let's assume I'll fix the skill to handle 'CN_GDP'.
        apiId = `CN_${config.id}`;
    }

    try {
        const data = await macroAPI.getHistoricalData(apiId);

        // Special handling for Fed Funds Futures to convert price to rate
        let history = data.data;
        let unit = data.units || config.unit || '';

        // Normalize dates
        history = history.map((item: MacroDataPoint) => {
            const normalized = normalizeDate(item.date);
            return normalized ? { ...item, date: normalized } : null;
        }).filter((item: MacroDataPoint | null): item is MacroDataPoint => item !== null);

        if (config.id === 'FED_FUNDS_FUTURES') {
            history = history.map((item: MacroDataPoint) => ({
                ...item,
                value: 100 - item.value // Convert price to implied rate
            }));
            unit = '%';
        }

        return {
            ...config,
            history: history,
            latest: history[history.length - 1],
            unit: unit
        };
    } catch (e) {
        console.error(`Failed to fetch ${config.name}`, e);
        return null;
    }
};

const MacroDataPage: React.FC = () => {
    const [indicators, setIndicators] = useState<IndicatorData[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIndicator, setSelectedIndicator] = useState<IndicatorData | null>(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            // We need to fix the ambiguity in the backend first.
            // For now, I will implement the frontend assuming 'CN_GDP' works.

            const promises = INDICATORS_CONFIG.map(cfg => fetchIndicator(cfg));
            const results = await Promise.all(promises);
            const validResults = results.filter(r => r !== null) as IndicatorData[];

            setIndicators(validResults);
            if (validResults.length > 0) {
                setSelectedIndicator(validResults[0]);
            }
            setLoading(false);
        };

        loadData();
    }, []);

    if (loading) {
        return (
            <div className="h-full flex flex-col bg-slate-900 text-white p-6 overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-slate-800 animate-pulse" />
                        <div className="w-48 h-8 bg-slate-800 rounded animate-pulse" />
                    </div>
                </div>

                <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)] overflow-hidden">
                    {/* Table Skeleton */}
                    <div className="col-span-5 bg-slate-800 rounded-xl border border-slate-700 flex flex-col overflow-hidden">
                        <div className="p-3 border-b border-slate-700/50 bg-slate-900/50 flex justify-between">
                            <div className="w-20 h-4 bg-slate-700/50 rounded animate-pulse" />
                            <div className="w-16 h-4 bg-slate-700/50 rounded animate-pulse" />
                        </div>
                        <div className="p-2 space-y-2">
                            {[...Array(10)].map((_, i) => (
                                <div key={i} className="flex justify-between items-center p-2">
                                    <div className="space-y-2">
                                        <div className="w-32 h-4 bg-slate-700/50 rounded animate-pulse" />
                                        <div className="w-20 h-3 bg-slate-700/30 rounded animate-pulse" />
                                    </div>
                                    <div className="space-y-2 flex flex-col items-end">
                                        <div className="w-24 h-4 bg-slate-700/50 rounded animate-pulse" />
                                        <div className="w-16 h-3 bg-slate-700/30 rounded animate-pulse" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Chart Skeleton */}
                    <div className="col-span-7 flex flex-col gap-6 overflow-hidden">
                        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex-1 flex flex-col">
                            <div className="mb-6 space-y-3">
                                <div className="w-48 h-6 bg-slate-700/50 rounded animate-pulse" />
                                <div className="w-64 h-4 bg-slate-700/30 rounded animate-pulse" />
                            </div>
                            <div className="flex-1 bg-slate-900/50 rounded-lg border border-slate-700/50 animate-pulse" />
                        </div>

                        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 h-1/3 shrink-0">
                            <div className="w-40 h-6 bg-slate-700/50 rounded animate-pulse mb-4" />
                            <div className="w-full h-4 bg-slate-700/30 rounded animate-pulse" />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Helper to get current Fed Funds Rate
    const currentFedRate = indicators.find(i => i.id === 'FED_FUNDS_RATE')?.latest?.value || 0;

    return (
        <div className="h-full flex flex-col bg-slate-900 text-white p-6 overflow-hidden">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Globe className="text-blue-500" />
                    Macroeconomic Data
                </h1>
            </div>

            <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)] overflow-hidden">
                {/* Table List */}
                <div className="col-span-5 bg-slate-800 rounded-xl border border-slate-700 flex flex-col overflow-hidden">
                    <div className="overflow-y-auto flex-1">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-900/50 sticky top-0">
                                <tr>
                                    <th className="p-3 text-left text-slate-400 font-medium">Indicator</th>
                                    <th className="p-3 text-right text-slate-400 font-medium">Latest</th>
                                    <th className="p-3 text-right text-slate-400 font-medium">Trend</th>
                                </tr>
                            </thead>
                            <tbody>
                                {indicators.map((item) => (
                                    <tr
                                        key={`${item.region}-${item.id}`}
                                        onClick={() => setSelectedIndicator(item)}
                                        className={`
                    cursor-pointer border-b border-slate-700/50 hover:bg-slate-700/50 transition-colors
                    ${selectedIndicator === item ? 'bg-slate-700/50' : ''}
                  `}
                                    >
                                        <td className="p-3">
                                            <div className="font-medium text-slate-200">{item.name}</div>
                                            <div className="text-xs text-slate-500">{item.region} • {item.category}</div>
                                        </td>
                                        <td className="p-3 text-right font-mono">
                                            {item.latest?.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            <span className="text-xs text-slate-500 ml-1">{item.unit}</span>
                                        </td>
                                        <td className="p-3 text-right">
                                            {/* Simple trend logic */}
                                            {item.history.length > 1 && (
                                                (() => {
                                                    const curr = item.latest?.value || 0;
                                                    const prev = item.history[item.history.length - 2].value;
                                                    const diff = curr - prev;
                                                    const color = diff > 0 ? 'text-red-500' : diff < 0 ? 'text-green-500' : 'text-slate-400';
                                                    // Note: Red is up, Green is down (CN style) or Green up Red down (US style)?
                                                    // Let's use standard colors: Red = Up, Green = Down (CN Market Style as requested by user implied by context)
                                                    return (
                                                        <div className={`flex items-center justify-end gap-1 ${color}`}>
                                                            {diff > 0 ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
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

                {/* Chart View */}
                <div className="col-span-7 flex flex-col gap-6 overflow-hidden">
                    {selectedIndicator && (
                        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex-1 flex flex-col min-h-0 overflow-y-auto">
                            <div className="mb-4 shrink-0">
                                <h2 className="text-xl font-bold text-white">{selectedIndicator.name}</h2>
                                <p className="text-slate-400 text-sm">
                                    Latest: {selectedIndicator.latest?.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {selectedIndicator.unit}
                                    <span className="mx-2">•</span>
                                    Date: {selectedIndicator.latest?.date}
                                </p>
                                {selectedIndicator.id === 'FED_FUNDS_FUTURES' && (
                                    <>
                                        <p className="text-xs text-slate-500 mt-1 mb-2">
                                            * Derived from 30-Day Fed Funds Futures (ZQ). Represents market's implied effective rate.
                                            For official probabilities, visit CME FedWatch Tool.
                                        </p>
                                        <FedWatchTable
                                            currentRate={currentFedRate}
                                            impliedRate={selectedIndicator.latest?.value || 0}
                                        />
                                    </>
                                )}
                            </div>

                            <div className="flex-1 min-h-[300px] bg-slate-900/50 rounded-lg border border-slate-700/50 p-4">
                                <ChartComponent data={selectedIndicator.history} />
                            </div>
                        </div>
                    )}

                    {/* Market Correlation */}
                    <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 h-1/3 shrink-0">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Activity size={18} className="text-emerald-500" />
                            Market Correlation
                        </h3>
                        <p className="text-slate-400 text-sm">
                            Select an indicator to see its correlation with major market indices.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MacroDataPage;
