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

    // 获取市场智能前瞻 (流式)
    async fetchMarketOutlook(onChunk: (content: string) => void): Promise<void> {
        try {
            const response = await fetch(`${this.baseURL}/agent/market/outlook`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}) // Empty body for now
            });

            if (!response.ok) {
                throw new Error(`Failed to start analysis: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            if (!reader) return;

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                
                // Process complete JSON objects
                let boundary = buffer.indexOf('\n');
                while (boundary !== -1) {
                    const line = buffer.substring(0, boundary).trim();
                    buffer = buffer.substring(boundary + 1);
                    
                    if (line) {
                        try {
                            const data = JSON.parse(line);
                            if (data.type === 'agent_response') {
                                onChunk(data.content);
                            } else if (data.type === 'error') {
                                console.error('Stream error:', data.content);
                                onChunk(`\n\n**Error:** ${data.content}`);
                            }
                        } catch (e) {
                            console.warn('Failed to parse chunk:', line);
                        }
                    }
                    boundary = buffer.indexOf('\n');
                }
            }
        } catch (error) {
            console.error('Market outlook analysis failed:', error);
            onChunk('\n\n**Analysis failed due to network error.**');
        }
    }
}

export const marketService = new MarketAPIService();
