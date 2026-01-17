import type { AssetItem, PortfolioSummary } from '../types/personalFinance';

const API_BASE_URL = 'http://localhost:8000/api/personal-finance';

export interface BackendAssetItem {
  id?: string;
  symbol?: string;
  name?: string;
  type: string;
  market?: string;
  quantity: number;
  cost_basis?: number;
  current_price?: number;
  total_value?: number;
}

export interface BackendPortfolioSnapshot {
  assets: BackendAssetItem[];
  cash_balance: number;
  query?: string;
}

export interface PerformanceDataPoint {
  date: string;
  nav_user: number;
  nav_ai: number;
  nav_sh: number;
  nav_sz: number;
}

export interface PerformanceResponse {
  start_date: string;
  series: PerformanceDataPoint[];
}

// Mapper Functions
const toBackendAsset = (asset: AssetItem): BackendAssetItem => ({
  id: asset.id,
  symbol: asset.code,
  name: asset.name,
  type: asset.type,
  quantity: asset.quantity,
  cost_basis: asset.avgCost,
  current_price: asset.currentPrice,
  total_value: asset.totalValue,
});

const fromBackendAsset = (asset: BackendAssetItem): AssetItem => {
  const quantity = asset.quantity || 0;
  const currentPrice = asset.current_price || 0;
  const avgCost = asset.cost_basis || 0;
  const totalValue = quantity * currentPrice;
  const totalCost = quantity * avgCost;
  const pnl = totalValue - totalCost;
  const pnlRate = totalCost > 0 ? pnl / totalCost : 0;

  return {
    id: asset.id || Date.now().toString(), // Fallback ID if missing
    code: asset.symbol || '',
    name: asset.name || 'Unknown',
    type: (asset.type as any) || 'Other',
    quantity,
    avgCost,
    currentPrice,
    totalValue,
    totalCost,
    pnl,
    pnlRate,
  };
};

export const personalFinanceAPI = {
  getPortfolio: async (): Promise<{ assets: AssetItem[]; cash: number }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/portfolio`);
      if (!response.ok) {
        throw new Error('Failed to fetch portfolio');
      }
      const data: BackendPortfolioSnapshot = await response.json();
      return {
        assets: (data.assets || []).map(fromBackendAsset),
        cash: data.cash_balance || 0,
      };
    } catch (error) {
      console.error('Error fetching portfolio:', error);
      throw error;
    }
  },

  savePortfolio: async (assets: AssetItem[], cash: number): Promise<void> => {
    try {
      const snapshot: BackendPortfolioSnapshot = {
        assets: assets.map(toBackendAsset),
        cash_balance: cash,
      };
      
      const response = await fetch(`${API_BASE_URL}/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(snapshot),
      });

      if (!response.ok) {
        throw new Error('Failed to save portfolio');
      }
    } catch (error) {
      console.error('Error saving portfolio:', error);
      throw error;
    }
  },

  updatePrices: async (assets: AssetItem[]): Promise<{ [symbol: string]: { price: number; change_percent: number; update_time: string } }> => {
    try {
      const payload = {
        assets: assets.map(toBackendAsset)
      };
      
      const response = await fetch(`${API_BASE_URL}/update-prices`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to update prices');
      }
      const data = await response.json();
      return data.prices || {};
    } catch (error) {
      console.error('Error updating prices:', error);
      throw error;
    }
  },

  getPerformanceHistory: async (): Promise<PerformanceResponse> => {
    try {
      const response = await fetch(`${API_BASE_URL}/performance`);
      if (!response.ok) {
        throw new Error('Failed to fetch performance history');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching performance history:', error);
      throw error;
    }
  }
};
