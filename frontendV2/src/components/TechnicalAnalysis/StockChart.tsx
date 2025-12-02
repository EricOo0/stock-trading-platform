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

interface StockData {
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ma5?: number;
    ma10?: number;
    ma20?: number;
    ma30?: number;
    ma60?: number;
    boll_upper?: number;
    boll_mid?: number;
    boll_lower?: number;
    macd_dif?: number;
    macd_dea?: number;
    macd_bar?: number;
    rsi14?: number;
    kdj_k?: number;
    kdj_d?: number;
    kdj_j?: number;
}

interface StockChartProps {
    data: StockData[];
    mainIndicator: 'MA' | 'BOLL' | 'NONE';
    subIndicator: 'MACD' | 'RSI' | 'KDJ' | 'VOL' | 'NONE';
}

const CandlestickShape = (props: any) => {
    const { x, y, width, height, low, high, open, close, yAxis } = props;

    // Safety check: if yAxis or scale is missing, or data is invalid, don't render
    if (!yAxis || !yAxis.scale || open === undefined || close === undefined || high === undefined || low === undefined) {
        return null;
    }

    const isRising = close > open;
    const color = isRising ? '#ef4444' : '#22c55e';

    const scale = yAxis.scale;
    const yOpen = scale(open);
    const yClose = scale(close);
    const yHigh = scale(high);
    const yLow = scale(low);

    const bodyHeight = Math.abs(yOpen - yClose);
    const bodyY = Math.min(yOpen, yClose);
    const finalBodyHeight = Math.max(1, bodyHeight);

    return (
        <g>
            <line
                x1={x + width / 2}
                y1={yHigh}
                x2={x + width / 2}
                y2={yLow}
                stroke={color}
                strokeWidth={1}
            />
            <rect
                x={x}
                y={bodyY}
                width={width}
                height={finalBodyHeight}
                fill={isRising ? 'none' : color}
                fillOpacity={1}
                stroke={color}
                strokeWidth={1}
            />
        </g>
    );
};


const StockChart: React.FC<StockChartProps> = ({ data, mainIndicator, subIndicator }) => {
    // 格式化日期
    const formatDate = (dateStr: string) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    };

    // 计算Y轴范围
    const prices = data.flatMap(d => [d.low, d.high, d.ma5, d.ma10, d.ma20, d.boll_upper, d.boll_lower].filter(v => v !== undefined) as number[]);
    const minPrice = Math.min(...prices) * 0.98;
    const maxPrice = Math.max(...prices) * 1.02;

    return (
        <div className="flex flex-col gap-2 h-[600px]">
            {/* 主图 */}
            <div className="flex-1 bg-slate-900 rounded-lg p-2 border border-slate-800">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                            itemStyle={{ color: '#f8fafc' }}
                            labelFormatter={(label) => new Date(label).toLocaleDateString()}
                            formatter={(value: number) => value.toFixed(2)}
                        />

                        {/* K线 (使用 Bar + ErrorBar 模拟，或者 Custom Shape) */}
                        {/* 这里为了简单，先用 Custom Shape 渲染蜡烛 */}
                        {/* 需要传入 low, high, open, close 给 shape */}
                        <Bar
                            dataKey="close" // 主要用于 tooltip，实际渲染由 shape 控制
                            shape={(props: any) => {
                                const { payload, x, y, width, height } = props;
                                return <CandlestickShape {...props} open={payload.open} close={payload.close} high={payload.high} low={payload.low} />;
                            }}
                            isAnimationActive={false}
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
                                    shape={(props: any) => {
                                        const { payload, x, y, width, height } = props;
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
                                    <Bar dataKey="macd_bar" name="MACD" shape={(props: any) => {
                                        const { x, y, width, height, payload } = props;
                                        const fill = payload.macd_bar > 0 ? '#ef4444' : '#22c55e';
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
