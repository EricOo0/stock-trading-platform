import React, { useState } from 'react';
import type { FinancialIndicatorsData } from '../../types/financial';
import IndicatorCard from './IndicatorCard';
import TrendChart from './TrendChart';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';

interface FinancialIndicatorsDisplayProps {
    data: FinancialIndicatorsData;
    isLoading?: boolean;
}

const FinancialIndicatorsDisplay: React.FC<FinancialIndicatorsDisplayProps> = ({
    data,
    isLoading = false
}) => {
    const [isExpanded, setIsExpanded] = useState(true);

    if (isLoading) {
        return (
            <div className="animate-pulse space-y-4">
                <div className="h-8 bg-gray-700 rounded w-1/4"></div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-32 bg-gray-700 rounded-xl"></div>
                    ))}
                </div>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                    Financial Health
                    <Info className="w-4 h-4 text-gray-400" />
                </h2>
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="p-1 hover:bg-gray-700 rounded-full transition-colors"
                >
                    {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                </button>
            </div>

            {isExpanded && (
                <div className="space-y-6 animate-in fade-in slide-in-from-top-4 duration-500">
                    {/* Key Metrics Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* Revenue Growth */}
                        <IndicatorCard
                            title="Revenue Growth (YoY)"
                            value={`${data.revenue.revenue_yoy}%`}
                            trend={data.revenue.revenue_yoy > 0 ? 'up' : 'down'}
                            subValue={data.revenue.core_revenue_ratio ? `${data.revenue.core_revenue_ratio}%` : undefined}
                            subLabel="Core Ratio"
                            tooltip="Year-over-year revenue growth rate"
                        />

                        {/* Net Margin */}
                        <IndicatorCard
                            title="Net Profit Margin"
                            value={`${data.profit.net_margin}%`}
                            trend={data.profit.net_margin > 15 ? 'up' : data.profit.net_margin > 5 ? 'neutral' : 'down'}
                            subValue={`${data.profit.gross_margin}%`}
                            subLabel="Gross"
                            tooltip="Net income as a percentage of revenue"
                        />

                        {/* ROE */}
                        <IndicatorCard
                            title="ROE"
                            value={`${data.shareholder_return.roe}%`}
                            trend={data.shareholder_return.roe > 15 ? 'up' : 'neutral'}
                            subValue={`${data.shareholder_return.dividend_yield}%`}
                            subLabel="Div Yield"
                            tooltip="Return on Equity"
                        />

                        {/* Debt Ratio */}
                        <IndicatorCard
                            title="Asset/Liability Ratio"
                            value={`${data.debt.asset_liability_ratio}%`}
                            trend={data.debt.asset_liability_ratio < 60 ? 'up' : 'down'}
                            subValue={data.debt.current_ratio ? `${data.debt.current_ratio}` : undefined}
                            subLabel="Current Ratio"
                            tooltip="Total liabilities divided by total assets"
                        />
                    </div>

                    {/* Charts Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <TrendChart
                            data={data.history}
                            title="Profitability Trends (Last 3 Years)"
                        />

                        {/* Cash Flow & Quality */}
                        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4">
                            <h3 className="text-gray-300 text-sm font-medium mb-4">Quality Metrics</h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center p-3 bg-gray-700/30 rounded-lg">
                                    <span className="text-gray-400 text-sm">Cash to Revenue</span>
                                    <span className={`font-mono font-medium ${data.revenue.cash_to_revenue > 0.8 ? 'text-green-400' : 'text-yellow-400'}`}>
                                        {data.revenue.cash_to_revenue}x
                                    </span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-700/30 rounded-lg">
                                    <span className="text-gray-400 text-sm">OCF / Net Profit</span>
                                    <span className={`font-mono font-medium ${data.cashflow.ocf_to_net_profit > 1 ? 'text-green-400' : 'text-yellow-400'}`}>
                                        {data.cashflow.ocf_to_net_profit}x
                                    </span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-700/30 rounded-lg">
                                    <span className="text-gray-400 text-sm">Non-Recurring Profit Impact</span>
                                    <span className="font-mono font-medium text-gray-300">
                                        {data.profit.non_recurring_net_profit ? 'Yes' : 'No'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FinancialIndicatorsDisplay;
