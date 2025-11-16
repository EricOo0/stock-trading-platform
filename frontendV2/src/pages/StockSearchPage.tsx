import React, { useState } from 'react';
import { stockAPI } from '../services/stockAPI';
import type { StockData } from '../services/stockAPI';
import TradingViewKLineChart from '../components/KLineChart/TradingViewKLineChart';
import SimpleKLineChart from '../components/KLineChart/SimpleKLineChart';
import type { UTCTimestamp } from 'lightweight-charts';

const StockSearchPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<StockData[]>([]);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<any[]>([]);
  const [useSimpleChart, setUseSimpleChart] = useState(false); // 备用图表开关
  const [chartError, setChartError] = useState<string>(''); // 图表错误信息

  // 处理图表错误
  const handleChartError = (error: Error) => {
    console.error('Chart error:', error);
    setChartError(error.message);
    // 自动切换到简单图表
    setUseSimpleChart(true);
  };

  // 生成模拟K线数据
  const generateKLineData = (basePrice: number, days: number = 30) => {
    const data = [];
    const now = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      const open = basePrice + (Math.random() - 0.5) * basePrice * 0.1;
      const close = open + (Math.random() - 0.5) * basePrice * 0.08;
      const high = Math.max(open, close) + Math.random() * basePrice * 0.05;
      const low = Math.min(open, close) - Math.random() * basePrice * 0.05;
      const volume = Math.floor(Math.random() * 1000000) + 100000;
      
      data.push({
        time: Math.floor(date.getTime() / 1000) as UTCTimestamp,
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume,
      });
    }
    
    return data;
  };

  // 处理搜索
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError('');
    
    try {
      const response = await stockAPI.searchStock(searchTerm);
      
      if (response.status === 'success' && response.data) {
        // 添加到搜索结果
        setSearchResults(prev => {
          const exists = prev.find(stock => stock.symbol === response.data!.symbol);
          if (exists) {
            return prev.map(stock => 
              stock.symbol === response.data!.symbol ? response.data! : stock
            );
          } else {
            return [response.data!, ...prev];
          }
        });
        
        // 自动生成K线数据
        const kData = generateKLineData(response.data.current_price);
        console.log('Generated K-line data:', kData); // 调试信息
        setKlineData(kData);
        
        // 选中该股票
        setSelectedStock(response.data);
      } else {
        setError(response.message || '未找到相关股票信息');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 快速搜索热门股票
  const quickSearch = async (symbol: string) => {
    setSearchTerm(symbol);
    
    setLoading(true);
    setError('');
    
    try {
      const response = await stockAPI.searchStock(symbol);
      
      if (response.status === 'success' && response.data) {
        setSearchResults(prev => {
          const exists = prev.find(stock => stock.symbol === response.data!.symbol);
          if (exists) {
            return prev.map(stock => 
              stock.symbol === response.data!.symbol ? response.data! : stock
            );
          } else {
            return [response.data!, ...prev];
          }
        });
        
        const kData = generateKLineData(response.data.current_price);
        setKlineData(kData);
        setSelectedStock(response.data);
      }
    } catch (err) {
      setError('快速搜索失败');
    } finally {
      setLoading(false);
    }
  };

  // 热门股票列表
  const hotStocks = [
    { symbol: '000001', name: '平安银行' },
    { symbol: '600036', name: '招商银行' },
    { symbol: 'AAPL', name: '苹果公司' },
    { symbol: 'TSLA', name: '特斯拉' },
    { symbol: '00700', name: '腾讯控股' },
    { symbol: '09988', name: '阿里巴巴' }
  ];

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      {/* 页面标题 */}
      <div style={{
        flex: '0 0 10%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '0 20px'
      }}>
        <h1 style={{
          fontSize: 'clamp(1.3rem, 2.5vw, 1.8rem)',
          fontWeight: '700',
          color: '#1f2937',
          margin: 0
        }}>
          股票搜索
        </h1>
        <p style={{
          fontSize: '0.9rem',
          color: '#6b7280',
          margin: '4px 0 0 0'
        }}>
          支持A股、美股、港股实时查询
        </p>
      </div>

      {/* 搜索区域 */}
      <div style={{
        flex: '0 0 15%',
        background: 'white',
        borderRadius: '12px',
        padding: '16px 20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}>
        <form onSubmit={handleSearch} style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'center'
        }}>
          <div style={{
            position: 'relative',
            flex: 1
          }}>
            <span style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#9ca3af',
              fontSize: '16px'
            }}>
              🔍
            </span>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="输入股票代码或名称，如：000001、AAPL、腾讯"
              style={{
                width: '100%',
                padding: '10px 10px 10px 40px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px',
                outline: 'none',
                transition: 'all 0.2s ease'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.boxShadow = '0 0 0 2px rgba(59, 130, 246, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              background: loading ? '#9ca3af' : 'linear-gradient(135deg, #3b82f6, #2563eb)',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)'
            }}
            onMouseOver={(e) => {
              if (!loading) {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
              }
            }}
            onMouseOut={(e) => {
              if (!loading) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.3)';
              }
            }}
          >
            {loading ? '搜索中...' : '搜索'}
          </button>
        </form>

        {/* 错误提示 */}
        {error && (
          <div style={{
            marginTop: '8px',
            padding: '8px 12px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            color: '#dc2626',
            fontSize: '0.8rem'
          }}>
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* 热门股票快速搜索 */}
      <div style={{
        flex: '0 0 10%',
        background: 'white',
        borderRadius: '12px',
        padding: '12px 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '8px'
        }}>
          <span style={{ fontSize: '14px' }}>🔥</span>
          <span style={{
            fontSize: '0.85rem',
            fontWeight: '500',
            color: '#1f2937'
          }}>
            热门股票
          </span>
        </div>
        <div style={{
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap'
        }}>
          {hotStocks.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => quickSearch(stock.symbol)}
              style={{
                padding: '4px 8px',
                background: '#f3f4f6',
                border: '1px solid #e5e7eb',
                borderRadius: '4px',
                fontSize: '0.75rem',
                color: '#374151',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#e5e7eb';
                e.currentTarget.style.borderColor = '#d1d5db';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = '#f3f4f6';
                e.currentTarget.style.borderColor = '#e5e7eb';
              }}
            >
              {stock.symbol} - {stock.name}
            </button>
          ))}
        </div>
      </div>

      {/* 搜索结果和K线图 */}
      <div style={{
        flex: '1',
        display: 'grid',
        gridTemplateColumns: selectedStock ? '1fr 1fr' : '1fr',
        gap: '16px',
        minHeight: 0
      }}>
        {/* 搜索结果列表 */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{
            padding: '12px 16px',
            borderBottom: '1px solid #f3f4f6',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{ fontSize: '14px' }}>📊</span>
            <div>
              <h3 style={{
                fontSize: '0.95rem',
                fontWeight: '600',
                color: '#1f2937',
                margin: 0
              }}>
                搜索结果
              </h3>
              <p style={{
                color: '#6b7280',
                margin: '2px 0 0 0',
                fontSize: '0.75rem'
              }}>
                点击股票查看K线图
              </p>
            </div>
          </div>
          
          <div style={{
            flex: 1,
            overflow: 'auto',
            padding: '8px'
          }}>
            {searchResults.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '40px 20px',
                color: '#9ca3af'
              }}>
                <div style={{
                  fontSize: '32px',
                  marginBottom: '12px'
                }}>
                  🔍
                </div>
                <p style={{
                  fontSize: '0.9rem',
                  margin: 0
                }}>
                  请输入股票代码或名称开始搜索
                </p>
              </div>
            ) : (
              searchResults.map((stock) => {
                const isPositive = stock.change_amount >= 0;
                
                return (
                  <div
                    key={stock.symbol}
                    onClick={() => {
                      setSelectedStock(stock);
                      const kData = generateKLineData(stock.current_price);
                      setKlineData(kData);
                    }}
                    style={{
                      padding: '10px 12px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      background: selectedStock?.symbol === stock.symbol ? '#eff6ff' : 'transparent',
                      borderLeft: selectedStock?.symbol === stock.symbol ? '3px solid #3b82f6' : '3px solid transparent',
                      borderRadius: '6px',
                      marginBottom: '4px'
                    }}
                    onMouseOver={(e) => {
                      if (selectedStock?.symbol !== stock.symbol) {
                        e.currentTarget.style.background = '#f9fafb';
                      }
                    }}
                    onMouseOut={(e) => {
                      if (selectedStock?.symbol !== stock.symbol) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          marginBottom: '2px'
                        }}>
                          <span style={{
                            fontSize: '0.9rem',
                            fontWeight: '600',
                            color: '#1f2937'
                          }}>
                            {stock.symbol}
                          </span>
                          <span style={{
                            fontSize: '0.7rem',
                            padding: '2px 6px',
                            background: stock.market === 'A-share' ? '#dbeafe' : 
                                       stock.market === 'US' ? '#dcfce7' : '#f3e8ff',
                            color: stock.market === 'A-share' ? '#1d4ed8' : 
                                   stock.market === 'US' ? '#166534' : '#7c3aed',
                            borderRadius: '3px',
                            fontWeight: '500'
                          }}>
                            {stock.market === 'A-share' ? 'A股' : 
                             stock.market === 'US' ? '美股' : '港股'}
                          </span>
                        </div>
                        <h3 style={{
                          fontWeight: '500',
                          color: '#374151',
                          margin: 0,
                          fontSize: '0.8rem'
                        }}>
                          {stock.name}
                        </h3>
                      </div>
                      
                      <div style={{
                        textAlign: 'right'
                      }}>
                        <div style={{
                          fontSize: '1rem',
                          fontWeight: '700',
                          color: '#1f2937',
                          marginBottom: '2px'
                        }}>
                          {stock.currency === 'CNY' ? '¥' : stock.currency === 'USD' ? '$' : 'HK$'}{stock.current_price.toFixed(2)}
                        </div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'flex-end',
                          gap: '4px',
                          fontSize: '0.75rem',
                          fontWeight: '500',
                          color: isPositive ? '#10b981' : '#ef4444'
                        }}>
                          <span>
                            {isPositive ? '📈' : '📉'}
                          </span>
                          <span>
                            {isPositive ? '+' : ''}{stock.change_amount.toFixed(2)}
                          </span>
                          <span>
                            ({isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%)
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* K线图 */}
        {selectedStock && (
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
              paddingBottom: '8px',
              borderBottom: '1px solid #f3f4f6'
            }}>
              <span style={{ fontSize: '16px' }}>📈</span>
              <div>
                <h3 style={{
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  color: '#1f2937',
                  margin: 0
                }}>
                  {selectedStock.symbol} - K线图
                </h3>
                <p style={{
                  color: '#6b7280',
                  margin: '2px 0 0 0',
                  fontSize: '0.75rem'
                }}>
                  {selectedStock.name}
                </p>
              </div>
            </div>
            
            <div style={{ flex: 1, minHeight: '200px' }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '8px'
              }}>
                <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>K线图预览</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {chartError && (
                    <span style={{ fontSize: '0.7rem', color: '#dc2626' }}>高级图表加载失败</span>
                  )}
                  <button
                    onClick={() => setUseSimpleChart(!useSimpleChart)}
                    style={{
                      padding: '4px 8px',
                      fontSize: '0.7rem',
                      background: useSimpleChart ? '#dbeafe' : '#f3f4f6',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: useSimpleChart ? '#2563eb' : '#374151'
                    }}
                  >
                    {useSimpleChart ? '使用高级图表' : '使用简单图表'}
                  </button>
                </div>
              </div>
              {useSimpleChart ? (
                <SimpleKLineChart
                  data={klineData}
                  width={600}
                  height={200}
                />
              ) : (
                <TradingViewKLineChart
                  data={klineData}
                  width={600}
                  height={200}
                  onError={handleChartError}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockSearchPage;