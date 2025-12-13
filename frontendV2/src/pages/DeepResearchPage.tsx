import React, { useState, useRef, useEffect } from 'react';
import { deepResearchAPI } from '../services/deepResearchAPI';
import ActivityCarousel from '../components/ActivityCarousel';
import type { ActivityCard } from '../components/ActivityCarousel';
import { FiSearch, FiCpu, FiFileText, FiLoader, FiLayers } from 'react-icons/fi';

interface StreamItem {
    id: string;
    type: 'thought' | 'tool_notice';
    content: string;
    timestamp: number;
}

const DeepResearchPage: React.FC = () => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // Unified stream state for the right panel
    const [streamItems, setStreamItems] = useState<StreamItem[]>([]);

    // We still keep activities for the left panel carousel
    const [activities, setActivities] = useState<ActivityCard[]>([]);
    const [logs, setLogs] = useState<string[]>([]);

    const addLog = (msg: string) => setLogs(prev => [...prev, msg]);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setIsLoading(true);
        setActivities([]);
        setLogs([]);
        setStreamItems([]);
        addLog(`Starting research on: "${query}"...`);

        try {
            const sessionId = await deepResearchAPI.createSession();
            addLog(`Session created: ${sessionId}`);

            const response = await fetch('/api/agent/deep-search/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, session_id: sessionId })
            });

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);

                        if (event.type === 'tool') {
                            const eventTime = Date.now();
                            if (event.status === 'start') {
                                // 1. Update Carousel Logic
                                const newActivity: ActivityCard = {
                                    id: event.id || eventTime.toString(),
                                    type: 'tool',
                                    title: `Invoking: ${event.tool}`,
                                    detail: event.input,
                                    status: 'pending',
                                    timestamp: eventTime
                                };
                                setActivities(prev => [...prev, newActivity]);
                                addLog(`[TOOL START] ${event.tool} on ${event.input}`);

                                // 2. Insert Tool Notice into Stream (Breaks the thought bubble)
                                setStreamItems(prev => [...prev, {
                                    id: `tool-${eventTime}`,
                                    type: 'tool_notice',
                                    content: `Calling Tool: ${event.tool}...`,
                                    timestamp: eventTime
                                }]);
                            }
                            else if (event.status === 'end') {
                                // Update Carousel Logic
                                setActivities(prev => {
                                    const copy = [...prev];
                                    let targetIndex = -1;

                                    if (event.id) {
                                        targetIndex = copy.findIndex(a => a.id === event.id);
                                    } else {
                                        // Find last pending activity (backward compatible replacement for findLastIndex)
                                        for (let i = copy.length - 1; i >= 0; i--) {
                                            if (copy[i].status === 'pending') {
                                                targetIndex = i;
                                                break;
                                            }
                                        }
                                    }

                                    if (targetIndex !== -1) {
                                        copy[targetIndex] = {
                                            ...copy[targetIndex],
                                            status: 'completed',
                                            detail: `${copy[targetIndex].detail}\n\nResult: ${event.output}`
                                        };
                                    }
                                    return copy;
                                });
                                addLog(`[TOOL END] Result: ${event.output}`);
                            }
                        }
                        else if (event.type === 'thought') {
                            setStreamItems(prev => {
                                const last = prev[prev.length - 1];
                                // If last item is a thought, merge content
                                if (last && last.type === 'thought') {
                                    return [
                                        ...prev.slice(0, -1),
                                        { ...last, content: last.content + event.content }
                                    ];
                                }
                                // Otherwise start new bubble
                                return [...prev, {
                                    id: `thought - ${Date.now()} `,
                                    type: 'thought',
                                    content: event.content,
                                    timestamp: Date.now()
                                }];
                            });
                        }
                        else if (event.type === 'result') {
                            addLog("[COMPLETE] Research finished.");
                        }
                        else if (event.type === 'error') {
                            addLog(`[ERROR] ${event.content} `);
                        }

                    } catch (e) {
                        console.warn("Failed to parse NDJSON line", line);
                    }
                }
            }
        } catch (error) {
            addLog('System Error: Failed to execute research.');
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const streamEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [streamItems]);

    return (
        <div className="h-screen bg-[#F5F5F7] text-gray-900 font-sans overflow-hidden flex flex-col">
            {/* Header */}
            <header className="px-8 py-5 flex items-center justify-between border-b border-gray-200 bg-white/80 backdrop-blur-md z-10">
                <div className="flex items-center gap-6">
                    <h1 className="text-xl font-bold flex items-center gap-2 tracking-tight">
                        <span className="w-8 h-8 rounded-lg bg-black text-white flex items-center justify-center">
                            <FiCpu size={16} />
                        </span>
                        网络舆情监测
                    </h1>
                    {/* Monitor Sources Box */}
                    <div className="hidden md:flex items-center gap-3 px-3 py-1.5 bg-gray-100/50 rounded-lg border border-gray-200/50">
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                            <FiLayers size={10} /> 接入源
                        </span>
                        <div className="h-3 w-px bg-gray-300" />
                        <div className="flex gap-2">
                            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-white rounded shadow-sm border border-gray-100 text-[10px] font-semibold text-gray-700">
                                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" /> Reddit
                            </span>
                            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-white rounded shadow-sm border border-gray-100 text-[10px] font-semibold text-gray-700">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" /> 雪球 (Xueqiu)
                            </span>
                        </div>
                    </div>
                </div>

                {/* Search Bar */}
                <div className="flex-1 max-w-2xl mx-12">
                    <div className="relative group">
                        <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-black transition-colors" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Type a research objective..."
                            className="w-full bg-gray-100 hover:bg-white border-none focus:bg-white focus:ring-1 focus:ring-gray-200 rounded-xl pl-12 pr-20 py-3 text-sm transition-all focus:shadow-lg shadow-sm"
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            disabled={isLoading}
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                            {isLoading ? <FiLoader className="animate-spin text-orange-500" /> :
                                <button onClick={handleSearch} className="p-1.5 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors shadow-sm">
                                    <FiSearch size={14} />
                                </button>
                            }
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <span className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-xs font-semibold text-gray-400 tracking-wide">SYSTEM READY</span>
                </div>
            </header>

            {/* Split Content */}
            <div className="flex-1 flex min-h-0">
                {/* Left Panel: Carousel */}
                <div className="w-[60%] p-8 flex flex-col bg-[#F5F5F7]">
                    <ActivityCarousel activities={activities} />
                </div>

                {/* Right Panel: Intelligence Stream */}
                <div className="w-[40%] border-l border-gray-200 bg-white flex flex-col shadow-xl z-20">
                    <div className="p-5 border-b border-gray-50 flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur z-10">
                        <h3 className="text-xs font-bold text-gray-900 uppercase tracking-widest flex items-center gap-2">
                            <FiFileText /> Intelligence Stream
                        </h3>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 custom-scrollbar-light space-y-6">
                        {streamItems.length === 0 && logs.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-gray-300 gap-4 opacity-50">
                                <FiFileText size={48} />
                                <p className="text-sm font-medium">Waiting for agent thoughts...</p>
                            </div>
                        ) : (
                            <>
                                {streamItems.map((item, idx) => (
                                    <div key={item.id} className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards" style={{ animationDelay: `${idx * 0.1} s` }}>
                                        {item.type === 'thought' ? (
                                            <div className="flex flex-col gap-2">
                                                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-wider ml-1 self-start">
                                                    Agent Thought
                                                </span>
                                                <div className="bg-blue-50/50 p-4 rounded-2xl rounded-tl-none border border-blue-100/50 text-gray-800 text-sm leading-relaxed shadow-sm">
                                                    <pre className="whitespace-pre-wrap font-sans bg-transparent p-0 m-0 border-none">{item.content}</pre>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="flex items-center justify-center py-4">
                                                <div className="bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200 flex items-center gap-2 shadow-sm">
                                                    <FiLoader className="animate-spin text-gray-400" size={12} />
                                                    <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wide">
                                                        {item.content}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}

                                {logs.length > 0 && (
                                    <div className="pt-8 opacity-40 hover:opacity-100 transition-opacity duration-300">
                                        <div className="h-px bg-gray-200 mb-4" />
                                        <div className="space-y-1 font-mono text-[10px] text-gray-400">
                                            {logs.slice(-5).map((log, i) => (
                                                <div key={i}>{log}</div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                <div ref={streamEndRef} />
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeepResearchPage;
