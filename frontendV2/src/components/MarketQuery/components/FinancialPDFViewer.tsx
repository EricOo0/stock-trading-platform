import React, { useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { FileText, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, ExternalLink, Loader2 } from 'lucide-react';
import type { FinancialReport } from './types';

// Set worker for PDF.js
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

interface FinancialPDFViewerProps {
  financialData: FinancialReport | null;
  pdfUrl: string;
  currentPdfPage: number;
  numPages: number | null;
  scale: number;
  highlightRect: [number, number, number, number] | null;
  onDocumentLoadSuccess: ({ numPages }: { numPages: number }) => void;
  changePage: (offset: number) => void;
  changeScale: (delta: number) => void;
  setShowPdf: (show: boolean) => void;
}

const pdfOptions = {
  cMapUrl: 'https://unpkg.com/pdfjs-dist@5.4.296/cmaps/',
  cMapPacked: true,
};

const FinancialPDFViewer: React.FC<FinancialPDFViewerProps> = ({
  financialData,
  pdfUrl,
  currentPdfPage,
  numPages,
  scale,
  highlightRect,
  onDocumentLoadSuccess,
  changePage,
  changeScale,
  setShowPdf
}) => {
  const pdfIframeRef = useRef<HTMLIFrameElement>(null);

  return (
    <div className="flex-1 bg-slate-900 rounded-xl border border-slate-700 flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
      <div className="flex items-center justify-between p-3 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-slate-400" />
          <span className="text-sm font-medium text-slate-200 truncate max-w-[200px]">
            {financialData?.symbol} 财报原件
          </span>
          {pdfUrl.toLowerCase().endsWith('.pdf') && (
              <div className="flex items-center gap-1 ml-2">
                  <button onClick={() => changePage(-1)} disabled={currentPdfPage <= 1} className="p-1 hover:bg-slate-700 rounded text-slate-400 disabled:opacity-30">
                      <ChevronLeft size={14} />
                  </button>
                  <span className="text-xs text-slate-400 min-w-[40px] text-center">
                    {currentPdfPage} / {numPages || '--'}
                  </span>
                  <button onClick={() => changePage(1)} disabled={currentPdfPage >= (numPages || 1)} className="p-1 hover:bg-slate-700 rounded text-slate-400 disabled:opacity-30">
                      <ChevronRight size={14} />
                  </button>
              </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {pdfUrl.toLowerCase().endsWith('.pdf') && (
              <div className="flex items-center gap-1 mr-2 border-r border-slate-700 pr-2">
                  <button onClick={() => changeScale(-0.1)} className="p-1 hover:bg-slate-700 rounded text-slate-400">
                      <ZoomOut size={14} />
                  </button>
                  <span className="text-xs text-slate-400 min-w-[30px] text-center">
                      {Math.round(scale * 100)}%
                  </span>
                  <button onClick={() => changeScale(0.1)} className="p-1 hover:bg-slate-700 rounded text-slate-400">
                      <ZoomIn size={14} />
                  </button>
              </div>
          )}
          <a 
            href={financialData?.latest_report?.download_url || pdfUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
            title="在新窗口打开"
          >
            <ExternalLink size={16} />
          </a>
          <button 
            onClick={() => setShowPdf(false)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
          >
            ✕
          </button>
        </div>
      </div>
      <div className="flex-1 bg-slate-500/10 relative overflow-auto flex justify-center p-4">
        {pdfUrl.toLowerCase().includes('.pdf') ? (
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              className="shadow-lg"
              options={pdfOptions}
              loading={<div className="flex items-center justify-center h-full text-slate-400"><Loader2 className="animate-spin mr-2"/> 加载PDF中...</div>}
              error={<div className="flex items-center justify-center h-full text-red-400">无法加载PDF文件</div>}
            >
              <Page 
                  key={`page_${currentPdfPage}_${scale}`} // Force re-render when page or scale changes
                  pageNumber={currentPdfPage} 
                  scale={scale} 
                  renderTextLayer={true} 
                  renderAnnotationLayer={true}
                  className="shadow-lg"
              >
                  {highlightRect && (
                      <div
                          style={{
                              position: 'absolute',
                              left: highlightRect[0] * scale,
                              top: highlightRect[1] * scale,
                              width: (highlightRect[2] - highlightRect[0]) * scale,
                              height: (highlightRect[3] - highlightRect[1]) * scale,
                              backgroundColor: 'rgba(255, 255, 0, 0.3)',
                              border: '2px solid orange',
                              pointerEvents: 'none',
                              zIndex: 10
                          }}
                      />
                  )}
              </Page>
            </Document>
        ) : (
            <iframe
              ref={pdfIframeRef}
              src={pdfUrl}
              className="w-full h-full bg-white rounded-lg shadow-lg"
              title="Financial Report HTML"
            />
        )}
      </div>
    </div>
  );
};

export default FinancialPDFViewer;
