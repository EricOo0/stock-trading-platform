/**
 * 财务指标相关的TypeScript类型定义
 */

// 收入端指标
export interface RevenueIndicators {
    revenue_yoy: number;           // 营业收入YoY
    core_revenue_ratio: number | null;  // 核心营收占比
    cash_to_revenue: number;       // 现金收入比
}

// 利润端指标
export interface ProfitIndicators {
    non_recurring_eps?: number;    // 扣非归母净利(每股)
    non_recurring_net_profit?: number;  // 扣非归母净利(总额)
    gross_margin: number;          // 经营毛利率
    net_margin: number;            // 核心净利率
}

// 现金流指标
export interface CashflowIndicators {
    ocf_to_net_profit: number;     // 经营现金流/归母净利
    free_cash_flow: number | null; // 自由现金流FCF
}

// 负债端指标
export interface DebtIndicators {
    asset_liability_ratio: number; // 资产负债率
    current_ratio: number | null;  // 流动比率
}

// 股东回报指标
export interface ShareholderIndicators {
    dividend_yield: number;        // 股息率
    roe: number;                   // ROE(净资产收益率)
}

// 历史数据点
export interface HistoricalDataPoint {
    date: string;
    roe: number;
    gross_margin: number;
    net_margin: number;
    asset_liability_ratio?: number;
}

// 所有财务指标
export interface FinancialIndicators {
    revenue: RevenueIndicators;
    profit: ProfitIndicators;
    cashflow: CashflowIndicators;
    debt: DebtIndicators;
    shareholder_return: ShareholderIndicators;
    history: HistoricalDataPoint[];
}

// API响应
export interface FinancialIndicatorsResponse {
    status: string;
    symbol: string;
    market: string;
    data_source: string;
    indicators: FinancialIndicators;
    timestamp: string;
}

// API请求参数
export interface FinancialIndicatorsRequest {
    symbol: string;
    years?: number;
    use_cache?: boolean;
}

// 错误响应
export interface FinancialIndicatorsError {
    status: 'error';
    message: string;
    symbol?: string;
}
