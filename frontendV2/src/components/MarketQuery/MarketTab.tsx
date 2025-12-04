import React, { useState, useEffect } from 'react';
import { stockAPI } from '../../services/stockAPI';
import type { StockData } from '../../services/stockAPI';
import TradingViewKLineChart from '../../components/KLineChart/TradingViewKLineChart';
import SimpleKLineChart from '../../components/KLineChart/SimpleKLineChart';
import { Search, BarChart2, TrendingUp, DollarSign, Activity, Bot, AlertCircle, Loader2 } from 'lucide-react';

interface KLineData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const MarketTab: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [useSimpleChart, setUseSimpleChart] = useState(false);
  const [chartError, setChartError] = useState<string>('');
  const [isAIChatOpen, setIsAIChatOpen] = useState(false);
  const [timeRange, setTimeRange] = useState<number>(30);

  const fetchHistoricalData = async (symbol: string, days: number) => {
    try {
      const historicalData = await stockAPI.getHistoricalData(symbol, '30d', days);
      return historicalData;
    } catch (error) {
      console.error('获取历史数据失败:', error);
      return [];
    }
  };

  useEffect(() => {
    if (selectedStock) {
      fetchHistoricalData(selectedStock.symbol, timeRange).then(kData => {
        setKlineData(kData);
      });
    }
  }, [timeRange, selectedStock]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await stockAPI.searchStock(searchTerm);

      if (response.status === 'success' && response.data) {
        setStockData(prev => {
          const exists = prev.find(stock => stock.symbol === response.data!.symbol);
          return exists ?
            prev.map(stock => stock.symbol === response.data!.symbol ? response.data! : stock) :
            [response.data!, ...prev];
        });

        setSelectedStock(response.data);
        fetchHistoricalData(response.data.symbol, timeRange).then(kData => {
          setKlineData(kData);
        });

        setSearchTerm('');
      } else {
        setError(response.message || '未找到相关股票信息');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleStockSelect = (stock: StockData) => {
    setSelectedStock(stock);
    fetchHistoricalData(stock.symbol, timeRange).then(kData => {
      setKlineData(kData);
    });
  };

  const handleChartError = (error: Error) => {
    setChartError(error.message);
    setUseSimpleChart(true);
  };

  const toggleAIChat = () => setIsAIChatOpen(!isAIChatOpen);

  return (
    <>
      <div className="bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Search size={18} className="text-blue-500" />
            股票搜索
          </h3>
          <button
            type="button"
            onClick={toggleAIChat}
            className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-200 flex items-center gap-2 group"
          >
            <Bot size={16} className="group-hover:rotate-12 transition-transform" />
            AI 智能分析
          </button>
        </div>

        <form onSubmit={handleSearch} className="flex gap-3 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="输入股票代码或名称 (例如: 000001, AAPL)"
              className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-sm shadow-blue-600/20"
          >
            {loading ? '搜索中...' : '搜索'}
          </button>
        </form>

        {error && (
          <div className="mt-3 p-3 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400 text-sm flex items-center gap-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {loading && !error && (
          <div className="mt-3 p-3 bg-blue-900/20 border border-blue-800/50 rounded-lg text-blue-400 text-sm flex items-center gap-2">
            <Loader2 size={16} className="animate-spin" />
            正在搜索股票数据...
          </div>
        )}
      </div>

      <div className={`flex-1 grid gap-6 min-h-0 ${selectedStock ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 overflow-hidden flex flex-col h-[600px]">
          <div className="p-4 border-b border-slate-700 bg-slate-900/50 flex items-center gap-2">
            <BarChart2 size={18} className="text-slate-400" />
            <div>
              <h2 className="text-sm font-semibold text-white">热门股票</h2>
              <p className="text-xs text-slate-400">点击查看详情</p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {stockData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm p-8 text-center">
                <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center mb-3">
                  <Search size={20} />
                </div>
                暂无股票数据<br />请搜索或等待加载
              </div>
            ) : (
              stockData.filter(stock => stock && stock.symbol).map((stock: StockData) => {
                const isPositive = stock.change_amount >= 0;
                const isSelected = selectedStock?.symbol === stock.symbol;

                return (
                  <div
                    key={stock.symbol}
                    onClick={() => handleStockSelect(stock)}
                    className={`
                      p-3 rounded-lg cursor-pointer transition-all duration-200 border
                      ${isSelected
                        ? 'bg-blue-900/30 border-blue-700/50 shadow-sm'
                        : 'bg-slate-800 border-transparent hover:bg-slate-700 hover:border-slate-600'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-sm font-bold ${isSelected ? 'text-blue-400' : 'text-white'}`}>
                            {stock.symbol}
                          </span>
                          {isSelected && <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />}
                        </div>
                        <h3 className="text-xs font-medium text-slate-400 truncate max-w-[120px]">
                          {stock.name}
                        </h3>
                      </div>

                      <div className="text-right">
                        <div className="text-sm font-bold text-white mb-1 font-mono">
                          ¥{stock.current_price?.toFixed(2) || '--'}
                        </div>
                        <div className={`
                          flex items-center justify-end gap-1 text-xs font-medium
                          ${isPositive ? 'text-red-500' : 'text-green-500'}
                        `}>
                          {isPositive ? <TrendingUp size={12} /> : <TrendingUp size={12} className="rotate-180" />}
                          <span>{isPositive ? '+' : ''}{stock.change_percent?.toFixed(2) || '--'}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {selectedStock && (
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-700">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-700">
                <div className="w-10 h-10 bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-500">
                  <DollarSign size={20} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    {selectedStock.name}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    {selectedStock.symbol} • 实时数据
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                <div className="p-4 bg-slate-900 rounded-xl">
                  <span className="text-xs text-slate-500 block mb-1">当前价格</span>
                  <span className="text-xl font-bold text-white font-mono">
                    ¥{selectedStock.current_price?.toFixed(2) || '--'}
                  </span>
                </div>
                <div className="p-4 bg-slate-900 rounded-xl">
                  <span className="text-xs text-slate-500 block mb-1">涨跌幅</span>
                  <span className={`text-xl font-bold font-mono ${selectedStock.change_amount >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                    {selectedStock.change_amount >= 0 ? '+' : ''}{selectedStock.change_percent?.toFixed(2) || '--'}%
                  </span>
                </div>
                <div className="p-4 bg-slate-900 rounded-xl">
                  <span className="text-xs text-slate-500 block mb-1">涨跌额</span>
                  <span className={`text-xl font-bold font-mono ${selectedStock.change_amount >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                    {selectedStock.change_amount >= 0 ? '+' : ''}{selectedStock.change_amount?.toFixed(2) || '--'}
                  </span>
                </div>
                <div className="p-4 bg-slate-900 rounded-xl">
                  <span className="text-xs text-slate-500 block mb-1">成交量</span>
                  <span className="text-xl font-bold text-white font-mono">
                    {selectedStock.volume ? (selectedStock.volume / 10000).toFixed(1) : '--'}万
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-700 flex-1 min-h-[400px] flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-2">
                  <Activity size={18} className="text-blue-500" />
                  <h4 className="text-sm font-bold text-white">K线走势图</h4>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex bg-slate-700 rounded-lg p-1">
                    {[7, 14, 30].map((days) => (
                      <button
                        key={days}
                        onClick={() => setTimeRange(days)}
                        className={`
                          px-3 py-1 text-xs font-medium rounded-md transition-colors
                          ${timeRange === days
                            ? 'bg-slate-600 text-white shadow-sm'
                            : 'text-slate-400 hover:text-slate-300'
                          }
                        `}
                      >
                        {days}天
                      </button>
                    ))}
                  </div>

                  <div className="w-px h-4 bg-slate-600 mx-1"></div>

                  {chartError && (
                    <span className="text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> 图表加载失败
                    </span>
                  )}
                  <button
                    onClick={() => setUseSimpleChart(!useSimpleChart)}
                    className={`
                      px-3 py-1.5 text-xs font-medium rounded-md transition-colors
                      ${useSimpleChart
                        ? 'bg-blue-900/30 text-blue-400'
                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                      }
                    `}
                  >
                    {useSimpleChart ? '切换高级图表' : '切换简单图表'}
                  </button>
                </div>
              </div>

              <div className="flex-1 bg-slate-900 rounded-lg border border-slate-700 overflow-hidden relative min-h-[300px]">
                {useSimpleChart ? (
                  <SimpleKLineChart
                    data={klineData.map(item => ({
                      ...item,
                      time: new Date(item.time).getTime() / 1000
                    }))}
                    width={800}
                    height={400}
                  />
                ) : (
                  <TradingViewKLineChart
                    data={klineData}
                    width={800}
                    height={400}
                    onError={handleChartError}
                  />
                )}

                {klineData.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm z-10">
                    <div className="text-center text-slate-400">
                      <Loader2 size={24} className="animate-spin mx-auto mb-2" />
                      <p className="text-sm">加载图表数据中...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default MarketTab;
