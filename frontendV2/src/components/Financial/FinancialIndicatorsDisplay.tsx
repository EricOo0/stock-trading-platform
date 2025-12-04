/**
 * 财务指标展示组件
 * 整合所有指标卡片和趋势图表
 */

import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    DollarSign,
    Activity,
    CreditCard,
    Award,
    FileText,
    Download,
    ExternalLink
} from 'lucide-react';
import { IndicatorCard } from './IndicatorCard';
import { TrendChart } from './TrendChart';
import type { FinancialIndicators } from '../../types/financial';

interface FinancialIndicatorsDisplayProps {
    indicators: FinancialIndicators;
    symbol: string;
    market: string;
}

interface LatestReport {
    status: string;
    market?: string;
    title?: string;
    form_type?: string;
    filing_date?: string;
    date?: string;
    download_url?: string;
    ir_url?: string;
    hkexnews_url?: string;
    cninfo_url?: string;
    message?: string;
    suggestions?: string[];
}

export const FinancialIndicatorsDisplay: React.FC<FinancialIndicatorsDisplayProps> = ({
    indicators,
    symbol,
    market
}) => {
    const { revenue, profit, cashflow, debt, shareholder_return, history } = indicators;
    const [latestReport, setLatestReport] = useState<LatestReport | null>(null);
    const [reportLoading, setReportLoading] = useState(false);

    // Fetch latest report when component mounts
    useEffect(() => {
        const fetchLatestReport = async () => {
            setReportLoading(true);
            try {
                const response = await fetch(`http://localhost:8000/api/financial-report/${symbol}`);
                const data = await response.json();
                if (data.status === 'success' && data.latest_report) {
                    setLatestReport(data.latest_report);
                }
            } catch (error) {
                console.error('Failed to fetch latest report:', error);
            } finally {
                setReportLoading(false);
            }
        };

        fetchLatestReport();
    }, [symbol]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-bold text-gray-900">财务指标分析</h3>
                    <p className="text-sm text-gray-500 mt-1">
                        {symbol} • {market === 'A-SHARE' ? 'A股' : market === 'US' ? '美股' : '港股'}
                    </p>
                </div>
            </div>

            {/* Indicator Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* 收入端 */}
                <IndicatorCard
                    title="收入端指标"
                    icon={TrendingUp}
                    iconColor="text-blue-600"
                    iconBgColor="bg-blue-100"
                    borderColor="border-blue-200"
                    metrics={[
                        {
                            label: '营业收入YoY',
                            value: revenue.revenue_yoy,
                            unit: '%',
                            trend: revenue.revenue_yoy > 0 ? 'up' : revenue.revenue_yoy < 0 ? 'down' : 'neutral'
                        },
                        {
                            label: '核心营收占比',
                            value: revenue.core_revenue_ratio,
                            unit: '%'
                        },
                        {
                            label: '现金收入比',
                            value: revenue.cash_to_revenue
                        }
                    ]}
                />

                {/* 利润端 */}
                <IndicatorCard
                    title="利润端指标"
                    icon={DollarSign}
                    iconColor="text-green-600"
                    iconBgColor="bg-green-100"
                    borderColor="border-green-200"
                    metrics={[
                        {
                            label: '扣非归母净利(EPS)',
                            value: profit.non_recurring_eps,
                            unit: '元'
                        },
                        {
                            label: '经营毛利率',
                            value: profit.gross_margin,
                            unit: '%'
                        },
                        {
                            label: '核心净利率',
                            value: profit.net_margin,
                            unit: '%'
                        }
                    ]}
                />

                {/* 现金流 */}
                <IndicatorCard
                    title="现金流指标"
                    icon={Activity}
                    iconColor="text-purple-600"
                    iconBgColor="bg-purple-100"
                    borderColor="border-purple-200"
                    metrics={[
                        {
                            label: '经营现金流/净利',
                            value: cashflow.ocf_to_net_profit
                        },
                        {
                            label: '自由现金流FCF',
                            value: cashflow.free_cash_flow,
                            format: 'currency'
                        }
                    ]}
                />

                {/* 负债端 */}
                <IndicatorCard
                    title="负债端指标"
                    icon={CreditCard}
                    iconColor="text-orange-600"
                    iconBgColor="bg-orange-100"
                    borderColor="border-orange-200"
                    metrics={[
                        {
                            label: '资产负债率',
                            value: debt.asset_liability_ratio,
                            unit: '%'
                        },
                        {
                            label: '流动比率',
                            value: debt.current_ratio
                        }
                    ]}
                />

                {/* 股东回报 */}
                <IndicatorCard
                    title="股东回报指标"
                    icon={Award}
                    iconColor="text-red-600"
                    iconBgColor="bg-red-100"
                    borderColor="border-red-200"
                    metrics={[
                        {
                            label: '股息率',
                            value: shareholder_return.dividend_yield,
                            unit: '%'
                        },
                        {
                            label: 'ROE(净资产收益率)',
                            value: shareholder_return.roe,
                            unit: '%',
                            trend: shareholder_return.roe > 15 ? 'up' : shareholder_return.roe < 10 ? 'down' : 'neutral'
                        }
                    ]}
                />
            </div>

            {/* Trend Chart */}
            {history && history.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h4 className="text-lg font-bold text-gray-900 mb-4">历史趋势分析</h4>
                    <TrendChart data={history} />
                </div>
            )}

            {/* Latest Financial Report */}
            {latestReport && (latestReport.status === 'success' || latestReport.status === 'partial') && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                            <FileText size={20} className="text-white" />
                        </div>
                        <div>
                            <h5 className="text-base font-bold text-gray-900">财报文档</h5>
                            <p className="text-xs text-gray-600">
                                {latestReport.market === 'US' && 'SEC EDGAR 官方文件'}
                                {latestReport.market === 'HK' && '港股披露易/公司IR'}
                                {latestReport.market === 'A-SHARE' && '巨潮资讯网'}
                            </p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {latestReport.title && (
                            <p className="text-sm text-gray-700">
                                <span className="font-medium">标题:</span> {latestReport.title}
                            </p>
                        )}
                        {latestReport.form_type && (
                            <p className="text-sm text-gray-700">
                                <span className="font-medium">类型:</span> {latestReport.form_type}
                            </p>
                        )}
                        {(latestReport.filing_date || latestReport.date) && (
                            <p className="text-sm text-gray-700">
                                <span className="font-medium">日期:</span> {latestReport.filing_date || latestReport.date}
                            </p>
                        )}

                        {latestReport.message && (
                            <p className="text-sm text-gray-600 bg-white/50 rounded-lg p-3">
                                {latestReport.message}
                            </p>
                        )}

                        {/* Download Button */}
                        {latestReport.download_url && (
                            <a
                                href={latestReport.download_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block w-full mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-blue-600/30 hover:shadow-xl hover:shadow-blue-600/40 text-center flex items-center justify-center gap-2"
                            >
                                <Download size={16} />
                                查看/下载财报
                                <ExternalLink size={14} />
                            </a>
                        )}

                        {/* Additional Links */}
                        <div className="flex gap-2 mt-3">
                            {latestReport.ir_url && (
                                <a
                                    href={latestReport.ir_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex-1 px-4 py-2 bg-white hover:bg-gray-50 text-blue-600 rounded-lg text-xs font-medium transition-colors border border-blue-200 text-center"
                                >
                                    公司IR页面
                                </a>
                            )}
                            {latestReport.hkexnews_url && (
                                <a
                                    href={latestReport.hkexnews_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex-1 px-4 py-2 bg-white hover:bg-gray-50 text-blue-600 rounded-lg text-xs font-medium transition-colors border border-blue-200 text-center"
                                >
                                    披露易搜索
                                </a>
                            )}
                            {latestReport.cninfo_url && (
                                <a
                                    href={latestReport.cninfo_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex-1 px-4 py-2 bg-white hover:bg-gray-50 text-blue-600 rounded-lg text-xs font-medium transition-colors border border-blue-200 text-center"
                                >
                                    巨潮资讯网
                                </a>
                            )}
                        </div>

                        {/* Suggestions */}
                        {latestReport.suggestions && latestReport.suggestions.length > 0 && (
                            <div className="mt-4 p-3 bg-white/70 rounded-lg">
                                <p className="text-xs font-medium text-gray-700 mb-2">💡 使用提示:</p>
                                <ul className="text-xs text-gray-600 space-y-1">
                                    {latestReport.suggestions.map((suggestion, idx) => (
                                        <li key={idx} className="flex items-start gap-2">
                                            <span className="text-blue-500 mt-0.5">•</span>
                                            <span>{suggestion}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
