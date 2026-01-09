import React, { useEffect, useState } from 'react';
import { marketService, type SectorFlowData, type SectorStock } from '../../services/marketService';
import { Flame, Snowflake, Activity, ChevronDown, ChevronUp, HelpCircle, BarChart2, TrendingUp, Layers, Hash } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SectorItem: React.FC<{ 
    item: SectorFlowData; 
    index: number; 
    type: 'hot' | 'cold';
    sortBy: 'amount' | 'percent';
    onSortChange: (newSort: 'amount' | 'percent') => void;
    sectorType: 'industry' | 'concept';
}> = ({ item, index, type, sortBy, onSortChange, sectorType }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [stocks, setStocks] = useState<SectorStock[]>([]);
    const [loadingStocks, setLoadingStocks] = useState(false);

    // 当 sortBy 或 sectorType 变化且已展开时，重新加载数据
    // 注意：sectorType 变化会导致父组件重新渲染 SectorList，Item 可能会被销毁重建
    // 如果 Item 是根据数据列表渲染的，数据变了 Item 自然会重建。
    // 但如果只是 sortBy 变了，我们需要在这里监听。
    useEffect(() => {
        if (isOpen) {
            loadStocks();
        }
    }, [sortBy]);

    const loadStocks = async () => {
        setLoadingStocks(true);
        try {
            const data = await marketService.getSectorStocks(item.name, 3, sortBy, sectorType);
            setStocks(data);
        } catch (e) {
            console.error("Failed to load stocks", e);
        } finally {
            setLoadingStocks(false);
        }
    };

    const handleToggle = () => {
        if (!isOpen && stocks.length === 0) {
            loadStocks();
        }
        setIsOpen(!isOpen);
    };

    return (
        <div className="rounded-lg bg-slate-900/40 border border-slate-800/50 hover:bg-slate-800/60 hover:border-slate-700/50 transition-all overflow-hidden">
            <div 
                className="flex items-center justify-between p-3 cursor-pointer group"
                onClick={handleToggle}
            >
                <div className="flex items-center gap-3">
                    <div className="relative group/rank">
                         <span className={`flex items-center justify-center w-6 h-6 rounded text-xs font-bold ${
                            index === 0 
                                ? type === 'hot' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'
                                : 'bg-slate-800 text-slate-500'
                        }`}>
                            {item.rank}
                        </span>
                    </div>
                   
                    <div>
                        <div className="text-sm font-medium text-slate-200 group-hover:text-white flex items-center gap-2">
                            {item.name}
                            {isOpen ? <ChevronUp size={14} className="text-slate-500"/> : <ChevronDown size={14} className="text-slate-500 group-hover:text-slate-400"/>}
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-1">
                            {!isOpen && <span>龙头: {item.leading_stock}</span>}
                        </div>
                    </div>
                </div>

                <div className="text-right">
                    <div className={`text-sm font-mono font-medium ${
                        item.change_percent > 0 ? 'text-red-400' : 'text-green-400'
                    }`}>
                        {item.change_percent > 0 ? '+' : ''}{item.change_percent}%
                    </div>
                    <div className={`text-xs font-mono ${
                        type === 'hot' ? 'text-red-500/60' : 'text-green-500/60'
                    }`}>
                        {type === 'hot' ? '+' : ''}{item.net_flow.toFixed(2)}亿
                    </div>
                </div>
            </div>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="bg-slate-900/50 border-t border-slate-800/50"
                    >
                        <div className="flex items-center justify-between px-3 pt-2 pb-1">
                            <div className="text-xs text-slate-500">Top 3 领涨股</div>
                            <div className="flex bg-slate-800 rounded-md p-0.5">
                                <button 
                                    onClick={(e) => { e.stopPropagation(); onSortChange('amount'); }}
                                    className={`p-1 rounded ${sortBy === 'amount' ? 'bg-slate-700 text-blue-400' : 'text-slate-500 hover:text-slate-400'}`}
                                    title="按成交额排序"
                                >
                                    <BarChart2 size={12} />
                                </button>
                                <button 
                                    onClick={(e) => { e.stopPropagation(); onSortChange('percent'); }}
                                    className={`p-1 rounded ${sortBy === 'percent' ? 'bg-slate-700 text-blue-400' : 'text-slate-500 hover:text-slate-400'}`}
                                    title="按涨跌幅排序"
                                >
                                    <TrendingUp size={12} />
                                </button>
                            </div>
                        </div>

                        {loadingStocks ? (
                            <div className="p-4 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" />
                                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce delay-100" />
                                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce delay-200" />
                            </div>
                        ) : (
                            <div className="p-3 grid grid-cols-1 gap-2 pt-1">
                                {stocks.map((stock) => (
                                    <div key={stock.symbol} className="flex items-center justify-between text-xs px-2 py-1 rounded hover:bg-slate-800/50">
                                        <div className="flex flex-col">
                                            <span className="text-slate-300 font-medium">{stock.name}</span>
                                            <span className="text-slate-600 font-mono scale-90 origin-left">{stock.symbol}</span>
                                        </div>
                                        <div className="flex flex-col items-end">
                                            <span className="font-mono text-slate-300">{stock.price}</span>
                                            <span className={`font-mono ${stock.change_percent > 0 ? 'text-red-400' : 'text-green-400'}`}>
                                                {stock.change_percent > 0 ? '+' : ''}{stock.change_percent}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                                {stocks.length === 0 && <div className="text-center text-xs text-slate-600 py-2">无详情数据</div>}
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const SectorList: React.FC<{ 
    title: string; 
    icon: React.ReactNode; 
    data: SectorFlowData[]; 
    type: 'hot' | 'cold';
    sectorType: 'industry' | 'concept';
}> = ({ title, icon, data, type, sectorType }) => {
    const [sortBy, setSortBy] = useState<'amount' | 'percent'>('amount');

    return (
        <div className="flex-1 min-w-[300px]">
            <div className="flex items-center gap-2 mb-4 px-2 group cursor-help relative">
                {icon}
                <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</h3>
                <HelpCircle size={14} className="text-slate-600 group-hover:text-slate-500 transition-colors" />
                
                <div className="absolute left-0 top-8 z-10 w-64 p-3 bg-slate-800 border border-slate-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all text-xs text-slate-400 leading-relaxed pointer-events-none">
                    板块前面的数字代表<strong>资金流向排名</strong>。
                    <br/>
                    {type === 'hot' ? 'Rank 1 代表全市场资金净流入最多的板块。' : 'Rank 1 代表全市场资金净流出最多的板块。'}
                </div>
            </div>
            
            <div className="space-y-2">
                {data.map((item, index) => (
                    <SectorItem 
                        key={item.name} 
                        item={item} 
                        index={index} 
                        type={type} 
                        sortBy={sortBy}
                        onSortChange={setSortBy}
                        sectorType={sectorType}
                    />
                ))}
                
                {data.length === 0 && (
                    <div className="p-4 text-center text-slate-600 text-sm">
                        暂无数据
                    </div>
                )}
            </div>
        </div>
    );
};

export const SectorFlowCard: React.FC = () => {
    const [hotSectors, setHotSectors] = useState<SectorFlowData[]>([]);
    const [coldSectors, setColdSectors] = useState<SectorFlowData[]>([]);
    const [loading, setLoading] = useState(true);
    const [sectorType, setSectorType] = useState<'industry' | 'concept'>('industry');

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const [hot, cold] = await Promise.all([
                    marketService.getSectorFlow('hot', 5, sectorType),
                    marketService.getSectorFlow('cold', 5, sectorType)
                ]);
                setHotSectors(hot);
                setColdSectors(cold);
            } catch (e) {
                console.error("Failed to load sector data", e);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [sectorType]);

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="w-full bg-slate-800/30 backdrop-blur-sm border border-slate-700/30 rounded-2xl p-6 mb-8"
        >
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Activity className="text-blue-400" size={20} />
                    <h2 className="text-lg font-semibold text-white">Market Radar · 资金流向</h2>
                </div>

                <div className="flex bg-slate-900/50 border border-slate-700/50 rounded-lg p-1">
                    <button
                        onClick={() => setSectorType('industry')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                            sectorType === 'industry' 
                                ? 'bg-slate-700 text-white shadow-sm' 
                                : 'text-slate-400 hover:text-slate-300'
                        }`}
                    >
                        <Layers size={14} />
                        行业板块
                    </button>
                    <button
                        onClick={() => setSectorType('concept')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                            sectorType === 'concept' 
                                ? 'bg-slate-700 text-white shadow-sm' 
                                : 'text-slate-400 hover:text-slate-300'
                        }`}
                    >
                        <Hash size={14} />
                        概念板块
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="w-full h-48 rounded-xl bg-slate-800/30 animate-pulse border border-slate-700/30 mb-8" />
            ) : (
                <div className="flex flex-col md:flex-row gap-8">
                    <SectorList 
                        title="资金净流入 Top 5" 
                        icon={<Flame size={16} className="text-red-500" />}
                        data={hotSectors}
                        type="hot"
                        sectorType={sectorType}
                    />
                    <div className="hidden md:block w-px bg-gradient-to-b from-transparent via-slate-700 to-transparent" />
                    <SectorList 
                        title="资金净流出 Top 5" 
                        icon={<Snowflake size={16} className="text-blue-400" />}
                        data={coldSectors}
                        type="cold"
                        sectorType={sectorType}
                    />
                </div>
            )}
        </motion.div>
    );
};
