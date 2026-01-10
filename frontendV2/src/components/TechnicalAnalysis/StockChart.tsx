import React from 'react';
import {
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Area,
} from 'recharts';
import type { StockData } from '../../types/stock';

export type { StockData }; // Re-export for compatibility

interface StockChartProps {
    data: StockData[];
    mainIndicator: 'MA' | 'BOLL' | 'NONE';
    subIndicator: 'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE';
}

interface ChartShapeProps {
    x: number;
    y: number;
    width: number;
    height: number;
    payload: StockData;
    // Add specific props if needed
    open?: number;
    close?: number;
    high?: number;
    low?: number;
    yAxis?: { scale: (v: number) => number };
}

// Custom Tooltip Component
const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        // Find the main stock data payload
        const data = payload[0].payload;
        
        return (
            <div className="bg-slate-800 border border-slate-700 p-3 rounded shadow-lg text-xs">
                <p className="text-slate-400 mb-2">{new Date(label).toLocaleDateString()}</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                    <div className="flex justify-between"><span className="text-slate-400">Open:</span> <span className={data.open > data.close ? "text-green-500" : "text-red-500"}>{Number(data.open).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Close:</span> <span className={data.open > data.close ? "text-green-500" : "text-red-500"}>{Number(data.close).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">High:</span> <span className={data.open > data.close ? "text-green-500" : "text-red-500"}>{Number(data.high).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Low:</span> <span className={data.open > data.close ? "text-green-500" : "text-red-500"}>{Number(data.low).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Vol:</span> <span className="text-slate-200">{Number(data.volume).toLocaleString()}</span></div>
                </div>
            </div>
        );
    }
    return null;
};

const CandlestickShape = (props: any) => {
    const { x, width, yAxis } = props;
    
    // Explicit props passed from <Bar ... />
    let open = props.open;
    let close = props.close;
    let high = props.high;
    let low = props.low;

    // Fallback to payload
    if (open === undefined) open = props.payload?.open;
    if (close === undefined) close = props.payload?.close;
    if (high === undefined) high = props.payload?.high;
    if (low === undefined) low = props.payload?.low;

    if (!yAxis || !yAxis.scale) return null;

    open = Number(open);
    close = Number(close);
    high = Number(high);
    low = Number(low);

    if (isNaN(open) || isNaN(close) || isNaN(high) || isNaN(low)) return null;

    const scale = yAxis.scale;
    const yOpen = scale(open);
    const yClose = scale(close);
    const yHigh = scale(high);
    const yLow = scale(low);

    const isRising = close >= open;
    const color = isRising ? '#ef4444' : '#22c55e'; 

    // Calculate dimensions
    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(1, Math.abs(yOpen - yClose));
    
    // Adjust width to ensure it's visible but not overlapping too much
    // Use a default width if calculated width is weird
    // width from Recharts can be 0 if data is dense or config is wrong
    const safeWidth = width && !isNaN(width) && width > 0 ? width : 20; 
    const candleWidth = Math.max(3, safeWidth * 0.7); 
    const xOffset = (safeWidth - candleWidth) / 2;

    return (
        <g>
            <line
                x1={x + safeWidth / 2}
                y1={yHigh}
                x2={x + safeWidth / 2}
                y2={yLow}
                stroke={color}
                strokeWidth={1}
            />
            <rect
                x={x + xOffset}
                y={bodyTop}
                width={candleWidth} 
                height={bodyHeight}
                fill={color}
                fillOpacity={1}
                stroke="none"
            />
        </g>
    );
};


