import React, { useState } from 'react';
import { stockAPI } from '../../services/stockAPI';
import { Search, BarChart2, AlertCircle, Loader2 } from 'lucide-react';

interface FinancialMetric {
  date: string;
  revenue: number;
  net_income: number;
  gross_profit: number;
  operating_income: number;
}

interface FinancialReport {
  symbol: string;
  metrics: FinancialMetric[];
  latest_report?: {
    market?: string;
    status?: string;
    title?: string;
    form_type?: string;
    filing_date?: string;
    date?: string;
    message?: string;
    download_url?: string;
    ir_url?: string;
    hkexnews_url?: string;
    cninfo_url?: string;
    suggestions?: string[];
  };
}

const FinancialTab: React.FC = () => {
  const [financialSearchQuery, setFinancialSearchQuery] = useState('');
  const [financialData, setFinancialData] = useState<FinancialReport | null>(null);
  const [financialLoading, setFinancialLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchFinancialReport = async (symbol: string) => {
    setFinancialLoading(true);
    setError('');

    try {
      const response = await stockAPI.getFinancialReport(symbol);

      if (response.status === 'success') {
        setFinancialData({
          symbol: response.symbol || symbol,
          metrics: response.metrics || [],
          latest_report: response.latest_report as unknown as FinancialReport['latest_report']
        });
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
    <div className="bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-700">
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="w-16 h-16 bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
          <BarChart2 size={32} className="text-blue-500" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-3">
          智能财报分析
        </h2>
        <p className="text-slate-400 mb-8">
          获取即时的、AI驱动的季度财报、年度报告和财务健康检查
        </p>

        <form onSubmit={handleFinancialSearch} className="max-w-xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              value={financialSearchQuery}
              onChange={(e) => setFinancialSearchQuery(e.target.value)}
              placeholder="搜索公司 (例如: Tesla 2023 Q4 或 腾讯 2024 财报)"
              className="w-full pl-12 pr-4 py-4 bg-slate-900 border-2 border-slate-700 rounded-xl text-base text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all"
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
          <div className="mt-6 p-4 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400 text-sm flex items-center justify-center gap-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}
      </div>

      {/* Financial Report Display */}
      {financialData && (
        <div className="mt-8 border-t border-slate-700 pt-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <BarChart2 size={20} className="text-blue-500" />
              <h4 className="text-lg font-bold text-white">财报数据 - {financialData.symbol}</h4>
            </div>
            <button
              onClick={() => setFinancialData(null)}
              className="text-slate-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Financial Metrics Table */}
          {financialData.metrics && financialData.metrics.length > 0 && (
            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">日期</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">营收</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">净利润</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">毛利润</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">营业利润</th>
                  </tr>
                </thead>
                <tbody>
                  {financialData.metrics.map((metric: FinancialMetric, index: number) => (
                    <tr key={index} className="border-b border-slate-700 hover:bg-slate-700/50 transition-colors">
                      <td className="py-4 px-4 font-mono text-slate-300 font-medium">{metric.date}</td>
                      <td className="py-4 px-4 text-right font-mono text-white">
                        {metric.revenue > 0 ? `$${(metric.revenue / 1e9).toFixed(2)}B` : '--'}
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-white">
                        {metric.net_income > 0 ? `$${(metric.net_income / 1e9).toFixed(2)}B` : '--'}
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-white">
                        {metric.gross_profit > 0 ? `$${(metric.gross_profit / 1e9).toFixed(2)}B` : '--'}
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-white">
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
            <div className="bg-gradient-to-br from-slate-700 to-slate-600 rounded-xl p-6 border border-slate-600">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <BarChart2 size={20} className="text-white" />
                </div>
                <div>
                  <h5 className="text-base font-bold text-white">财报文档</h5>
                  <p className="text-xs text-slate-300">
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
                    <p className="text-sm text-slate-200">
                      <span className="font-medium text-slate-400">标题:</span> {financialData.latest_report.title}
                    </p>
                  )}
                  {financialData.latest_report.form_type && (
                    <p className="text-sm text-slate-200">
                      <span className="font-medium text-slate-400">类型:</span> {financialData.latest_report.form_type}
                    </p>
                  )}
                  {financialData.latest_report.filing_date && (
                    <p className="text-sm text-slate-200">
                      <span className="font-medium text-slate-400">日期:</span> {financialData.latest_report.filing_date}
                    </p>
                  )}
                  {financialData.latest_report.date && (
                    <p className="text-sm text-slate-200">
                      <span className="font-medium text-slate-400">日期:</span> {financialData.latest_report.date}
                    </p>
                  )}

                  {/* Message */}
                  {financialData.latest_report.message && (
                    <p className="text-sm text-slate-300 bg-slate-800/50 rounded-lg p-3">
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
                        className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-blue-400 rounded-lg text-xs font-medium transition-colors border border-slate-600 text-center"
                      >
                        公司IR页面
                      </a>
                    )}
                    {financialData.latest_report.hkexnews_url && (
                      <a
                        href={financialData.latest_report.hkexnews_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-blue-400 rounded-lg text-xs font-medium transition-colors border border-slate-600 text-center"
                      >
                        披露易搜索
                      </a>
                    )}
                    {financialData.latest_report.cninfo_url && (
                      <a
                        href={financialData.latest_report.cninfo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-blue-400 rounded-lg text-xs font-medium transition-colors border border-slate-600 text-center"
                      >
                        巨潮资讯网
                      </a>
                    )}
                  </div>

                  {/* Suggestions */}
                  {financialData.latest_report.suggestions && financialData.latest_report.suggestions.length > 0 && (
                    <div className="mt-4 p-3 bg-slate-800/70 rounded-lg">
                      <p className="text-xs font-medium text-slate-400 mb-2">💡 使用提示:</p>
                      <ul className="text-xs text-slate-500 space-y-1">
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
                <p className="text-sm text-slate-400">
                  {financialData.latest_report.message || '暂无报告数据'}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FinancialTab;
