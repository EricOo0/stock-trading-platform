import React, { useState, useEffect, useMemo } from 'react';
import { Search, Brain, Loader2, AlertCircle, Database, User as UserIcon, Tag, Info } from 'lucide-react';
import AgentSelector from '../components/Memory/AgentSelector';
import MemoryCard from '../components/Memory/MemoryCard';
import { memoryService } from '../services/memoryService';
import type { MemoryData, AgentInfo } from '../types/memory';

const AGENT_METADATA: Record<string, { displayName: string, color: string }> = {
    'chairman': { displayName: '董事长 (Chairman)', color: 'bg-violet-500' },
    'receptionist': { displayName: '接待员 (Receptionist)', color: 'bg-indigo-500' },
    'market': { displayName: '市场数据调查员', color: 'bg-blue-500' },
    'macro': { displayName: '宏观数据调查员', color: 'bg-cyan-500' },
    'sentiment': { displayName: '情绪调查员', color: 'bg-pink-500' },
    'web_search': { displayName: '网络搜索员', color: 'bg-amber-500' },
    'research_agent': { displayName: '科研Agent (Research)', color: 'bg-emerald-500' },
};

const DEFAULT_USERS = ['test_user_001'];
const DEFAULT_AGENTS = ['chairman'];

const MemoryVisualizationPage: React.FC = () => {
    const [availableUsers, setAvailableUsers] = useState<string[]>(DEFAULT_USERS);
    const [availableAgents, setAvailableAgents] = useState<AgentInfo[]>([]);
    const [selectedAgent, setSelectedAgent] = useState(DEFAULT_AGENTS[0]);
    const [selectedUser, setSelectedUser] = useState(DEFAULT_USERS[0]);
    const [searchQuery, setSearchQuery] = useState('');
    const [memoryData, setMemoryData] = useState<MemoryData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch identities on mount
    useEffect(() => {
        const fetchIdentities = async () => {
            try {
                const { users, agents } = await memoryService.getIdentities();
                if (users.length > 0) setAvailableUsers(users);
                
                const agentInfos: AgentInfo[] = agents.map(id => ({
                    id,
                    name: id,
                    displayName: AGENT_METADATA[id]?.displayName || `Agent: ${id}`,
                    color: AGENT_METADATA[id]?.color || 'bg-slate-500'
                }));
                setAvailableAgents(agentInfos);
                
                // If current selection is not in new lists, update them
                if (users.length > 0 && !users.includes(selectedUser)) setSelectedUser(users[0]);
                if (agents.length > 0 && !agents.includes(selectedAgent)) setSelectedAgent(agents[0]);
            } catch (err) {
                console.error('Failed to fetch identities', err);
            }
        };
        fetchIdentities();
    }, []);

    // Fetch memories when agent or user changes
    useEffect(() => {
        const fetchMemories = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await memoryService.getAgentMemories(selectedAgent, selectedUser);
                setMemoryData(data);
            } catch (err) {
                setError('获取记忆数据失败，请稍后重试');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (selectedAgent && selectedUser) {
            fetchMemories();
        }
    }, [selectedAgent, selectedUser]);

    // Filter and sort memories
    const filteredMemories = useMemo(() => {
        if (!memoryData) return null;

        const query = searchQuery.trim().toLowerCase();

        const sortByTimeDesc = (a: any, b: any) => {
            const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
            const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
            return timeB - timeA;
        };

        return {
            ...memoryData,
            working_memory: (memoryData.working_memory || [])
                .filter((item) =>
                    !query || item.content.toLowerCase().includes(query)
                )
                .sort(sortByTimeDesc),
            episodic_memory: (memoryData.episodic_memory || [])
                .filter((item) => {
                    if (!query) return true;
                    const content = typeof item.content === 'string'
                        ? item.content
                        : JSON.stringify(item.content);
                    return content.toLowerCase().includes(query);
                })
                .sort(sortByTimeDesc),
            semantic_memory: (memoryData.semantic_memory || []).filter((item) => {
                if (!query) return true;
                const content = typeof item.content === 'string'
                    ? item.content
                    : JSON.stringify(item.content);
                return content.toLowerCase().includes(query);
            }),
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
                    <div className="flex flex-col xl:flex-row gap-4">
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="flex items-center gap-2 px-4 py-2 bg-slate-800/80 border border-slate-700 rounded-xl">
                                <UserIcon size={18} className="text-slate-400" />
                                <select
                                    value={selectedUser}
                                    onChange={(e) => setSelectedUser(e.target.value)}
                                    className="bg-transparent text-white border-none focus:ring-0 text-sm min-w-[120px]"
                                >
                                    {availableUsers.map(id => (
                                        <option key={id} value={id} className="bg-slate-800">{id}</option>
                                    ))}
                                </select>
                            </div>

                            <AgentSelector
                                agents={availableAgents}
                                selectedAgent={selectedAgent}
                                onAgentChange={setSelectedAgent}
                            />
                        </div>

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

                    {/* User Persona Banner */}
                    {memoryData?.user_persona && (
                        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 border border-purple-500/20 backdrop-blur-sm">
                            <div className="flex items-center gap-2 mb-3">
                                <Brain size={18} className="text-purple-400" />
                                <h3 className="text-sm font-semibold text-white">用户画像 (User Persona)</h3>
                                <div className="ml-auto flex items-center gap-2">
                                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                        风险偏好: {memoryData.user_persona.risk_preference || '未知'}
                                    </span>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                        <Tag size={12} className="text-blue-400" />
                                        投资风格
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {memoryData.user_persona.investment_style?.map((s, i) => (
                                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">{s}</span>
                                        )) || <span className="text-[10px] text-slate-500 italic">暂无数据</span>}
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                        <Info size={12} className="text-cyan-400" />
                                        感兴趣领域
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {memoryData.user_persona.interested_sectors?.map((s, i) => (
                                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">{s}</span>
                                        )) || <span className="text-[10px] text-slate-500 italic">暂无数据</span>}
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                        <Brain size={12} className="text-purple-400" />
                                        观察特质
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {memoryData.user_persona.observed_traits?.map((s, i) => (
                                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">{s}</span>
                                        )) || <span className="text-[10px] text-slate-500 italic">暂无数据</span>}
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                        <Search size={12} className="text-pink-400" />
                                        分析习惯
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {memoryData.user_persona.analysis_habits?.map((s, i) => (
                                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">{s}</span>
                                        )) || <span className="text-[10px] text-slate-500 italic">暂无数据</span>}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
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
