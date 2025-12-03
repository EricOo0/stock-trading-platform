import React, { useState, useEffect } from 'react';
import { stockAPI } from '../services/stockAPI';
import type { StockData } from '../services/stockAPI';
import TradingViewKLineChart from '../components/KLineChart/TradingViewKLineChart';
import SimpleKLineChart from '../components/KLineChart/SimpleKLineChart';
import AIChatSidebar from '../components/AIChat/AIChatSidebar';
import { Search, BarChart2, TrendingUp, DollarSign, Activity, Bot, AlertCircle, Loader2 } from 'lucide-react';

const MarketQueryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<any[]>([]);
  const [useSimpleChart, setUseSimpleChart] = useState(false);
  const [chartError, setChartError] = useState<string>('');
  const [isAIChatOpen, setIsAIChatOpen] = useState(false);
  const [webSearchQuery, setWebSearchQuery] = useState('');
  const [webSearchResults, setWebSearchResults] = useState<Array<{ title: string; href: string; body: string }>>([]);
  const [webSearchLoading, setWebSearchLoading] = useState(false);
  const [financialData, setFinancialData] = useState<any>(null);
  const [financialLoading, setFinancialLoading] = useState(false);
  const [financialSearchQuery, setFinancialSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'market' | 'financial' | 'web'>('market');

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

  // Remove default hot stocks loading
  // useEffect(() => {
  //   loadHotStocks();
  // }, []);

  // 当时间范围改变时，重新获取数据
  useEffect(() => {
    if (selectedStock) {
      fetchHistoricalData(selectedStock.symbol, timeRange).then(kData => {
        setKlineData(kData);
      });
    }
  }, [timeRange, selectedStock]);

  const loadHotStocks = async () => {
    try {
      setLoading(true);
      const hotStocks = await stockAPI.getHotStocks();
      setStockData(hotStocks);

      if (hotStocks.length > 0) {
        setSelectedStock(hotStocks[0]);
        // 初始加载使用默认时间范围
        fetchHistoricalData(hotStocks[0].symbol, 30).then(kData => {
          setKlineData(kData);
        });
      }
    } catch (err) {
      setError('加载热门股票失败');
    } finally {
      setLoading(false);
    }
  };

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
        // 搜索新股票时重置为默认30天或保持当前选择
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
    // 切换股票时使用当前选择的时间范围
    fetchHistoricalData(stock.symbol, timeRange).then(kData => {
      setKlineData(kData);
    });
  };

  const handleChartError = (error: Error) => {
    setChartError(error.message);
    setUseSimpleChart(true);
  };

  const toggleAIChat = () => setIsAIChatOpen(!isAIChatOpen);
  const closeAIChat = () => setIsAIChatOpen(false);

  const handleWebSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!webSearchQuery.trim()) return;

    setWebSearchLoading(true);
    setError('');

    try {
      const response = await stockAPI.webSearch(webSearchQuery);

      if (response.status === 'success' && response.results) {
        setWebSearchResults(response.results);
      } else {
        setError(response.message || '搜索失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
    } finally {
      setWebSearchLoading(false);
    }
  };

  const fetchFinancialReport = async (symbol: string) => {
    setFinancialLoading(true);
    setError('');

    try {
      const response = await stockAPI.getFinancialReport(symbol);

      if (response.status === 'success') {
        setFinancialData(response);
      } else {
        setError(response.message || '获取财报数据失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取财报数据失败');
    } finally {
      setFinancialLoading(false);
    }
  };

  const handleFinancialSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!financialSearchQuery.trim()) return;
    await fetchFinancialReport(financialSearchQuery.trim());
  };

  return (
    <div className="h-full flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* Page Title */}
      <div className="flex flex-col justify-center">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
          市场分析
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          实时行情、财报分析、新闻搜索
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('market')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${activeTab === 'market'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <TrendingUp size={18} />
              行情查询
            </div>
          </button>
          <button
            onClick={() => setActiveTab('financial')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${activeTab === 'financial'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <BarChart2 size={18} />
              财报分析
            </div>
          </button>
          <button
            onClick={() => setActiveTab('web')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${activeTab === 'web'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Search size={18} />
              新闻搜索
            </div>
          </button>
        </div>
      </div>

      {/* Market Query Tab Content */}
      {activeTab === 'market' && (
        <>
          {/* Search Section */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-semibold text-gray-800 flex items-center gap-2">
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
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="输入股票代码或名称 (例如: 000001, AAPL)"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
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
              <div className="mt-3 p-3 bg-red-50 border border-red-100 rounded-lg text-red-600 text-sm flex items-center gap-2">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            {loading && !error && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-lg text-blue-600 text-sm flex items-center gap-2">
                <Loader2 size={16} className="animate-spin" />
                正在搜索股票数据...
              </div>
            )}
          </div>
        </>
      )}

      {/* Financial Analysis Tab Content */}
      {activeTab === 'financial' && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="max-w-2xl mx-auto text-center py-12">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <BarChart2 size={32} className="text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              智能财报分析
            </h2>
            <p className="text-gray-600 mb-8">
              获取即时的、AI驱动的季度财报、年度报告和财务健康检查
            </p>

            <form onSubmit={handleFinancialSearch} className="max-w-xl mx-auto">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  value={financialSearchQuery}
                  onChange={(e) => setFinancialSearchQuery(e.target.value)}
                  placeholder="搜索公司 (例如: Tesla 2023 Q4 或 腾讯 2024 财报)"
                  className="w-full pl-12 pr-4 py-4 bg-gray-50 border-2 border-gray-200 rounded-xl text-base focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all"
                />
              </div>
              <button
                type="submit"
                disabled={financialLoading}
                className="mt-4 w-full bg-blue-600 text-white px-6 py-4 rounded-xl text-base font-medium hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2"
              >
                {financialLoading ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    分析中...
                  </>
                ) : (
                  '开始分析'
                )}
              </button>
            </form>

            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-100 rounded-lg text-red-600 text-sm flex items-center justify-center gap-2">
                <AlertCircle size={16} />
                {error}
              </div>
            )}
          </div>

          {/* Financial Report Display */}
          {financialData && (
            <div className="mt-8 border-t border-gray-200 pt-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <BarChart2 size={20} className="text-blue-500" />
                  <h4 className="text-lg font-bold text-gray-800">财报数据 - {financialData.symbol}</h4>
                </div>
                <button
                  onClick={() => setFinancialData(null)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* Financial Metrics Table */}
              {financialData.metrics && financialData.metrics.length > 0 && (
                <div className="overflow-x-auto mb-6">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 border-gray-200">
                        <th className="text-left py-3 px-4 text-gray-700 font-semibold">日期</th>
                        <th className="text-right py-3 px-4 text-gray-700 font-semibold">营收</th>
                        <th className="text-right py-3 px-4 text-gray-700 font-semibold">净利润</th>
                        <th className="text-right py-3 px-4 text-gray-700 font-semibold">毛利润</th>
                        <th className="text-right py-3 px-4 text-gray-700 font-semibold">营业利润</th>
                      </tr>
                    </thead>
                    <tbody>
                      {financialData.metrics.map((metric: any, index: number) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                          <td className="py-4 px-4 font-mono text-gray-700 font-medium">{metric.date}</td>
                          <td className="py-4 px-4 text-right font-mono text-gray-900">
                            {metric.revenue > 0 ? `$${(metric.revenue / 1e9).toFixed(2)}B` : '--'}
                          </td>
                          <td className="py-4 px-4 text-right font-mono text-gray-900">
                            {metric.net_income > 0 ? `$${(metric.net_income / 1e9).toFixed(2)}B` : '--'}
                          </td>
                          <td className="py-4 px-4 text-right font-mono text-gray-900">
                            {metric.gross_profit > 0 ? `$${(metric.gross_profit / 1e9).toFixed(2)}B` : '--'}
                          </td>
                          <td className="py-4 px-4 text-right font-mono text-gray-900">
                            {metric.operating_income > 0 ? `$${(metric.operating_income / 1e9).toFixed(2)}B` : '--'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Latest Report Link */}
              {financialData.latest_report && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                      <BarChart2 size={20} className="text-white" />
                    </div>
                    <div>
                      <h5 className="text-base font-bold text-gray-900">财报文档</h5>
                      <p className="text-xs text-gray-600">
                        {financialData.latest_report.market === 'US' && 'SEC EDGAR 官方文件'}
                        {financialData.latest_report.market === 'HK' && '港股披露易/公司IR'}
                        {financialData.latest_report.market === 'A-SHARE' && '巨潮资讯网'}
                      </p>
                    </div>
                  </div>

                  {financialData.latest_report.status === 'success' || financialData.latest_report.status === 'partial' ? (
                    <div className="space-y-3">
                      {/* Title and Date */}
                      {financialData.latest_report.title && (
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">标题:</span> {financialData.latest_report.title}
                        </p>
                      )}
                      {financialData.latest_report.form_type && (
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">类型:</span> {financialData.latest_report.form_type}
                        </p>
                      )}
                      {financialData.latest_report.filing_date && (
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">日期:</span> {financialData.latest_report.filing_date}
                        </p>
                      )}
                      {financialData.latest_report.date && (
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">日期:</span> {financialData.latest_report.date}
                        </p>
                      )}

                      {/* Message */}
                      {financialData.latest_report.message && (
                        <p className="text-sm text-gray-600 bg-white/50 rounded-lg p-3">
                          {financialData.latest_report.message}
                        </p>
                      )}

                      {/* Download Button */}
                      {financialData.latest_report.download_url && (
                        <a
                          href={financialData.latest_report.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block w-full mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-blue-600/30 hover:shadow-xl hover:shadow-blue-600/40 text-center"
                        >
                          📄 查看/下载财报 →
                        </a>
                      )}

                      {/* Additional Links */}
                      <div className="flex gap-2 mt-3">
                        {financialData.latest_report.ir_url && (
                          <a
                            href={financialData.latest_report.ir_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 px-4 py-2 bg-white hover:bg-gray-50 text-blue-600 rounded-lg text-xs font-medium transition-colors border border-blue-200 text-center"
                          >
                            公司IR页面
                          </a>
                        )}
                        {financialData.latest_report.hkexnews_url && (
                          <a
                            href={financialData.latest_report.hkexnews_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 px-4 py-2 bg-white hover:bg-gray-50 text-blue-600 rounded-lg text-xs font-medium transition-colors border border-blue-200 text-center"
                          >
                            披露易搜索
                          </a>
                        )}
                        {financialData.latest_report.cninfo_url && (
                          <a
                            href={financialData.latest_report.cninfo_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 px-4 py-2 bg-white hover:bg-gray-50 text-blue-600 rounded-lg text-xs font-medium transition-colors border border-blue-200 text-center"
                          >
                            巨潮资讯网
                          </a>
                        )}
                      </div>

                      {/* Suggestions */}
                      {financialData.latest_report.suggestions && financialData.latest_report.suggestions.length > 0 && (
                        <div className="mt-4 p-3 bg-white/70 rounded-lg">
                          <p className="text-xs font-medium text-gray-700 mb-2">💡 使用提示:</p>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {financialData.latest_report.suggestions.map((suggestion: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-2">
                                <span className="text-blue-500 mt-0.5">•</span>
                                <span>{suggestion}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600">
                      {financialData.latest_report.message || '暂无报告数据'}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Web Search Tab Content */}
      {activeTab === 'web' && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-base font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <Search size={18} className="text-green-500" />
            新闻资讯搜索
          </h3>
          <form onSubmit={handleWebSearch} className="flex gap-3 items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                value={webSearchQuery}
                onChange={(e) => setWebSearchQuery(e.target.value)}
                placeholder="输入关键词搜索新闻资讯 (例如: NVIDIA 最新新闻)"
                className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={webSearchLoading}
              className="bg-green-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-sm shadow-green-600/20"
            >
              {webSearchLoading ? '搜索中...' : '搜索'}
            </button>
          </form>

          {webSearchResults.length > 0 && (
            <div className="mt-4 space-y-3 max-h-[500px] overflow-y-auto">
              {webSearchResults.map((result, index) => {
                // Extract domain from URL
                const getDomain = (url: string) => {
                  try {
                    const urlObj = new URL(url);
                    return urlObj.hostname.replace('www.', '');
                  } catch {
                    return '';
                  }
                };

                const domain = getDomain(result.href);
                const faviconUrl = `https://icons.duckduckgo.com/ip3/${domain}.ico`;

                return (
                  <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <a
                      href={result.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-base font-semibold text-blue-600 hover:text-blue-800 hover:underline mb-2 block"
                    >
                      {result.title}
                    </a>
                    <p className="text-sm text-gray-600 line-clamp-3 mb-2">{result.body}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <img
                        src={faviconUrl}
                        alt={domain}
                        className="w-4 h-4 rounded-sm"
                        onError={(e) => {
                          // Fallback to a default icon if favicon fails to load
                          e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>';
                        }}
                      />
                      <span className="truncate">{domain}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {webSearchLoading && (
            <div className="mt-3 p-3 bg-green-50 border border-green-100 rounded-lg text-green-600 text-sm flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              正在搜索新闻资讯...
            </div>
          )}
        </div>
      )}

      {/* Main Content - Only show in Market Tab */}
      {activeTab === 'market' && (
        <div className={`flex-1 grid gap-6 min-h-0 ${selectedStock ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
          {/* Stock List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col h-[600px]">
            <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2">
              <BarChart2 size={18} className="text-gray-500" />
              <div>
                <h2 className="text-sm font-semibold text-gray-800">热门股票</h2>
                <p className="text-xs text-gray-500">点击查看详情</p>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {stockData.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 text-sm p-8 text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
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
                          ? 'bg-blue-50 border-blue-200 shadow-sm'
                          : 'bg-white border-transparent hover:bg-gray-50 hover:border-gray-100'
                        }
                    `}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-sm font-bold ${isSelected ? 'text-blue-700' : 'text-gray-900'}`}>
                              {stock.symbol}
                            </span>
                            {isSelected && <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />}
                          </div>
                          <h3 className="text-xs font-medium text-gray-500 truncate max-w-[120px]">
                            {stock.name}
                          </h3>
                        </div>

                        <div className="text-right">
                          <div className="text-sm font-bold text-gray-900 mb-1 font-mono">
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

          {/* Stock Details */}
          {selectedStock && (
            <div className="lg:col-span-2 flex flex-col gap-6">
              {/* Detail Card */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                    <DollarSign size={20} />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900">
                      {selectedStock.name}
                    </h3>
                    <p className="text-xs text-gray-500 font-mono">
                      {selectedStock.symbol} • 实时数据
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <span className="text-xs text-gray-500 block mb-1">当前价格</span>
                    <span className="text-xl font-bold text-gray-900 font-mono">
                      ¥{selectedStock.current_price?.toFixed(2) || '--'}
                    </span>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <span className="text-xs text-gray-500 block mb-1">涨跌幅</span>
                    <span className={`text-xl font-bold font-mono ${selectedStock.change_amount >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {selectedStock.change_amount >= 0 ? '+' : ''}{selectedStock.change_percent?.toFixed(2) || '--'}%
                    </span>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <span className="text-xs text-gray-500 block mb-1">涨跌额</span>
                    <span className={`text-xl font-bold font-mono ${selectedStock.change_amount >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {selectedStock.change_amount >= 0 ? '+' : ''}{selectedStock.change_amount?.toFixed(2) || '--'}
                    </span>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <span className="text-xs text-gray-500 block mb-1">成交量</span>
                    <span className="text-xl font-bold text-gray-900 font-mono">
                      {selectedStock.volume ? (selectedStock.volume / 10000).toFixed(1) : '--'}万
                    </span>
                  </div>
                </div>
              </div>

              {/* Chart Card */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex-1 min-h-[400px] flex flex-col">
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center gap-2">
                    <Activity size={18} className="text-blue-500" />
                    <h4 className="text-sm font-bold text-gray-800">K线走势图</h4>
                  </div>

                  <div className="flex items-center gap-3">
                    {/* Time Range Selector */}
                    <div className="flex bg-gray-100 rounded-lg p-1">
                      {[7, 14, 30].map((days) => (
                        <button
                          key={days}
                          onClick={() => setTimeRange(days)}
                          className={`
                          px-3 py-1 text-xs font-medium rounded-md transition-colors
                          ${timeRange === days
                              ? 'bg-white text-blue-600 shadow-sm'
                              : 'text-gray-500 hover:text-gray-700'
                            }
                        `}
                        >
                          {days}天
                        </button>
                      ))}
                    </div>

                    <div className="w-px h-4 bg-gray-200 mx-1"></div>

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
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }
                    `}
                    >
                      {useSimpleChart ? '切换高级图表' : '切换简单图表'}
                    </button>
                  </div>
                </div>

                <div className="flex-1 bg-gray-50 rounded-lg border border-gray-100 overflow-hidden relative min-h-[300px]">
                  {useSimpleChart ? (
                    <SimpleKLineChart
                      data={klineData}
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
                    <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-10">
                      <div className="text-center text-gray-400">
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
      )}

      <AIChatSidebar
        isOpen={isAIChatOpen}
        onClose={closeAIChat}
        stockData={selectedStock}
        klineData={klineData}
        onToggle={toggleAIChat}
      />
    </div>
  );
};

export default MarketQueryPage;