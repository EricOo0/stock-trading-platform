import React, { useState } from 'react';
import { stockAPI } from '../../services/stockAPI';
import FinancialReportHeader from './components/FinancialReportHeader';
import FinancialAnalysisPanel from './components/FinancialAnalysisPanel';
import FinancialPDFViewer from './components/FinancialPDFViewer';
import type { FinancialReport, AnchorMap, Citation } from './components/types';
import { Send, Bot, User, Maximize2, Minimize2 } from 'lucide-react';

import { FinancialIndicatorsDisplay } from '../Financial';
import { getFinancialIndicators } from '../../services/financialService';
import type { FinancialIndicators } from '../../types/financial';

interface AIChatPanelProps {
    isExpanded?: boolean;
    onToggleExpand?: () => void;
}

// Simple AI Chat Panel Component
const AIChatPanel: React.FC<AIChatPanelProps> = ({ isExpanded, onToggleExpand }) => {
    const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string }[]>([
        { role: 'ai', content: '你好！我是你的AI财报助手。关于这家公司的财报，你有什么想问的吗？' }
    ]);
    const [input, setInput] = useState('');

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages(prev => [...prev, { role: 'user', content: input }]);
        // Simulate AI response
        setTimeout(() => {
            setMessages(prev => [...prev, { role: 'ai', content: '这是一个实验性功能，目前仅用于展示布局。' }]);
        }, 1000);
        setInput('');
    };

    return (
        <div className={`flex flex-col h-full bg-slate-800 rounded-xl border border-slate-700 overflow-hidden transition-all duration-300 ${isExpanded ? 'shadow-2xl' : ''}`}>
            <div className="p-4 border-b border-slate-700 bg-slate-800/50 flex justify-between items-center">
                <h3 className="text-white font-medium flex items-center gap-2">
                    <Bot size={18} className="text-blue-400" />
                    AI 助手
                </h3>
                {onToggleExpand && (
                    <button
                        onClick={onToggleExpand}
                        className="text-slate-400 hover:text-white transition-colors p-1 hover:bg-slate-700 rounded"
                        title={isExpanded ? "Minimize" : "Expand"}
                    >
                        {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                    </button>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'ai' ? 'bg-blue-600' : 'bg-slate-600'
                            }`}>
                            {msg.role === 'ai' ? <Bot size={16} /> : <User size={16} />}
                        </div>
                        <div className={`rounded-lg p-3 text-sm max-w-[80%] ${msg.role === 'ai' ? 'bg-slate-700 text-slate-200' : 'bg-blue-600 text-white'
                            }`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 border-t border-slate-700 bg-slate-800/50">
                <div className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="输入你的问题..."
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-4 pr-10 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                    <button
                        onClick={handleSend}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-400 transition-colors"
                    >
                        <Send size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};

const ExperimentalFinancialTab: React.FC = () => {
    const [chatExpanded, setChatExpanded] = useState(false);
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

        // Find the anchor info
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
        <div className="flex flex-col h-[calc(100vh-140px)] gap-4">
            {/* Search Header */}
            <FinancialReportHeader
                financialSearchQuery={financialSearchQuery}
                setFinancialSearchQuery={setFinancialSearchQuery}
                handleFinancialSearch={handleFinancialSearch}
                financialLoading={financialLoading}
                isFullScreen={isFullScreen}
                setIsFullScreen={setIsFullScreen}
                error={error}
            />

            {/* 3-Column Layout */}
            <div className="flex-1 grid grid-cols-12 gap-4 min-h-0 relative">

                {/* Left Column: AI Chat (20%) */}
                <div className={`
                    ${chatExpanded ? 'absolute inset-0 z-50 bg-slate-900/95 backdrop-blur-sm p-4' : 'col-span-3 min-h-0'} 
                    transition-all duration-300 ease-in-out
                `}>
                    <AIChatPanel isExpanded={chatExpanded} onToggleExpand={() => setChatExpanded(!chatExpanded)} />
                </div>

                {/* Placeholder for Layout Stability */}
                {chatExpanded && <div className="col-span-3 min-h-0" />}

                {/* Middle Column: Financial Analysis (50%) */}
                <div className="col-span-6 flex flex-col gap-4 min-h-0 overflow-y-auto bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <h3 className="text-white font-medium mb-2">财报对比分析</h3>

                    <div className="flex-1 flex flex-col gap-4">
                        {/* Analysis Panel */}
                        <FinancialAnalysisPanel
                            financialData={financialData}
                            financialLoading={financialLoading}
                            isAnalyzing={isAnalyzing}
                            analysisReport={analysisReport}
                            analysisDate={analysisDate}
                            citations={citations}
                            showPdf={showPdf}
                            handleAnalyze={handleAnalyze}
                            handleCitationClick={handleCitationClick}
                        />

                        {/* PDF Viewer - Stacked below analysis in middle column */}
                        {showPdf && (
                            <div className="h-[600px] border-t border-slate-700 pt-4">
                                <FinancialPDFViewer
                                    financialData={financialData}
                                    pdfUrl={pdfUrl} // Note: This needs to be set correctly. In original it's derived.
                                    // We might need to pass the logic to setPdfUrl from FinancialAnalysisPanel or handle it here
                                    // For simplicity, we assume FinancialPDFViewer handles the URL generation internally or we need to copy that logic
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
                        )}
                    </div>
                </div>

                {/* Right Column: Financial Indicators (30%) */}
                <div className="col-span-3 min-h-0 overflow-y-auto bg-slate-50 rounded-xl p-4">
                    <h3 className="text-gray-900 font-bold mb-4">关键财务指标</h3>
                    {financialIndicators ? (
                        <div className="space-y-6">
                            {/* We need to adapt FinancialIndicatorsDisplay to fit in a narrow column 
                   or just render the cards vertically. 
                   The component itself has a grid layout: grid-cols-1 md:grid-cols-2 lg:grid-cols-3
                   In a narrow column, it will likely fall back to grid-cols-1, which is perfect.
               */}
                            <FinancialIndicatorsDisplay
                                indicators={financialIndicators}
                                symbol={indicatorSymbol}
                                market={indicatorMarket}
                            />
                        </div>
                    ) : (
                        <div className="text-gray-500 text-center mt-10">
                            暂无数据，请先搜索股票
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default ExperimentalFinancialTab;
