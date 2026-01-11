import React, { useState, useRef, useEffect } from 'react';
import { Bot, X, Send, User, Sparkles, Loader2, Maximize2, Minimize2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import RecommendationCard, { type RecommendationCardProps } from './RecommendationCard';
import type { AssetItem } from '../../types/personalFinance';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
  cards?: RecommendationCardProps[];
}

interface FinanceAssistantWidgetProps {
  assets: AssetItem[];
  cash: number;
}

const FinanceAssistantWidget: React.FC<FinanceAssistantWidgetProps> = ({ assets, cash }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: '您好！我是您的私人理财助手。我可以为您分析持仓风险、提供投资建议或解读市场动态。',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen, isExpanded]);

  const handleSend = async (text: string = inputValue) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: text,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Stream Response
      const response = await fetch('/api/personal-finance/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assets: assets.map(a => ({
            symbol: a.code,
            name: a.name,
            type: a.type,
            quantity: a.quantity,
            cost_basis: a.avgCost,
            current_price: a.currentPrice,
            total_value: a.totalValue
          })),
          cash_balance: cash,
          query: text
        }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botMsgId = (Date.now() + 1).toString();
      let botText = '';
      let cards: RecommendationCardProps[] = [];

      // Initial Bot Message Placeholder
      setMessages(prev => [...prev, {
        id: botMsgId,
        sender: 'bot',
        text: '',
        timestamp: new Date()
      }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            
            if (data.type === 'report_chunk') {
              botText += data.content;
            } else if (data.type === 'card') {
              cards.push(data.data);
            } else if (data.type === 'error') {
              botText += `\n\n[系统错误: ${data.content}]`;
            }

            // Update Message
            setMessages(prev => prev.map(msg => 
              msg.id === botMsgId 
                ? { ...msg, text: botText, cards: [...cards] } 
                : msg
            ));
          } catch (e) {
            console.error('Error parsing stream:', e);
          }
        }
      }

    } catch (error) {
      console.error('Analysis failed:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'bot',
        text: '抱歉，分析服务暂时不可用，请稍后再试。',
        timestamp: new Date()
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAnalysis = () => {
    handleSend("请分析我当前的持仓风险和机会，并给出操作建议。");
  };

  return (
    <div className={`fixed z-50 flex flex-col items-end transition-all duration-300 ${isExpanded ? 'inset-0 bg-slate-900/80 backdrop-blur-sm justify-center items-center' : 'bottom-6 right-6'}`}>
      {/* Chat Window */}
      {isOpen && (
        <div 
          className={`
            bg-slate-800 rounded-2xl shadow-2xl border border-slate-700 flex flex-col overflow-hidden 
            transition-all duration-300
            ${isExpanded 
              ? 'w-[90vw] h-[90vh] max-w-6xl' 
              : 'mb-4 w-[400px] h-[600px] animate-in slide-in-from-bottom-5 fade-in'
            }
          `}
        >
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 flex justify-between items-center text-white shrink-0">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-white/20 rounded-lg">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="font-bold text-sm">AI 理财顾问</h3>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-xs text-blue-100">在线</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1 hover:bg-white/20 rounded-lg transition-colors"
                title={isExpanded ? "还原" : "展开"}
              >
                {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
              </button>
              <button 
                onClick={() => {
                  setIsOpen(false);
                  setIsExpanded(false);
                }}
                className="p-1 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-900/50">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                  ${msg.sender === 'user' ? 'bg-slate-700' : 'bg-blue-600'}
                `}>
                  {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div className={`
                  max-w-[85%] space-y-3
                  ${msg.sender === 'user' ? 'flex flex-col items-end' : ''}
                `}>
                  {msg.text && (
                    <div className={`
                      p-3 rounded-2xl text-sm leading-relaxed
                      ${msg.sender === 'user' 
                        ? 'bg-blue-600 text-white rounded-tr-none' 
                        : 'bg-slate-700 text-slate-200 rounded-tl-none border border-slate-600'
                      }
                    `}>
                      {msg.sender === 'bot' ? (
                        <div className="prose prose-invert prose-sm max-w-none">
                          <ReactMarkdown 
                            components={{
                              p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                              ul: ({children}) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                              li: ({children}) => <li className="mb-1">{children}</li>,
                              strong: ({children}) => <span className="font-bold text-blue-300">{children}</span>
                            }}
                          >
                            {msg.text}
                          </ReactMarkdown>
                        </div>
                      ) : msg.text}
                    </div>
                  )}
                  
                  {/* Render Cards if any */}
                  {msg.cards && msg.cards.length > 0 && (
                    <div className={`grid gap-3 w-full ${isExpanded ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
                      {msg.cards.map((card, idx) => (
                        <RecommendationCard key={idx} {...card} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <Bot size={14} />
                </div>
                <div className="bg-slate-700 p-3 rounded-2xl rounded-tl-none border border-slate-600 flex items-center gap-2 text-slate-400 text-xs">
                  <Loader2 size={14} className="animate-spin" />
                  AI 正在思考中...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions & Input */}
          <div className="bg-slate-800 border-t border-slate-700 p-4 space-y-3 shrink-0">
            {/* Quick Actions */}
            {messages.length < 3 && (
              <button
                onClick={handleQuickAnalysis}
                disabled={isTyping}
                className="flex items-center gap-2 px-3 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-lg text-indigo-300 text-xs transition-colors w-fit"
              >
                <Sparkles size={12} />
                一键分析我的持仓
              </button>
            )}

            <div className="flex gap-2 relative">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="输入您的问题..."
                className="w-full bg-slate-900 border border-slate-600 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 pr-10"
              />
              <button 
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isTyping}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="group flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white p-4 rounded-full shadow-lg shadow-blue-600/30 transition-all hover:scale-110 active:scale-95"
        >
          <Bot size={28} />
          <span className="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 font-bold whitespace-nowrap">
            理财助手
          </span>
        </button>
      )}
    </div>
  );
};

export default FinanceAssistantWidget;