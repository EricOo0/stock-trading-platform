import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import PixelAvatar from './PixelAvatar';
import PixelChatLog from './PixelChatLog';

// Avatar Configuration
const AVATARS = [
    { id: 'Chairman', name: 'Chairman', role: 'Leader', image: '/assets/council/avatar_chairman.png', position: 'top-20 right-[52%]' },
    { id: 'MacroDataInvestigator', name: 'Macro', role: 'Economist', image: '/assets/council/avatar_macro.png', position: 'top-32 left-8' },
    { id: 'MarketDataInvestigator', name: 'Market', role: 'Analyst', image: '/assets/council/avatar_market.png', position: 'top-32 right-8' },
    { id: 'SentimentInvestigator', name: 'Sentiment', role: 'Tracker', image: '/assets/council/avatar_sentiment.png', position: 'bottom-32 left-8' },
    { id: 'WebSearchInvestigator', name: 'Search', role: 'Hunter', image: '/assets/council/avatar_search.png', position: 'bottom-32 right-8' },
    { id: 'Receptionist', name: 'Receptionist', role: 'Greeter', image: '/assets/council/avatar_receptionist.png', position: 'bottom-4 left-1/2 -translate-x-1/2' },
    { id: 'Critic', name: 'Critic', role: 'Reviewer', image: '/assets/council/avatar_chairman.png', position: 'top-20 left-[52%]' },
];

interface Message {
    role: string;
    content: string;
    agentName?: string;
}

