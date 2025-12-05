import axios from 'axios';
import type { FinancialIndicatorsResponse } from '../types/financial';

const API_BASE_URL = 'http://localhost:8000'; // Adjust if needed

export const getFinancialIndicators = async (symbol: string): Promise<FinancialIndicatorsResponse> => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/tools/financial_report_tool/get_financial_indicators`, {
            symbol: symbol,
            years: 3
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching financial indicators:', error);
        throw error;
    }
};
