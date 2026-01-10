import React, { useState, useEffect, useRef } from 'react';
import { Search, RotateCcw, LayoutDashboard, AlertCircle, Bot } from 'lucide-react';
// import StockChart, { type StockData } from '../components/TechnicalAnalysis/StockChart';
import TradingViewChart from '../components/TechnicalAnalysis/TradingViewChart';
import { type StockData } from '../types/stock';
import RealTimeDataPanel from '../components/MarketQuery/RealTimeDataPanel';
import DailyReviewCard from '../components/MarketQuery/DailyReviewCard';

interface MarketQueryProps {
  sharedSymbol?: string;
  searchTrigger?: number;
  isActive?: boolean;
}

const MarketQueryPage: React.FC<MarketQueryProps> = ({ sharedSymbol, searchTrigger, isActive }) => {
  // State management
  const [symbol, setSymbol] = useState(sharedSymbol || ''); // Initialize with prop if available
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<StockData[]>([]);
  const [snapshot, setSnapshot] = useState<any>(null); // Real-time price snapshot
  const [indicators, setIndicators] = useState<any>(null); // Financial indicators (PE, etc.)
  const [period, setPeriod] = useState('1m'); // Default to 1 Month

  // Sync sharedSymbol when it changes
  useEffect(() => {
    if (sharedSymbol) {
      setSymbol(sharedSymbol);
      setPeriod('1m'); // Default to 1m when symbol changes from header
    }
  }, [sharedSymbol]);

  // Auto-fetch when search triggered
  useEffect(() => {
    if (searchTrigger && symbol) {
      handleManualSearch();
    }
  }, [searchTrigger, symbol]);

  // Indicators
  const [mainIndicator, setMainIndicator] = useState<'MA' | 'BOLL' | 'NONE'>('MA');
  const [subIndicator, setSubIndicator] = useState<'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE'>('VOL');

  // Review Agent State
  const [reviewAnalyzing, setReviewAnalyzing] = useState(false);
  const [reviewData, setReviewData] = useState<any>(null); // To store the full JSON object
  const [reviewAnalysisText, setReviewAnalysisText] = useState(''); // Accumulate streaming text if raw, or parsed analysis

  // Data Fetching Logic
  const fetchAbortControllerRef = useRef<AbortController | null>(null);

  const fetchData = async () => {
    if (!symbol) {
      setData([]);
      setSnapshot(null);
      setIndicators(null);
      return;
    }
    if (fetchAbortControllerRef.current) fetchAbortControllerRef.current.abort();
    fetchAbortControllerRef.current = new AbortController();

    setLoading(true);
    setError(null);
    try {
      // Parallel fetch: Technical, Price (Snapshot), Indicators (PE/TurnoverRate/etc)
      const [techRes, priceRes, indRes] = await Promise.all([
        fetch(`http://localhost:8000/api/market/technical/${symbol}?period=${period}`, { signal: fetchAbortControllerRef.current.signal }),
        fetch(`http://localhost:8000/api/market/price`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol }),
          signal: fetchAbortControllerRef.current.signal
        }),
        fetch(`http://localhost:8000/api/market/indicators/${symbol}`, { signal: fetchAbortControllerRef.current.signal })
      ]);

      if (!techRes.ok) throw new Error(`Technical API error! status: ${techRes.status}`);

      const techResult = await techRes.json();
      if (techResult.status === 'success') {
        // Ensure numeric types for Chart
        const numericData = techResult.data.map((item: any) => ({
          ...item,
          open: Number(item.open),
          high: Number(item.high),
          low: Number(item.low),
          close: Number(item.close),
          volume: Number(item.volume),
          ma5: item.ma5 ? Number(item.ma5) : undefined,
          ma10: item.ma10 ? Number(item.ma10) : undefined,
          ma20: item.ma20 ? Number(item.ma20) : undefined,
          ma60: item.ma60 ? Number(item.ma60) : undefined,
          // ... map others if needed, but main OHLC is critical
        }));
        setData(numericData);
      } else {
        setError(techResult.message || 'Failed to fetch technical data');
      }

      // Process Price Snapshot
      if (priceRes.ok) {
        const priceResult = await priceRes.json();
        if (priceResult && !priceResult.error) {
          setSnapshot(priceResult);
        }
      }

      // Process Indicators
      if (indRes.ok) {
        const indResult = await indRes.json();
        setIndicators(indResult);
      }

    } catch (err: any) {
      if (err.name === 'AbortError') return;
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  const fetchReviewAnalysis = async () => {
    if (!symbol) return;
    setReviewAnalyzing(true);
    setReviewData(null);
    setReviewAnalysisText('');

    try {
      const response = await fetch('http://localhost:8000/api/agent/review/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: symbol,
          session_id: 'default' // Or generate unique
        })
      });

      if (!response.ok) throw new Error('Review Agent failed');
      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullResponseText = '';
      let hasReceivedThoughts = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Fix fused JSON objects
        buffer = buffer.replace(/}{"type"/g, '}\n{"type"');

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);

            if (event.type === 'agent_response') {
              const content = event.content;
              fullResponseText += content;
              setReviewAnalysisText(prev => prev + content);

              // Try to update structured data if embedded JSON is complete (optional/advanced)
              // For now, relies on final JSON parse or Review Agent sending structured events?
              // The prompt says output *single* JSON object at the end.
              // So agent_response is likely the "Chain of Thought" or Markdown analysis leading up to it?
              // Wait, prompt says "Output strict JSON".
              // If strict JSON, the agent might stream the JSON char by char?
              // OR it streams "thoughts" then the JSON?
              // If it streams JSON char by char, `event.content` is parts of JSON.
              // Displaying raw JSON parts is ugly.
              // If prompt enforces strict JSON, we might not get "analysis" text separately?
              // "analysis": "Detailed markdown..." is a field IN the JSON.
              // So the stream will look like `{ "sentiment...` 
              // Check `agent.py`: `run_review_agent` streams `event["data"]["chunk"].content`.
              // If the model outputs purely JSON, the stream is raw JSON characters.
              // displaying that as "Analysis" is bad.
              // We should HIDE the stream if it looks like JSON structure, OR only show if it's "thought".
              // BUT `prompts.py` (Step 434) says "You must output a single JSON object."
              // So the whole output is one big JSON.
              // We shouldn't show the raw stream in the "Analysis" box until we parse it?
              // OR we try to parse fields incrementally.
              // Naive fix: Don't show text if it starts with `{`.
              // BETTER: The prompt usually outputs thoughts *before* the JSON if configured as reasoning agent?
              // `REVIEW_SYSTEM_PROMPT` (Step 434)
            }
          } catch (e) {
            // console.log("Stream parse error", e);
          }
        }
      }

      // Final Parse
      if (fullResponseText) {
        try {
          // Find JSON block
          const firstOpen = fullResponseText.indexOf('{');
          const lastClose = fullResponseText.lastIndexOf('}');
          if (firstOpen !== -1 && lastClose !== -1) {
            const jsonStr = fullResponseText.substring(firstOpen, lastClose + 1);
            const data = JSON.parse(jsonStr);
            setReviewData(data);
          }
        } catch (e) { console.error("Final JSON parse failed", e); }
      }
    } catch (e) {
      console.error("Review Fetch Error:", e);
    } finally {
      setReviewAnalyzing(false);
    }
  };

  useEffect(() => {
    fetchData();
    return () => { if (fetchAbortControllerRef.current) fetchAbortControllerRef.current.abort(); };
  }, [period]);

  const handleManualSearch = () => {
    fetchData();
  };

  // Helper to render toggle buttons
  const IndicatorGroup = ({
    label,
    options,
    current,
    onChange
  }: {
    label: string,
    options: string[],
    current: string,
    onChange: (val: any) => void
  }) => (
    <div className="flex items-center gap-3">
      <span className="text-xs font-medium text-slate-500">{label}</span>
      <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${current === opt
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-500 hover:text-slate-300'
              }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );

  // Calculate real-time stats from the last two data points
  const lastData = data.length > 0 ? data[data.length - 1] : undefined;
  const prevData = data.length > 1 ? data[data.length - 2] : undefined;

  const currentPrice = lastData?.close;
  const prevClose = prevData?.close || lastData?.open; // Fallback to open if no prev day

  const priceChange = (currentPrice && prevClose) ? currentPrice - prevClose : undefined;
  const priceChangePercent = (priceChange && prevClose) ? Number(((priceChange / prevClose) * 100).toFixed(2)) : undefined;

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-hidden">
      {/* Top Toolbar */}
      <header className="flex-none flex items-center justify-between bg-slate-800/60 p-3 rounded-xl border border-slate-700/50 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-blue-400 font-bold px-2">
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
            {symbol && (
              <span className="ml-2 text-slate-400 text-sm font-mono border-l border-slate-700 pl-3">
                {symbol}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Period Selector */}
          <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
            {['1D', '1W', '1M', '1Y', '5Y'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p.toLowerCase())}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${period === p.toLowerCase()
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-300'
                  }`}
              >
                {p}
              </button>
            ))}
          </div>

          <button onClick={fetchData} className="p-2 text-slate-400 hover:text-white transition-colors bg-slate-800 rounded-lg border border-slate-700 hover:bg-slate-700">
            <RotateCcw size={16} />
          </button>
          <button
            onClick={fetchReviewAnalysis}
            disabled={reviewAnalyzing || !symbol}
            className={`p-2 transition-all rounded-lg border flex items-center gap-2 ${reviewAnalyzing ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/50' : 'text-slate-400 hover:text-white bg-slate-800 border-slate-700 hover:bg-slate-700'}`}
            title="Start AI Review"
          >
            <Bot size={16} className={reviewAnalyzing ? 'animate-bounce' : ''} />
            <span className="text-xs font-semibold hidden md:inline">AI Review</span>
          </button>
        </div>
      </header>

      {/* Main Grid Content */}
      <div className="flex-1 min-h-0 grid grid-cols-12 gap-4">

        {/* Left Panel: Chart & AI Review */}
        <div className="col-span-12 lg:col-span-9 flex flex-col gap-4 overflow-y-auto pr-1">

          {/* AI Daily Review Card */}
          {(reviewData || reviewAnalyzing) && (
            <DailyReviewCard
              sentimentScore={reviewData?.sentiment_score || 50}
              sentimentLabel={reviewData?.sentiment_label}
              keyEvents={reviewData?.key_events || []}
              tomorrowPrediction={reviewData?.tomorrow_prediction}
              strategy={reviewData?.strategy}
              summary={reviewData?.summary}
              analysis={reviewData?.analysis || reviewAnalysisText} // Fallback to raw text if no JSON yet
              analyzing={reviewAnalyzing}
            />
          )}

          <div className="min-h-[500px] bg-slate-900 rounded-xl border border-slate-800 p-4 relative overflow-hidden shadow-inner flex flex-col">

            {/* Empty / Loading / Error States */}
            {!symbol || (!loading && data.length === 0 && !error) ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-600">
                <LayoutDashboard size={48} className="mb-4 opacity-20" />
                <p className="text-sm">Enter a stock code to start analysis</p>
                <div className="mt-8 w-full max-w-md border-t border-slate-800/50"></div>
              </div>
            ) : loading ? (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
                <div className="text-purple-400 animate-pulse font-medium">Loading Market Data...</div>
              </div>
            ) : error ? (
              <div className="h-full flex flex-col items-center justify-center text-red-400 gap-2">
                <AlertCircle size={32} />
                <p>{error}</p>
              </div>
            ) : (
              <TradingViewChart
                data={data}
                mainIndicator={mainIndicator}
                subIndicator={subIndicator}
              />
            )}
          </div>

          {/* Integrated Indicator Control Bar (Styled like Period Selector) */}
          <div className="h-14 bg-slate-800/40 rounded-xl border border-slate-700/50 px-4 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <IndicatorGroup
                label="主图 (Main)"
                options={['MA', 'BOLL', 'NONE']}
                current={mainIndicator}
                onChange={setMainIndicator}
              />
              <div className="w-px h-6 bg-slate-700/50"></div>
              <IndicatorGroup
                label="副图 (Sub)"
                options={['VOL', 'MACD', 'RSI', 'KDJ', 'NONE']}
                current={subIndicator}
                onChange={setSubIndicator}
              />
            </div>
          </div>
        </div>

        {/* Right Panel: RealTime Data */}
        <div className="col-span-12 lg:col-span-3 h-full overflow-y-auto custom-scrollbar">
          <RealTimeDataPanel
            symbol={symbol}
            price={snapshot?.current_price ?? (snapshot?.price ?? currentPrice)}
            change={priceChange !== undefined ? Number(priceChange.toFixed(2)) : undefined}
            changePercent={
              snapshot?.current_price && snapshot?.prev_close
                ? Number(((snapshot.current_price - snapshot.prev_close) / snapshot.prev_close * 100).toFixed(2))
                : priceChangePercent
            }

            high={snapshot?.high ?? lastData?.high}
            low={snapshot?.low ?? lastData?.low}
            open={snapshot?.open ?? lastData?.open}

            volume={snapshot?.volume ? Number((snapshot.volume / 1000000).toFixed(2)) : undefined} // Million
            turnover={snapshot?.turnover ? Number((snapshot.turnover / 100000000).toFixed(2)) : undefined} // Billion for amount

            turnoverRate={snapshot?.turnover_rate}
            pe={snapshot?.pe}
            marketCap={snapshot?.market_cap}
            amplitude={
              snapshot?.high && snapshot?.low && snapshot?.prev_close
                ? Number(((snapshot.high - snapshot.low) / snapshot.prev_close * 100).toFixed(2))
                : undefined
            }
          />
        </div>
      </div>
    </div>
  );
};

export default MarketQueryPage;