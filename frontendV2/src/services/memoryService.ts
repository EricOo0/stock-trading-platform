// Memory System API Service

import type { MemoryData } from '../types/memory';

const MEMORY_API_BASE = 'http://localhost:10000/api/v1';

export const memoryService = {
    /**
     * Get all memories for a specific agent
     */
    async getAgentMemories(agentId: string): Promise<MemoryData> {
        try {
            const response = await fetch(`${MEMORY_API_BASE}/memory/context`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agent_id: agentId,
                    query: '', // Empty query to get all memories
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch memories: ${response.statusText}`);
            }

            const data = await response.json();
            return data.context || {
                working_memory: [],
                episodic_memory: [],
                semantic_memory: [],
            };
        } catch (error) {
            console.error('Error fetching agent memories:', error);
            throw error;
        }
    },

    /**
     * Search memories with a query
     */
    async searchMemories(agentId: string, query: string): Promise<MemoryData> {
        try {
            const response = await fetch(`${MEMORY_API_BASE}/memory/context`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agent_id: agentId,
                    query: query,
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to search memories: ${response.statusText}`);
            }

            const data = await response.json();
            return data.context || {
                working_memory: [],
                episodic_memory: [],
                semantic_memory: [],
            };
        } catch (error) {
            console.error('Error searching memories:', error);
            throw error;
        }
    },

    /**
     * Get memory statistics
     */
    async getMemoryStats(agentId: string) {
        try {
            const memories = await this.getAgentMemories(agentId);
            return {
                working_count: memories.working_memory?.length || 0,
                episodic_count: memories.episodic_memory?.length || 0,
                semantic_count: memories.semantic_memory?.length || 0,
                total_tokens: memories.token_usage?.total || 0,
            };
        } catch (error) {
            console.error('Error fetching memory stats:', error);
            return {
                working_count: 0,
                episodic_count: 0,
                semantic_count: 0,
                total_tokens: 0,
            };
        }
    },
};
