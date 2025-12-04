export interface FinancialIndicator {
    [key: string]: number | string | null;
}

export interface RevenueIndicators {
    revenue_yoy: number;
    core_revenue_ratio: number | null;
    cash_to_revenue: number;
}

export interface ProfitIndicators {
    non_recurring_eps?: number;
    non_recurring_net_profit?: number;
    gross_margin: number;
    net_margin: number;
}

export interface CashFlowIndicators {
    ocf_to_net_profit: number;
    free_cash_flow: number | null;
}

export interface DebtIndicators {
    asset_liability_ratio: number;
    current_ratio: number | null;
}

export interface ShareholderIndicators {
    dividend_yield: number;
    roe: number;
}

export interface HistoryItem {
    date: string;
    roe: number;
    gross_margin: number;
    net_margin: number;
    asset_liability_ratio?: number;
}

export interface FinancialIndicatorsData {
    revenue: RevenueIndicators;
    profit: ProfitIndicators;
    cashflow: CashFlowIndicators;
    debt: DebtIndicators;
    shareholder_return: ShareholderIndicators;
    history: HistoryItem[];
}

export interface FinancialIndicatorsResponse {
    status: string;
    symbol: string;
    market: string;
    data_source: string;
    indicators: FinancialIndicatorsData;
    timestamp: string;
    message?: string;
}
