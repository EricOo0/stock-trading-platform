import React, { useState } from 'react';
import { TrendingUp, BarChart2, Search } from 'lucide-react';
import MarketTab from '../components/MarketQuery/MarketTab';
import FinancialTab from '../components/MarketQuery/FinancialTab';
import WebSearchTab from '../components/MarketQuery/WebSearchTab';

const MarketQueryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'market' | 'financial' | 'web'>('market');

  return (
    <div className="h-full flex flex-col gap-6 max-w-7xl mx-auto w-full p-6">
      {/* Page Title */}
      <div className="flex flex-col justify-center">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          市场分析
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          实时行情、财报分析、新闻搜索
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-slate-800 rounded-xl p-1 shadow-sm border border-slate-700">
        <div className="flex">
          <button
            onClick={() => setActiveTab('market')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors rounded-lg ${activeTab === 'market'
              ? 'text-blue-400 bg-slate-700'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <TrendingUp size={18} />
              市场行情
            </div>
          </button>
          <button
            onClick={() => setActiveTab('financial')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors rounded-lg ${activeTab === 'financial'
              ? 'text-blue-400 bg-slate-700'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <BarChart2 size={18} />
              财报分析
            </div>
          </button>
          <button
            onClick={() => setActiveTab('web')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors rounded-lg ${activeTab === 'web'
              ? 'text-blue-400 bg-slate-700'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Search size={18} />
              新闻搜索
            </div>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'market' && <MarketTab />}
      {activeTab === 'financial' && <FinancialTab />}
      {activeTab === 'web' && <WebSearchTab />}
    </div>
  );
};

export default MarketQueryPage;
