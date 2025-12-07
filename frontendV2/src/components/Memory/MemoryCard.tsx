import React from 'react';
import { Clock, User, Bot, Shield } from 'lucide-react';
import type { WorkingMemoryItem, EpisodicMemoryItem, SemanticMemoryItem } from '../../types/memory';

interface MemoryCardProps {
    type: 'working' | 'episodic' | 'semantic';
    data: WorkingMemoryItem | EpisodicMemoryItem | SemanticMemoryItem;
}

const MemoryCard: React.FC<MemoryCardProps> = ({ type, data }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);

    const getCardStyle = () => {
        switch (type) {
            case 'working':
                return 'border-blue-500/30 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 hover:border-blue-400/50';
            case 'episodic':
                return 'border-purple-500/30 bg-gradient-to-br from-purple-500/5 to-pink-500/5 hover:border-purple-400/50';
            case 'semantic':
                return 'border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 hover:border-emerald-400/50';
        }
    };

    const getIconColor = () => {
        switch (type) {
            case 'working':
                return 'text-blue-400';
            case 'episodic':
                return 'text-purple-400';
            case 'semantic':
                return 'text-emerald-400';
        }
    };

    const getRoleIcon = (role?: string) => {
        switch (role) {
            case 'user':
                return <User size={14} className="text-blue-400" />;
            case 'agent':
                return <Bot size={14} className="text-purple-400" />;
            case 'system':
                return <Shield size={14} className="text-emerald-400" />;
            default:
                return <Bot size={14} className="text-slate-400" />;
        }
    };

    const formatTimestamp = (timestamp?: string) => {
        if (!timestamp) return '未知时间';
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now.getTime() - date.getTime();
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);

            if (minutes < 1) return '刚刚';
            if (minutes < 60) return `${minutes}分钟前`;
            if (hours < 24) return `${hours}小时前`;
            if (days < 7) return `${days}天前`;
            return date.toLocaleDateString('zh-CN');
        } catch {
            return timestamp;
        }
    };

    const getContent = () => {
        if (type === 'working') {
            const item = data as WorkingMemoryItem;
            return item.content;
        } else if (type === 'episodic') {
            const item = data as EpisodicMemoryItem;
            if (typeof item.content === 'string') {
                return item.content;
            }
            return item.content.summary || item.content.key_findings || JSON.stringify(item.content);
        } else {
            const item = data as SemanticMemoryItem;
            return item.content;
        }
    };

    const content = getContent();
    const shouldTruncate = content.length > 150;
    const displayContent = isExpanded || !shouldTruncate ? content : content.slice(0, 150) + '...';

    return (
        <div
            className={`
        relative rounded-xl border backdrop-blur-sm p-4 transition-all duration-300
        ${getCardStyle()}
        hover:shadow-lg hover:scale-[1.02]
      `}
        >
            {/* Content */}
            <div className="mb-3">
                <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {displayContent}
                </p>
                {shouldTruncate && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-xs text-blue-400 hover:text-blue-300 mt-2 transition-colors"
                    >
                        {isExpanded ? '收起' : '展开更多'}
                    </button>
                )}
            </div>

            {/* Metadata Footer */}
            <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-700/50">
                <div className="flex items-center gap-2">
                    {type === 'working' && (
                        <div className="flex items-center gap-1">
                            {getRoleIcon((data as WorkingMemoryItem).role)}
                            <span className="capitalize">{(data as WorkingMemoryItem).role}</span>
                        </div>
                    )}
                    {type === 'episodic' && (data as EpisodicMemoryItem).event_type && (
                        <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                            {(data as EpisodicMemoryItem).event_type}
                        </span>
                    )}
                    {type === 'semantic' && (data as SemanticMemoryItem).importance && (
                        <div className="flex items-center gap-1">
                            <div className="flex gap-0.5">
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className={`w-1 h-3 rounded-full ${i < ((data as SemanticMemoryItem).importance || 0) * 5
                                                ? 'bg-emerald-400'
                                                : 'bg-slate-700'
                                            }`}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-1">
                    <Clock size={12} className={getIconColor()} />
                    <span>{formatTimestamp((data as any).timestamp)}</span>
                </div>
            </div>
        </div>
    );
};

export default MemoryCard;
