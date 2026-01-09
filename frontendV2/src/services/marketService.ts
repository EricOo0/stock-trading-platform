// 市场综合服务层
export interface SectorFlowData {
    rank: number;
    name: string;
    change_percent: number;
    net_flow: number; // 单位：万
    leading_stock: string;
}

export interface SectorResponse {
    status: string;
    type: string;
    data: SectorFlowData[];
    timestamp: string;
}

export interface SectorStock {
    symbol: string;
    name: string;
    price: number;
    change_percent: number;
    volume: number;
    amount: number;
}

export interface SectorDetailsResponse {
    status: string;
    data: {
        sector_name: string;
        stocks: SectorStock[];
    };
    timestamp: string;
}

class MarketAPIService {
    private baseURL = 'http://localhost:8000/api';

    // 获取板块资金流向
    async getSectorFlow(type: 'hot' | 'cold' = 'hot', limit: number = 5, sectorType: 'industry' | 'concept' = 'industry'): Promise<SectorFlowData[]> {
        try {
            const response = await fetch(`${this.baseURL}/market/sectors/flow?type=${type}&limit=${limit}&sector_type=${sectorType}`);
            if (!response.ok) {
                console.warn(`Sector flow API error: ${response.status}`);
                return [];
            }
            const result: SectorResponse = await response.json();
            if (result.status === 'success') {
                return result.data;
            }
            return [];
        } catch (error) {
            console.error('Failed to fetch sector flow:', error);
            return [];
        }
    }

    // 获取板块龙头股详情
    async getSectorStocks(sectorName: string, limit: number = 5, sortBy: 'amount' | 'percent' = 'amount', sectorType: 'industry' | 'concept' = 'industry'): Promise<SectorStock[]> {
        try {
            // URL encode sector name just in case
            const encodedName = encodeURIComponent(sectorName);
            const response = await fetch(`${this.baseURL}/market/sectors/${encodedName}/stocks?limit=${limit}&sort_by=${sortBy}&sector_type=${sectorType}`);
            
            if (!response.ok) {
                console.warn(`Sector stocks API error: ${response.status}`);
                return [];
            }
            const result: SectorDetailsResponse = await response.json();
            if (result.status === 'success' && result.data && result.data.stocks) {
                return result.data.stocks;
            }
            return [];
        } catch (error) {
            console.error(`Failed to fetch stocks for sector ${sectorName}:`, error);
            return [];
        }
    }
}

export const marketService = new MarketAPIService();
