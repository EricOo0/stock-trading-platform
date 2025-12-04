/**
 * 财务指标API服务
 */

import axios from 'axios';
import type {
    FinancialIndicatorsRequest,
    FinancialIndicatorsResponse,
    FinancialIndicatorsError
} from '../types/financial';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class FinancialService {
    /**
     * 获取财务指标数据
     */
    static async getFinancialIndicators(
        params: FinancialIndicatorsRequest
    ): Promise<FinancialIndicatorsResponse> {
        try {
            const response = await axios.post<FinancialIndicatorsResponse>(
                `${API_BASE_URL}/api/financial/indicators`,
                {
                    symbol: params.symbol,
                    years: params.years || 3,
                    use_cache: params.use_cache !== false
                }
            );

            if (response.data.status !== 'success') {
                throw new Error((response.data as unknown as FinancialIndicatorsError).message);
            }

            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                throw new Error(
                    error.response?.data?.message ||
                    error.message ||
                    '获取财务指标失败'
                );
            }
            throw error;
        }
    }

    /**
     * 清除缓存并重新获取
     */
    static async refreshFinancialIndicators(
        symbol: string,
        years?: number
    ): Promise<FinancialIndicatorsResponse> {
        return this.getFinancialIndicators({
            symbol,
            years,
            use_cache: false
        });
    }
}
