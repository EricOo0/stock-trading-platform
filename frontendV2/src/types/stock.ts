export interface StockData {
    timestamp: string;
    date?: string; // Add support for date field
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ma5?: number;
    ma10?: number;
    ma20?: number;
    ma30?: number;
    ma60?: number;
    boll_upper?: number;
    boll_mid?: number;
    boll_lower?: number;
    macd_dif?: number;
    macd_dea?: number;
    macd_bar?: number;
    rsi14?: number;
    kdj_k?: number;
    kdj_d?: number;
    kdj_j?: number;
    [key: string]: number | string | undefined | null | object;
}
