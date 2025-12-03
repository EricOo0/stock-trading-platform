import React from 'react';
import { Layout } from './components/Layout';
import { MarketQueryPage, HomePage, StockSearchPage } from './pages';
import TechnicalAnalysisPage from './pages/TechnicalAnalysisPage';
import MacroDataPage from './pages/MacroDataPage';

import CouncilRoom from './components/Council/CouncilRoom';

function App() {
  const [activeTab, setActiveTab] = React.useState('home');

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
  };

  const getPageTitle = (tab: string) => {
    switch (tab) {
      case 'home':
        return '首页';
      case 'council':
        return 'AI 顾问团';
      case 'test':
        return '测试页面';
      case 'debug':
        return '调试页面';
      case 'market-query':
        return '行情查询';
      case 'technical-analysis':
        return '技术分析';
      case 'stock-search':
        return '股票搜索';
      case 'watchlist':
        return '自选股票';
      case 'macro-data':
        return '宏观数据';
      default:
        return '行情系统';
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <HomePage onNavigate={handleTabChange} />;
      case 'council':
        return <CouncilRoom />;
      case 'market-query':
        return <MarketQueryPage />;
      case 'technical-analysis':
        return <TechnicalAnalysisPage />;
      case 'stock-search':
        return <StockSearchPage />;
      case 'watchlist':
        return (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">自选股票</h2>
              <p className="text-gray-600">功能开发中...</p>
            </div>
          </div>
        );
      case 'macro-data':
        return <MacroDataPage />;
      default:
        return <HomePage onNavigate={handleTabChange} />;
    }
  };

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={handleTabChange}
      title={getPageTitle(activeTab)}
    >
      {renderContent()}
    </Layout>
  );
}

export default App;
