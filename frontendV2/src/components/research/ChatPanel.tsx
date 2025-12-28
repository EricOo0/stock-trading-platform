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
        <div className="flex flex-col h-full bg-white border-r border-gray-200">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h2 className="text-lg font-semibold text-gray-800">Research Chat</h2>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-gray-500 mt-10">
                        <p>Ask me to research a topic...</p>
                    </div>
                )}

                {messages.map((msg, idx) => {
                    // Handle Artifact Rendering
                    if (msg.role === 'artifact' && msg.artifact) {
                        return (
                            <div key={idx} className="flex justify-start w-full">
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
                            <div className={`max-w-[85%] rounded-lg p-3 ${msg.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : msg.role === 'system'
                                    ? 'bg-gray-100 text-gray-500 text-sm italic'
                                    : 'bg-white border border-gray-200 shadow-sm text-gray-800'
                                } break-words overflow-x-auto`}>
                                {msg.role === 'assistant' ? (
                                    <div className="prose prose-sm max-w-none">
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
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg p-3 text-gray-500 text-sm animate-pulse">
                            Thinking...
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-200 bg-white">
                <form onSubmit={handleSubmit} className="flex gap-2">
                    <input
                        type="text"
                        className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-400 bg-white"
                        placeholder="Type a message or remark..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                    />
                    <button
                        type="submit"
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                        disabled={isLoading}
                    >
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
};
