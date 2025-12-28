import React, { useEffect, useRef } from 'react';
import type { ResearchEvent } from '../../hooks/useResearchStream';

interface DashboardPanelProps {
    events: ResearchEvent[];
}

export const DashboardPanel: React.FC<DashboardPanelProps> = ({ events }) => {
    const listRef = useRef<HTMLDivElement>(null);
    // Combine relevant events for the operations timeline
    // We include logs, tool usage, status updates, AND artifacts in the timeline stream
    const timelineEvents = events.filter(e =>
        ['log', 'tool_start', 'tool_end', 'status', 'artifact'].includes(e.type)
    );

    useEffect(() => {
        if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
        }
    }, [timelineEvents.length]);

    return (
        <div className="flex flex-col h-full bg-gray-900 border-l border-gray-800 text-gray-300 font-mono text-xs">
            {/* Header */}
            <div className="p-3 border-b border-gray-800 bg-gray-900 flex justify-between items-center">
                <span className="font-semibold text-gray-100 uppercase tracking-wider">Operations Log</span>
                <span className="bg-gray-800 text-gray-400 px-2 py-0.5 rounded text-[10px]">{timelineEvents.length} events</span>
            </div>

            {/* Timeline Stream */}
            <div
                ref={listRef}
                className="flex-1 overflow-y-auto p-4 space-y-4"
            >
                {timelineEvents.length === 0 && (
                    <div className="text-center text-gray-600 mt-10 italic">
                        Ready to process...
                    </div>
                )}

                {timelineEvents.map((event, idx) => {
                    const time = event.timestamp ? new Date(event.timestamp).toLocaleTimeString([], { hour12: false }) : '';

                    return (
                        <div key={idx} className="flex gap-3 group">
                            {/* Timestamp Column */}
                            <div className="flex-shrink-0 w-16 text-gray-600 text-[10px] pt-0.5 text-right">
                                {time}
                            </div>

                            {/* Connector Line (visual only, simplified) */}
                            <div className="flex-shrink-0 flex flex-col items-center">
                                <div className={`w-2 h-2 rounded-full mt-1.5 ${event.type === 'tool_start' ? 'bg-yellow-500' :
                                    event.type === 'tool_end' ? 'bg-green-500' :
                                        event.type === 'status' ? 'bg-purple-500' :
                                            event.type === 'artifact' ? 'bg-blue-400' :
                                                'bg-gray-700'
                                    }`} />
                                <div className="w-px h-full bg-gray-800 group-last:hidden mt-1" />
                            </div>

                            {/* Content */}
                            <div className="flex-1 pb-2 min-w-0">
                                {/* Header / Type */}
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`uppercase font-bold text-[10px] ${event.type === 'tool_start' ? 'text-yellow-500' :
                                        event.type === 'tool_end' ? 'text-green-500' :
                                            event.type === 'status' ? 'text-purple-400' :
                                                'text-gray-500'
                                        }`}>
                                        {event.type.replace('_', ' ')}
                                    </span>
                                </div>

                                {/* Payload */}
                                <div className="text-gray-300 break-words whitespace-pre-wrap leading-relaxed">
                                    {renderPayload(event)}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// Helper to render event payloads nicely
const renderPayload = (event: ResearchEvent) => {
    const { type, payload } = event;

    if (type === 'tool_start') {
        const args = typeof payload === 'string' ? payload :
            (payload.args ? JSON.stringify(payload.args) : JSON.stringify(payload));
        return (
            <div className="bg-gray-800/50 p-2 rounded border border-gray-700/50 text-yellow-100/90">
                <div className="font-semibold text-yellow-500 mb-1">🛠 {payload.tool || 'Unknown Tool'}</div>
                <div className="opacity-80 font-mono text-[10px]">{args}</div>
            </div>
        );
    }

    if (type === 'tool_end') {
        const output = typeof payload === 'string' ? payload :
            (payload.output || JSON.stringify(payload));
        return (
            <div className="text-green-100/80 italic">
                {output.length > 200 ? output.slice(0, 200) + '...' : output}
            </div>
        );
    }

    if (type === 'thought') {
        // Thoughts often come as streams of deltas, might be noisy here if not aggregated.
        // Assuming aggregated or we just show chunks.
        // If payload has 'delta', it's a stream chunk.
        if (payload.delta) return <span className="text-gray-500">{payload.delta}</span>;
        return <span className="text-gray-400 italic">{JSON.stringify(payload)}</span>;
    }

    if (type === 'status') {
        return <span className="font-bold text-white">{typeof payload === 'string' ? payload : JSON.stringify(payload)}</span>;
    }

    if (type === 'artifact') {
        return (
            <div className="bg-blue-900/20 border border-blue-800 p-2 rounded text-blue-200">
                <div className="flex items-center gap-2">
                    <span>📄</span>
                    <span className="font-semibold">{payload.title || 'New Artifact'}</span>
                </div>
                {payload.type && <div className="text-[10px] opacity-70 mt-1 uppercase">{payload.type}</div>}
            </div>
        );
    }

    if (type === 'log') {
        const msg = payload.message || payload;
        return <span className="text-gray-500">{typeof msg === 'string' ? msg : JSON.stringify(msg)}</span>;
    }

    return JSON.stringify(payload);
};
