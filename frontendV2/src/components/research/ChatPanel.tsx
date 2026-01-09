import React, { useState, useEffect, useRef } from 'react';
import type { ResearchEvent } from '../../hooks/useResearchStream';
import ReactMarkdown from 'react-markdown';
import { ArtifactRenderer } from './artifacts/ArtifactRenderer';

interface ChatPanelProps {
    events: ResearchEvent[];
    onSendMessage: (msg: string) => void;
    isLoading?: boolean;
    initialQuery?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ events, onSendMessage, isLoading, initialQuery }) => {
    const [input, setInput] = useState('');
    const bottomRef = useRef<HTMLDivElement>(null);

    // Filter relevant events for visual chat flow
    // We want to combine sequential 'thought' events into one message block if possible, 
    // or just render them as they come. For now, simple list.

    // Better strategy: Derive "Messages" from events
    const messages = React.useMemo(() => {
        // Define message type including artifact
        type Message = {
            role: 'user' | 'assistant' | 'system' | 'artifact',
            content?: string,
            artifact?: { type: string, title: string, data: any }
        };

        const msgs: Message[] = [];

        // Add initial query as first user message
        if (initialQuery) {
            msgs.push({ role: 'user', content: initialQuery });
        }

        let currentThought = '';

        events.forEach(e => {
            if (e.type === 'thought') {
                if (e.payload.delta) currentThought += e.payload.delta;
            } else if (e.type === 'tool_start') {
                // Flush thought before tool
                if (currentThought) {
                    msgs.push({ role: 'assistant', content: currentThought });
                    currentThought = '';
                }
                msgs.push({ role: 'system', content: `🛠 Using tool: ${e.payload.tool}` });
            } else if (e.type === 'user_remark') {
                if (currentThought) {
                    msgs.push({ role: 'assistant', content: currentThought });
                    currentThought = '';
                }
                const content = typeof e.payload === 'string' ? e.payload : e.payload.content || JSON.stringify(e.payload);
                msgs.push({ role: 'user', content: `(Feedback) ${content}` });
            } else if (e.type === 'artifact') {
                // Flush thought before artifact
                if (currentThought) {
                    msgs.push({ role: 'assistant', content: currentThought });
                    currentThought = '';
                }
                // Push artifact message
                msgs.push({
                    role: 'artifact',
                    artifact: {
                        type: e.payload.type,
                        title: e.payload.title,
                        data: e.payload.data
                    }
                });
            }
        });

        if (currentThought) {
            msgs.push({ role: 'assistant', content: currentThought });
        }

        return msgs;
    }, [events, initialQuery]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages.length, events.length]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;
        onSendMessage(input);
        setInput('');
    };

    return (
        <div className="flex flex-col h-full bg-gray-900 border-r border-gray-800">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-gray-900/50 backdrop-blur">
                <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                    <span className="text-blue-500">✨</span> Research Chat
                </h2>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-5">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500 space-y-4">
                        <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center text-3xl opacity-50">
                            🤖
                        </div>
                        <p className="text-sm">Ask me to research a topic...</p>
                    </div>
                )}

                {messages.map((msg, idx) => {
                    // Handle Artifact Rendering
                    if (msg.role === 'artifact' && msg.artifact) {
                        return (
                            <div key={idx} className="flex justify-start w-full pl-2">
                                <div className="max-w-[90%] w-full">
                                    <ArtifactRenderer
                                        type={msg.artifact.type}
                                        title={msg.artifact.title}
                                        data={msg.artifact.data}
                                    />
                                </div>
                            </div>
                        );
                    }

                    return (
                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${msg.role === 'user'
                                ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-tr-none'
                                : msg.role === 'system'
                                    ? 'bg-gray-800/40 text-gray-400 text-xs font-mono border border-gray-700/50'
                                    : 'bg-gray-800 border border-gray-700 text-gray-200 rounded-tl-none'
                                } break-words overflow-x-auto leading-relaxed`}>
                                {msg.role === 'assistant' ? (
                                    <div className="prose prose-sm prose-invert max-w-none">
                                        <ReactMarkdown>
                                            {msg.content || ''}
                                        </ReactMarkdown>
                                    </div>
                                ) : (
                                    msg.content
                                )}
                            </div>
                        </div>
                    );
                })}

                {isLoading && (
                    <div className="flex justify-start pl-2">
                        <div className="flex items-center gap-2 text-gray-400 bg-gray-800/50 px-4 py-2 rounded-full text-sm">
                            <span className="animate-pulse">●</span>
                            <span className="animate-pulse delay-100">●</span>
                            <span className="animate-pulse delay-200">●</span>
                            <span className="ml-2 text-xs uppercase tracking-wider font-semibold opacity-70">Thinking</span>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-800 bg-gray-900">
                <form onSubmit={handleSubmit} className="relative flex items-center gap-3 bg-gray-800 p-2 rounded-xl border border-gray-700 focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
                    <input
                        type="text"
                        className="flex-1 bg-transparent border-none px-3 py-2 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-0"
                        placeholder="Type a message or remark..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                    />
                    <button
                        type="submit"
                        className={`p-2 rounded-lg transition-all duration-200 ${input.trim()
                                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'
                                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            }`}
                        disabled={isLoading || !input.trim()}
                    >
                        <svg className="w-5 h-5 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    );
};
