import axios from 'axios';

// API Base URL
const API_BASE_URL = '/api';

export interface DeepSearchResponse {
    status: string;
    session_id: string;
    adk_session_id?: string;
    data: any;
    message?: string;
}

export const newsSentimentAPI = {
    /**
     * Create a new Browser Session
     */
    createSession: async (): Promise<string> => {
        try {
            const response = await axios.post(`${API_BASE_URL}/browser/session`, {});
            if (response.data.status === 'success' && response.data.data) {
                return response.data.data.session_id;
            }
            throw new Error("Failed to create session");
        } catch (error) {
            console.error("Session Creation Error:", error);
            throw error;
        }
    },

    /**
     * Start a News Sentiment session
     * @param query The research query
     * @param sessionId Optional session ID (for browser persistence)
     */
    startResearch: async (query: string, sessionId?: string): Promise<DeepSearchResponse> => {
        try {
            // Generate a session ID if not provided? Or let backend handle it.
            // But for Browser View, we need a known session ID.
            const sid = sessionId || `session_${Math.random().toString(36).substr(2, 9)}`;

            const response = await axios.post(`${API_BASE_URL}/agent/news-sentiment/start`, {
                query: query,
                session_id: sid
            });
            return response.data;
        } catch (error) {
            console.error("News Sentiment Error:", error);
            throw error;
        }
    },

    /**
     * Get the Browser Session View URL
     * @param sessionId The session ID
     */
    getBrowserViewUrl: (sessionId: string) => {
        // Steel session view usually requires a specific URL provided by backend
        // Assume backend proxy or direct Steel URL. 
        // Based on `backend/entrypoints/api/routers/browser.py` (if it existed), or direct.
        // For now, let's assume we call an endpoint to get the *actual* iframe URL.
        // Wait, does backend expose one?
        return `${API_BASE_URL}/browser/session/${sessionId}/view`;
    }
};
