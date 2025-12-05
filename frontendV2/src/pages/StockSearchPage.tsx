import React, { useState } from 'react';
import { stockAPI } from '../services/stockAPI';
import type { StockData } from '../services/stockAPI';
import TradingViewKLineChart from '../components/KLineChart/TradingViewKLineChart';
import SimpleKLineChart from '../components/KLineChart/SimpleKLineChart';
import type { UTCTimestamp } from 'lightweight-charts';
import { Search, TrendingUp, AlertCircle, Loader2, BarChart2, Activity } from 'lucide-react';

interface KLineData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const StockSearchPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<StockData[]>([]);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [useSimpleChart, setUseSimpleChart] = useState(false); // 备用图表开关
  const [chartError, setChartError] = useState<string>(''); // 图表错误信息

  // 处理图表错误
  const handleChartError = (error: Error) => {
    console.error('Chart error:', error);
    setChartError(error.message);
    // 自动切换到简单图表
    setUseSimpleChart(true);
  };

  // 生成模拟K线数据
  const generateKLineData = (basePrice: number, days: number = 30) => {
    const data = [];
    const now = new Date();

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      const open = basePrice + (Math.random() - 0.5) * basePrice * 0.1;
      const close = open + (Math.random() - 0.5) * basePrice * 0.08;
      const high = Math.max(open, close) + Math.random() * basePrice * 0.05;
      const low = Math.min(open, close) - Math.random() * basePrice * 0.05;
      const volume = Math.floor(Math.random() * 1000000) + 100000;

      data.push({
        time: Math.floor(date.getTime() / 1000) as UTCTimestamp,
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume,
      });
    }

    return data;
  };

  // 处理搜索
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await stockAPI.searchStock(searchTerm);

      if (response.status === 'success' && response.data) {
        // 添加到搜索结果
        setSearchResults(prev => {
          const exists = prev.find(stock => stock.symbol === response.data!.symbol);
          if (exists) {
            return prev.map(stock =>
              stock.symbol === response.data!.symbol ? response.data! : stock
            );
          } else {
            return [response.data!, ...prev];
          }
        });

        // 自动生成K线数据
        const kData = generateKLineData(response.data.current_price);
        console.log('Generated K-line data:', kData); // 调试信息
        setKlineData(kData);

        // 选中该股票
        setSelectedStock(response.data);
      } else {
        setError(response.message || '未找到相关股票信息');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 快速搜索热门股票
  const quickSearch = async (symbol: string) => {
    setSearchTerm(symbol);

    setLoading(true);
    setError('');

    try {
      const response = await stockAPI.searchStock(symbol);

      if (response.status === 'success' && response.data) {
        setSearchResults(prev => {
          const exists = prev.find(stock => stock.symbol === response.data!.symbol);
          if (exists) {
            return prev.map(stock =>
              stock.symbol === response.data!.symbol ? response.data! : stock
            );
          } else {
            return [response.data!, ...prev];
          }
        });

        const kData = generateKLineData(response.data.current_price);
        setKlineData(kData);
        setSelectedStock(response.data);
      }
    } catch {
      setError('快速搜索失败');
    } finally {
      setLoading(false);
    }
  };

  // 热门股票列表
  const hotStocks = [
    { symbol: '000001', name: '平安银行' },
    { symbol: '600036', name: '招商银行' },
    { symbol: 'AAPL', name: '苹果公司' },
    { symbol: 'TSLA', name: '特斯拉' },
    { symbol: '00700', name: '腾讯控股' },
    { symbol: '09988', name: '阿里巴巴' }
  ];

  return (
    <div className="h-full flex flex-col gap-4 max-w-7xl mx-auto w-full p-6">
      {/* 页面标题 */}
      <div className="flex flex-col justify-center py-2">
        <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
          股票搜索
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          支持A股、美股、港股实时查询
        </p>
      </div>

      {/* 搜索区域 */}
      <div className="bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-700 flex flex-col justify-center">
        <form onSubmit={handleSearch} className="flex gap-3 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="输入股票代码或名称，如：000001、AAPL、腾讯"
              className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-sm shadow-blue-600/20 flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                搜索中...
              </>
            ) : (
              '搜索'
            )}
          </button>
        </form>

        {/* 错误提示 */}
        {error && (
          <div className="mt-3 p-3 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400 text-sm flex items-center gap-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}
      </div>

      {/* 热门股票快速搜索 */}
      <div className="bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">🔥</span>
          <span className="text-sm font-medium text-white">
            热门股票
          </span>
        </div>
        <div className="flex gap-2 flex-wrap">
          {hotStocks.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => quickSearch(stock.symbol)}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded text-xs text-slate-300 hover:text-white transition-all duration-200"
            >
              {stock.symbol} - {stock.name}
            </button>
          ))}
        </div>
      </div>

      {/* 搜索结果和K线图 */}
      <div className={`flex-1 grid gap-4 min-h-0 ${selectedStock ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
        {/* 搜索结果列表 */}
        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 overflow-hidden flex flex-col">
          <div className="p-3 border-b border-slate-700 bg-slate-900/30 flex items-center gap-2">
            <BarChart2 size={16} className="text-slate-400" />
            <div>
              <h3 className="text-sm font-semibold text-white">
                搜索结果
              </h3>
              <p className="text-xs text-slate-500">
                点击股票查看K线图
              </p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {searchResults.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm p-10 text-center">
                <Search size={32} className="mb-3 text-slate-600" />
                <p>请输入股票代码或名称开始搜索</p>
              </div>
            ) : (
              searchResults.filter(stock => stock && stock.symbol).map((stock) => {
                const isPositive = stock.change_amount >= 0;
                const isSelected = selectedStock?.symbol === stock.symbol;

                return (
                  <div
                    key={stock.symbol}
                    onClick={() => {
                      setSelectedStock(stock);
                      const kData = generateKLineData(stock.current_price);
                      setKlineData(kData);
                    }}
                    className={`
                      p-3 mb-1 rounded-lg cursor-pointer transition-all duration-200 border-l-4
                      ${isSelected
                        ? 'bg-blue-900/20 border-l-blue-500'
                        : 'bg-transparent border-l-transparent hover:bg-slate-700/50'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-bold text-white">
                            {stock.symbol}
                          </span>
                          <span className={`
                            text-[10px] px-1.5 py-0.5 rounded font-medium
                            ${stock.market === 'A-share' ? 'bg-blue-900/40 text-blue-400' :
                              stock.market === 'US' ? 'bg-green-900/40 text-green-400' : 'bg-purple-900/40 text-purple-400'}
                          `}>
                            {stock.market === 'A-share' ? 'A股' :
                              stock.market === 'US' ? '美股' : '港股'}
                          </span>
                        </div>
                        <h3 className="text-xs font-medium text-slate-400">
                          {stock.name}
                        </h3>
                      </div>

                      <div className="text-right">
                        <div className="text-base font-bold text-white mb-0.5 font-mono">
                          {stock.currency === 'CNY' ? '¥' : stock.currency === 'USD' ? '$' : 'HK$'}{stock.current_price?.toFixed(2) || '--'}
                        </div>
                        <div className={`
                          flex items-center justify-end gap-1 text-xs font-medium
                          ${isPositive ? 'text-red-500' : 'text-green-500'}
                        `}>
                          {isPositive ? <TrendingUp size={12} /> : <TrendingUp size={12} className="rotate-180" />}
                          <span>{isPositive ? '+' : ''}{stock.change_amount?.toFixed(2) || '--'}</span>
                          <span>({isPositive ? '+' : ''}{stock.change_percent?.toFixed(2) || '--'}%)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* K线图 */}
        {selectedStock && (
          <div className="bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-700 flex flex-col">
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-700">
              <Activity size={18} className="text-blue-500" />
              <div>
                <h3 className="text-sm font-semibold text-white">
                  {selectedStock.symbol} - K线图
                </h3>
                <p className="text-xs text-slate-400">
                  {selectedStock.name}
                </p>
              </div>
            </div>

            <div className="flex-1 min-h-[300px] flex flex-col">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-500">K线图预览</span>
                <div className="flex items-center gap-2">
                  {chartError && (
                    <span className="text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> 高级图表加载失败
                    </span>
                  )}
                  <button
                    onClick={() => setUseSimpleChart(!useSimpleChart)}
                    className={`
                      px-2 py-1 text-xs rounded transition-colors border
                      ${useSimpleChart
                        ? 'bg-blue-900/30 text-blue-400 border-blue-800'
                        : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'
                      }
                    `}
                  >
                    {useSimpleChart ? '使用高级图表' : '使用简单图表'}
                  </button>
                </div>
              </div>
              <div className="flex-1 bg-slate-900 rounded-lg border border-slate-700 overflow-hidden relative">
                {useSimpleChart ? (
                  <SimpleKLineChart
                    data={klineData}
                    width={600}
                    height={300}
                  />
                ) : (
                  <TradingViewKLineChart
                    data={klineData}
                    width={600}
                    height={300}
                    onError={handleChartError}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockSearchPage;
