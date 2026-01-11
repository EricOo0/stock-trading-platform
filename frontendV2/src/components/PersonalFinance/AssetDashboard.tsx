import React from 'react';
import { Wallet, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import type { PortfolioSummary } from '../../types/personalFinance';

interface AssetDashboardProps {
  summary: PortfolioSummary;
}

const AssetDashboard: React.FC<AssetDashboardProps> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      {/* Total Assets Card */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <Wallet size={24} />
          </div>
          <div>
            <div className="text-slate-400 text-sm">总资产 (Total Assets)</div>
            <div className="text-2xl font-bold text-white tracking-tight">
              ¥{summary.totalAssets.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>
        <div className="h-1 w-full bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500 w-full" />
        </div>
      </div>

      {/* Total P&L Card */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center gap-4 mb-4">
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${summary.totalPnL >= 0 ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
            {summary.totalPnL >= 0 ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
          </div>
          <div>
            <div className="text-slate-400 text-sm">总盈亏 (Total P&L)</div>
            <div className={`text-2xl font-bold tracking-tight ${summary.totalPnL >= 0 ? 'text-red-400' : 'text-green-400'}`}>
              {summary.totalPnL >= 0 ? '+' : ''}¥{summary.totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">收益率</span>
          <span className={`font-mono font-medium ${summary.totalYieldRate >= 0 ? 'text-red-400' : 'text-green-400'}`}>
            {(summary.totalYieldRate * 100).toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Cash Balance Card */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
            <DollarSign size={24} />
          </div>
          <div>
            <div className="text-slate-400 text-sm">现金余额 (Cash)</div>
            <div className="text-2xl font-bold text-white tracking-tight">
              ¥{summary.cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">可用资金占比</span>
          <span className="text-blue-400 font-mono">
            {summary.totalAssets > 0 
              ? ((summary.cashBalance / summary.totalAssets) * 100).toFixed(1)
              : 0}%
          </span>
        </div>
      </div>
    </div>
  );
};

export default AssetDashboard;
