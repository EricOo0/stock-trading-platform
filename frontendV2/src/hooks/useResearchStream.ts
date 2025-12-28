import { useState, useRef, useCallback } from 'react';

export interface ResearchEvent {
    type: 'status' | 'thought' | 'tool_start' | 'tool_end' | 'log' | 'artifact' | 'user_remark';
    payload: any;
    timestamp?: string;
}

export interface ResearchJob {
    id: string;
    query: string;
    status: string;
}

export function useResearchStream() {
    const [job, setJob] = useState<ResearchJob | null>(null);
    const [events, setEvents] = useState<ResearchEvent[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);

    const connectStream = useCallback((jobId: string) => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        const es = new EventSource(`http://localhost:8000/api/research/${jobId}/stream`);

        es.onopen = () => {
            console.log("SSE Connected");
            setIsConnected(true);
        };

        es.onerror = (err) => {
            console.error("SSE Error:", err);
            setIsConnected(false);
            // Reconnection logic is often built-in to EventSource, 
            // but for deep control we might want manual backoff here.
        };

        // Generic event listener? EventSource requires named listeners usually, 
        // unless server sends 'message' type.
        // Our backend sends named events: 'status', 'thought', 'tool_start', etc.

        ['status', 'thought', 'tool_start', 'tool_end', 'log', 'artifact', 'user_remark'].forEach(type => {
            es.addEventListener(type, (e: any) => {
                try {
                    const data = e.data ? JSON.parse(e.data) : null;
                    const newEvent: ResearchEvent = { type: type as any, payload: data, timestamp: new Date().toISOString() };

                    if (type === 'status') {
                        console.log("Received status update:", data);
                    }

                    setEvents(prev => [...prev, newEvent]);

                    // Update job status if needed
                    if (type === 'status') {
                        if (typeof data === 'string') {
                            setJob(prev => {
                                console.log("Updating job status (string):", prev, "->", data);
                                return prev ? { ...prev, status: data } : null;
                            });
                        } else if (data && data.status) {
                            setJob(prev => {
                                console.log("Updating job status (obj):", prev, "->", data.status);
                                return prev ? { ...prev, status: data.status } : null;
                            });
                        }
                    }
                } catch {
                    console.warn("Failed to parse event data:", e.data);
                }
            });
        });

        eventSourceRef.current = es;
    }, []);

    const startResearch = useCallback(async (query: string) => {
        try {
            const res = await fetch('http://localhost:8000/api/research/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            if (data.status === 'created') {
                setJob({ id: data.job_id, query, status: 'starting' });
                connectStream(data.job_id);
            }
        } catch (err) {
            console.error("Failed to start research:", err);
        }
    }, [connectStream]);

    const disconnect = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
            setIsConnected(false);
        }
    }, []);

    const restoreJob = useCallback(async (jobId: string) => {
        try {
            // 1. Fetch full state (job details + history)
            const res = await fetch(`http://localhost:8000/api/research/${jobId}/state`);
            if (!res.ok) throw new Error("Job not found");
            const data = await res.json();

            // 2. Set Job State
            setJob(data.job);

            // 3. Restore Events
            // Backend returns SQLModel objects, we might need to map them if structure differs
            // Assuming they match ResearchEvent interface roughly or need simple mapping
            const historyEvents = data.events.map((e: any) => ({
                type: e.type,
                payload: typeof e.payload === 'string' ? JSON.parse(e.payload) : e.payload,
                timestamp: e.created_at
            }));
            setEvents(historyEvents);

            // 4. Connect to Stream (if job not completed/failed, or just to catch late events)
            if (data.job.status === 'running' || data.job.status === 'starting' || data.job.status === 'created') {
                connectStream(jobId);
            } else {
                setIsConnected(false); // Job finished, no need to stream
            }

        } catch (err) {
            console.error("Failed to restore job:", err);
            setJob(null);
        }
    }, [connectStream]);

    const reset = useCallback(() => {
        disconnect();
        setJob(null);
        setEvents([]);
    }, [disconnect]);

    return {
        job,
        events,
        isConnected,
        startResearch,
        restoreJob,
        disconnect,
        reset
    };
}
