import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Brain, Loader2, FileText } from 'lucide-react';
import type { FinancialReport, Citation } from './types';

interface FinancialAnalysisPanelProps {
  financialData: FinancialReport | null;
  financialLoading: boolean;
  isAnalyzing: boolean;
  analysisReport: string;
  analysisDate: string;
  citations: Citation[];
  showPdf: boolean;
  handleAnalyze: () => void;
  handleCitationClick: (anchorId: string) => void;
}

const FinancialAnalysisPanel: React.FC<FinancialAnalysisPanelProps> = ({
  financialData,
  financialLoading,
  isAnalyzing,
  analysisReport,
  analysisDate,
  citations,
  showPdf,
  handleAnalyze,
  handleCitationClick
}) => {

  // Custom Markdown Components to render citations
  const MarkdownComponents = {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    a: (props: any) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { node, href, ...rest } = props;
      const linkHref = href || '';
      
      // Handle anchor links (e.g., #html_123, #pdf_1_2)
      if (linkHref.startsWith('#html_') || linkHref.startsWith('#pdf_')) {
        const id = linkHref.replace(/^#/, '');
        return (
            <button
              onClick={(e) => {
                e.preventDefault();
                handleCitationClick(id);
              }}
              className="inline-flex items-center justify-center px-1.5 mx-1 text-[10px] font-bold text-blue-400 bg-blue-900/50 border border-blue-500/50 rounded hover:bg-blue-500 hover:text-white transition-all cursor-pointer -translate-y-0.5"
              title={`Jump to anchor ${id}`}
            >
              {id}
            </button>
        );
      }

      if (linkHref.startsWith('#cite-')) {
        const id = linkHref.replace('#cite-', '');
        const citation = citations.find(c => c.id === id);
        if (citation) {
          return (
            <button
              onClick={(e) => {
                e.preventDefault();
                handleCitationClick(citation.id);
              }}
              className="inline-flex items-center justify-center w-5 h-5 mx-1 text-[10px] font-bold text-blue-400 bg-blue-900/50 border border-blue-500/50 rounded-full hover:bg-blue-500 hover:text-white transition-all cursor-pointer -translate-y-1"
              title={`Page ${citation.page_num}: ${citation.content.substring(0, 50)}...`}
            >
              {id}
            </button>
          );
        }
      }
      return <a href={linkHref} {...rest} className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer" />;
    }
  };

  // Pre-process report text to convert [锚点: ID] or [ID] to link
  const processedReport = useMemo(() => {
    if (!analysisReport) return '';
    
    let processed = analysisReport;

    // 1. Normalize: Remove hallucinated links from LLM (e.g., [html_123](...) or [html_123] (...))
    // Matches [html_123] followed optionally by (url) with optional whitespace
    // Replaces with simple [html_123] to ensure clean state
    processed = processed.replace(/\[\s*(?:锚点:\s*)?((?:pdf|html)_[0-9a-zA-Z_-]+)\s*\](?:\s*\([^)]+\))?/g, '[$1]');

    // 2. Convert to Markdown Links
    // Replace [html_123] with [html_123](#html_123), BUT ONLY if not already followed by (
    // Also handle potential spaces inside brackets: [ html_123 ]
    processed = processed.replace(/\[\s*((?:pdf|html)_[0-9a-zA-Z_-]+)\s*\](?!\s*\()/g, '[$1](#$1)');
    
    // 4. Fix potential markdown rendering issues
    processed = processed.replace(/([^\n])\n(\*\*|##)/g, '$1\n\n$2');
    
    return processed;
  }, [analysisReport]);

  return (
    <div className={`flex flex-col min-h-0 overflow-hidden transition-all duration-300 ${showPdf ? 'flex-1' : 'w-full max-w-3xl mx-auto'}`}>
      
      {/* Initial Empty State */}
      {!financialData && !financialLoading && (
         <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
           <Brain size={48} className="mb-4 opacity-20" />
           <p>请输入股票代码开始分析</p>
         </div>
      )}

      {/* Analysis Content */}
      {financialData && (
        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
          {/* Basic Info Card */}
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50 mb-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-bold text-white mb-1">{financialData.symbol} 财报概览</h3>
                <p className="text-xs text-slate-400">
                  {financialData.latest_report?.title || '最新财报'} 
                  {financialData.latest_report?.date && ` • ${financialData.latest_report.date}`}
                </p>
              </div>
              {!isAnalyzing && !analysisReport && (
                <button
                  onClick={handleAnalyze}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-medium transition-colors flex items-center gap-1.5"
                >
                  <Brain size={14} />
                  生成AI解读
                </button>
              )}
            </div>
            
            {/* Metrics Preview */}
            {financialData.metrics && financialData.metrics.length > 0 && (
              <div className="grid grid-cols-4 gap-2 mt-4">
                {financialData.metrics.slice(0, 4).map((m, i) => (
                  <div key={i} className="bg-slate-800 p-2 rounded border border-slate-700">
                    <div className="text-[10px] text-slate-400 mb-0.5">{m.date}</div>
                    <div className="text-sm font-mono text-white font-medium">
                      ${(m.revenue / 1e9).toFixed(1)}B
                    </div>
                    <div className="text-[10px] text-slate-500">营收</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Analysis Output */}
          {(isAnalyzing || analysisReport) && (
            <div className="bg-gradient-to-br from-indigo-900/30 to-blue-900/10 rounded-xl p-6 border border-indigo-500/30 relative min-h-[300px]">
              {isAnalyzing && (
                 <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Loader2 className="text-indigo-400 animate-spin mb-3" size={32} />
                    <h6 className="text-white font-medium mb-1">AI 正在阅读财报全文...</h6>
                    <p className="text-indigo-300/60 text-xs">分析关键指标 • 提取风险提示 • 总结业务亮点</p>
                 </div>
              )}
              
              {!isAnalyzing && analysisReport && (
                <>
                  <div className="flex items-center justify-between mb-4 pb-2 border-b border-indigo-500/20">
                    <div className="flex items-center gap-2">
                        <Brain size={18} className="text-indigo-400" />
                        <h4 className="font-bold text-white">深度分析报告</h4>
                    </div>
                    {analysisDate && (
                        <span className="text-xs text-indigo-300/60 font-mono">{analysisDate}</span>
                    )}
                  </div>
                  <div className="prose prose-invert prose-sm max-w-none prose-headings:text-indigo-100 prose-p:text-slate-300 prose-strong:text-white prose-li:text-slate-300">
                    <ReactMarkdown components={MarkdownComponents}>{processedReport}</ReactMarkdown>
                  </div>
                  
                  {/* Citation List Footer */}
                  {citations.length > 0 && (
                    <div className="mt-8 pt-4 border-t border-indigo-500/20">
                      <h5 className="text-xs font-bold text-indigo-300 mb-2 uppercase tracking-wider">参考来源</h5>
                      <div className="space-y-2">
                        {citations.map((cite) => (
                          <div 
                            key={cite.id} 
                            onClick={() => handleCitationClick(cite.id)}
                            className="flex gap-2 p-2 rounded bg-indigo-950/30 hover:bg-indigo-900/50 cursor-pointer transition-colors border border-transparent hover:border-indigo-500/30 group"
                          >
                            <div className="flex-none h-5 px-1.5 rounded bg-indigo-500/20 text-indigo-300 flex items-center justify-center text-[10px] font-bold border border-indigo-500/30 group-hover:border-indigo-400 whitespace-nowrap">
                              {cite.id}
                            </div>
                            <div>
                              <p className="text-xs text-slate-300 line-clamp-2">{cite.content}</p>
                              <p className="text-[10px] text-indigo-400 mt-0.5 flex items-center gap-1">
                                <FileText size={10} />
                                {cite.type === 'pdf' ? `Page ${cite.page_num}` : 'HTML Section'}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FinancialAnalysisPanel;
