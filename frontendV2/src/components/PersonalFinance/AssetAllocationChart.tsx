import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { AssetItem } from '../../types/personalFinance';

interface AssetAllocationChartProps {
  assets: AssetItem[];
  cash: number;
}

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const AssetAllocationChart: React.FC<AssetAllocationChartProps> = ({ assets, cash }) => {
  // 准备图表数据
  const data = React.useMemo(() => {
    const assetGroups = assets.reduce((acc, asset) => {
      acc[asset.type] = (acc[asset.type] || 0) + asset.totalValue;
      return acc;
    }, {} as Record<string, number>);

    const result = Object.entries(assetGroups).map(([name, value]) => ({
      name,
      value
    }));

    // 添加现金
    if (cash > 0) {
      result.push({ name: 'Cash', value: cash });
    }

    // 按金额降序排序
    return result.sort((a, b) => b.value - a.value);
  }, [assets, cash]);

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg h-full">
      <h3 className="text-lg font-bold text-white mb-6">投资分布 (Allocation)</h3>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0.2)" />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem' }}
              itemStyle={{ color: '#e2e8f0' }}
              formatter={(value: number) => `¥${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              formatter={(value) => <span className="text-slate-300 ml-1">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AssetAllocationChart;