const CouncilRoom: React.FC = () => {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeAgent, setActiveAgent] = useState<string | null>(null);
    const [agentStatus, setAgentStatus] = useState<'idle' | 'thinking' | 'speaking'>('idle');

    // Playback Queue
    const playbackQueue = useRef<{ type: string; agent: string; content?: string; status?: string; to?: string; from?: string; instruction?: string; tool_name?: string }[]>([]);
    const isPlaying = useRef(false);

    const processQueue = async () => {
        if (isPlaying.current || playbackQueue.current.length === 0) return;

        isPlaying.current = true;
        const event = playbackQueue.current.shift();

        if (event) {
            if (event.type === 'agent_start') {
                // Always activate agent and update status, even if it's already active
                setActiveAgent(event.agent);
                setAgentStatus(event.status as 'thinking' | 'speaking' || 'thinking');

                if (event.status === 'thinking') {
                    await new Promise(resolve => setTimeout(resolve, 800));
                }
            }
            else if (event.type === 'routing') {
                // Show routing event
                // event: { type: 'routing', from: 'Chairman', to: 'Market', message: '...', instruction: '...' }

                // 1. Finish current agent
                setAgentStatus('idle');
                await new Promise(resolve => setTimeout(resolve, 200));

                // 2. Show the Command in Chat Log (for debugging/transparency)
                if (event.instruction) {
                    setMessages(prev => [...prev, {
                        role: 'system',
                        content: `📋 COMMAND to ${event.to}: ${event.instruction}`,
                        agentName: event.from || 'Chairman'
                    }]);
                }

                // 3. Don't activate next agent here - let agent_start event handle it
                // This ensures proper state transition
            }
            else if (event.type === 'agent_message' && event.content) {
                setActiveAgent(event.agent); // Ensure correct agent is active
                setAgentStatus('speaking');
                setMessages(prev => [...prev, { role: 'assistant', content: event.content!, agentName: event.agent }]);
                // Reading time
                const delay = Math.max(1500, Math.min(event.content.length * 20, 4000));
                await new Promise(resolve => setTimeout(resolve, delay));
            }
            else if (event.type === 'agent_status_change') {
                // Update agent status (for progress indication)
                if (event.agent === activeAgent && event.status) {
                    setAgentStatus(event.status as 'thinking' | 'speaking');
                }
            }
            else if (event.type === 'tool_call') {
                // Show tool execution in chat log
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: `🔧 ${event.agent} used ${event.tool_name}`,
                    agentName: event.agent
                }]);
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            else if (event.type === 'error') {
                // Display errors to user
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: `❌ ${event.agent || 'System'}: ${event.content}`,
                    agentName: event.agent || 'System'
                }]);
                setAgentStatus('idle');
                setActiveAgent(null);
            }
            else if (event.type === 'system_end') {
                // Signal workflow completion
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: '✅ Analysis complete',
                }]);
                setAgentStatus('idle');
                setActiveAgent(null);
                setIsLoading(false);
            }
            else if (event.type === 'agent_end') {
                // Use a timeout to allow next agent_start to override
                setTimeout(() => {
                    // Only go idle if no new agent has been activated
                    if (activeAgent === event.agent && agentStatus !== 'thinking') {
                        setAgentStatus('idle');
                        setActiveAgent(null);
                    }
                }, 300);
            }
        }

        isPlaying.current = false;
        processQueue();
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || isLoading) return;

        const userQuery = query;
        setQuery('');
        setIsLoading(true);
        setMessages(prev => [...prev, { role: 'user', content: userQuery }]);

        try {
            const response = await fetch('http://localhost:8001/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userQuery, thread_id: "council_session_" + Date.now() }),
            });

            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            // Start Playback Loop if not running
            processQueue();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        playbackQueue.current.push(event);
                    } catch (e) {
                        console.error('Error parsing JSON chunk', e);
                    }
                }
            }

        } catch (error) {
            console.error("Error:", error);
            setMessages(prev => [...prev, { role: 'system', content: 'Connection Error. The Council is offline.' }]);
        } finally {
            setIsLoading(false);
            setActiveAgent(null);
        }
    };

    // Trigger queue processing when queue changes (if not already playing)
    useEffect(() => {
        const interval = setInterval(() => {
            processQueue();
        }, 500);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col h-screen bg-gray-900 text-white overflow-hidden font-sans">
            {/* Header */}
            <header className="bg-black/50 p-4 border-b border-white/10 flex justify-between items-center backdrop-blur-md z-50">
                <h1 className="text-xl font-bold font-mono text-yellow-400 flex items-center gap-2">
                    <span className="text-2xl">👾</span> AI ADVISORY COUNCIL
                </h1>
                <div className="text-xs text-gray-400 font-mono">
                    STATUS: {isLoading ? <span className="text-green-400 animate-pulse">SESSION ACTIVE</span> : 'IDLE'}
                </div>
            </header>

            <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">

                {/* LEFT: The Room (Visuals) */}
                <div className="flex-1 relative bg-[#1a1a1a] overflow-hidden flex items-center justify-center">
                    {/* Background Image */}
                    <div
                        className="absolute inset-0 bg-cover bg-center opacity-50"
                        style={{ backgroundImage: 'url(/assets/council/council_room_bg.png)', imageRendering: 'pixelated' }}
                    ></div>

                    {/* Grid Overlay for retro feel */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:20px_20px]"></div>

                    {/* Avatars Layer */}
                    <div className="relative w-full h-full max-w-4xl mx-auto">
                        {AVATARS.map(avatar => (
                            <div key={avatar.id} className={`absolute ${avatar.position} transition-all duration-500`}>
                                <PixelAvatar
                                    name={avatar.name}
                                    role={avatar.role}
                                    imageSrc={avatar.image}
                                    isActive={activeAgent === avatar.id}
                                    status={activeAgent === avatar.id ? agentStatus : 'idle'}
                                />
                            </div>
                        ))}
                    </div>
                </div>

                {/* RIGHT: The Log (Text) */}
                <div className="w-full md:w-1/3 bg-gray-900 border-l border-white/10 flex flex-col z-40 shadow-2xl">
                    <div className="flex-1 p-4 overflow-hidden">
                        <PixelChatLog messages={messages} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-black/80 border-t border-white/10">
                        <form onSubmit={handleSubmit} className="flex gap-2">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Consult the council..."
                                className="flex-1 bg-gray-800 border-2 border-gray-600 rounded p-3 text-white font-mono focus:border-yellow-400 focus:outline-none transition-colors"
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="bg-yellow-600 hover:bg-yellow-500 text-black font-bold p-3 rounded border-2 border-yellow-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
                            >
                                {isLoading ? <Loader2 className="animate-spin" /> : <Send />}
                            </button>
                        </form>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default CouncilRoom;
