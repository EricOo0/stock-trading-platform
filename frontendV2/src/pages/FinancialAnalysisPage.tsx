import React, { useState, useRef, useEffect } from 'react';
import { stockAPI } from '../services/stockAPI';
import FinancialReportHeader from '../components/MarketQuery/components/FinancialReportHeader';
import FinancialAnalysisPanel from '../components/MarketQuery/components/FinancialAnalysisPanel';
import FinancialPDFViewer from '../components/MarketQuery/components/FinancialPDFViewer';
import type { FinancialReport, AnchorMap, Citation } from '../components/MarketQuery/components/types';
import { Send, Bot, User, Sparkles, X, ChevronDown, Maximize2, Minimize2, FileText } from 'lucide-react';

import { FinancialIndicatorsDisplay } from '../components/Financial';
import { getFinancialIndicators } from '../services/financialService';
import type { FinancialIndicators } from '../types/financial';

// Floating AI Assistant Component
const FloatingAIAssistant: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string }[]>([
        { role: 'ai', content: '你好！我是你的智能财报助手。我可以帮你解读财报、分析风险或回答具体财务问题。' }
    ]);
    const inputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isChatOpen]);

    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const handleSend = async () => {
        if (!input.trim()) return;

        // If chat is not open, open it
        if (!isChatOpen) {
            setIsChatOpen(true);
            setIsOpen(false); // Close the input bar as we move to chat window
        }

        const userMessage = input;
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setInput('');

        // Create a placeholder for AI response
        setMessages(prev => [...prev, { role: 'ai', content: '' }]);

        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: userMessage }),
            });

            if (!response.ok) throw new Error('Network response was not ok');
            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiResponse = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                aiResponse += chunk;

                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage.role === 'ai') {
                        lastMessage.content = aiResponse;
                    }
                    return newMessages;
                });
            }
        } catch (error) {
            console.error('Error calling AI agent:', error);
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage.role === 'ai') {
                    lastMessage.content = '抱歉，我遇到了一些问题，请稍后再试。';
                }
                return newMessages;
            });
        }
    };

    const handleInputSubmit = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    return (
        <>
            {/* 1. Floating Icon Trigger (Always visible if chat is closed) */}
            {!isChatOpen && !isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full shadow-lg shadow-blue-500/30 flex items-center justify-center text-white hover:scale-110 transition-transform duration-300 z-50 group"
                >
                    <Bot size={28} className="group-hover:rotate-12 transition-transform" />
                    <span className="absolute -top-10 right-0 bg-white text-slate-900 text-xs px-2 py-1 rounded shadow-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                        AI 财报助手
                    </span>
                </button>
            )}

            {/* 2. Floating Input Bar (Visible when Icon clicked) */}
            {isOpen && !isChatOpen && (
                <div className="fixed bottom-8 right-8 z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
                    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-2xl p-2 flex items-center gap-2 w-[400px]">
                        <div className="p-2 bg-blue-500/20 rounded-xl">
                            <Bot size={20} className="text-blue-400" />
                        </div>
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleInputSubmit}
                            placeholder="输入问题，AI 立即解答..."
                            className="flex-1 bg-transparent border-none text-white placeholder-slate-400 focus:ring-0 text-sm"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim()}
                            className="p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Send size={16} />
                        </button>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
                        >
                            <X size={16} />
                        </button>
                    </div>
                </div>
            )}

            {/* 3. Floating Chat Window (Visible after sending message) */}
            {isChatOpen && (
                <div className="fixed bottom-8 right-8 z-50 w-[400px] h-[600px] bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl flex flex-col animate-in slide-in-from-bottom-10 fade-in duration-300 overflow-hidden">
                    {/* Header */}
                    <div className="p-4 border-b border-slate-700/50 bg-slate-800/50 flex items-center justify-between cursor-move">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                                <Bot size={18} className="text-white" />
                            </div>
                            <div>
                                <h3 className="text-white font-bold text-sm">AI 财报助手</h3>
                                <p className="text-[10px] text-blue-300 flex items-center gap-1">
                                    <Sparkles size={10} />
                                    深度分析中
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => {
                                    setIsChatOpen(false);
                                    setIsOpen(false); // Reset to icon state
                                }}
                                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                            >
                                <ChevronDown size={18} />
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-900/50">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg ${msg.role === 'ai'
                                    ? 'bg-slate-800 border border-slate-700'
                                    : 'bg-blue-600 border border-blue-500'
                                    }`}>
                                    {msg.role === 'ai' ? <Bot size={14} className="text-blue-400" /> : <User size={14} className="text-white" />}
                                </div>
                                <div className={`rounded-2xl p-3 text-sm max-w-[85%] shadow-md leading-relaxed ${msg.role === 'ai'
                                    ? 'bg-slate-800 text-slate-200 border border-slate-700/50 rounded-tl-none'
                                    : 'bg-blue-600 text-white border border-blue-500 rounded-tr-none'
                                    }`}>
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 border-t border-slate-700/50 bg-slate-800/30">
                        <div className="relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleInputSubmit}
                                placeholder="继续追问..."
                                className="w-full bg-slate-950/50 border border-slate-700 rounded-xl pl-4 pr-10 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                                autoFocus
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim()}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-blue-400 disabled:opacity-30 transition-colors"
                            >
                                <Send size={16} />
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

const FinancialAnalysisPage: React.FC = () => {
    const [financialSearchQuery, setFinancialSearchQuery] = useState('');
    const [isFullScreen, setIsFullScreen] = useState(false);
    const [financialData, setFinancialData] = useState<FinancialReport | null>(null);
    const [financialLoading, setFinancialLoading] = useState(false);
    const [error, setError] = useState('');

    // Indicators State
    const [financialIndicators, setFinancialIndicators] = useState<FinancialIndicators | null>(null);
    const [indicatorsLoading, setIndicatorsLoading] = useState(false);
    const [indicatorSymbol, setIndicatorSymbol] = useState<string>('');
    const [indicatorMarket, setIndicatorMarket] = useState<string>('');

    // Analysis States
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisReport, setAnalysisReport] = useState('');
    const [analysisDate, setAnalysisDate] = useState('');
    const [citations, setCitations] = useState<Citation[]>([]);
    const [anchorMap, setAnchorMap] = useState<AnchorMap>({});
    const [pdfUrl, setPdfUrl] = useState<string>('');
    const [currentPdfPage, setCurrentPdfPage] = useState<number>(1);
    const [showPdf, setShowPdf] = useState(false);

    // PDF Viewer State
    const [numPages, setNumPages] = useState<number | null>(null);
    const [scale, setScale] = useState<number>(1.0);
    const [highlightRect, setHighlightRect] = useState<[number, number, number, number] | null>(null);

    // Layout State
    const [isIndicatorsExpanded, setIsIndicatorsExpanded] = useState(false);


    const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
    };

    const changePage = (offset: number) => {
        setCurrentPdfPage(prev => Math.min(Math.max(prev + offset, 1), numPages || 1));
    };

    const changeScale = (delta: number) => {
        setScale(prev => Math.min(Math.max(prev + delta, 0.5), 3.0));
    };

    const fetchFinancialReport = async (symbol: string) => {
        setFinancialLoading(true);
        setIndicatorsLoading(true);
        setError('');
        setAnalysisReport('');
        setAnalysisDate('');
        setCitations([]);
        setPdfUrl('');
        setShowPdf(false);
        setFinancialIndicators(null);

        try {
            // Parallel fetch
            const [reportResponse, indicatorsResponse] = await Promise.allSettled([
                stockAPI.getFinancialReport(symbol),
                getFinancialIndicators(symbol)
            ]);

            // Handle Report Response
            if (reportResponse.status === 'fulfilled') {
                const response = reportResponse.value;
                if (response.status === 'success') {
                    setFinancialData({
                        symbol: response.symbol || symbol,
                        metrics: response.metrics || [],
                        latest_report: response.latest_report as unknown as FinancialReport['latest_report']
                    });
                } else {
                    setError(response.message || '获取财报数据失败');
                }
            } else {
                setError('获取财报数据失败');
            }

            // Handle Indicators Response
            if (indicatorsResponse.status === 'fulfilled') {
                const response = indicatorsResponse.value;
                if (response.status === 'success') {
                    setFinancialIndicators(response.indicators);
                    setIndicatorSymbol(response.symbol);
                    setIndicatorMarket(response.market);
                }
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : '获取财报数据失败');
        } finally {
            setFinancialLoading(false);
            setIndicatorsLoading(false);
        }
    };

    const handleFinancialSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (financialSearchQuery.trim()) {
            fetchFinancialReport(financialSearchQuery.toUpperCase());
        }
    };

    const handleAnalyze = async () => {
        if (!financialData?.symbol) return;

        setIsAnalyzing(true);
        try {
            const response = await stockAPI.analyzeFinancialReport(financialData.symbol);
            if (response.status === 'success') {
                setAnalysisReport(response.report || '');
                setAnalysisDate(response.report_date || '');
                setCitations(response.citations || []);

                // Build anchor map
                const newAnchorMap: AnchorMap = {};
                response.citations?.forEach((citation) => {
                    newAnchorMap[citation.id] = {
                        ...citation,
                        type: citation.type || 'pdf'
                    };
                });
                setAnchorMap(newAnchorMap);

                // Handle PDF URL
                if (response.pdf_url) {
                    setPdfUrl(response.pdf_url);
                    setShowPdf(true);
                } else if (financialData.latest_report?.download_url) {
                    setPdfUrl(financialData.latest_report.download_url);
                    setShowPdf(true);
                }
            }
        } catch (error) {
            console.error('Analysis failed:', error);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleCitationClick = (anchorId: string) => {
        if (!showPdf) setShowPdf(true);

        const anchor = anchorMap[anchorId];
        if (anchor) {
            if (anchor.type === 'pdf') {
                if (anchor.page) setCurrentPdfPage(anchor.page);
                if (anchor.rect) setHighlightRect(anchor.rect);
            } else if (anchor.type === 'html') {
                const currentBaseUrl = pdfUrl.split('#')[0];
                const newUrl = `${currentBaseUrl}#${anchorId}`;
                setPdfUrl(newUrl);
            }
        } else {
            // Fallback logic
            const pageNum = parseInt(anchorId);
            if (!isNaN(pageNum)) {
                setCurrentPdfPage(pageNum);
                return;
            }

            if (anchorId.startsWith('pdf_')) {
                const parts = anchorId.split('_');
                if (parts.length >= 2) {
                    const page = parseInt(parts[1]);
                    if (!isNaN(page)) {
                        setCurrentPdfPage(page);
                        setHighlightRect(null);
                    }
                }
            }
        }
    };



    return (
        <div className="min-h-screen flex flex-col gap-6 p-6 max-w-[1920px] mx-auto w-full relative overflow-y-auto pb-20">
            {/* Header / Search Bar */}
            <div className="flex-none z-10">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                            <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
                                <span className="w-1.5 h-6 bg-indigo-500 rounded-full block"></span>
                            </div>
                            新财报分析
                        </h1>
                    </div>
                </div>

                <FinancialReportHeader
                    financialSearchQuery={financialSearchQuery}
                    setFinancialSearchQuery={setFinancialSearchQuery}
                    handleFinancialSearch={handleFinancialSearch}
                    financialLoading={financialLoading}
                    isFullScreen={isFullScreen}
                    setIsFullScreen={setIsFullScreen}
                    error={error}
                />
            </div>

            {/* Top Section: Financial Indicators */}
            <div
                className={`
                    transition-all duration-300 bg-slate-50/95 backdrop-blur-sm shadow-xl border border-slate-200/50 overflow-hidden
                    ${isIndicatorsExpanded
                        ? 'fixed inset-4 z-50 h-[calc(100vh-2rem)] rounded-2xl p-6' // Fullscreen Overlay Mode
                        : `flex-none rounded-2xl p-5 ${financialIndicators ? 'h-[380px]' : 'h-32'}` // Normal Mode
                    }
                `}
            >
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-slate-800 font-bold text-lg tracking-wide flex items-center gap-2">
                        <span className="w-1 h-5 bg-emerald-500 rounded-full"></span>
                        关键财务指标
                    </h3>
                    <div className="flex items-center gap-2">
                        {financialIndicators && (
                            <button
                                onClick={() => setIsIndicatorsExpanded(!isIndicatorsExpanded)}
                                className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors bg-slate-100/50"
                                title={isIndicatorsExpanded ? "退出全屏" : "全屏查看"}
                            >
                                {isIndicatorsExpanded ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
                            </button>
                        )}
                    </div>
                </div>

                <div className="h-[calc(100%-3rem)] w-full overflow-hidden">
                    {financialIndicators ? (
                        <div className="h-full w-full overflow-auto custom-scrollbar pb-4">
                            <FinancialIndicatorsDisplay
                                indicators={financialIndicators}
                                symbol={indicatorSymbol}
                                market={indicatorMarket}
                                compact={false}
                            />
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-full text-slate-400 gap-3">
                            <div className="w-10 h-10 bg-slate-200/50 rounded-full flex items-center justify-center">
                                <Sparkles size={20} className="text-slate-400" />
                            </div>
                            <p className="text-sm font-medium">输入股票代码开始分析</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Backdrop for fullscreen mode */}
            {isIndicatorsExpanded && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" onClick={() => setIsIndicatorsExpanded(false)} />
            )}

            {/* Bottom Section: Analysis & PDF Split View */}
            {/* Added min-h-[800px] to force scrolling and give space */}
            <div className="flex-1 grid grid-cols-2 gap-6 min-h-[800px]">
                {/* Left: AI Analysis */}
                <div className="flex flex-col gap-4 bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-5 shadow-xl overflow-hidden h-full">
                    <div className="flex-none flex items-center justify-between mb-2">
                        <h3 className="text-white font-medium text-lg tracking-wide flex items-center gap-2">
                            <span className="w-1 h-5 bg-indigo-500 rounded-full"></span>
                            智能财报分析
                        </h3>
                        {financialData?.symbol && (
                            <span className="text-xs font-mono text-slate-400 bg-slate-800/50 px-2 py-1 rounded-md border border-slate-700/50">
                                {financialData.symbol}
                            </span>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 relative">
                        <FinancialAnalysisPanel
                            financialData={financialData}
                            financialLoading={financialLoading}
                            isAnalyzing={isAnalyzing}
                            analysisReport={analysisReport}
                            analysisDate={analysisDate}
                            citations={citations}
                            showPdf={false}
                            handleAnalyze={handleAnalyze}
                            handleCitationClick={handleCitationClick}
                        />
                    </div>
                </div>

                {/* Right: PDF Viewer */}
                <div className="flex flex-col gap-4 bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 shadow-xl overflow-hidden relative h-full">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500/50 to-purple-500/50 z-10"></div>
                    {showPdf ? (
                        <div className="h-full w-full">
                            <FinancialPDFViewer
                                financialData={financialData}
                                pdfUrl={pdfUrl}
                                currentPdfPage={currentPdfPage}
                                numPages={numPages}
                                scale={scale}
                                highlightRect={highlightRect}
                                onDocumentLoadSuccess={onDocumentLoadSuccess}
                                changePage={changePage}
                                changeScale={changeScale}
                                setShowPdf={setShowPdf}
                            />
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4 p-8 text-center bg-slate-800/20">
                            <div className="w-16 h-16 bg-slate-800/50 rounded-2xl flex items-center justify-center border border-slate-700/50">
                                <FileText size={32} className="text-slate-600" />
                            </div>
                            <div>
                                <h4 className="text-slate-400 font-medium mb-1">暂无财报 PDF</h4>
                                <p className="text-xs text-slate-600">点击左侧"生成 AI 解读"可自动加载相关财报文件</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Floating AI Assistant */}
            <FloatingAIAssistant />
        </div>
    );
};

export default FinancialAnalysisPage;
