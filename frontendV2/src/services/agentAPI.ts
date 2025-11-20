/**
 * Agent API Service
 * Connects to the Stock Analysis Agent backend for real AI analysis
 */

export interface AgentChatRequest {
    message: string;
    session_id?: string;
}

export interface ToolCall {
    tool_name: string;
    tool_input: any;
    tool_output: string;
}

export interface AgentChatResponse {
    response: string;
    session_id: string;
    tool_calls: ToolCall[];
    success: boolean;
    error?: string;
}

export interface ToolInfo {
    name: string;
    description: string;
}

export interface ToolsResponse {
    tools: ToolInfo[];
    count: number;
}

class AgentAPI {
    private baseURL: string;

    constructor() {
        // Agent service runs on port 8001
        this.baseURL = 'http://localhost:8001/api';
    }

    /**
     * Send a chat message to the agent
     */
    async chat(message: string, sessionId?: string): Promise<AgentChatResponse> {
        try {
            const response = await fetch(`${this.baseURL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message,
                    session_id: sessionId,
                } as AgentChatRequest),
            });

            if (!response.ok) {
                throw new Error(`Agent request failed: ${response.statusText}`);
            }

            const data: AgentChatResponse = await response.json();
            return data;
        } catch (error) {
            console.error('Agent chat error:', error);
            throw error;
        }
    }

    /**
     * Get list of available tools
     */
    async getTools(): Promise<ToolsResponse> {
        try {
            const response = await fetch(`${this.baseURL}/tools`);

            if (!response.ok) {
                throw new Error(`Failed to fetch tools: ${response.statusText}`);
            }

            return response.json();
        } catch (error) {
            console.error('Get tools error:', error);
            throw error;
        }
    }

    /**
     * Health check
     */
    async healthCheck(): Promise<{ status: string; version: string; tools_loaded: number }> {
        try {
            const response = await fetch(`${this.baseURL}/health`);

            if (!response.ok) {
                throw new Error('Agent service unhealthy');
            }

            return response.json();
        } catch (error) {
            console.error('Health check error:', error);
            throw error;
        }
    }
}

// Export singleton instance
export const agentAPI = new AgentAPI();
