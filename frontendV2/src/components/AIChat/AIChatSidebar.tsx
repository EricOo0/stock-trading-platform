import React, { useState, useRef, useEffect } from 'react';
import type { StockData } from '../../services/stockAPI';
import { agentAPI, type AgentChatResponse, type ToolCall } from '../../services/agentAPI';

interface AIChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type?: 'analysis' | 'recommendation' | 'market_insight';
  toolCalls?: ToolCall[];  // Tool calls from agent
  sessionId?: string;       // Session ID for continuity
}

interface AIChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  stockData: StockData | null;
  klineData: any[];
  onToggle: () => void;
}

const AIChatSidebar: React.FC<AIChatSidebarProps> = ({
  isOpen,
  onClose,
  stockData,
  klineData,
  onToggle
}) => {
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [useRealAgent] = useState(true);  // Toggle for using real agent
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 当股票数据变化时，清空消息并重新生成初始分析
  useEffect(() => {
    if (stockData) {
      // 清空之前的消息和会话
      setMessages([]);
      setSessionId(undefined);
      // 触发新的分析
      generateInitialAnalysis();
    }
  }, [stockData?.symbol]); // 监听symbol变化而不是整个stockData对象

  // 生成初始股票分析 - 使用真实Agent
  const generateInitialAnalysis = async () => {
    if (!stockData) return;

    setIsLoading(true);

    try {
      if (useRealAgent) {
        // 使用真实的AI Agent进行分析
        const query = `请分析${stockData.symbol}(${stockData.name})的投资价值和风险`;
        const response: AgentChatResponse = await agentAPI.chat(query, sessionId);

        // 保存session ID以保持对话连续性
        setSessionId(response.session_id);

        const initialMessage: AIChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          type: 'analysis',
          toolCalls: response.tool_calls,
          sessionId: response.session_id
        };

        setMessages([initialMessage]);
      } else {
        // 使用mock数据（fallback）
        const analysis = generateMockAIAnalysis(stockData, klineData);

        const initialMessage: AIChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: analysis,
          timestamp: new Date(),
          type: 'analysis'
        };

        setMessages([initialMessage]);
      }
    } catch (error) {
      console.error('AI analysis failed:', error);
      // 显示AI服务不可用的提示，而不是降级到mock
      const errorMessage: AIChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ **AI服务暂时不可用**\n\n无法连接到AI分析服务。请确保：\n1. Agent服务已启动 (端口8001)\n2. 网络连接正常\n\n--`,
        timestamp: new Date(),
        type: 'analysis'
      };
      setMessages([errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 生成历史数据表格（仅使用真实数据）
  const generateHistoryTable = (klineData: any[]): string => {
    if (!klineData || klineData.length === 0) {
      return '⚠️ **暂无历史数据**\n\n该股票暂时没有可用的历史交易数据。';
    }

    // 检查数据来源
    const hasRealData = klineData.some(item => item.data_source === 'real');
    const dataSource = hasRealData ? '📊 **真实市场数据**' : '⚠️ **数据状态未知**';

    // 获取最近10天的数据
    const recentData = klineData.slice(-10).reverse();

    let table = `${dataSource}\n\n`;
    table += '📈 **近10日开盘收盘价数据**\n\n';
    table += '```\n';
    table += '日期        开盘价    收盘价    涨跌幅\n';
    table += '----------  --------  --------  --------\n';

    recentData.forEach((item, index) => {
      const date = item.date || new Date(item.time * 1000).toISOString().split('T')[0];
      const openPrice = item.open.toFixed(2);
      const closePrice = item.close.toFixed(2);
      const change = index === 0 ? 0 : ((item.close - recentData[index - 1].close) / recentData[index - 1].close * 100);
      const changeStr = index === 0 ? '0.00%' : `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;

      table += `${date}  ${openPrice.padStart(8)}  ${closePrice.padStart(8)}  ${changeStr.padStart(8)}\n`;
    });

    table += '```\n\n';

    // 添加统计信息
    const avgOpen = recentData.reduce((sum, item) => sum + item.open, 0) / recentData.length;
    const avgClose = recentData.reduce((sum, item) => sum + item.close, 0) / recentData.length;
    const maxPrice = Math.max(...recentData.map(item => item.high));
    const minPrice = Math.min(...recentData.map(item => item.low));

    table += '📊 **统计信息**\n';
    table += `• 10日平均开盘价: ¥${avgOpen.toFixed(2)}\n`;
    table += `• 10日平均收盘价: ¥${avgClose.toFixed(2)}\n`;
    table += `• 10日最高价: ¥${maxPrice.toFixed(2)}\n`;
    table += `• 10日最低价: ¥${minPrice.toFixed(2)}\n`;
    table += `• 价格波动范围: ${((maxPrice - minPrice) / minPrice * 100).toFixed(2)}%\n`;

    return table;
  };

  // 生成模拟AI分析（基于真实数据）
  const generateMockAIAnalysis = (data: StockData, klineData: any[]): string => {
    const { symbol, name, current_price, change_percent, volume, turnover, market } = data;

    // 基于涨跌幅生成不同的分析
    const isPositive = change_percent >= 0;
    const trend = isPositive ? '上涨' : '下跌';
    const sentiment = change_percent > 5 ? '强势' : change_percent < -5 ? '弱势' : '中性';

    // 计算一些技术指标
    const volumeAnalysis = volume > 1000000 ? '放量' : '缩量';
    const turnoverRate = (turnover / (current_price * 1000000)) * 100; // 模拟换手率

    // 生成历史数据表格
    const historyTable = generateHistoryTable(klineData);

    // 检查是否有历史数据
    const hasHistoricalData = klineData && klineData.length > 0;
    const dataStatus = hasHistoricalData ? '📊 **基于真实历史数据分析**' : '⚠️ **当前无历史数据支持**';

    // 获取真实的基本面数据（如果可用）
    const fundamentalData = (data as any).fundamental_data;
    const peRatio = fundamentalData?.trailing_pe ? `${fundamentalData.trailing_pe.toFixed(2)}倍` : '暂无数据';
    const pbRatio = fundamentalData?.price_to_book ? `${fundamentalData.price_to_book.toFixed(2)}倍` : '暂无数据';
    const week52High = fundamentalData?.fifty_two_week_high ? `¥${fundamentalData.fifty_two_week_high.toFixed(2)}` : '暂无数据';
    const week52Low = fundamentalData?.fifty_two_week_low ? `¥${fundamentalData.fifty_two_week_low.toFixed(2)}` : '暂无数据';

    // 避免未使用变量的警告
    console.log('K线数据长度:', klineData.length);
    console.log('市场类型:', market);
    console.log('是否有历史数据:', hasHistoricalData);
    console.log('基本面数据:', fundamentalData);

    return `📊 **${name} (${symbol}) 智能分析报告**

${dataStatus}

**当前行情：**
• 当前价格：¥${current_price.toFixed(2)}
• 涨跌幅：${change_percent >= 0 ? '+' : ''}${change_percent.toFixed(2)}%
• 成交量：${(volume / 10000).toFixed(1)}万手
• 市场情绪：${sentiment}

${historyTable}

**技术分析：**
• 短期趋势：${trend}趋势明显
• 成交量分析：${volumeAnalysis}，${volume > 1000000 ? '资金活跃度较高' : '资金观望情绪浓厚'}
• 换手率：${turnoverRate.toFixed(2)}%，${turnoverRate > 3 ? '流动性较好' : '流动性一般'}

**关键指标：**
• 市盈率：${peRatio}
• 市净率：${pbRatio}
• 52周最高：${week52High}
• 52周最低：${week52Low}

**AI建议：**
${isPositive ?
        '✅ 当前处于上涨趋势，但需注意风险控制' :
        '⚠️ 当前处于调整阶段，建议关注支撑位情况'
      }

**风险提示：**
${hasHistoricalData ?
        '以上分析基于真实市场数据，仅供参考，投资有风险，入市需谨慎。' :
        '⚠️ 当前缺乏历史数据支持，建议等待更多数据后再做决策。投资有风险，入市需谨慎。'
      }
建议结合个人风险承受能力做出投资决策。`;
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !stockData) return;

    // 添加用户消息
    const userMessage: AIChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      if (useRealAgent) {
        // 使用真实Agent API
        const response: AgentChatResponse = await agentAPI.chat(currentInput, sessionId);
        setSessionId(response.session_id);

        const aiMessage: AIChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          type: getMessageType(currentInput),
          toolCalls: response.tool_calls,
          sessionId: response.session_id
        };

        setMessages(prev => [...prev, aiMessage]);
      } else {
        // 使用mock响应
        const aiResponse = generateMockAIResponse(currentInput, stockData, klineData);

        const aiMessage: AIChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: aiResponse,
          timestamp: new Date(),
          type: getMessageType(currentInput)
        };

        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Agent chat error:', error);
      // 显示AI服务不可用的提示
      const errorMessage: AIChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ **AI服务暂时不可用**\n\n无法连接到AI分析服务。\n\n--`,
        timestamp: new Date(),
        type: getMessageType(currentInput)
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 快速提问处理函数 - 已内联到onClick中

  // 生成模拟AI响应
  const generateMockAIResponse = (userInput: string, stockData: StockData, klineData: any[]): string => {
    const { name } = stockData;
    const lowerInput = userInput.toLowerCase();

    // 避免未使用变量的警告
    console.log('K线数据长度:', klineData.length);
    console.log('股票名称:', name);
    console.log('涨跌幅:', stockData.change_percent);

    // 关键词匹配生成不同类型的回复
    if (lowerInput.includes('历史') || lowerInput.includes('开盘') || lowerInput.includes('收盘') || lowerInput.includes('表格')) {
      return generateHistoryTable(klineData);
    } else if (lowerInput.includes('建议') || lowerInput.includes('推荐')) {
      return generateRecommendation(stockData);
    } else if (lowerInput.includes('风险') || lowerInput.includes('安全')) {
      return generateRiskAnalysis(stockData);
    } else if (lowerInput.includes('技术') || lowerInput.includes('分析')) {
      return generateTechnicalAnalysis(stockData, klineData);
    } else if (lowerInput.includes('未来') || lowerInput.includes('预测')) {
      return generateFutureOutlook(stockData);
    } else {
      return generateGeneralResponse(stockData, userInput);
    }
  };

  // 获取消息类型
  const getMessageType = (userInput: string): AIChatMessage['type'] => {
    const lowerInput = userInput.toLowerCase();
    if (lowerInput.includes('历史') || lowerInput.includes('开盘') || lowerInput.includes('收盘') || lowerInput.includes('表格')) return 'analysis';
    if (lowerInput.includes('建议') || lowerInput.includes('推荐')) return 'recommendation';
    if (lowerInput.includes('技术') || lowerInput.includes('分析')) return 'analysis';
    if (lowerInput.includes('市场') || lowerInput.includes('行情')) return 'market_insight';
    return undefined;
  };

  // 生成投资建议
  const generateRecommendation = (data: StockData): string => {
    const { change_percent, current_price } = data;

    if (change_percent > 5) {
      return `💡 **投资建议**

考虑到当前${data.name}涨幅较大(${change_percent.toFixed(2)}%)，建议：

• 短期：可考虑分批获利了结，锁定部分收益
• 中长期：如看好公司基本面，可保留核心仓位
• 风险控制：设置止盈位在¥${(current_price * 1.1).toFixed(2)}附近

⚠️ 注意：涨幅较大时追高风险增加，建议谨慎操作。`;
    } else if (change_percent < -5) {
      return `💡 **投资建议**

当前${data.name}调整幅度较大(${change_percent.toFixed(2)}%)，建议：

• 价值投资者：可考虑分批建仓，但需控制仓位
• 技术派：等待企稳信号，关注支撑位¥${(current_price * 0.95).toFixed(2)}
• 风险控制：设置止损位在¥${(current_price * 0.9).toFixed(2)}附近

📌 提醒：下跌过程中需关注基本面变化，避免盲目抄底。`;
    } else {
      return `💡 **投资建议**

${data.name}当前走势相对平稳(${change_percent.toFixed(2)}%)，建议：

• 稳健投资者：可小仓位参与，等待更明确信号
• 短线交易者：关注突破机会，上方目标¥${(current_price * 1.05).toFixed(2)}
• 风险控制：仓位控制在总资金的20%以内

🎯 策略：建议采用定投或分批建仓策略，分散时间风险。`;
    }
  };

  // 生成风险分析
  const generateRiskAnalysis = (data: StockData): string => {
    const volatility = Math.abs(data.change_percent) > 3 ? '高' : Math.abs(data.change_percent) > 1 ? '中' : '低';

    return `⚠️ **风险分析报告 - ${data.name}**

**当前风险评估：**
• 价格波动性：${volatility}风险
• 日内振幅：${Math.abs(data.change_percent).toFixed(2)}%
• 成交量变化：${data.volume > 1000000 ? '活跃，流动性风险较低' : '一般，需注意流动性风险'}

**主要风险因素：**
• 市场风险：受整体行情影响较大
• 行业风险：需关注${data.market}市场政策变化
• 个股风险：公司基本面变化风险

**风险控制建议：**
• 单只股票仓位不超过总资金的30%
• 设置止损位：¥${(data.current_price * 0.92).toFixed(2)}
• 建议分批操作，避免一次性重仓

**适合人群：**
${volatility === '高' ? '• 适合风险承受能力较强的投资者' : '• 适合稳健型投资者关注'}
• 不适合保守型投资者重仓持有`;
  };

  // 生成技术分析
  const generateTechnicalAnalysis = (data: StockData, klineData: any[]): string => {
    // 避免未使用变量的警告
    console.log('K线数据长度:', klineData.length);

    const trend = data.change_percent >= 0 ? '上升趋势' : '下降趋势';
    const support = (data.current_price * 0.95).toFixed(2);
    const resistance = (data.current_price * 1.05).toFixed(2);

    return `📈 **技术分析报告 - ${data.name}**

**趋势分析：**
• 当前趋势：${trend}
• 价格动量：${Math.abs(data.change_percent).toFixed(2)}%
• 技术形态：${data.change_percent > 2 ? '突破形态' : data.change_percent < -2 ? '破位形态' : '整理形态'}

**关键价位：**
• 支撑位：¥${support}
• 阻力位：¥${resistance}
• 当前价格：¥${data.current_price.toFixed(2)}

**指标分析：**
• RSI(14)：${(50 + data.change_percent * 2).toFixed(0)} (${data.change_percent > 0 ? '偏多' : '偏空'})
• MACD：${data.change_percent > 0 ? '金叉' : '死叉'}状态
• 成交量：${data.volume > 1000000 ? '放量' : '缩量'}${data.change_percent > 0 ? '上涨' : '下跌'}

**操作建议：**
${data.change_percent > 0 ?
        '• 关注能否突破上方阻力位' :
        '• 关注下方支撑位能否守住'
      }
• 建议等待更明确的技术信号
• 结合基本面分析做出决策`;
  };

  // 生成未来展望
  const generateFutureOutlook = (data: StockData): string => {
    const outlook = data.change_percent > 3 ? '积极乐观' :
      data.change_percent < -3 ? '谨慎观望' : '中性偏稳';

    return `🔮 **未来展望 - ${data.name}**

**短期展望（1-3个月）：**
• 市场情绪：${outlook}
• 预期目标价：¥${(data.current_price * (1 + data.change_percent / 100 * 0.5)).toFixed(2)}
• 关键催化剂：财报发布、行业政策变化

**中期展望（3-12个月）：**
• 行业发展趋势：需关注${data.market}市场整体表现
• 公司基本面：关注业绩增长可持续性
• 估值水平：当前估值${data.change_percent > 0 ? '偏高' : '合理'}

**风险提示：**
• 宏观经济变化影响
• 行业政策调整风险
• 公司经营业绩波动

**策略建议：**
${outlook === '积极乐观' ?
        '• 可考虑逢低布局，但需控制仓位' :
        outlook === '谨慎观望' ?
          '• 建议观望，等待更明确信号' :
          '• 保持现有仓位，密切关注变化'
      }

⚠️ 以上分析基于当前市场情况，实际走势可能受多种因素影响。`;
  };

  // 生成通用回复
  const generateGeneralResponse = (data: StockData, userInput: string): string => {
    return `🤖 **AI助手回复**

关于${data.name}(${data.symbol})的问题：

**当前状态：**
• 价格：¥${data.current_price.toFixed(2)}
• 涨跌幅：${data.change_percent >= 0 ? '+' : ''}${data.change_percent.toFixed(2)}%
• 成交量：${(data.volume / 10000).toFixed(1)}万手

**针对您的问题：**
"${userInput}"

基于当前市场数据，建议您：
1. 关注技术面和基本面结合分析
2. 合理控制投资风险
3. 考虑个人投资目标和风险承受能力

如需更详细的分析，请告诉我您想了解的具体方面（如技术分析、投资建议、风险评估等）。`;
  };

  // 处理回车键
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 快速提问按钮
  const quickQuestions = [
    { text: '投资建议', icon: '💡' },
    { text: '风险分析', icon: '⚠️' },
    { text: '技术分析', icon: '📈' },
    { text: '历史数据', icon: '📊' }
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: isOpen ? 0 : '-400px',
      width: '400px',
      height: '100%',
      background: 'linear-gradient(135deg, #ffffff, #f8fafc)',
      boxShadow: '-4px 0 20px rgba(0,0,0,0.15)',
      transition: 'right 0.3s ease-in-out',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      borderLeft: '1px solid #e5e7eb'
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px 20px',
        background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px' }}>🤖</span>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>AI股票助手</h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '12px', opacity: 0.9 }}>
              {stockData ? `分析中: ${stockData.symbol}` : '等待选择股票'}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'rgba(255,255,255,0.2)',
            border: 'none',
            color: 'white',
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
            transition: 'all 0.2s ease'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.3)';
            e.currentTarget.style.transform = 'scale(1.1)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          ×
        </button>
      </div>

      {/* 股票信息卡片 */}
      {stockData && (
        <div style={{
          padding: '16px 20px',
          background: '#f8fafc',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px'
            }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
                  {stockData.symbol}
                </h4>
                <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#6b7280' }}>
                  {stockData.name}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '18px',
                  fontWeight: '700',
                  color: (stockData.change_percent || 0) >= 0 ? '#10b981' : '#ef4444'
                }}>
                  ¥{stockData.current_price?.toFixed(2) || '--'}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: (stockData.change_percent || 0) >= 0 ? '#10b981' : '#ef4444'
                }}>
                  {(stockData.change_percent || 0) >= 0 ? '+' : ''}{stockData.change_percent?.toFixed(2) || '--'}%
                </div>
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '8px',
              fontSize: '11px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>成交量:</span>
                <span style={{ fontWeight: '500' }}>{stockData.volume ? (stockData.volume / 10000).toFixed(1) : '--'}万</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>换手率:</span>
                <span style={{ fontWeight: '500' }}>
                  {(() => {
                    const fundamentalData = (stockData as any).fundamental_data;
                    if (fundamentalData?.float_shares && stockData.volume) {
                      // 使用yfinance提供的真实流通股本数据计算换手率
                      const floatShares = fundamentalData.float_shares; // 流通股数（股）
                      const dailyVolumeShares = stockData.volume * 100; // 当日成交量（股）
                      const turnoverRate = (dailyVolumeShares / floatShares) * 100;
                      return `${turnoverRate.toFixed(2)}%`;
                    } else if (fundamentalData?.average_volume_10days && stockData.volume) {
                      // 如果没有流通股本，显示相对成交量
                      const avgVolume = fundamentalData.average_volume_10days;
                      const relativeVolume = (stockData.volume * 100) / avgVolume;
                      return `${relativeVolume.toFixed(1)}倍均量`;
                    }
                    return '暂无数据';
                  })()}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>市盈率:</span>
                <span style={{ fontWeight: '500' }}>
                  {(() => {
                    const fundamentalData = (stockData as any).fundamental_data;
                    if (fundamentalData?.trailing_pe) {
                      return `${fundamentalData.trailing_pe.toFixed(2)}倍`;
                    }
                    return '暂无数据';
                  })()}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>市值:</span>
                <span style={{ fontWeight: '500' }}>
                  {(() => {
                    const fundamentalData = (stockData as any).fundamental_data;
                    if (fundamentalData?.market_cap) {
                      // 直接使用yfinance提供的市值数据
                      const marketCap = fundamentalData.market_cap;
                      if (marketCap >= 1000000000000) {
                        return `${(marketCap / 1000000000000).toFixed(1)}万亿`;
                      } else if (marketCap >= 100000000) {
                        return `${(marketCap / 100000000).toFixed(0)}亿`;
                      } else {
                        return `${(marketCap / 10000).toFixed(0)}万`;
                      }
                    }
                    return '暂无数据';
                  })()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 快速提问按钮 */}
      {stockData && (
        <div style={{
          padding: '12px 20px',
          background: '#f8fafc',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '8px'
          }}>
            {quickQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => {
                  setInputMessage(question.text);
                  setTimeout(() => {
                    inputRef.current?.focus();
                  }, 100);
                }}
                style={{
                  background: 'white',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.2s ease',
                  color: '#374151'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = '#f3f4f6';
                  e.currentTarget.style.borderColor = '#3b82f6';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'white';
                  e.currentTarget.style.borderColor = '#d1d5db';
                }}
              >
                <span>{question.icon}</span>
                <span>{question.text}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 消息列表 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px 20px',
            color: '#6b7280'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
            <h4 style={{ margin: '0 0 8px 0', color: '#374151' }}>AI股票助手</h4>
            <p style={{ fontSize: '14px', margin: 0 }}>
              {stockData ?
                '正在为您分析选中股票，请稍候...' :
                '请先选择一只股票，我将为您提供专业分析'
              }
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
                gap: '8px'
              }}
            >
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: message.role === 'user' ? '#3b82f6' : '#10b981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '14px',
                flexShrink: 0
              }}>
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div style={{
                maxWidth: '280px',
                background: message.role === 'user' ? '#3b82f6' : '#f3f4f6',
                color: message.role === 'user' ? 'white' : '#374151',
                padding: '12px 16px',
                borderRadius: message.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                fontSize: '13px',
                lineHeight: '1.5',
                whiteSpace: 'pre-line'
              }}>
                {message.content}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            background: '#f3f4f6',
            borderRadius: '16px 16px 16px 4px',
            fontSize: '13px',
            color: '#6b7280'
          }}>
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid #3b82f6',
              borderTop: '2px solid transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            AI正在分析中...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div style={{
        padding: '16px 20px',
        background: '#f8fafc',
        borderTop: '1px solid #e5e7eb'
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={stockData ? '询问关于这只股票的问题...' : '请先选择一只股票'}
            disabled={!stockData || isLoading}
            style={{
              width: '100%',
              minHeight: '60px',
              padding: '12px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '13px',
              resize: 'vertical',
              fontFamily: 'inherit',
              background: !stockData || isLoading ? '#f3f4f6' : 'white',
              color: '#374151',
              outline: 'none',
              transition: 'border-color 0.2s ease'
            }}
            onFocus={(e) => {
              if (stockData && !isLoading) {
                e.target.style.borderColor = '#3b82f6';
              }
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#d1d5db';
            }}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{
              fontSize: '11px',
              color: '#6b7280'
            }}>
              按Enter发送，Shift+Enter换行
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || !stockData || isLoading}
              style={{
                background: (!inputMessage.trim() || !stockData || isLoading) ? '#d1d5db' : 'linear-gradient(135deg, #3b82f6, #2563eb)',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '13px',
                cursor: (!inputMessage.trim() || !stockData || isLoading) ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                fontWeight: '500'
              }}
              onMouseOver={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
                }
              }}
              onMouseOut={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }
              }}
            >
              {isLoading ? '分析中...' : '发送'}
            </button>
          </div>
        </div>
      </div>

      {/* 侧边栏切换按钮 */}
      <button
        onClick={onToggle}
        style={{
          position: 'absolute',
          left: '-40px',
          top: '50%',
          transform: 'translateY(-50%)',
          background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
          color: 'white',
          border: 'none',
          width: '40px',
          height: '80px',
          borderRadius: '8px 0 0 8px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          boxShadow: '-4px 0 12px rgba(0,0,0,0.15)',
          transition: 'all 0.3s ease'
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.transform = 'translateY(-50%) scale(1.05)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
        }}
      >
        {isOpen ? '→' : '←'}
      </button>

      {/* CSS动画 */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AIChatSidebar;