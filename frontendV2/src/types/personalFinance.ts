export type AssetType = 'Cash' | 'Stock' | 'Fund' | 'Crypto' | 'Bond' | 'Other';

export interface AssetItem {
  id: string;
  code?: string; // 项目代码 (Symbol)
  name: string;
  type: AssetType;
  quantity: number;      // 持仓数量
  avgCost: number;       // 平均成本单价
  currentPrice: number;  // 当前市场单价 (模拟数据)
  totalValue: number;    // currentPrice * quantity
  totalCost: number;     // avgCost * quantity
  pnl: number;           // totalValue - totalCost
  pnlRate: number;       // pnl / totalCost
}

export interface PortfolioSummary {
  totalAssets: number;
  totalPnL: number;
  totalYieldRate: number;
  cashBalance: number;   // 现金余额
}

export type TransactionType = 'Buy' | 'Sell' | 'Deposit' | 'Withdraw' | 'Update';

export interface Transaction {
  id: string;
  date: string;
  type: TransactionType;
  assetId?: string;      // 关联资产 (充提时为空)
  assetName?: string;
  amount: number;        // 交易总金额
  price?: number;        // 交易单价
  quantity?: number;     // 交易数量
  description?: string;
}
