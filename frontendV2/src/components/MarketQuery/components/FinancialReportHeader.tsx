import React from 'react';
import { Search, BarChart2, AlertCircle, Loader2, Maximize2, Minimize2 } from 'lucide-react';

interface FinancialReportHeaderProps {
  financialSearchQuery: string;
  setFinancialSearchQuery: (query: string) => void;
  handleFinancialSearch: (e: React.FormEvent) => void;
  financialLoading: boolean;
  isFullScreen: boolean;
  setIsFullScreen: (isFullScreen: boolean) => void;
  error: string;
}

const FinancialReportHeader: React.FC<FinancialReportHeaderProps> = ({
  financialSearchQuery,
  setFinancialSearchQuery,
  handleFinancialSearch,
  financialLoading,
  isFullScreen,
  setIsFullScreen,
  error
}) => {
  return (
    <div className="flex-none mb-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-900/30 rounded-full flex items-center justify-center">
            <BarChart2 size={24} className="text-blue-500" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">智能财报分析</h2>
            <p className="text-sm text-slate-400">AI驱动的财报解读与原文对照</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <form onSubmit={handleFinancialSearch} className="flex gap-2 w-80 lg:w-96">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                value={financialSearchQuery}
                onChange={(e) => setFinancialSearchQuery(e.target.value)}
                placeholder="搜索公司 (例如: Tesla)"
                className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={financialLoading}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-70 transition-colors"
            >
              {financialLoading ? <Loader2 size={18} className="animate-spin" /> : '分析'}
            </button>
          </form>
          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            title={isFullScreen ? "退出全屏" : "全屏显示"}
          >
            {isFullScreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
          </button>
        </div>
      </div>
      
      {error && (
        <div className="p-3 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400 text-sm flex items-center gap-2">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
    </div>
  );
};

export default FinancialReportHeader;
