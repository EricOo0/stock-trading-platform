
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    TrendingUp,
    Search,
    BarChart2,
    FileText,
    Sparkles,
    Zap
} from 'lucide-react';

import MarketQueryPage from './MarketQueryPage';
import InspiringPage from './InspiringPage';
import NewsSentimentPage from './NewsSentimentPage';
import TechnicalAnalysisPage from './TechnicalAnalysisPage';
import FinancialAnalysisPage from './FinancialAnalysisPage';
import StockSimulationPage from './StockSimulationPage';

// Import background image (assuming Vite handles this)
import bgImage from '../assets/stock_analysis_bg.png';

export default function StockAnalysisPage() {
    const [activeTab, setActiveTab] = useState('market-query');

    // Global Symbol State
    const [globalInput, setGlobalInput] = useState('');
    const [sharedSymbol, setSharedSymbol] = useState('');
    const [searchTrigger, setSearchTrigger] = useState(0);

    const handleGlobalSearch = () => {
        if (globalInput.trim()) {
            const sym = globalInput.trim().toUpperCase();
            setSharedSymbol(sym);
            setSearchTrigger(Date.now());
        }
    };

    const tabs = [
        { id: 'market-query', label: '行情复盘', icon: <TrendingUp size={16} /> },
        { id: 'technical-analysis', label: '技术分析', icon: <BarChart2 size={16} /> },
        { id: 'inspiring', label: '深度投研', icon: <Sparkles size={16} /> },
        { id: 'news-sentiment', label: '消息面分析', icon: <Search size={16} /> },
        { id: 'financial-analysis', label: '财报分析', icon: <FileText size={16} /> },
        { id: 'stock-simulation', label: '模拟回测', icon: <Zap size={16} /> },
    ];

    const renderContent = () => {
        const commonProps = {
            sharedSymbol,
            searchTrigger,
            isActive: false // Default false, overridden below
        };

        const getProps = (id: string) => ({
            ...commonProps,
            isActive: activeTab === id
        });

        switch (activeTab) {
            case 'market-query':
                return <MarketQueryPage {...getProps('market-query')} />;
            case 'inspiring':
                return <InspiringPage />;
            case 'news-sentiment':
                return <NewsSentimentPage {...getProps('news-sentiment')} />;
            case 'technical-analysis':
                return <TechnicalAnalysisPage {...getProps('technical-analysis')} />;
            case 'financial-analysis':
                return <FinancialAnalysisPage {...getProps('financial-analysis')} />;
            case 'stock-simulation':
                return <StockSimulationPage />;
            default:
                return <MarketQueryPage {...getProps('market-query')} />;
        }
    };

    return (
        <div className="relative w-full h-screen overflow-hidden text-gray-100 font-sans">
            {/* Dynamic Background */}
            <div
                className="absolute inset-0 z-0 bg-cover bg-center pointer-events-none"
                style={{
                    backgroundImage: `url(${bgImage})`,
                    filter: 'brightness(0.6) contrast(1.1)'
                }}
            />
            {/* Glassmorphism Overlay */}
            <div className="absolute inset-0 z-0 bg-slate-900/60 backdrop-blur-[2px]" />

            {/* Main Content Container */}
            <div className="relative z-10 flex flex-col h-full bg-transparent">

                {/* Header Section */}
                <header className="flex-none px-6 py-4 flex items-center justify-between border-b border-white/10 bg-white/5 backdrop-blur-md shadow-lg gap-8">
                    <div className="flex items-center gap-3 min-w-fit">
                        {/* Title can be here if needed, but tabs are primary nav */}
                        <div className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent transform hover:scale-105 transition-transform cursor-default">
                            个股分析
                        </div>
                    </div>

                    {/* Navigation Tabs (Centered-ish) */}
                    <nav className="flex items-center gap-1 bg-black/20 p-1 rounded-xl shadow-inner border border-white/5 overflow-x-auto custom-scrollbar">
                        {tabs.map((tab) => {
                            const isActive = activeTab === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`
                    relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 flex items-center gap-2 whitespace-nowrap
                    ${isActive ? 'text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'}
                  `}
                                >
                                    {isActive && (
                                        <motion.div
                                            layoutId="activeTabBg"
                                            className="absolute inset-0 bg-blue-600/80 rounded-lg shadow-[0_0_15px_rgba(37,99,235,0.4)]"
                                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                        />
                                    )}
                                    <span className="relative z-10 flex items-center gap-2">
                                        {tab.icon}
                                        {tab.label}
                                    </span>
                                </button>
                            );
                        })}
                    </nav>

                    {/* Global Search Input */}
                    <div className="flex items-center gap-2 min-w-fit">
                        <div className="relative group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-400 transition-colors" size={16} />
                            <input
                                type="text"
                                value={globalInput}
                                onChange={(e) => setGlobalInput(e.target.value.toUpperCase())}
                                onKeyDown={(e) => e.key === 'Enter' && handleGlobalSearch()}
                                className="bg-slate-900/80 border border-slate-700/50 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 w-48 shadow-inner transition-all hover:bg-slate-900"
                                placeholder="输入股票代码..."
                            />
                        </div>
                        <button
                            onClick={handleGlobalSearch}
                            className="bg-blue-600 hover:bg-blue-500 text-white p-2.5 rounded-lg transition-all shadow-lg shadow-blue-500/20 active:scale-95 flex items-center justify-center"
                            title="Start Analysis"
                        >
                            <Search size={20} />
                        </button>
                    </div>
                </header>

                {/* Page Content Area */}
                <main className="flex-1 overflow-hidden relative">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                            className="w-full h-full overflow-y-auto custom-scrollbar"
                        >
                            {/* 
                  Container for content. 
                  We intentionally use transparent backgrounds here 
                  so the nebula background shows through where possible.
               */}
                            <div className="min-h-full p-4">
                                {renderContent()}
                            </div>
                        </motion.div>
                    </AnimatePresence>
                </main>
            </div>

            {/* Global Styles for this page */}
            <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
        </div>
    );
}
