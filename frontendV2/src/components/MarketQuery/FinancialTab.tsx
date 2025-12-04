import React, { useState } from 'react';
import { stockAPI } from '../../services/stockAPI';
import FinancialReportHeader from './components/FinancialReportHeader';
import FinancialAnalysisPanel from './components/FinancialAnalysisPanel';
import FinancialPDFViewer from './components/FinancialPDFViewer';
import type { FinancialReport, AnchorMap, Citation } from './components/types';

import { FinancialIndicatorsDisplay } from '../Financial';
import { getFinancialIndicators } from '../../services/financialService';
import type { FinancialIndicatorsData } from '../../types/financial';

const FinancialTab: React.FC = () => {
  const [financialSearchQuery, setFinancialSearchQuery] = useState('');
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [financialData, setFinancialData] = useState<FinancialReport | null>(null);
  const [financialLoading, setFinancialLoading] = useState(false);
  const [error, setError] = useState('');

  // Indicators State
  const [financialIndicators, setFinancialIndicators] = useState<FinancialIndicatorsData | null>(null);
  const [indicatorsLoading, setIndicatorsLoading] = useState(false);

  // Analysis States
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisReport, setAnalysisReport] = useState('');
  const [analysisDate, setAnalysisDate] = useState('');
  const [citations, setCitations] = useState<Citation[]>([]); // Keep legacy citations for backward compat if needed
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
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '获取财报数据失败');
    } finally {
      setFinancialLoading(false);
      setIndicatorsLoading(false);
    }
  };

  const handleFinancialSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!financialSearchQuery.trim()) return;

    let query = financialSearchQuery.trim();
    const match = query.match(/\((.*?)\)/);
    if (match && match[1]) {
      query = match[1].trim();
    }

    await fetchFinancialReport(query);
  };

  const handleAnalyze = async () => {
    if (!financialData?.symbol) return;

    setIsAnalyzing(true);
    setError('');
    setAnalysisReport('');
    setCitations([]);

    try {
      const response = await stockAPI.analyzeFinancialReport(financialData.symbol);
      if (response.status === 'success' && response.report) {
        setAnalysisReport(response.report);
        if (response.report_date) setAnalysisDate(response.report_date);

        // Handle anchor map
        if (response.anchor_map) {
          setAnchorMap(response.anchor_map);
        }

        // Handle citations and PDF
        if (response.citations && response.citations.length > 0) {
          setCitations(response.citations);
        }

        if (response.pdf_url) {
          setPdfUrl(response.pdf_url);
          setShowPdf(true); // Automatically show PDF if available
        } else if (financialData.latest_report?.download_url) {
          // Fallback to download_url if pdf_url not returned by analysis
          setPdfUrl(financialData.latest_report.download_url);
          setShowPdf(true);
        }

      } else {
        setError(response.message || '分析失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
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
        // For HTML, we simply append the anchor ID as a hash to the URL
        // React state update will propagate to the iframe src, causing a jump
        const currentBaseUrl = pdfUrl.split('#')[0];
        const newUrl = `${currentBaseUrl}#${anchorId}`;
        // Only update if different to avoid unnecessary re-renders, 
        // though setting same URL might be needed if user scrolled away and wants to jump back.
        // For iframe hash changes, simply setting it works.
        setPdfUrl(newUrl);
      }
    } else {
      // Fallback logic for when anchor is not found in map

      // 1. Try legacy numeric support
      const pageNum = parseInt(anchorId);
      if (!isNaN(pageNum)) {
        setCurrentPdfPage(pageNum);
        return;
      }

      // 2. Try parsing pdf_PAGE_... format
      // Format: pdf_PAGE_START-END (e.g. pdf_4_56-57)
      if (anchorId.startsWith('pdf_')) {
        const parts = anchorId.split('_');
        if (parts.length >= 2) {
          const page = parseInt(parts[1]);
          if (!isNaN(page)) {
            setCurrentPdfPage(page);
            setHighlightRect(null);
            return;
          }
        }
      }

      // 3. Try HTML fallback (if anchorId starts with html_)
      if (anchorId.startsWith('html_')) {
        const currentBaseUrl = pdfUrl.split('#')[0];
        const newUrl = `${currentBaseUrl}#${anchorId}`;
        setPdfUrl(newUrl);
      }
    }
  };

  return (
    <div className={`${isFullScreen
      ? 'fixed inset-0 z-[100] bg-slate-800 h-screen w-screen rounded-none'
      : 'bg-slate-800 rounded-xl h-[calc(100vh-140px)] min-h-[600px] relative'
      } p-6 shadow-sm border border-slate-700 flex flex-col transition-all duration-200`}>

      <FinancialReportHeader
        financialSearchQuery={financialSearchQuery}
        setFinancialSearchQuery={setFinancialSearchQuery}
        handleFinancialSearch={handleFinancialSearch}
        financialLoading={financialLoading}
        isFullScreen={isFullScreen}
        setIsFullScreen={setIsFullScreen}
        error={error}
      />

      {/* Main Content Area - Flex Container */}
      <div className="flex-1 flex flex-col gap-6 min-h-0 overflow-hidden">

        {/* Financial Indicators Section */}
        {financialIndicators && (
          <div className="flex-shrink-0">
            <FinancialIndicatorsDisplay
              data={financialIndicators}
              isLoading={indicatorsLoading}
            />
          </div>
        )}

        <div className="flex-1 flex gap-6 min-h-0 overflow-hidden">
          {/* Left Column: Analysis Result */}
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

          {/* Right Column: PDF Viewer */}
          {showPdf && pdfUrl && (
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
          )}
        </div>
      </div>
    </div>
  );
};

export default FinancialTab;
