import React from 'react';
import { ChevronDown } from 'lucide-react';
import type { AgentInfo } from '../../types/memory';

interface AgentSelectorProps {
    agents: AgentInfo[];
    selectedAgent: string;
    onAgentChange: (agentId: string) => void;
}

const AgentSelector: React.FC<AgentSelectorProps> = ({
    agents,
    selectedAgent,
    onAgentChange,
}) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const selectedAgentInfo = agents.find((a) => a.id === selectedAgent);

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="
          flex items-center justify-between gap-3 px-4 py-3 rounded-xl
          bg-slate-800/50 border border-slate-700 hover:border-slate-600
          text-white transition-all duration-200 min-w-[240px]
          hover:bg-slate-800/70
        "
            >
                <div className="flex items-center gap-3">
                    <div
                        className={`w-3 h-3 rounded-full ${selectedAgentInfo?.color || 'bg-slate-500'}`}
                    />
                    <span className="font-medium">{selectedAgentInfo?.displayName || 'Select Agent'}</span>
                </div>
                <ChevronDown
                    size={18}
                    className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''
                        }`}
                />
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute top-full left-0 mt-2 w-full bg-slate-800 border border-slate-700 rounded-xl shadow-2xl z-20 overflow-hidden">
                        {agents.map((agent) => (
                            <button
                                key={agent.id}
                                onClick={() => {
                                    onAgentChange(agent.id);
                                    setIsOpen(false);
                                }}
                                className={`
                  w-full flex items-center gap-3 px-4 py-3 transition-colors
                  ${selectedAgent === agent.id
                                        ? 'bg-slate-700/50 text-white'
                                        : 'text-slate-300 hover:bg-slate-700/30 hover:text-white'
                                    }
                `}
                            >
                                <div className={`w-3 h-3 rounded-full ${agent.color}`} />
                                <span className="font-medium">{agent.displayName}</span>
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
};

export default AgentSelector;
