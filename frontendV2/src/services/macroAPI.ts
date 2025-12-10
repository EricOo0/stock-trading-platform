import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface MacroDataPoint {
    date: string;
    value: number;
    growth?: number;
    yoy?: number;
    open?: number;
    high?: number;
    low?: number;
    volume?: number;
}

export interface MacroDataResponse {
    indicator: string;
    symbol?: string;
    data: MacroDataPoint[];
    units?: string;
    frequency?: string;
    title?: string;
}

// Renamed CACHE_EXPIRY to CACHE_DURATION for consistency with the provided snippet
const CACHE_DURATION = 60 * 60 * 1000; // 1 hour
// Renamed CACHE_KEY to CACHE_KEY_PREFIX for consistency with the provided snippet
const CACHE_KEY_PREFIX = 'macro_data_v3'; // Incremented to v3 to force clear old cache

export const macroAPI = {
    getHistoricalData: async (indicatorId: string): Promise<any> => {
        const cacheKey = `${CACHE_KEY_PREFIX}history_${indicatorId}`;
        const cached = localStorage.getItem(cacheKey);

        if (cached) {
            const { timestamp, data } = JSON.parse(cached);
            if (Date.now() - timestamp < CACHE_DURATION) {
                // console.log(`[MacroAPI] Using cached data for ${indicatorId}`);
                return data;
            }
        }

        try {
            const response = await fetch(`${API_BASE_URL}/macro-data/historical/${indicatorId}?period=5y`);
            const result = await response.json();

            if (result.status === 'success') {
                localStorage.setItem(cacheKey, JSON.stringify({
                    timestamp: Date.now(),
                    data: result.data
                }));
                return result.data;
            } else {
                console.error(`[MacroAPI] Failed to fetch ${indicatorId}:`, result);
                return null;
            }
        } catch (error) {
            console.error(`Error fetching macro history for ${indicatorId}:`, error);
            return null;
        }
    },

    getFedImpliedProbability: async (): Promise<any> => {
        try {
            const response = await fetch(`${API_BASE_URL}/macro-data/fed-implied-probability`);
            const result = await response.json();
            return result.status === 'success' ? result : null;
        } catch (error) {
            console.error("Error fetching Fed probability:", error);
            return null;
        }
    },

    clearCache: () => {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(CACHE_KEY_PREFIX)) localStorage.removeItem(key);
        });
        console.log('[MacroAPI] Cache cleared');
    }
};
