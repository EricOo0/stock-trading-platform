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
      console.error('真实API调用失败，使用模拟数据:', error);
      // 如果真实API失败，回退到模拟数据
      return this.getMockStockData(query);
    }
  }

  // 获取模拟数据（作为后备方案）
  private getMockStockData(query: string): MarketResponse {
    const symbol = this.extractSymbolFromQuery(query);
    const mockData = this.generateMockStockData(query);
    console.log(`生成模拟数据 - 查询: ${query}, 股票代码: ${symbol}, 价格: ${mockData.current_price}`);
    
    const mockResponse: MarketResponse = {
      status: 'success',
      symbol: symbol,
      data: mockData,
      timestamp: new Date().toISOString(),
      data_source: 'mock',
      cache_hit: false,
      response_time_ms: 150
    };
    return mockResponse;
  }

  // 从查询中提取股票代码
  private extractSymbolFromQuery(query: string): string {
    // 移除空格并转换为大写
    const cleanQuery = query.trim().toUpperCase();
    
    // 如果是纯数字，可能是A股代码
    if (/^\d{6}$/.test(cleanQuery)) {
      return cleanQuery;
    }
    
    // 如果是字母开头，可能是美股代码
    if (/^[A-Z]{1,5}$/.test(cleanQuery)) {
      return cleanQuery;
    }
    
    // 如果是0开头的5位数字，可能是港股
    if (/^0\d{4}$/.test(cleanQuery)) {
      return cleanQuery;
    }
    
    // 默认返回查询内容
    return cleanQuery;
  }

  // 生成模拟股票数据
  private generateMockStockData(query: string): StockData {
    const symbol = this.extractSymbolFromQuery(query);
    const basePrice = 50 + Math.random() * 200;
    const change = (Math.random() - 0.5) * 10;
    const changePercent = (change / basePrice) * 100;
    
    // 根据代码格式判断市场
    let market = 'A-share';
    let name = '未知股票';
    
    if (/^\d{6}$/.test(symbol)) {
      market = 'A-share';
      name = this.getMockAStockName(symbol);
    } else if (/^[A-Z]{1,5}$/.test(symbol)) {
      market = 'US';
      name = this.getMockUSStockName(symbol);
    } else if (/^0\d{4}$/.test(symbol)) {
      market = 'HK';
      name = this.getMockHKStockName(symbol);
    }

    return {
      symbol,
      name,
      current_price: Number((basePrice + change).toFixed(2)),
      open_price: Number((basePrice - 1 + Math.random() * 2).toFixed(2)),
      high_price: Number((basePrice + Math.abs(change) + Math.random() * 5).toFixed(2)),
      low_price: Number((basePrice - Math.abs(change) - Math.random() * 5).toFixed(2)),
      previous_close: Number(basePrice.toFixed(2)),
      change_amount: Number(change.toFixed(2)),
      change_percent: Number(changePercent.toFixed(2)),
      volume: Math.floor(Math.random() * 10000000),
      turnover: Number((Math.random() * 100000000).toFixed(0)),
      timestamp: new Date().toISOString(),
      market,
      currency: market === 'A-share' ? 'CNY' : market === 'US' ? 'USD' : 'HKD',
      status: 'ACTIVE'
    };
  }

  // 获取模拟A股名称
  private getMockAStockName(symbol: string): string {
    const aStockNames: { [key: string]: string } = {
      '000001': '平安银行',
      '000002': '万科A',
      '600036': '招商银行',
      '600519': '贵州茅台',
      '000858': '五粮液',
      '002415': '海康威视',
      '300750': '宁德时代'
    };
    return aStockNames[symbol] || `${symbol.slice(-2)}公司`;
  }

  // 获取模拟美股名称
  private getMockUSStockName(symbol: string): string {
    const usStockNames: { [key: string]: string } = {
      'AAPL': '苹果公司',
      'TSLA': '特斯拉',
      'MSFT': '微软',
      'GOOGL': '谷歌',
      'AMZN': '亚马逊',
      'META': 'Meta',
      'NVDA': '英伟达'
    };
    return usStockNames[symbol] || `${symbol}公司`;
  }

  // 获取模拟港股名称
  private getMockHKStockName(symbol: string): string {
    const hkStockNames: { [key: string]: string } = {
      '00700': '腾讯控股',
      '03690': '美团',
      '09988': '阿里巴巴',
      '01810': '小米集团',
      '02318': '中国平安',
      '03968': '招商银行'
    };
    return hkStockNames[symbol] || `${symbol.slice(-2)}公司`;
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
        console.warn('获取热门股票失败，使用默认列表');
        return this.getDefaultHotStocks();
      }
    } catch (error) {
      console.error('获取热门股票失败，使用模拟数据:', error);
      return this.getDefaultHotStocks();
    }
  }

  // 默认热门股票列表（后备方案）
  private getDefaultHotStocks(): StockData[] {
    const hotStocks = ['000001', '600036', 'AAPL', 'TSLA', '00700', '000002'];
    return hotStocks.map(symbol => this.generateMockStockData(symbol));
  }
}

export const stockAPI = new StockAPIService();