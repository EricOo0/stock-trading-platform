// API服务层 - 连接后端market_data_tool
export interface StockData {
  symbol: string;
  name: string;
  current_price: number;
  open_price: number;
  high_price: number;
  low_price: number;
  previous_close: number;
  change_amount: number;
  change_percent: number;
  volume: number;
  turnover: number;
  timestamp: string;
  market: string;
  currency: string;
  status: string;
}

export interface MarketResponse {
  status: 'success' | 'error' | 'partial';
  symbol: string;
  data?: StockData;
  message?: string;
  timestamp: string;
  data_source: string;
  cache_hit: boolean;
  response_time_ms: number;
}

class StockAPIService {
  private baseURL = 'http://localhost:8000/api'; // 后端API地址

  // 调用后端market_data_tool技能
  async searchStock(query: string): Promise<MarketResponse> {
    try {
      console.log(`开始调用真实API搜索: ${query}`);
      // 调用真实的后端API
      const response = await fetch(`${this.baseURL}/market-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query
        })
      });

      console.log(`API响应状态: ${response.status}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('API返回数据:', result);

      // 转换格式以匹配我们的接口
      if (result.status === 'success' && result.data) {
        console.log('搜索成功，返回数据');
        return {
          status: 'success',
          symbol: result.symbol,
          data: result.data,
          timestamp: result.timestamp || new Date().toISOString(),
          data_source: 'real',
          cache_hit: result.cache_hit || false,
          response_time_ms: result.response_time_ms || 0
        };
      } else {
        console.log('搜索失败，返回错误:', result.message);
        return {
          status: 'error',
          symbol: query,
          message: result.message || '查询失败',
          timestamp: new Date().toISOString(),
          data_source: 'real',
          cache_hit: false,
          response_time_ms: 0
        };
      }
    } catch (error) {
      console.error('真实API调用失败:', error);
      // 如果真实API失败，返回错误状态而不是模拟数据
      return {
        status: 'error',
        symbol: query,
        message: '服务暂时不可用，请稍后重试',
        timestamp: new Date().toISOString(),
        data_source: 'none',
        cache_hit: false,
        response_time_ms: 0
      };
    }
  }



  // 获取历史K线数据（仅使用真实数据，默认30天）
  async getHistoricalData(symbol: string, period: string = '30d', count: number = 30): Promise<any[]> {
    try {
      console.log(`开始获取历史数据: ${symbol}, 周期: ${period}, 数量: ${count}`);

      const response = await fetch(`${this.baseURL}/market/historical/${symbol}?period=${period}&count=${count}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      console.log(`历史数据API响应状态: ${response.status}`);

      if (!response.ok) {
        console.warn(`历史数据API返回错误状态: ${response.status}`);
        return []; // 返回空数组，不使用模拟数据
      }

      const result = await response.json();
      console.log('历史数据API返回:', result);

      if (result.status === 'success' && result.data && Array.isArray(result.data) && result.data.length > 0) {
        // 转换数据格式以匹配前端需求
        const historicalData = result.data.map((candle: any) => {
          try {
            // 验证时间戳
            if (!candle.timestamp) return null;
            const dateObj = new Date(candle.timestamp);
            if (isNaN(dateObj.getTime())) return null;

            return {
              // 使用 YYYY-MM-DD 字符串格式，启用 Business Day 模式 (自动跳过周末)
              time: dateObj.toISOString().split('T')[0],
              open: Number(candle.open),
              high: Number(candle.high),
              low: Number(candle.low),
              close: Number(candle.close),
              volume: Number(candle.volume),
              date: dateObj.toISOString().split('T')[0],
              data_source: 'real'
            };
          } catch (e) {
            console.warn('Skipping invalid candle data:', candle, e);
            return null;
          }
        }).filter((item: any) => item !== null); // 过滤掉无效数据

        console.log(`成功获取 ${historicalData.length} 条真实历史数据`);
        return historicalData;
      } else {
        console.warn('历史数据API返回空数据或格式错误');
        return []; // 返回空数组，不使用模拟数据
      }
    } catch (error) {
      console.error('获取历史数据失败:', error);
      return []; // 返回空数组，不使用模拟数据
    }
  }

  // 批量搜索股票
  async searchMultipleStocks(queries: string[]): Promise<MarketResponse[]> {
    const results = await Promise.all(
      queries.map(query => this.searchStock(query))
    );
    return results;
  }

  // 获取热门股票（用于初始化展示）
  async getHotStocks(): Promise<StockData[]> {
    try {
      // 调用真实的后端API获取热门股票
      const response = await fetch(`${this.baseURL}/market-data/hot`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.status === 'success' && result.data) {
        return result.data;
      } else {
        console.warn('获取热门股票失败');
        return [];
      }
    } catch (error) {
      console.error('获取热门股票失败:', error);
      return [];
    }
  }

  // Web search for news and research
  async webSearch(query: string): Promise<{
    status: string;
    results?: Array<{ title: string; href: string; body: string }>;
    provider?: string;
    message?: string
  }> {
    try {
      const response = await fetch(`${this.baseURL}/web-search?q=${encodeURIComponent(query)}`);
      return response.json();
    } catch (error) {
      console.error('Web search failed:', error);
      return {
        status: 'error',
        message: 'Web search failed'
      };
    }
  }

  // Get financial report data
  async getFinancialReport(symbol: string): Promise<{
    status: string;
    symbol?: string;
    metrics?: Array<{
      date: string;
      revenue: number;
      net_income: number;
      gross_profit: number;
      operating_income: number;
    }>;
    latest_report?: {
      status: string;
      symbol?: string;
      form_type?: string;
      filing_date?: string;
      accession_number?: string;
      url?: string;
      search_query?: string;
      message?: string;
    };
    message?: string;
  }> {
    try {
      const response = await fetch(`${this.baseURL}/financial-report/${symbol}`);
      return response.json();
    } catch (error) {
      console.error('获取财报数据失败:', error);
      return {
        status: 'error',
        message: '获取财报数据失败'
      };
    }
  }

}
export const stockAPI = new StockAPIService();