import React, { useState, useEffect, useMemo } from 'react';
import { Search, Brain, Loader2, AlertCircle, Database } from 'lucide-react';
import AgentSelector from '../components/Memory/AgentSelector';
import MemoryCard from '../components/Memory/MemoryCard';
import { memoryService } from '../services/memoryService';
import type { MemoryData, AgentInfo } from '../types/memory';

const AGENTS: AgentInfo[] = [
    {
        id: 'chairman_agent',
        name: 'Chairman',
        displayName: '董事长 (Chairman)',
        color: 'bg-violet-500',
    },
    {
        id: 'marketdatainvestigator_agent',
        name: 'MarketDataInvestigator',
        displayName: '市场数据调查员',
        color: 'bg-blue-500',
    },
    {
        id: 'macrodatainvestigator_agent',
        name: 'MacroDataInvestigator',
        displayName: '宏观数据调查员',
        color: 'bg-cyan-500',
    },
    {
        id: 'sentimentinvestigator_agent',
        name: 'SentimentInvestigator',
        displayName: '情绪调查员',
        color: 'bg-pink-500',
    },
    {
        id: 'newsinvestigator_agent',
        name: 'NewsInvestigator',
        displayName: '新闻调查员',
        color: 'bg-amber-500',
    },
    {
        id: 'financialreportagent_agent',
        name: 'FinancialReportAgent',
        displayName: '财报分析员',
        color: 'bg-emerald-500',
    },
];

const MemoryVisualizationPage: React.FC = () => {
    const [selectedAgent, setSelectedAgent] = useState(AGENTS[0].id);
    const [searchQuery, setSearchQuery] = useState('');
    const [memoryData, setMemoryData] = useState<MemoryData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch memories when agent changes
    useEffect(() => {
        const fetchMemories = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await memoryService.getAgentMemories(selectedAgent);
                setMemoryData(data);
            } catch (err) {
                setError('获取记忆数据失败，请稍后重试');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchMemories();
    }, [selectedAgent]);

    // Filter memories based on search query
    const filteredMemories = useMemo(() => {
        if (!memoryData || !searchQuery.trim()) return memoryData;

        const query = searchQuery.toLowerCase();
        return {
            ...memoryData,
            working_memory: memoryData.working_memory?.filter((item) =>
                item.content.toLowerCase().includes(query)
            ) || [],
            episodic_memory: memoryData.episodic_memory?.filter((item) => {
                const content = typeof item.content === 'string'
                    ? item.content
                    : JSON.stringify(item.content);
                return content.toLowerCase().includes(query);
            }) || [],
            semantic_memory: memoryData.semantic_memory?.filter((item) => {
                const content = typeof item.content === 'string'
                    ? item.content
                    : JSON.stringify(item.content);
                return content.toLowerCase().includes(query);
            }) || [],
        };
    }, [memoryData, searchQuery]);

    const workingCount = filteredMemories?.working_memory?.length || 0;
    const episodicCount = filteredMemories?.episodic_memory?.length || 0;
    const semanticCount = filteredMemories?.semantic_memory?.length || 0;

    return (
        <div className="h-full flex flex-col bg-slate-900">
            {/* Header */}
            <div className="flex-shrink-0 bg-slate-800/50 border-b border-slate-700 p-6">
                <div className="max-w-[1800px] mx-auto">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                            <Brain size={24} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-white">记忆可视化</h1>
                            <p className="text-sm text-slate-400">查看和搜索 Agent 的三层记忆系统</p>
                        </div>
                    </div>

                    {/* Controls */}
                    <div className="flex flex-col sm:flex-row gap-4">
                        <AgentSelector
                            agents={AGENTS}
                            selectedAgent={selectedAgent}
                            onAgentChange={setSelectedAgent}
                        />

                        <div className="flex-1 relative">
                            <Search
                                size={20}
                                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                            />
                            <input
                                type="text"
                                placeholder="搜索记忆内容..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="
                  w-full pl-12 pr-4 py-3 rounded-xl
                  bg-slate-800/50 border border-slate-700
                  text-white placeholder-slate-400
                  focus:outline-none focus:border-slate-600 focus:bg-slate-800/70
                  transition-all duration-200
                "
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="max-w-[1800px] mx-auto">
                    {loading ? (
                        <div className="flex items-center justify-center h-96">
                            <div className="text-center">
                                <Loader2 size={48} className="text-purple-500 animate-spin mx-auto mb-4" />
                                <p className="text-slate-400">加载记忆数据中...</p>
                            </div>
                        </div>
                    ) : error ? (
                        <div className="flex items-center justify-center h-96">
                            <div className="text-center">
                                <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
                                <p className="text-slate-300 mb-2">{error}</p>
                                <button
                                    onClick={() => window.location.reload()}
                                    className="text-sm text-blue-400 hover:text-blue-300"
                                >
                                    重新加载
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                            {/* Working Memory Column */}
                            <div className="flex flex-col min-h-0">
                                <div className="flex-shrink-0 mb-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-blue-500 shadow-lg shadow-blue-500/50" />
                                            短期记忆
                                        </h2>
                                        <span className="text-sm text-slate-400">{workingCount} 条</span>
                                    </div>
                                    <p className="text-xs text-slate-500">Working Memory - 近期对话</p>
                                </div>

                                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                                    {workingCount === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                                            <Database size={32} className="mb-2 opacity-50" />
                                            <p className="text-sm">暂无短期记忆</p>
                                        </div>
                                    ) : (
                                        filteredMemories?.working_memory?.map((item, index) => (
                                            <MemoryCard key={index} type="working" data={item} />
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Episodic Memory Column */}
                            <div className="flex flex-col min-h-0">
                                <div className="flex-shrink-0 mb-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
                                            中期记忆
                                        </h2>
                                        <span className="text-sm text-slate-400">{episodicCount} 条</span>
                                    </div>
                                    <p className="text-xs text-slate-500">Episodic Memory - 事件与总结</p>
                                </div>

                                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                                    {episodicCount === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                                            <Database size={32} className="mb-2 opacity-50" />
                                            <p className="text-sm">暂无中期记忆</p>
                                        </div>
                                    ) : (
                                        filteredMemories?.episodic_memory?.map((item, index) => (
                                            <MemoryCard key={index} type="episodic" data={item} />
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Semantic Memory Column */}
                            <div className="flex flex-col min-h-0">
                                <div className="flex-shrink-0 mb-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
                                            长期记忆
                                        </h2>
                                        <span className="text-sm text-slate-400">{semanticCount} 条</span>
                                    </div>
                                    <p className="text-xs text-slate-500">Semantic Memory - 核心原则</p>
                                </div>

                                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                                    {/* Core Principles */}
                                    {filteredMemories?.core_principles && (
                                        <div className="mb-4 p-4 rounded-xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/30">
                                            <h3 className="text-sm font-semibold text-emerald-400 mb-2">核心原则</h3>
                                            <p className="text-sm text-slate-300 whitespace-pre-wrap">
                                                {filteredMemories.core_principles}
                                            </p>
                                        </div>
                                    )}

                                    {semanticCount === 0 && !filteredMemories?.core_principles ? (
                                        <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                                            <Database size={32} className="mb-2 opacity-50" />
                                            <p className="text-sm">暂无长期记忆</p>
                                        </div>
                                    ) : (
                                        filteredMemories?.semantic_memory?.map((item, index) => (
                                            <MemoryCard key={index} type="semantic" data={item} />
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MemoryVisualizationPage;
