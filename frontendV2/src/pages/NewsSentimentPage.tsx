import React, { useState, useRef, useEffect } from 'react';
import { newsSentimentAPI } from '../services/newsSentimentAPI';
import ConclusionCard from '../components/ConclusionCard';
import PlanList from '../components/NewsSentiment/PlanList';
import { FiSearch, FiCpu, FiFileText, FiLoader, FiLayers, FiZap, FiCheckCircle, FiArrowLeft } from 'react-icons/fi';
import { 
    EventType, 
} from '../types/newsSentiment';
import type { 
    NewsPlan, 
    TaskUpdatePayload, 
    ConclusionPayload, 
    AgentEvent 
} from '../types/newsSentiment';

interface StreamItem {
    id: string;
    type: 'thought' | 'tool_notice' | 'tool_result' | 'output';
    content: string;
    task_id?: string;
    task_title?: string;
    timestamp: number;
    tool_name?: string;
}

const NewsSentimentPage: React.FC = () => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // State
    const [plan, setPlan] = useState<NewsPlan>({ tasks: [] });
    const [streamItems, setStreamItems] = useState<StreamItem[]>([]);
    const [logs, setLogs] = useState<string[]>([]);
    const [conclusion, setConclusion] = useState<ConclusionPayload | null>(null);
    const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

    const addLog = (msg: string) => setLogs(prev => [...prev, msg]);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setIsLoading(true);
        setPlan({ tasks: [] });
        setLogs([]);
        setStreamItems([]);
        setConclusion(null);
        setSelectedTaskId(null);
        addLog(`Starting research on: "${query}"...`);

        try {
            const sessionId = await newsSentimentAPI.createSession();
            addLog(`Session created: ${sessionId}`);

            const response = await fetch('/api/agent/news-sentiment/start', {
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
                        const event: AgentEvent = JSON.parse(line);

                        switch (event.type) {
                            case EventType.PLAN_UPDATE:
                                setPlan(event.payload as NewsPlan);
                                break;
                            
                            case EventType.TASK_UPDATE:
                                const payload = event.payload as TaskUpdatePayload;
                                handleTaskUpdate(payload);
                                break;
                                
                            case EventType.CONCLUSION:
                                setConclusion(event.payload as ConclusionPayload);
                                addLog("Conclusion received.");
                                break;
                                
                            case EventType.ERROR:
                                addLog(`[ERROR] ${event.payload}`);
                                break;
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
            addLog("Stream closed.");
        }
    };

    const handleTaskUpdate = (payload: TaskUpdatePayload) => {
        const timestamp = payload.timestamp || Date.now();
        const uniqueId = `item-${timestamp}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Find task title for context
        // Note: Using a ref or functional update inside setStreamItems might be better if plan is stale,
        // but here we just need a snapshot or lookup. 
        // We'll trust React state update batching or use a functional update with closure issues potentially.
        // For simplicity, we won't inject title here to avoid dependency complexity, 
        // or we'll fetch it from the latest plan state in a simplified way.
        
        if (payload.type === 'thought') {
            setStreamItems(prev => {
                const last = prev[prev.length - 1];
                // Merge consecutive thoughts for the SAME task
                if (last && last.type === 'thought' && last.task_id === payload.task_id) {
                    return [
                        ...prev.slice(0, -1),
                        { ...last, content: last.content + payload.content }
                    ];
                }
                return [...prev, {
                    id: uniqueId,
                    type: 'thought',
                    content: payload.content,
                    task_id: payload.task_id,
                    timestamp
                }];
            });
        } else if (payload.type === 'tool_call') {
            setStreamItems(prev => [...prev, {
                id: uniqueId,
                type: 'tool_notice',
                content: payload.content, // e.g. "Calling search_web..."
                tool_name: payload.tool_name,
                task_id: payload.task_id,
                timestamp
            }]);
        } else if (payload.type === 'tool_result') {
            setStreamItems(prev => [...prev, {
                id: uniqueId,
                type: 'tool_result',
                content: payload.tool_output || payload.content,
                tool_name: payload.tool_name,
                task_id: payload.task_id,
                timestamp
            }]);
        } else if (payload.type === 'output') {
             setStreamItems(prev => [...prev, {
                id: uniqueId,
                type: 'output',
                content: payload.content,
                task_id: payload.task_id,
                timestamp
            }]);
        }
    };

    const streamEndRef = useRef<HTMLDivElement>(null);
    const streamContainerRef = useRef<HTMLDivElement>(null);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

    // Detect if user scrolled up
    const handleScroll = () => {
        if (!streamContainerRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = streamContainerRef.current;
        // If user is near bottom (within 50px), enable auto-scroll. Otherwise disable.
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
        setShouldAutoScroll(isNearBottom);
    };

    useEffect(() => {
        if (shouldAutoScroll) {
            streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [streamItems, shouldAutoScroll]);

    // Helper to get task title
    const getTaskTitle = (taskId?: string) => {
        if (!taskId) return "System";
        const task = plan.tasks.find(t => t.id === taskId);
        return task ? task.title : taskId;
    };

    const handleSelectTask = (taskId: string) => {
        setSelectedTaskId(taskId);
    };

    const handleBackToOverview = () => {
        setSelectedTaskId(null);
    };

    const displayedItems = streamItems.filter(item => {
        if (!selectedTaskId) {
            // Master View: Show items with no task_id (system) or task_id='master_planning'
            return !item.task_id || item.task_id === 'master_planning';
        }
        return item.task_id === selectedTaskId;
    });

    return (
        <div className="h-screen bg-[#F5F5F7] text-gray-900 font-sans overflow-hidden flex flex-col">
            {/* Header */}
            <header className="px-8 py-5 flex items-center justify-between border-b border-gray-200 bg-white/80 backdrop-blur-md z-10">
                <div className="flex items-center gap-6">
                    <h1 className="text-xl font-bold flex items-center gap-2 tracking-tight">
                        <span className="w-8 h-8 rounded-lg bg-black text-white flex items-center justify-center">
                            <FiCpu size={16} />
                        </span>
                        消息面分析 (v2.0)
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
                            placeholder="Type a research objective (e.g., 'NVDA RTX 5090 supply chain analysis')..."
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
                {/* Left Panel: Plan List & Conclusion */}
                <div className="w-[45%] p-8 flex flex-col bg-[#F5F5F7] overflow-y-auto custom-scrollbar">
                    {conclusion && (
                        <div className="mb-8 animate-in fade-in slide-in-from-top-4 duration-700">
                            <ConclusionCard data={conclusion} />
                        </div>
                    )}
                    <PlanList plan={plan} onSelectTask={handleSelectTask} selectedTaskId={selectedTaskId} />
                </div>

                {/* Right Panel: Intelligence Stream */}
                <div className="w-[55%] border-l border-gray-200 bg-white flex flex-col shadow-xl z-20">
                    <div className="p-5 border-b border-gray-50 flex items-center justify-between bg-white/95 backdrop-blur z-10 min-h-[73px]">
                        {selectedTaskId ? (
                            <div className="flex items-center gap-4 animate-in fade-in slide-in-from-left-2 duration-300">
                                <button 
                                    onClick={handleBackToOverview}
                                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors group"
                                    title="Back to Master Plan"
                                >
                                    <FiArrowLeft className="text-gray-500 group-hover:text-black transition-colors" size={18} />
                                </button>
                                <div>
                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Focusing on Task</div>
                                    <h3 className="text-sm font-bold text-gray-900 truncate max-w-[400px]">
                                        {getTaskTitle(selectedTaskId)}
                                    </h3>
                                </div>
                            </div>
                        ) : (
                            <h3 className="text-xs font-bold text-gray-900 uppercase tracking-widest flex items-center gap-2 animate-in fade-in duration-300">
                                <FiFileText /> Master Intelligence Stream
                            </h3>
                        )}
                    </div>

                    {/* Top Section: Thoughts & Tool Notices (Flex Grow) */}
                    <div 
                        ref={streamContainerRef}
                        onScroll={handleScroll}
                        className="flex-1 overflow-y-auto p-6 custom-scrollbar-light space-y-6 min-h-0 border-b border-gray-100"
                    >
                        {displayedItems.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-gray-300 gap-4 opacity-50">
                                <FiFileText size={48} />
                                <p className="text-sm font-medium">
                                    {selectedTaskId ? "Waiting for worker updates..." : "Waiting for master agent..."}
                                </p>
                            </div>
                        ) : (
                            <>
                                {displayedItems.map((item, idx) => (
                                    <div key={item.id} className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards" style={{ animationDelay: `${idx * 0.05} s` }}>
                                        
                                        {/* Task Context Header if available */}
                                        {item.task_id && (
                                            <div className="flex items-center gap-2 mb-1 opacity-50">
                                                <FiZap size={10} />
                                                <span className="text-[10px] uppercase font-bold tracking-wider">
                                                    {getTaskTitle(item.task_id)}
                                                </span>
                                            </div>
                                        )}

                                        {item.type === 'thought' && (
                                            <div className="flex flex-col gap-2">
                                                <div className="bg-blue-50/50 p-4 rounded-2xl rounded-tl-none border border-blue-100/50 text-gray-800 text-sm leading-relaxed shadow-sm">
                                                    <pre className="whitespace-pre-wrap font-sans bg-transparent p-0 m-0 border-none">{item.content}</pre>
                                                </div>
                                            </div>
                                        )}

                                        {item.type === 'tool_notice' && (
                                            <div className="flex items-center justify-center py-2">
                                                <div className="bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200 flex items-center gap-2 shadow-sm">
                                                    <FiLoader className="animate-spin text-gray-400" size={12} />
                                                    <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wide">
                                                        {item.content}
                                                    </span>
                                                </div>
                                            </div>
                                        )}

                                        {item.type === 'tool_result' && (
                                            <div className="ml-4 pl-4 border-l-2 border-gray-100 py-1">
                                                <div className="text-[10px] font-bold text-gray-400 uppercase mb-1">
                                                    Result: {item.tool_name}
                                                </div>
                                                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded line-clamp-4 hover:line-clamp-none transition-all cursor-pointer">
                                                    {item.content}
                                                </div>
                                            </div>
                                        )}

                                        {item.type === 'output' && (
                                            <div className="bg-green-50 border border-green-100 p-4 rounded-xl text-sm text-gray-800">
                                                <div className="flex items-center gap-2 mb-2 text-green-600 font-bold text-xs uppercase">
                                                    <FiCheckCircle size={12}/> Task Output
                                                </div>
                                                {item.content}
                                            </div>
                                        )}
                                    </div>
                                ))}
                                <div ref={streamEndRef} />
                            </>
                        )}
                    </div>

                    {/* Bottom Section: Logs (Fixed Height) */}
                    <div className="h-1/4 min-h-[150px] overflow-y-auto p-4 bg-gray-50/50 border-t border-gray-200 text-xs font-mono text-gray-500 custom-scrollbar-light">
                        <div className="mb-2 font-bold text-gray-400 uppercase tracking-wider text-[10px]">System Logs</div>
                        <div className="space-y-1">
                            {logs.map((log, i) => (
                                <div key={i} className="break-all hover:text-gray-800 transition-colors border-l-2 border-transparent hover:border-gray-300 pl-2 -ml-2 py-0.5">
                                    {log}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NewsSentimentPage;
