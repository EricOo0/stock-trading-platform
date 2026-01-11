import React, { useState, useEffect } from 'react';
import type { AssetItem } from '../../types/personalFinance';
import { Edit2, Trash2 } from 'lucide-react';

interface AssetTableProps {
  assets: AssetItem[];
  onEdit: (asset: AssetItem) => void;
  onUpdateAsset: (id: string, field: keyof AssetItem, value: string | number) => void;
  onDelete: (asset: AssetItem) => void;
}

interface EditableCellProps {
  value: string | number;
  type?: 'text' | 'number';
  onUpdate: (val: string | number) => void;
  align?: 'left' | 'right';
  className?: string;
}

const EditableCell: React.FC<EditableCellProps> = ({ value, type = 'text', onUpdate, align = 'left', className = '' }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [tempValue, setTempValue] = useState(value.toString());

  useEffect(() => {
    setTempValue(value.toString());
  }, [value]);

  const handleCommit = () => {
    if (tempValue !== value.toString()) {
      if (type === 'number') {
        const num = parseFloat(tempValue);
        if (!isNaN(num) && num >= 0) {
          onUpdate(num);
        } else {
          setTempValue(value.toString());
        }
      } else {
        onUpdate(tempValue);
      }
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCommit();
    if (e.key === 'Escape') {
      setTempValue(value.toString());
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <input
        autoFocus
        type={type}
        className={`w-full bg-slate-900 border border-blue-500 rounded px-2 py-1 text-white focus:outline-none text-sm ${align === 'right' ? 'text-right' : 'text-left'}`}
        value={tempValue}
        onChange={e => setTempValue(e.target.value)}
        onBlur={handleCommit}
        onKeyDown={handleKeyDown}
        step={type === 'number' ? "0.01" : undefined}
      />
    );
  }

  return (
    <div 
      onClick={() => {
        setTempValue(value.toString());
        setIsEditing(true);
      }}
      className={`cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1 transition-colors flex items-center gap-2 group ${align === 'right' ? 'justify-end' : 'justify-start'} ${className}`}
      title="点击修改"
    >
      <span className="truncate">{type === 'number' ? `¥${Number(value).toLocaleString()}` : value || '-'}</span>
      <Edit2 size={12} className="opacity-0 group-hover:opacity-50 text-slate-400 flex-shrink-0" />
    </div>
  );
};

const AssetTable: React.FC<AssetTableProps> = ({ assets, onEdit, onUpdateAsset, onDelete }) => {
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
      <div className="p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="text-lg font-bold text-white">持仓列表 (Holdings)</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-700/50 text-slate-400 text-sm">
              <th className="p-4 font-medium w-[20%]">项目名称</th>
              <th className="p-4 font-medium w-[15%]">代码</th>
              <th className="p-4 font-medium w-[10%]">类型</th>
              <th className="p-4 font-medium text-right w-[10%]">持有数量</th>
              <th className="p-4 font-medium text-right w-[10%]">现价</th>
              <th className="p-4 font-medium text-right">总市值</th>
              <th className="p-4 font-medium text-right">成本</th>
              <th className="p-4 font-medium text-right">浮动盈亏</th>
              <th className="p-4 font-medium text-right">收益率</th>
              <th className="p-4 font-medium text-center w-[100px]">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {assets.length === 0 ? (
              <tr>
                <td colSpan={10} className="p-8 text-center text-slate-500">
                  暂无持仓
                </td>
              </tr>
            ) : (
              assets.map((asset) => (
                <tr key={asset.id} className="hover:bg-slate-700/30 transition-colors">
                  <td className="p-4 font-medium text-white">
                    <EditableCell 
                      value={asset.name} 
                      onUpdate={(val) => onUpdateAsset(asset.id, 'name', val)} 
                    />
                  </td>
                  <td className="p-4 text-slate-400 text-sm font-mono">
                    <EditableCell 
                      value={asset.code || ''} 
                      onUpdate={(val) => onUpdateAsset(asset.id, 'code', val)} 
                    />
                  </td>
                  <td className="p-4 text-slate-400 text-sm">{asset.type}</td>
                  <td className="p-4 text-right text-slate-300">{asset.quantity.toLocaleString()}</td>
                  <td className="p-4 text-right text-slate-300">
                    <EditableCell 
                      value={asset.currentPrice} 
                      type="number" 
                      align="right"
                      onUpdate={(val) => onUpdateAsset(asset.id, 'currentPrice', val)} 
                    />
                  </td>
                  <td className="p-4 text-right font-medium text-white">¥{asset.totalValue.toLocaleString()}</td>
                  <td className="p-4 text-right text-slate-400">
                    <div>¥{asset.totalCost.toLocaleString()}</div>
                    <div className="text-xs text-slate-500 font-mono">(@ ¥{asset.avgCost.toLocaleString()})</div>
                  </td>
                  <td className={`p-4 text-right font-medium ${asset.pnl >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {asset.pnl >= 0 ? '+' : ''}{asset.pnl.toLocaleString()}
                  </td>
                  <td className={`p-4 text-right font-medium ${asset.pnlRate >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {(asset.pnlRate * 100).toFixed(2)}%
                  </td>
                  <td className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button 
                        onClick={() => onEdit(asset)}
                        className="p-1.5 rounded-lg hover:bg-slate-600 text-slate-400 hover:text-white transition-colors"
                        title="快速交易"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button 
                        onClick={() => onDelete(asset)}
                        className="p-1.5 rounded-lg hover:bg-slate-600 text-slate-400 hover:text-red-400 transition-colors"
                        title="清仓卖出"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AssetTable;
