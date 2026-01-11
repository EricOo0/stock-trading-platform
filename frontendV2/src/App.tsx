import React from 'react';
import { Layout } from './components/Layout';
import { MarketQueryPage, HomePage, StockSearchPage, InspiringPage, StockAnalysisPage } from './pages';
import TechnicalAnalysisPage from './pages/TechnicalAnalysisPage';
import MacroDataPage from './pages/MacroDataPage';
import FinancialAnalysisPage from './pages/FinancialAnalysisPage';
import MemoryVisualizationPage from './pages/MemoryVisualizationPage';
import StockSimulationPage from './pages/StockSimulationPage';
import NewsSentimentPage from './pages/NewsSentimentPage';
import PersonalFinancePage from './pages/PersonalFinancePage';
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
      case 'stock-analysis':
        return '个股分析';
      case 'council':
        return 'AI 顾问团';
      case 'inspiring':
        return '深度投研';
      case 'stock-simulation':
        return '股票模拟回测';
      case 'news-sentiment':
        return '消息面分析';
      case 'test':
        return '测试页面';
      case 'debug':
        return '调试页面';
      case 'market-query':
        return '行情查询';
      case 'financial-analysis':
        return '财报分析';
      case 'technical-analysis':
        return '技术分析';
      case 'stock-search':
        return '股票搜索';
      case 'watchlist':
        return '自选股票';
      case 'macro-data':
        return '宏观数据';
      case 'personal-finance':
        return '私人理财经理';
      case 'memory-viz':
        return '记忆可视化';
      default:
        return '行情系统';
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <HomePage onNavigate={handleTabChange} />;
      case 'stock-analysis':
        return <StockAnalysisPage />;
      case 'council':
        return <CouncilRoom />;
      case 'inspiring':
        return <InspiringPage />;
      case 'stock-simulation':
        return <StockSimulationPage />;
      case 'news-sentiment':
        return <NewsSentimentPage />;
      case 'market-query':
        return <MarketQueryPage />;
      case 'financial-analysis':
        return <FinancialAnalysisPage />;
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
      case 'personal-finance':
        return <PersonalFinancePage />;
      case 'memory-viz':
        return <MemoryVisualizationPage />;
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
