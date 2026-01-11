import React, { useState, useEffect, useMemo, useCallback } from 'react';
import type { AssetItem, PortfolioSummary, Transaction } from '../types/personalFinance';
import AssetDashboard from '../components/PersonalFinance/AssetDashboard';
import AssetAllocationChart from '../components/PersonalFinance/AssetAllocationChart';
import AssetTable from '../components/PersonalFinance/AssetTable';
import AssetOperationModal from '../components/PersonalFinance/AssetOperationModal';
import FinanceAssistantWidget from '../components/PersonalFinance/FinanceAssistantWidget';
import { Edit, RefreshCw } from 'lucide-react';
import { personalFinanceAPI } from '../services/personalFinanceAPI';

const PersonalFinancePage: React.FC = () => {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [cash, setCash] = useState<number>(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<AssetItem | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 加载数据
  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        setIsLoading(true);
        const data = await personalFinanceAPI.getPortfolio();
        setAssets(data.assets);
        setCash(data.cash);
      } catch (error) {
        console.error('Failed to load portfolio:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadPortfolio();
  }, []);

  // 辅助：保存数据到后端
  const saveData = async (newAssets: AssetItem[], newCash: number) => {
    try {
      await personalFinanceAPI.savePortfolio(newAssets, newCash);
    } catch (error) {
      console.error('Failed to save portfolio:', error);
      // 可选：添加错误提示
    }
  };

  // 实时计算汇总信息
  const summary: PortfolioSummary = useMemo(() => {
    const assetsValue = assets.reduce((sum, asset) => sum + asset.totalValue, 0);
    const totalAssets = assetsValue + cash;
    const totalCost = assets.reduce((sum, asset) => sum + asset.totalCost, 0);
    const totalPnL = assets.reduce((sum, asset) => sum + asset.pnl, 0);
    const totalYieldRate = totalCost > 0 ? totalPnL / totalCost : 0;

    return {
      totalAssets,
      totalPnL,
      totalYieldRate,
      cashBalance: cash,
    };
  }, [assets, cash]);

  // 处理行内修改 (Name, Code, CurrentPrice)
  const handleUpdateAsset = async (id: string, field: keyof AssetItem, value: string | number) => {
    const newAssets = assets.map(asset => {
      if (asset.id === id) {
        if (field === 'name') {
          return { ...asset, name: value as string };
        } else if (field === 'code') {
          return { ...asset, code: value as string };
        } else if (field === 'currentPrice') {
          const newPrice = Number(value);
          const newTotalValue = newPrice * asset.quantity;
          const newPnl = newTotalValue - asset.totalCost;
          const newPnlRate = asset.totalCost > 0 ? newPnl / asset.totalCost : 0;
          return {
            ...asset,
            currentPrice: newPrice,
            totalValue: newTotalValue,
            pnl: newPnl,
            pnlRate: newPnlRate
          };
        }
      }
      return asset;
    });
    setAssets(newAssets);
    await saveData(newAssets, cash);
  };

  // 处理删除资产（清仓逻辑）
  const handleDeleteAsset = (asset: AssetItem) => {
    if (window.confirm(`确定要清仓卖出 ${asset.name} 吗？将按当前现价 ¥${asset.currentPrice} 全部卖出。`)) {
        // eslint-disable-next-line react-hooks/purity
      const txId = Date.now().toString();
      handleTransaction({
        id: txId,
        date: new Date().toISOString(),
        type: 'Sell',
        assetName: asset.name,
        amount: asset.quantity * asset.currentPrice,
        price: asset.currentPrice,
        quantity: asset.quantity
      });
    }
  };

  // 核心交易处理逻辑
  const handleTransaction = async (tx: Transaction) => {
    console.log('Processing Transaction:', tx);
    
    let nextCash = cash;
    let nextAssets = [...assets];

    if (tx.type === 'Deposit') {
      nextCash += tx.amount;
    } else if (tx.type === 'Withdraw') {
      if (nextCash >= tx.amount) {
        nextCash -= tx.amount;
      } else {
        alert('现金不足');
        return;
      }
    } else if (tx.type === 'Buy') {
      if (nextCash < tx.amount) {
        alert('现金不足');
        return;
      }
      nextCash -= tx.amount;
      
      const existingIndex = nextAssets.findIndex(a => a.name === tx.assetName); // 简化逻辑：按名称匹配
      if (existingIndex >= 0) {
        // 更新已有资产 (加权平均成本)
        const existing = nextAssets[existingIndex];
        const newQuantity = existing.quantity + (tx.quantity || 0);
        const newTotalCost = existing.totalCost + tx.amount;
        const newAvgCost = newTotalCost / newQuantity;
        
        const updatedAsset: AssetItem = {
          ...existing,
          quantity: newQuantity,
          avgCost: newAvgCost,
          totalCost: newTotalCost,
          totalValue: existing.currentPrice * newQuantity,
          pnl: (existing.currentPrice * newQuantity) - newTotalCost,
          pnlRate: ((existing.currentPrice * newQuantity) - newTotalCost) / newTotalCost
        };
        nextAssets[existingIndex] = updatedAsset;
      } else {
        // 新增资产
        const newAsset: AssetItem = {
          id: Date.now().toString(),
          name: tx.assetName || 'Unknown',
          type: 'Stock', 
          quantity: tx.quantity || 0,
          avgCost: tx.price || 0,
          currentPrice: tx.price || 0, 
          totalCost: tx.amount,
          totalValue: tx.amount,
          pnl: 0,
          pnlRate: 0,
          code: tx.assetName || '' // 暂用名称作为代码，实际应分开
        };
        nextAssets.push(newAsset);
      }
    } else if (tx.type === 'Sell') {
      const existingIndex = nextAssets.findIndex(a => a.name === tx.assetName);
      if (existingIndex === -1) {
        alert('未持有该资产');
        return;
      }
      
      const existing = nextAssets[existingIndex];
      if (existing.quantity < (tx.quantity || 0)) {
        alert('持仓不足');
        return;
      }

      nextCash += tx.amount;
      
      const sellQty = tx.quantity || 0;
      const remainingQty = existing.quantity - sellQty;
      
      if (remainingQty <= 0) {
        // 全部卖出
        nextAssets = nextAssets.filter((_, i) => i !== existingIndex);
      } else {
        // 部分卖出
        const costBasisReduced = existing.avgCost * sellQty;
        const newTotalCost = existing.totalCost - costBasisReduced;
        
        const updatedAsset: AssetItem = {
          ...existing,
          quantity: remainingQty,
          totalCost: newTotalCost,
          totalValue: existing.currentPrice * remainingQty,
          pnl: (existing.currentPrice * remainingQty) - newTotalCost,
          pnlRate: ((existing.currentPrice * remainingQty) - newTotalCost) / newTotalCost
        };
        nextAssets[existingIndex] = updatedAsset;
      }
    } else if (tx.type === 'Update') {
      const existingIndex = nextAssets.findIndex(a => a.name === tx.assetName);
      if (existingIndex === -1) {
        alert('未找到该资产');
        return;
      }

      const existing = nextAssets[existingIndex];
      const newQuantity = tx.quantity || 0;
      const newAvgCost = tx.price || 0; 
      const newTotalCost = newAvgCost * newQuantity;
      
      const updatedAsset: AssetItem = {
        ...existing,
        quantity: newQuantity,
        avgCost: newAvgCost,
        totalCost: newTotalCost,
        totalValue: existing.currentPrice * newQuantity,
        pnl: (existing.currentPrice * newQuantity) - newTotalCost,
        pnlRate: newTotalCost > 0 ? ((existing.currentPrice * newQuantity) - newTotalCost) / newTotalCost : 0
      };
      
      nextAssets[existingIndex] = updatedAsset;
    }

    setAssets(nextAssets);
    setCash(nextCash);
    await saveData(nextAssets, nextCash);
  };

  // 刷新逻辑 - 调用后端API更新价格
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
        const prices = await personalFinanceAPI.updatePrices(assets);
        
        // Update local assets with new prices
        const updatedAssets = assets.map(asset => {
            const code = asset.code || asset.name; // Fallback
            // Note: backend uses 'symbol', frontend uses 'code'
            // We need to match by symbol/code
            
            // Try to find by code (symbol)
            let update = prices[code];
            // If not found, maybe try name? (Unlikely to work for API but safe fallback)
            
            if (update) {
                const newPrice = update.price;
                const newTotalValue = newPrice * asset.quantity;
                const newPnl = newTotalValue - asset.totalCost;
                const newPnlRate = asset.totalCost > 0 ? newPnl / asset.totalCost : 0;
                
                return {
                    ...asset,
                    currentPrice: newPrice,
                    totalValue: newTotalValue,
                    pnl: newPnl,
                    pnlRate: newPnlRate
                };
            }
            return asset;
        });
        
        setAssets(updatedAssets);
        await saveData(updatedAssets, cash);
        
    } catch (error) {
        console.error("Refresh failed:", error);
        alert('更新价格失败，请稍后重试');
    } finally {
        setIsRefreshing(false);
    }
  };

  const handleOpenModal = (asset?: AssetItem) => {
    setSelectedAsset(asset || null);
    setIsModalOpen(true);
  };

  if (isLoading) {
    return (
        <div className="p-6 text-white min-h-screen bg-slate-900 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <RefreshCw size={32} className="animate-spin text-blue-500" />
                <p className="text-slate-400">正在加载资产数据...</p>
            </div>
        </div>
    );
  }

  return (
    <div className="p-6 text-white min-h-screen bg-slate-900">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <span>私人理财经理</span>
          <span className="text-xs font-normal text-slate-400 bg-slate-800 px-2 py-1 rounded">Beta</span>
        </h1>
        <div className="flex gap-3">
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`
              flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors font-medium border border-slate-700
              ${isRefreshing ? 'opacity-70 cursor-not-allowed' : ''}
            `}
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            <span>{isRefreshing ? '更新中...' : '更新收益'}</span>
          </button>
          
          <button 
            onClick={() => handleOpenModal()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium shadow-lg shadow-blue-500/20"
          >
            <Edit size={16} />
            <span>资产操作 (Edit)</span>
          </button>
        </div>
      </div>
      
      {/* 资产仪表盘 */}
      <AssetDashboard summary={summary} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* 左侧：资产分布图 */}
        <div className="lg:col-span-1 h-[400px]">
          <AssetAllocationChart assets={assets} cash={cash} />
        </div>
        
        {/* 右侧：表格 */}
        <div className="lg:col-span-2 space-y-6">
           <AssetTable 
             assets={assets} 
             onEdit={handleOpenModal} 
             onUpdateAsset={handleUpdateAsset} 
             onDelete={handleDeleteAsset}
           />
        </div>
      </div>

      <AssetOperationModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleTransaction}
        currentAssets={assets}
        initialAsset={selectedAsset}
      />

      {/* 悬浮助手 */}
      <FinanceAssistantWidget assets={assets} cash={cash} />
      
    </div>
  );
};

export default PersonalFinancePage;
