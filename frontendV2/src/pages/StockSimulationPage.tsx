
import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, TrendingUp, History, Calendar, DollarSign, Activity, RefreshCw, ChevronDown, ChevronRight, Plus } from 'lucide-react';
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';
import { simulationAPI } from '../services/simulationAPI';
import type { SimulationTask, DailyRecord } from '../services/simulationAPI';

const StockSimulationPage: React.FC = () => {
    const [tasks, setTasks] = useState<SimulationTask[]>([]);
    const [selectedTask, setSelectedTask] = useState<SimulationTask | null>(null);
    const [expandedLog, setExpandedLog] = useState<number | null>(null);

    const ScoreBadge = ({ label, score }: { label: string, score: number }) => {
        let color = 'text-slate-400 border-slate-600';
        if (score >= 7) color = 'text-green-400 border-green-800 bg-green-900/20';
        else if (score <= 3) color = 'text-red-400 border-red-800 bg-red-900/20';
        else color = 'text-yellow-400 border-yellow-800 bg-yellow-900/20';

        return (
            <div className={`flex flex-col items-center p-1 rounded border ${color}`}>
                <span className="text-[10px] opacity-70">{label}</span>
                <span className="font-bold">{score}</span>
            </div>
        );
    };
    const [loading, setLoading] = useState(false);
    const [running, setRunning] = useState(false);
    const [showNewTaskModal, setShowNewTaskModal] = useState(false);
    const [newSymbol, setNewSymbol] = useState('');

    // Fetch tasks on mount
    useEffect(() => {
        fetchTasks();
    }, []);

    const fetchTasks = async () => {
        setLoading(true);
        const data = await simulationAPI.getAllTasks();
        setTasks(data);

        // If we have a selected task, refresh its data
        if (selectedTask) {
            const updated = data.find(t => t.id === selectedTask.id);
            if (updated) setSelectedTask(updated);
        } else if (data.length > 0) {
            // Default select first
            setSelectedTask(data[0]);
        }
        setLoading(false);
    };

    const handleCreateTask = async () => {
        if (!newSymbol) return;
        setLoading(true);
        const newTask = await simulationAPI.createTask(newSymbol);
        if (newTask) {
            await fetchTasks();
            setSelectedTask(newTask);
            setShowNewTaskModal(false);
            setNewSymbol('');
        }
        setLoading(false);
    };

    const handleRunDay = async () => {
        if (!selectedTask) return;
        setRunning(true);
        const result = await simulationAPI.runDailySimulation(selectedTask.id);
        if (result.status === 'success') {
            // Refresh data
            const updatedTask = await simulationAPI.getTask(selectedTask.id);
            if (updatedTask) {
                setSelectedTask(updatedTask);
                // Also update list
                setTasks(prev => prev.map(t => t.id === updatedTask.id ? updatedTask : t));
            }
        } else {
            alert(`Simulation failed: ${result.message} `);
        }
        setRunning(false);
    };

    // Prepare chart data
    const chartData = selectedTask?.daily_records.map(record => ({
        date: record.date,
        totalValue: record.total_value,
        price: record.price,
        cash: record.cash,
        holdingsValue: record.holdings * record.price,
        avgCost: record.avg_cost || 0
    })) || [];

    return (
        <div className="h-full flex flex-col bg-slate-900 text-slate-100 overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                        股票模拟回测 & 模拟交易
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">
                        基于 AI Agent 的自主投资决策模拟系统
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowNewTaskModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors text-white font-medium"
                    >
                        <Plus size={18} />
                        新建模拟任务
                    </button>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Left Panel: Task List & Details */}
                <div className="w-1/3 border-r border-slate-700 flex flex-col bg-slate-800/30">

                    {/* Task Selector */}
                    <div className="p-4 border-b border-slate-700">
                        <label className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-2 block">
                            当前任务 (Task)
                        </label>
                        <div className="flex gap-2 overflow-x-auto pb-2">
                            {tasks.map(task => (
                                <button
                                    key={task.id}
                                    onClick={() => setSelectedTask(task)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${selectedTask?.id === task.id
                                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                        }`}
                                >
                                    {task.symbol}
                                </button>
                            ))}
                            {tasks.length === 0 && (
                                <span className="text-slate-500 text-sm py-2">暂无任务，请新建</span>
                            )}
                        </div>
                    </div>

                    {/* Task Stats */}
                    {selectedTask && (
                        <div className="p-4 grid grid-cols-2 gap-4 border-b border-slate-700 bg-slate-800/50">
                            <div className="p-3 bg-slate-700/50 rounded-xl border border-slate-600/50">
                                <div className="text-slate-400 text-xs mb-1 flex items-center gap-1">
                                    <DollarSign size={12} /> 总资产 (Total Value)
                                </div>
                                <div className={`text-xl font-bold ${selectedTask.total_value >= selectedTask.initial_capital ? 'text-green-400' : 'text-red-400'}`}>
                                    ${selectedTask.total_value.toFixed(2)}
                                </div>
                                <div className="text-xs text-slate-500 mt-1">
                                    Init: ${selectedTask.initial_capital}
                                </div>
                            </div>
                            <div className="p-3 bg-slate-700/50 rounded-xl border border-slate-600/50">
                                <div className="text-slate-400 text-xs mb-1 flex items-center gap-1">
                                    <Activity size={12} /> 持仓 (Holdings)
                                </div>
                                <div className="text-xl font-bold text-blue-400">
                                    {selectedTask.holdings} 股
                                </div>
                                <div className="text-xs text-slate-500 mt-1">
                                    Cash: ${selectedTask.current_cash.toFixed(2)}
                                </div>
                            </div>
                            {/* Cost Basis Card */}
                            <div className="col-span-2 p-3 bg-slate-700/50 rounded-xl border border-slate-600/50 flex justify-between items-center">
                                <div>
                                    <div className="text-slate-400 text-xs mb-1">持仓均价 (Avg Cost)</div>
                                    <div className="text-lg font-bold text-orange-400">
                                        ${selectedTask.avg_cost?.toFixed(2) || '0.00'}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-slate-400 text-xs mb-1">浮动盈亏 (Unrealized P&L)</div>
                                    <div className={`text-lg font-bold ${(selectedTask.total_value - selectedTask.initial_capital) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        ${((selectedTask.holdings * (chartData[chartData.length - 1]?.price || 0)) - (selectedTask.holdings * (selectedTask.avg_cost || 0))).toFixed(2)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Action Area */}
                    {selectedTask && (
                        <div className="p-4 flex gap-3 border-b border-slate-700">
                            <button
                                onClick={handleRunDay}
                                disabled={running}
                                className={`flex-1 py-3 rounded-xl font-bold text-center flex items-center justify-center gap-2 transition-all ${running
                                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                                    }`}
                            >
                                {running ? <RefreshCw className="animate-spin" size={20} /> : <Play size={20} />}
                                {running ? 'Agent 思考中...' : '模拟运行一天 (Run Day)'}
                            </button>

                            {/* Placeholder for Auto Run */}
                            <button
                                disabled
                                className="px-4 py-3 rounded-xl bg-slate-700 text-slate-500 font-medium cursor-not-allowed tooltip"
                                title="Coming Soon"
                            >
                                Auto Run
                            </button>
                        </div>
                    )}

                    {/* Transaction History */}
                    <div className="flex-1 overflow-y-auto p-4">
                        <h3 className="text-sm font-bold text-slate-400 mb-3 flex items-center gap-2">
                            <Calendar size={16} /> 每日记录 (Daily Log)
                        </h3>
                        <div className="space-y-3">
                            {selectedTask?.daily_records.slice().reverse().map((record, idx) => (
                                <div
                                    key={idx}
                                    onClick={() => setExpandedLog(expandedLog === idx ? null : idx)}
                                    className={`bg-slate-800 rounded-xl p-3 border transition-all cursor-pointer ${expandedLog === idx ? 'border-blue-500 shadow-md shadow-blue-500/10' : 'border-slate-700 hover:border-slate-600'}`}
                                >
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center gap-2">
                                            {expandedLog === idx ? <ChevronDown size={14} className="text-blue-400" /> : <ChevronRight size={14} className="text-slate-500" />}
                                            <span className="text-slate-400 font-mono text-xs">{record.date}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {(record.action_taken === 'BUY' || record.action_taken === 'SELL') && (
                                                <span className="text-xs font-mono text-slate-300">
                                                    {record.quantity ? `${record.quantity}股` : '-'}
                                                </span>
                                            )}
                                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${record.action_taken === 'BUY' ? 'bg-green-500/20 text-green-400' :
                                                record.action_taken === 'SELL' ? 'bg-red-500/20 text-red-400' :
                                                    'bg-slate-600/50 text-slate-300'
                                                }`}>
                                                {record.action_taken}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex justify-between text-slate-300 mb-2 pl-6">
                                        <span>Price: ${record.price.toFixed(2)}</span>
                                        <span className="text-xs text-slate-500">Value: ${record.total_value.toFixed(0)}</span>
                                    </div>

                                    {/* Detailed Analysis View */}
                                    {expandedLog === idx && record.analysis && (
                                        <div className="mt-3 mb-2 pl-2 border-t border-slate-700/50 pt-3">
                                            <div className="grid grid-cols-4 gap-2 mb-3">
                                                <ScoreBadge label="Tech" score={record.analysis.technical_score} />
                                                <ScoreBadge label="Fund" score={record.analysis.fundamental_score} />
                                                <ScoreBadge label="Sent" score={record.analysis.sentiment_score} />
                                                <ScoreBadge label="Macr" score={record.analysis.macro_score} />
                                            </div>
                                            <div className="text-xs text-slate-400 bg-slate-900/50 p-2 rounded italic leading-relaxed">
                                                {record.analysis.reasoning}
                                            </div>
                                        </div>
                                    )}

                                    {/* Fallback Reason if no analysis or not expanded */}
                                    {(expandedLog !== idx || !record.analysis) && (
                                        <div className="text-xs text-slate-500 bg-slate-900/50 p-2 rounded italic pl-6 truncate">
                                            "{record.reason}"
                                        </div>
                                    )}
                                </div>
                            ))}
                            {(!selectedTask?.daily_records || selectedTask.daily_records.length === 0) && (
                                <div className="text-center text-slate-600 py-10">
                                    暂无交易记录，请点击运行
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Panel: Charts */}
                <div className="flex-1 p-6 flex flex-col gap-6 overflow-y-auto bg-slate-900">
                    {selectedTask ? (
                        <>
                            {/* Chart 1: Total Value Curve */}
                            <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 shadow-xl">
                                <h3 className="text-lg font-bold text-slate-200 mb-6 flex items-center gap-2">
                                    <TrendingUp className="text-green-400" /> 收益曲线 (Asset Value)
                                </h3>
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={chartData}>
                                            <defs>
                                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="date" stroke="#94a3b8" />
                                            <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                                            />
                                            <Legend />
                                            <Area
                                                type="monotone"
                                                dataKey="totalValue"
                                                stroke="#34d399"
                                                fillOpacity={1}
                                                fill="url(#colorValue)"
                                                name="Total Assets ($)"
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Chart 3: Price vs Cost */}
                            <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 shadow-xl">
                                <h3 className="text-lg font-bold text-slate-200 mb-6 flex items-center gap-2">
                                    <TrendingUp className="text-blue-400" /> 股价与成本 (Price vs Avg Cost)
                                </h3>
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="date" stroke="#94a3b8" />
                                            <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                                            />
                                            <Legend />
                                            <Area type="monotone" dataKey="price" stroke="#3b82f6" fillOpacity={0.1} fill="#3b82f6" name="Price" dot={true} />
                                            <Area type="step" dataKey="avgCost" stroke="#f59e0b" fillOpacity={0} strokeDasharray="5 5" strokeWidth={2} name="Avg Cost" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Chart 2: Cash vs Holdings */}
                            <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700 shadow-xl">
                                <h3 className="text-lg font-bold text-slate-200 mb-6 flex items-center gap-2">
                                    <DollarSign className="text-blue-400" /> 资产分布 (Cash vs Holdings)
                                </h3>
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="date" stroke="#94a3b8" />
                                            <YAxis stroke="#94a3b8" />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                                            />
                                            <Legend />
                                            <Area type="monotone" dataKey="cash" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="Cash" />
                                            <Area type="monotone" dataKey="holdingsValue" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" name="Stock Value" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500">
                            <Activity size={64} className="mb-4 opacity-50" />
                            <p className="text-xl">请选择或创建一个模拟任务</p>
                        </div>
                    )}
                </div>
            </div>

            {/* New Task Modal */}
            {showNewTaskModal && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-800 p-8 rounded-2xl w-96 border border-slate-700 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-6">新建模拟任务</h2>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-400 mb-2">股票代码 (Symbol)</label>
                            <input
                                type="text"
                                value={newSymbol}
                                onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                                placeholder="e.g. AAPL, TSLA"
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                                autoFocus
                            />
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowNewTaskModal(false)}
                                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-300 transition-colors"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleCreateTask}
                                disabled={!newSymbol || loading}
                                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? '创建中...' : '开始模拟'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StockSimulationPage;
