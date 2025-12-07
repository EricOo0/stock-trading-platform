// Memory System Type Definitions

export interface WorkingMemoryItem {
    role: 'user' | 'agent' | 'system';
    content: string;
    timestamp?: string;
    metadata?: Record<string, any>;
}

export interface EpisodicMemoryItem {
    id?: string;
    event_type?: string;
    content: string | {
        summary?: string;
        key_findings?: string;
        [key: string]: any;
    };
    timestamp?: string;
    importance?: number;
    metadata?: Record<string, any>;
}

export interface SemanticMemoryItem {
    content: string;
    category?: string;
    importance?: number;
    metadata?: Record<string, any>;
}

export interface MemoryData {
    working_memory: WorkingMemoryItem[];
    episodic_memory: EpisodicMemoryItem[];
    semantic_memory: SemanticMemoryItem[];
    core_principles?: string;
    system_prompt?: string;
    token_usage?: {
        working_memory: number;
        episodic_memory: number;
        semantic_memory: number;
        total: number;
    };
}

export interface MemoryStats {
    working_count: number;
    episodic_count: number;
    semantic_count: number;
    total_tokens: number;
}

export interface AgentInfo {
    id: string;
    name: string;
    displayName: string;
    color: string;
}
