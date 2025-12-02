import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, AlertCircle } from 'lucide-react';
import StockChart from '../components/TechnicalAnalysis/StockChart';
import AnalysisPanel from '../components/TechnicalAnalysis/AnalysisPanel';
import IndicatorSelector from '../components/TechnicalAnalysis/IndicatorSelector';

const TechnicalAnalysisPage: React.FC = () => {
    const [symbol, setSymbol] = useState('AAPL');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<any[]>([]);
    const [period, setPeriod] = useState('1y');

    // 指标状态
    const [mainIndicator, setMainIndicator] = useState<'MA' | 'BOLL' | 'NONE'>('MA');
    const [subIndicator, setSubIndicator] = useState<'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE'>('VOL');

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`http://localhost:8000/api/market/technical/${symbol}?period=${period}`);
            const result = await response.json();

            if (result.status === 'success') {
                setData(result.data);
            } else {
                setError(result.message || '获取数据失败');
            }
        } catch (err) {
            setError('网络请求失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []); // 初始加载

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        fetchData();
    };

    return (
        <div className="p-6 max-w-[1600px] mx-auto space-y-6">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">技术面分析 (Technical Analysis)</h1>
                    <p className="text-slate-400">专业级K线图表与多维技术指标分析</p>
                </div>

                <div className="flex items-center gap-4">
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <div className="relative">
                            <input
                                type="text"
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                placeholder="输入股票代码 (e.g. AAPL)"
                                className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 pl-10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
                            />
                            <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            {loading ? '分析中...' : '分析'}
                        </button>
                    </form>

                    <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
                        {['6mo', '1y', '2y', '5y'].map((p) => (
                            <button
                                key={p}
                                onClick={() => { setPeriod(p); setTimeout(fetchData, 0); }} // 简单的触发重新获取
                                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${period === p ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-white'
                                    }`}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3 text-red-400">
                    <AlertCircle size={20} />
                    <span>{error}</span>
                </div>
            )}

            {loading && !data.length ? (
                <div className="h-96 flex items-center justify-center text-slate-400">
                    <RefreshCw className="animate-spin mr-2" />
                    加载数据中...
                </div>
            ) : (
                <>
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
                                <h3 className="text-white font-medium mb-2">指标说明</h3>
                                <div className="space-y-2 text-sm text-slate-400">
                                    <p><span className="text-yellow-400">MA</span>: 移动平均线 (5/10/20/60日)</p>
                                    <p><span className="text-purple-400">BOLL</span>: 布林带 (20日, 2倍标准差)</p>
                                    <p><span className="text-blue-400">MACD</span>: 指数平滑异同移动平均线</p>
                                    <p><span className="text-green-400">RSI</span>: 相对强弱指标 (14日)</p>
                                    <p><span className="text-orange-400">KDJ</span>: 随机指标</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default TechnicalAnalysisPage;
