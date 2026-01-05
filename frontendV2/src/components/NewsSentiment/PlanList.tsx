import React from 'react';
import { FiCheckCircle, FiCircle, FiLoader, FiUser, FiZap } from 'react-icons/fi';
import { TaskStatus, AgentType } from '../../types/newsSentiment';
import type { NewsPlan } from '../../types/newsSentiment';

interface PlanListProps {
    plan: NewsPlan;
    onSelectTask: (taskId: string) => void;
    selectedTaskId: string | null;
}

const PlanList: React.FC<PlanListProps> = ({ plan, onSelectTask, selectedTaskId }) => {
    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900 tracking-tight">Analysis Plan</h2>
                <div className="text-xs font-medium px-2 py-1 bg-gray-100 rounded-md text-gray-500">
                    {plan.tasks.length} Tasks
                </div>
            </div>

            <div className="flex flex-col gap-4">
                {plan.tasks.length === 0 ? (
                    <div className="p-8 text-center border-2 border-dashed border-gray-200 rounded-xl">
                        <p className="text-sm text-gray-400">Waiting for Master Agent to generate plan...</p>
                    </div>
                ) : (
                    plan.tasks.map((task) => {
                        const isSelected = selectedTaskId === task.id;
                        return (
                        <div 
                            key={task.id}
                            onClick={() => onSelectTask(task.id)}
                            className={`
                                relative p-5 rounded-xl border transition-all duration-300 cursor-pointer
                                ${isSelected 
                                    ? 'bg-white border-black ring-1 ring-black shadow-md z-10' 
                                    : 'hover:border-gray-300 hover:shadow-sm'
                                }
                                ${!isSelected && task.status === TaskStatus.IN_PROGRESS 
                                    ? 'bg-white border-blue-200 shadow-lg ring-1 ring-blue-100 scale-[1.02]' 
                                    : ''
                                }
                                ${!isSelected && task.status === TaskStatus.COMPLETED
                                    ? 'bg-gray-50 border-gray-200 opacity-90'
                                    : ''
                                }
                                ${!isSelected && task.status === TaskStatus.PENDING
                                    ? 'bg-white border-gray-100'
                                    : ''
                                }
                            `}
                        >
                            {/* Status Icon */}
                            <div className="absolute top-5 right-5 z-10">
                                {task.status === TaskStatus.COMPLETED && <FiCheckCircle className="text-green-500 fill-green-50" size={20} />}
                                {task.status === TaskStatus.IN_PROGRESS && <FiLoader className="text-blue-500 animate-spin" size={18} />}
                                {task.status === TaskStatus.PENDING && <FiCircle className="text-gray-300" size={18} />}
                                {task.status === TaskStatus.FAILED && <span className="text-red-500 text-xs font-bold">FAILED</span>}
                            </div>

                            {/* Agent Type Badge */}
                            <div className="flex items-center gap-2 mb-2">
                                <span className={`
                                    text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1
                                    ${task.agent_type === AgentType.MASTER 
                                        ? 'bg-purple-100 text-purple-600' 
                                        : 'bg-orange-100 text-orange-600'
                                    }
                                `}>
                                    {task.agent_type === AgentType.MASTER ? <FiUser size={10} /> : <FiZap size={10} />}
                                    {task.agent_type}
                                </span>
                            </div>

                            <h3 className={`font-semibold text-base mb-1 ${task.status === TaskStatus.COMPLETED ? 'text-gray-700' : 'text-gray-900'}`}>
                                {task.title}
                            </h3>
                            
                            <p className="text-sm text-gray-500 leading-relaxed mb-3">
                                {task.description}
                            </p>

                            {/* Result Preview */}
                            {task.result && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                    <div className="text-xs font-medium text-gray-400 uppercase mb-1">Result</div>
                                    <div className="text-sm text-gray-700 line-clamp-3">
                                        {task.result}
                                    </div>
                                </div>
                            )}
                        </div>
                    )})
                )}
            </div>
        </div>
    );
};

export default PlanList;
