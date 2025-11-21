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

interface CacheItem {
    timestamp: number;
    data: MacroDataResponse;
}

const CACHE_DURATION = 60 * 60 * 1000; // 1 hour
const cache: Record<string, CacheItem> = {};

export const macroAPI = {
    getHistoricalData: async (indicator: string, period: string = '1y'): Promise<MacroDataResponse> => {
        const cacheKey = `${indicator}-${period}`;
        const now = Date.now();

        if (cache[cacheKey] && (now - cache[cacheKey].timestamp < CACHE_DURATION)) {
            console.log(`[MacroAPI] Using cached data for ${indicator}`);
            return cache[cacheKey].data;
        }

        try {
            const response = await axios.get(`${API_BASE_URL}/macro-data/historical/${indicator}`, {
                params: { period }
            });

            if (response.data.status === 'success') {
                const data = response.data.data;
                cache[cacheKey] = {
                    timestamp: now,
                    data: data
                };
                return data;
            } else {
                throw new Error(response.data.message || 'Failed to fetch data');
            }
        } catch (error) {
            console.error(`Error fetching macro data for ${indicator}:`, error);
            throw error;
        }
    },

    clearCache: () => {
        for (const key in cache) {
            delete cache[key];
        }
        console.log('[MacroAPI] Cache cleared');
    }
};
