import React, { useState } from 'react';
import { stockAPI } from '../../services/stockAPI';
import { Search, Loader2, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';

const WebSearchTab: React.FC = () => {
  const [webSearchQuery, setWebSearchQuery] = useState('');
  const [webSearchResults, setWebSearchResults] = useState<Array<{ title: string; href: string; body: string }>>([]);
  const [webSearchLoading, setWebSearchLoading] = useState(false);
  const [webSearchPage, setWebSearchPage] = useState(1);
  const [jumpToPage, setJumpToPage] = useState('');
  const [error, setError] = useState('');
  const ITEMS_PER_PAGE = 5;

  const totalPages = Math.ceil(webSearchResults.length / ITEMS_PER_PAGE);

  const handleJumpToPage = (e: React.FormEvent) => {
    e.preventDefault();
    const page = parseInt(jumpToPage);
    if (page >= 1 && page <= totalPages) {
      setWebSearchPage(page);
      setJumpToPage('');
    }
  };

  const handleWebSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!webSearchQuery.trim()) return;

    setWebSearchLoading(true);
    setError('');

    try {
      const response = await stockAPI.webSearch(webSearchQuery);

      if (response.status === 'success' && response.results) {
        setWebSearchResults(response.results);
        setWebSearchPage(1);
      } else {
        setError(response.message || '搜索失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
    } finally {
      setWebSearchLoading(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-700">
      <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
        <Search size={18} className="text-green-500" />
        新闻资讯搜索
      </h3>
      <form onSubmit={handleWebSearch} className="flex gap-3 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            value={webSearchQuery}
            onChange={(e) => setWebSearchQuery(e.target.value)}
            placeholder="输入股票代码或公司名称搜索最新资讯 (例如: NVIDIA)"
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20 transition-all"
          />
        </div>
        <button
          type="submit"
          disabled={webSearchLoading}
          className="bg-green-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-sm shadow-green-600/20"
        >
          {webSearchLoading ? '搜索中...' : '搜索'}
        </button>
      </form>

      {webSearchLoading && (
        <div className="mt-3 p-3 bg-green-900/20 border border-green-800/50 rounded-lg text-green-400 text-sm flex items-center gap-2">
          <Loader2 size={16} className="animate-spin" />
          正在搜索新闻资讯...
        </div>
      )}

      {error && (
        <div className="mt-3 p-3 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400 text-sm flex items-center gap-2">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {webSearchResults.length > 0 && (
        <div className="mt-4 space-y-3">
          {webSearchResults
            .slice((webSearchPage - 1) * ITEMS_PER_PAGE, webSearchPage * ITEMS_PER_PAGE)
            .map((result, index) => {
              // Extract domain from URL
              const getDomain = (url: string) => {
                try {
                  const urlObj = new URL(url);
                  return urlObj.hostname.replace('www.', '');
                } catch {
                  return '';
                }
              };

              const domain = getDomain(result.href);
              const faviconUrl = `https://icons.duckduckgo.com/ip3/${domain}.ico`;

              return (
                <div key={index} className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <a
                    href={result.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-base font-semibold text-blue-400 hover:text-blue-300 hover:underline mb-2 block"
                  >
                    {result.title}
                  </a>
                  <p className="text-sm text-slate-400 line-clamp-2 mb-2">{result.body}</p>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <img
                      src={faviconUrl}
                      alt={domain}
                      className="w-4 h-4 rounded-sm"
                      onError={(e) => {
                        // Fallback to a default icon if favicon fails to load
                        e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>';
                      }}
                    />
                    <span className="truncate">{domain}</span>
                  </div>
                </div>
              );
            })}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex flex-wrap justify-center items-center gap-4 mt-6 pt-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setWebSearchPage(p => Math.max(1, p - 1))}
                  disabled={webSearchPage === 1}
                  className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft size={20} />
                </button>

                <span className="text-sm text-slate-400 font-medium min-w-[80px] text-center">
                  {webSearchPage} / {totalPages} 页
                </span>

                <button
                  onClick={() => setWebSearchPage(p => Math.min(totalPages, p + 1))}
                  disabled={webSearchPage === totalPages}
                  className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRight size={20} />
                </button>
              </div>

              {/* Jump to Page */}
              <form onSubmit={handleJumpToPage} className="flex items-center gap-2 pl-4 border-l border-slate-700">
                <input
                  type="number"
                  min={1}
                  max={totalPages}
                  value={jumpToPage}
                  onChange={(e) => setJumpToPage(e.target.value)}
                  placeholder="页码"
                  className="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded-md text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-center"
                />
                <button
                  type="submit"
                  disabled={!jumpToPage || parseInt(jumpToPage) < 1 || parseInt(jumpToPage) > totalPages}
                  className="px-3 py-1 bg-slate-700 text-slate-300 text-sm rounded-md hover:bg-slate-600 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  跳转
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WebSearchTab;
