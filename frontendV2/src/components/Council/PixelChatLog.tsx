import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface Message {
    role: string;
    content: string;
    agentName?: string;
}

interface PixelChatLogProps {
    messages: Message[];
}

const PixelChatLog: React.FC<PixelChatLogProps> = ({ messages }) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const getAgentColor = (name?: string) => {
        switch (name) {
            case 'Receptionist': return 'text-pink-400';
            case 'Chairman': return 'text-yellow-400';
            case 'MacroDataInvestigator': return 'text-blue-400';
            case 'MarketDataInvestigator': return 'text-green-400';
            case 'SentimentInvestigator': return 'text-purple-400';
            case 'WebSearchInvestigator': return 'text-cyan-400';
            case 'Critic': return 'text-red-400';
            default: return 'text-gray-300';
        }
    };

    return (
        <div className="bg-black/90 border-4 border-gray-700 rounded-lg p-4 h-full flex flex-col font-mono text-sm shadow-2xl relative overflow-hidden">
            {/* CRT Scanline Effect */}
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%]"></div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar" ref={scrollRef}>
                {messages.map((msg, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3 }}
                        className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                    >
                        <div className={`max-w-[90%] ${msg.role === 'user' ? 'bg-blue-900/50' : 'bg-gray-800/50'} p-3 rounded border border-white/10`}>
                            {msg.agentName && (
                                <span className={`block text-xs font-bold mb-1 ${getAgentColor(msg.agentName)} uppercase tracking-wider`}>
                                    {msg.agentName}
                                </span>
                            )}
                            <p className="whitespace-pre-wrap text-gray-200 leading-relaxed">
                                {msg.content}
                            </p>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default PixelChatLog;
