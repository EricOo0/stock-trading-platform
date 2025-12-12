import React, { useState } from 'react';
import { deepResearchAPI } from '../services/deepResearchAPI';
import { FiSearch, FiMonitor, FiCpu, FiFileText } from 'react-icons/fi';

const DeepResearchPage: React.FC = () => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [sessionId, setSessionId] = useState<string>('');
    const [logs, setLogs] = useState<string[]>([]);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setIsLoading(true);
        setLogs(prev => [...prev, `Starting research on: "${query}"...`]);
        setResult(null);

        // Generate a new session ID for this task
        const newSessionId = `research_${Date.now()}`;
        setSessionId(newSessionId);

        try {
            setLogs(prev => [...prev, `Initializing session: ${newSessionId}`]);

            const response = await deepResearchAPI.startResearch(query, newSessionId);

            if (response.status === 'success') {
                setResult(response.data);
                setLogs(prev => [...prev, 'Research completed successfully.']);
            } else {
                setLogs(prev => [...prev, `Error: ${response.message}`]);
            }
        } catch (error) {
            setLogs(prev => [...prev, 'System Error: Failed to execute research.']);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="p-6 h-full flex flex-col gap-6">
            <header>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <FiSearch className="text-blue-500" />
                    Deep Research Agent
                </h1>
                <p className="text-gray-400 text-sm mt-1">
                    Powered by browser automation and recursive search.
                </p>
            </header>

            {/* Input Section */}
            <div className="bg-[#1e1e1e] p-4 rounded-xl border border-gray-800 flex gap-4">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter a complex research topic (e.g., 'Latest trends in renewable energy stocks for Q4 2025')..."
                    className="flex-1 bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    disabled={isLoading}
                />
                <button
                    onClick={handleSearch}
                    disabled={isLoading}
                    className={`px-6 py-2 rounded-lg font-medium transition-all ${isLoading
                            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-900/20'
                        }`}
                >
                    {isLoading ? 'Researching...' : 'Start Research'}
                </button>
            </div>

            {/* Main Content Grid */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">

                {/* Left Panel: Logs & Results */}
                <div className="flex flex-col gap-6 h-full overflow-hidden">
                    {/* Live Logs */}
                    <div className="flex-1 bg-[#151515] rounded-xl border border-gray-800 flex flex-col overflow-hidden">
                        <div className="p-3 border-b border-gray-800 bg-[#1e1e1e] flex items-center gap-2">
                            <FiCpu className="text-green-500" />
                            <span className="font-medium text-sm">Execution Logs</span>
                        </div>
                        <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-2 text-gray-300">
                            {logs.length === 0 && (
                                <div className="text-gray-600 italic">Waiting for input...</div>
                            )}
                            {logs.map((log, i) => (
                                <div key={i} className="break-words border-l-2 border-green-900 pl-2">
                                    <span className="text-green-600 mr-2">{'>'}</span>
                                    {log}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Final Result */}
                    {result && (
                        <div className="flex-1 bg-[#1e1e1e] rounded-xl border border-gray-800 p-4 overflow-y-auto">
                            <h3 className="font-bold mb-2 flex items-center gap-2 text-blue-400">
                                <FiFileText /> Research Findings
                            </h3>
                            <div className="prose prose-invert max-w-none text-sm">
                                <pre className="whitespace-pre-wrap font-sans text-gray-300">
                                    {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
                                </pre>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Panel: Browser View */}
                <div className="bg-[#151515] rounded-xl border border-gray-800 flex flex-col overflow-hidden shadow-2xl">
                    <div className="p-3 border-b border-gray-800 bg-[#1e1e1e] flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <FiMonitor className="text-purple-500" />
                            <span className="font-medium text-sm">Live Browser Session</span>
                        </div>
                        {sessionId && (
                            <span className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-400">
                                SID: {sessionId.slice(-6)}
                            </span>
                        )}
                    </div>

                    <div className="flex-1 relative bg-black flex items-center justify-center">
                        {sessionId ? (
                            <iframe
                                src={`/api/browser/session/${sessionId}/view`}
                                className="absolute inset-0 w-full h-full border-0"
                                title="Browser Session"
                                allow="clipboard-read; clipboard-write"
                            />
                        ) : (
                            <div className="text-center text-gray-500">
                                <FiMonitor size={48} className="mx-auto mb-4 opacity-20" />
                                <p>Browser inactive</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeepResearchPage;
