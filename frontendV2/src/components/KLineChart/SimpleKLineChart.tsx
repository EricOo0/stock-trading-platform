import React from 'react';

interface SimpleKLineData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface SimpleKLineChartProps {
  data: SimpleKLineData[];
  width?: number;
  height?: number;
}

const SimpleKLineChart: React.FC<SimpleKLineChartProps> = ({ data, width = 600, height = 200 }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        width, 
        height, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        border: '1px solid #ddd',
        borderRadius: '4px'
      }}>
        <span style={{ color: '#666' }}>暂无数据</span>
      </div>
    );
  }

  // 计算价格范围
  const prices = data.flatMap(d => [d.high, d.low]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;

  // 计算图表参数
  const candleWidth = Math.max(2, (width - 40) / data.length - 1);
  const chartHeight = height - 40;
  const scale = chartHeight / priceRange;

  const priceToY = (price: number) => {
    return chartHeight - ((price - minPrice) * scale) + 20;
  };

  return (
    <div style={{ 
      width, 
      height, 
      backgroundColor: 'white',
      border: '1px solid #e0e0e0',
      borderRadius: '4px',
      padding: '10px'
    }}>
      <svg width={width - 20} height={height - 20}>
        {/* 网格线 */}
        {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
          const y = ratio * chartHeight + 10;
          const price = minPrice + (1 - ratio) * priceRange;
          return (
            <g key={ratio}>
              <line
                x1={30}
                y1={y}
                x2={width - 30}
                y2={y}
                stroke="#f0f0f0"
                strokeWidth={1}
              />
              <text
                x={25}
                y={y + 4}
                fontSize={10}
                fill="#666"
                textAnchor="end"
              >
                {price.toFixed(2)}
              </text>
            </g>
          );
        })}
        
        {/* K线 */}
        {data.map((candle, index) => {
          const x = 30 + index * (candleWidth + 1);
          const openY = priceToY(candle.open);
          const closeY = priceToY(candle.close);
          const highY = priceToY(candle.high);
          const lowY = priceToY(candle.low);
          
          const isUp = candle.close >= candle.open;
          const color = isUp ? '#10b981' : '#ef4444';
          const bodyTop = Math.min(openY, closeY);
          const bodyHeight = Math.abs(closeY - openY);
          
          return (
            <g key={index}>
              {/* 上下影线 */}
              <line
                x1={x + candleWidth / 2}
                y1={highY}
                x2={x + candleWidth / 2}
                y2={lowY}
                stroke={color}
                strokeWidth={1}
              />
              {/* K线实体 */}
              <rect
                x={x}
                y={bodyTop}
                width={candleWidth}
                height={Math.max(1, bodyHeight)}
                fill={color}
                stroke={color}
                strokeWidth={1}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default SimpleKLineChart;