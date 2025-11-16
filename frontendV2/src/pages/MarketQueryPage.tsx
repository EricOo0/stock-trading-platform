import React, { useState, useEffect } from 'react';
import { stockAPI } from '../services/stockAPI';
import type { StockData } from '../services/stockAPI';
import TradingViewKLineChart from '../components/KLineChart/TradingViewKLineChart';
import SimpleKLineChart from '../components/KLineChart/SimpleKLineChart';
import AIChatSidebar from '../components/AIChat/AIChatSidebar';
import type { UTCTimestamp } from 'lightweight-charts';

const MarketQueryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<any[]>([]); // 添加K线数据状态
  const [useSimpleChart, setUseSimpleChart] = useState(false); // 图表类型切换
  const [chartError, setChartError] = useState<string>(''); // 图表错误信息
  const [isAIChatOpen, setIsAIChatOpen] = useState(false); // AI对话侧边栏状态

  // 获取真实历史K线数据（仅使用真实数据，默认30天）
  const fetchHistoricalData = async (symbol: string, days: number = 30) => {
    try {
      console.log(`获取 ${symbol} 的历史数据，周期: ${days} 天`);
      const historicalData = await stockAPI.getHistoricalData(symbol, '30d', days);
      console.log(`成功获取 ${historicalData.length} 条历史数据`);
      
      if (historicalData.length === 0) {
        console.warn(`股票 ${symbol} 没有可用的历史数据`);
      }
      
      return historicalData;
    } catch (error) {
      console.error('获取历史数据失败:', error);
      return []; // 返回空数组，不使用模拟数据
    }
  };

  // 加载热门股票
  useEffect(() => {
    loadHotStocks();
  }, []);

  const loadHotStocks = async () => {
    try {
      setLoading(true);
      const hotStocks = await stockAPI.getHotStocks();
      console.log('加载热门股票:', hotStocks);
      if (hotStocks.length > 0) {
        console.log('第一个热门股票:', hotStocks[0]);
        console.log('股票名称:', hotStocks[0].name);
        console.log('当前价格:', hotStocks[0].current_price);
      }
      setStockData(hotStocks);
      
      // 默认选中第一个
      if (hotStocks.length > 0) {
        setSelectedStock(hotStocks[0]);
        // 异步获取历史数据（仅真实数据，30天）
        fetchHistoricalData(hotStocks[0].symbol, 30).then(kData => {
          setKlineData(kData);
          if (kData.length === 0) {
            console.warn(`股票 ${hotStocks[0].symbol} 暂无历史数据`);
          }
        });
      } else {
        console.log('没有获取到热门股票数据');
      }
    } catch (err) {
      console.error('加载热门股票失败:', err);
      setError('加载热门股票失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError('');
    
    try {
      console.log('开始搜索:', searchTerm);
      const response = await stockAPI.searchStock(searchTerm);
      console.log('搜索响应:', response);
      
      if (response.status === 'success' && response.data) {
        console.log('搜索成功，数据:', response.data);
        // 添加到股票列表
        setStockData(prev => {
          const exists = prev.find(stock => stock.symbol === response.data!.symbol);
          const newData = exists ? 
            prev.map(stock => 
              stock.symbol === response.data!.symbol ? response.data! : stock
            ) : 
            [response.data!, ...prev];
          console.log('更新后的股票列表:', newData);
          return newData;
        });
        
        // 获取真实历史数据（30天）
        fetchHistoricalData(response.data.symbol, 30).then(kData => {
          setKlineData(kData);
          if (kData.length === 0) {
            console.warn(`股票 ${response.data.symbol} 暂无历史数据`);
          }
        });
        
        // 选中该股票
        setSelectedStock(response.data);
        setSearchTerm(''); // 清空搜索框
      } else {
        console.log('搜索失败:', response.message);
        setError(response.message || '未找到相关股票信息');
      }
    } catch (err) {
      console.error('搜索错误:', err);
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleStockSelect = (stock: StockData) => {
    console.log('选中股票:', stock);
    console.log('股票名称:', stock.name);
    console.log('当前价格:', stock.current_price);
    setSelectedStock(stock);
    // 获取真实历史数据（30天）
    fetchHistoricalData(stock.symbol, 30).then(kData => {
      setKlineData(kData);
      if (kData.length === 0) {
        console.warn(`股票 ${stock.symbol} 暂无历史数据`);
      }
    });
  };

  // 处理图表错误
  const handleChartError = (error: Error) => {
    console.error('Chart error:', error);
    setChartError(error.message);
    // 自动切换到简单图表
    setUseSimpleChart(true);
  };

  // AI对话侧边栏控制
  const toggleAIChat = () => {
    setIsAIChatOpen(!isAIChatOpen);
  };

  const closeAIChat = () => {
    setIsAIChatOpen(false);
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      {/* 页面标题 - 10% */}
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
          行情查询
        </h1>
        <p style={{
          fontSize: '0.9rem',
          color: '#6b7280',
          margin: '4px 0 0 0'
        }}>
          实时股票行情数据查询
        </p>
      </div>

      {/* 搜索区域 - 15% */}
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
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <h3 style={{
            margin: 0,
            fontSize: '1rem',
            fontWeight: '600',
            color: '#1f2937'
          }}>
            股票搜索
          </h3>
          <button
            type="button"
            onClick={toggleAIChat}
            style={{
              background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <span>🤖</span>
            AI分析
          </button>
        </div>
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
              placeholder="输入股票代码或名称"
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
            style={{
              background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.3)';
            }}
          >
            搜索
          </button>
        </form>
        
        {/* 错误和加载状态 */}
        {error && (
          <div style={{
            marginTop: '8px',
            padding: '8px 12px',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            color: '#dc2626',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}
        
        {loading && (
          <div style={{
            marginTop: '8px',
            padding: '8px 12px',
            background: '#eff6ff',
            border: '1px solid #dbeafe',
            borderRadius: '6px',
            color: '#2563eb',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid #2563eb',
              borderTop: '2px solid transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            搜索中...
          </div>
        )}
      </div>

      {/* 主要内容区域 - 75% */}
      <div style={{
        flex: '1',
        display: 'grid',
        gridTemplateColumns: selectedStock ? '2fr 1fr' : '1fr',
        gap: '16px',
        minHeight: 0
      }}>
        {/* 左侧：股票列表 */}
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
            <span style={{
              fontSize: '16px'
            }}>
              📊
            </span>
            <div>
              <h2 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#1f2937',
                margin: 0
              }}>
                热门股票
              </h2>
              <p style={{
                color: '#6b7280',
                margin: '2px 0 0 0',
                fontSize: '0.8rem'
              }}>
                点击股票查看详细行情
              </p>
            </div>
          </div>
          
          <div style={{
            flex: 1,
            overflow: 'auto',
            padding: '8px'
          }}>
            {stockData.length === 0 ? (
              <div style={{
                padding: '20px',
                textAlign: 'center',
                color: '#6b7280',
                fontSize: '0.9rem'
              }}>
                暂无股票数据，请先搜索或等待加载
              </div>
            ) : (
              stockData.map((stock: StockData) => {
                const isPositive = stock.change_amount >= 0;
                
                return (
                  <div
                    key={stock.symbol}
                    onClick={() => handleStockSelect(stock)}
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
                          ¥{stock.current_price.toFixed(2)}
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

        {/* 右侧：选中股票详情 */}
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
              <span style={{
                fontSize: '16px'
              }}>
                💰
              </span>
              <div>
                <h3 style={{
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  color: '#1f2937',
                  margin: 0
                }}>
                  股票详情
                </h3>
                <p style={{
                  color: '#6b7280',
                  margin: '2px 0 0 0',
                  fontSize: '0.75rem'
                }}>
                  实时数据
                </p>
              </div>
            </div>
            
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 0'
              }}>
                <span style={{
                  color: '#6b7280',
                  fontSize: '0.8rem'
                }}>
                  选中股票
                </span>
                <span style={{
                  fontWeight: '600',
                  color: '#1f2937',
                  fontSize: '0.85rem'
                }}>
                  {selectedStock ? `${selectedStock.symbol} - ${selectedStock.name}` : ''}
                </span>
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 0'
              }}>
                <span style={{
                  color: '#6b7280',
                  fontSize: '0.8rem'
                }}>
                  当前价格
                </span>
                <span style={{
                  fontWeight: '700',
                  color: '#1f2937',
                  fontSize: '0.9rem'
                }}>
                  {selectedStock ? `¥${selectedStock.current_price.toFixed(2)}` : '¥0.00'}
                </span>
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 0'
              }}>
                <span style={{
                  color: '#6b7280',
                  fontSize: '0.8rem'
                }}>
                  涨跌幅
                </span>
                <span style={{
                  fontWeight: '600',
                  color: '#10b981',
                  fontSize: '0.85rem'
                }}>
                  +1.42%
                </span>
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 0'
              }}>
                <span style={{
                  color: '#6b7280',
                  fontSize: '0.8rem'
                }}>
                  成交量
                </span>
                <span style={{
                  fontWeight: '600',
                  color: '#1f2937',
                  fontSize: '0.85rem'
                }}>
                  15.3万手
                </span>
              </div>
            </div>
            
            <div style={{
              marginTop: '12px'
            }}>
              <h4 style={{
                fontSize: '0.85rem',
                fontWeight: '600',
                color: '#1f2937',
                margin: '0 0 6px 0'
              }}>
                K线图
              </h4>
              <div style={{
                height: '200px',
                background: '#f8fafc',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{
                    color: '#6b7280',
                    fontSize: '0.8rem',
                    fontWeight: '500'
                  }}>
                    K线图预览
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {chartError && (
                      <span style={{ fontSize: '0.7rem', color: '#dc2626' }}>图表加载失败</span>
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
                      {useSimpleChart ? '高级图表' : '简单图表'}
                    </button>
                  </div>
                </div>
                
                {selectedStock ? (
                  <div style={{ flex: 1, minHeight: '150px' }}>
                    {useSimpleChart ? (
                      <SimpleKLineChart
                        data={klineData}
                        width={280}
                        height={150}
                      />
                    ) : (
                      <TradingViewKLineChart
                        data={klineData}
                        width={280}
                        height={150}
                        onError={handleChartError}
                      />
                    )}
                  </div>
                ) : (
                  <div style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#9ca3af',
                    fontSize: '0.8rem'
                  }}>
                    点击左侧股票查看K线图
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* AI对话侧边栏 */}
      <AIChatSidebar
        isOpen={isAIChatOpen}
        onClose={closeAIChat}
        stockData={selectedStock}
        klineData={klineData}
        onToggle={toggleAIChat}
      />
    </div>
  );
};

export default MarketQueryPage;