const StockChart: React.FC<StockChartProps> = ({ data, mainIndicator, subIndicator }) => {
    if (!data || data.length === 0) return <div>No Data</div>;

    // 格式化日期
    const formatDate = (dateStr: string) => {
        if (!dateStr) return '';
        try {
            const date = new Date(dateStr);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        } catch {
            return dateStr;
        }
    };

    // 计算Y轴范围
    // 强制转换为数字并过滤非法值和0值
    const prices = data.flatMap(d => [
        d.low, d.high,
        d.ma5, d.ma10, d.ma20, d.ma30, d.ma60,
        d.boll_upper, d.boll_lower
    ].filter(v => v !== undefined && v !== null && !isNaN(Number(v)) && Number(v) > 0).map(Number));

    // 如果数据点太少（例如只有一个），min和max可能相同，导致 domain 计算问题，需要处理
    let minPrice = prices.length > 0 ? Math.min(...prices) * 0.98 : 0;
    let maxPrice = prices.length > 0 ? Math.max(...prices) * 1.02 : 100;
    
    if (minPrice === maxPrice) {
        minPrice = minPrice * 0.95;
        maxPrice = maxPrice * 1.05;
    }
    
    if (minPrice <= 0) minPrice = 0;
    if (maxPrice <= 0) maxPrice = 100;

    return (
        <div className="flex flex-col gap-2 h-[600px]">
            {/* 主图 */}
            <div className="flex-1 bg-slate-900 rounded-lg p-2 border border-slate-800">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart key={data.length} data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                        <XAxis
                            dataKey="timestamp"
                            tickFormatter={formatDate}
                            stroke="#94a3b8"
                            tick={{ fontSize: 12 }}
                            minTickGap={30}
                        />
                        <YAxis
                            domain={[minPrice, maxPrice]}
                            orientation="right"
                            stroke="#94a3b8"
                            tick={{ fontSize: 12 }}
                            tickFormatter={(val) => val.toFixed(2)}
                            allowDataOverflow={true}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '3 3' }} />

                        {/* K线 */}
                        <Bar
                            dataKey="close"
                            barSize={20} // Force barSize to ensure rendering even if XAxis scale fails
                            shape={(props: any) => (
                                <CandlestickShape
                                    {...props}
                                    open={props.payload.open}
                                    close={props.payload.close}
                                    high={props.payload.high}
                                    low={props.payload.low}
                                />
                            )}
                            isAnimationActive={false}
                            minPointSize={2}
                        />

                        {/* MA 指标 */}
                        {mainIndicator === 'MA' && (
                            <>
                                <Line type="monotone" dataKey="ma5" stroke="#fbbf24" dot={false} strokeWidth={1} name="MA5" />
                                <Line type="monotone" dataKey="ma10" stroke="#38bdf8" dot={false} strokeWidth={1} name="MA10" />
                                <Line type="monotone" dataKey="ma20" stroke="#c084fc" dot={false} strokeWidth={1} name="MA20" />
                                <Line type="monotone" dataKey="ma60" stroke="#22c55e" dot={false} strokeWidth={1} name="MA60" />
                            </>
                        )}

                        {/* BOLL 指标 */}
                        {mainIndicator === 'BOLL' && (
                            <>
                                <Line type="monotone" dataKey="boll_upper" stroke="#fbbf24" dot={false} strokeWidth={1} strokeDasharray="3 3" name="Upper" />
                                <Line type="monotone" dataKey="boll_mid" stroke="#f8fafc" dot={false} strokeWidth={1} name="Mid" />
                                <Line type="monotone" dataKey="boll_lower" stroke="#c084fc" dot={false} strokeWidth={1} strokeDasharray="3 3" name="Lower" />
                                <Area type="monotone" dataKey="boll_upper" fill="#fbbf24" fillOpacity={0.05} stroke="none" />
                            </>
                        )}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* 副图 */}
            {subIndicator !== 'NONE' && (
                <div className="h-[200px] bg-slate-900 rounded-lg p-2 border border-slate-800">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="timestamp" hide />
                            <YAxis orientation="right" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                labelFormatter={() => ''}
                                formatter={(value: number) => value.toFixed(2)}
                            />

                            {/* 成交量 */}
                            {subIndicator === 'VOL' && (
                                <Bar
                                    dataKey="volume"
                                    fill="#38bdf8"
                                    name="Volume"
                                    shape={(props: unknown) => {
                                        const { payload, x, y, width, height } = props as ChartShapeProps;
                                        const isRising = payload.close > payload.open;
                                        return <rect x={x} y={y} width={width} height={height} fill={isRising ? '#ef4444' : '#22c55e'} />;
                                    }}
                                />
                            )}

                            {/* MACD */}
                            {subIndicator === 'MACD' && (
                                <>
                                    <Line type="monotone" dataKey="macd_dif" stroke="#fbbf24" dot={false} strokeWidth={1} name="DIF" />
                                    <Line type="monotone" dataKey="macd_dea" stroke="#38bdf8" dot={false} strokeWidth={1} name="DEA" />
                                    <Bar dataKey="macd_bar" name="MACD" shape={(props: unknown) => {
                                        const { x, y, width, height, payload } = props as ChartShapeProps;
                                        const fill = payload.macd_bar !== undefined && payload.macd_bar > 0 ? '#ef4444' : '#22c55e';
                                        return <rect x={x} y={y} width={width} height={height} fill={fill} />;
                                    }} />
                                </>
                            )}

                            {/* RSI */}
                            {subIndicator === 'RSI' && (
                                <>
                                    <Line type="monotone" dataKey="rsi14" stroke="#c084fc" dot={false} strokeWidth={1} name="RSI14" />
                                    <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" />
                                    <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" />
                                </>
                            )}

                            {/* KDJ */}
                            {subIndicator === 'KDJ' && (
                                <>
                                    <Line type="monotone" dataKey="kdj_k" stroke="#fbbf24" dot={false} strokeWidth={1} name="K" />
                                    <Line type="monotone" dataKey="kdj_d" stroke="#38bdf8" dot={false} strokeWidth={1} name="D" />
                                    <Line type="monotone" dataKey="kdj_j" stroke="#c084fc" dot={false} strokeWidth={1} name="J" />
                                </>
                            )}
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default StockChart;