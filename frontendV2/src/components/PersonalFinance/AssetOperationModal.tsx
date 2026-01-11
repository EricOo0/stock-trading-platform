import React, { useState, useEffect } from 'react';
import { X, ArrowDownRight, ArrowUpRight, Plus, Minus, Edit3 } from 'lucide-react';
import type { AssetItem, Transaction, TransactionType, AssetType } from '../../types/personalFinance';

interface AssetOperationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (tx: Transaction) => void;
  currentAssets: AssetItem[];
  initialAsset?: AssetItem | null; // 如果从表格点击编辑，传入初始资产
}

const AssetOperationModal: React.FC<AssetOperationModalProps> = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  currentAssets,
  initialAsset 
}) => {
  const [type, setType] = useState<TransactionType>('Buy');
  const [assetName, setAssetName] = useState('');
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [quantity, setQuantity] = useState<string>('');
  const [assetType, setAssetType] = useState<AssetType>('Stock');

  useEffect(() => {
    if (isOpen) {
      if (initialAsset) {
        setAssetName(initialAsset.name);
        setPrice(initialAsset.currentPrice.toString());
        setAssetType(initialAsset.type);
        // Default to Update if initialAsset is provided, otherwise Buy
        if (initialAsset) {
          setType('Update');
        } else {
          setType('Buy');
        }
      } else {
        // Reset form
        setAssetName('');
        setAmount('');
        setPrice('');
        setQuantity('');
        setType('Buy');
      }
    }
  }, [isOpen, initialAsset]);

  // 当选择已有资产时，自动填充现价 (Update 模式也适用)
  useEffect(() => {
    if (type === 'Sell' || type === 'Buy' || type === 'Update') {
      const existing = currentAssets.find(a => a.name === assetName);
      if (existing) {
        if (!price && type !== 'Update') { // Update 模式下尽量保留用户输入或初始值，不强行覆盖，除非是切换资产
           setPrice(existing.currentPrice.toString());
        }
      }
    }
  }, [assetName, currentAssets, type, price]);

  // 自动计算逻辑：
  // Update 模式下，通常直接修改 Quantity 或 Price，Amount 会随之变化
  const handlePriceChange = (val: string) => {
    setPrice(val);
    if (val && quantity) {
      setAmount((parseFloat(val) * parseFloat(quantity)).toFixed(2));
    }
  };

  const handleQuantityChange = (val: string) => {
    setQuantity(val);
    if (val && price) {
      setAmount((parseFloat(val) * parseFloat(price)).toFixed(2));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const tx: Transaction = {
      id: Date.now().toString(),
      date: new Date().toISOString(),
      type,
      amount: parseFloat(amount) || 0,
    };

    if (type === 'Buy' || type === 'Sell' || type === 'Update') {
      tx.assetName = assetName;
      tx.price = parseFloat(price);
      tx.quantity = parseFloat(quantity);
    }

    onSubmit(tx);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
          <h3 className="text-lg font-bold text-white">资产操作 (Transaction)</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="grid grid-cols-5 p-2 gap-2 bg-slate-900/30">
          {(['Buy', 'Sell', 'Update', 'Deposit', 'Withdraw'] as TransactionType[]).map(t => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={`
                py-2 text-xs font-medium rounded-lg transition-all flex items-center justify-center gap-1
                ${type === t 
                  ? t === 'Buy' || t === 'Deposit' ? 'bg-emerald-600 text-white' 
                    : t === 'Update' ? 'bg-blue-600 text-white'
                    : 'bg-red-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }
              `}
            >
              {t === 'Buy' && <Plus size={14} />}
              {t === 'Sell' && <Minus size={14} />}
              {t === 'Update' && <Edit3 size={14} />}
              {t === 'Deposit' && <ArrowDownRight size={14} />}
              {t === 'Withdraw' && <ArrowUpRight size={14} />}
              {t === 'Buy' ? '买入' : t === 'Sell' ? '卖出' : t === 'Update' ? '修正' : t === 'Deposit' ? '充值' : '提现'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          
          {(type === 'Buy' || type === 'Sell' || type === 'Update') && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">资产名称 (Asset Name)</label>
                {type === 'Sell' || type === 'Update' ? (
                  <select 
                    value={assetName} 
                    onChange={e => setAssetName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                    required
                    disabled={!!initialAsset && type === 'Update'} // 如果是从表格进来的Update，锁定名字
                  >
                    <option value="">选择资产...</option>
                    {currentAssets.map(a => (
                      <option key={a.id} value={a.name}>{a.name} (持仓: {a.quantity})</option>
                    ))}
                  </select>
                ) : (
                  <input 
                    type="text" 
                    value={assetName}
                    onChange={e => setAssetName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="例如: AAPL, BTC..."
                    required
                    list="asset-suggestions"
                  />
                )}
                <datalist id="asset-suggestions">
                   {currentAssets.map(a => <option key={a.id} value={a.name} />)}
                </datalist>
              </div>

              {type === 'Buy' && !currentAssets.find(a => a.name === assetName) && (
                <div>
                   <label className="block text-sm text-slate-400 mb-1">资产类型</label>
                   <select
                      value={assetType}
                      onChange={(e) => setAssetType(e.target.value as AssetType)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"
                   >
                     <option value="Stock">股票 (Stock)</option>
                     <option value="Fund">基金 (Fund)</option>
                     <option value="Crypto">加密货币 (Crypto)</option>
                     <option value="Bond">债券 (Bond)</option>
                     <option value="Other">其他 (Other)</option>
                   </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">
                    {type === 'Update' ? '修正后单价/成本' : '单价 (Price)'}
                  </label>
                  <input 
                    type="number" 
                    value={price}
                    onChange={e => handlePriceChange(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">
                    {type === 'Update' ? '修正后数量' : '数量 (Quantity)'}
                  </label>
                  <input 
                    type="number" 
                    value={quantity}
                    onChange={e => handleQuantityChange(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="0"
                    step="0.0001"
                    min="0"
                    required
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-sm text-slate-400 mb-1">
               {type === 'Update' ? '修正后总价值' : '交易总金额 (Total Amount)'}
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">¥</span>
              <input 
                type="number" 
                value={amount}
                onChange={e => setAmount(e.target.value)}
                readOnly={type === 'Buy' || type === 'Sell' || type === 'Update'} // 买卖时由单价*数量计算，暂不支持反算
                className={`w-full bg-slate-900 border border-slate-700 rounded-lg p-2 pl-8 text-white focus:outline-none focus:border-blue-500 ${type !== 'Deposit' && type !== 'Withdraw' ? 'opacity-75 cursor-not-allowed' : ''}`}
                placeholder="0.00"
                step="0.01"
                min="0"
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            className={`
              w-full py-3 rounded-lg font-bold text-white shadow-lg transition-transform active:scale-95
              ${type === 'Buy' || type === 'Deposit' ? 'bg-emerald-600 hover:bg-emerald-500' 
                : type === 'Update' ? 'bg-blue-600 hover:bg-blue-500'
                : 'bg-red-600 hover:bg-red-500'}
            `}
          >
            确认{type === 'Buy' ? '买入' : type === 'Sell' ? '卖出' : type === 'Update' ? '修正' : type === 'Deposit' ? '充值' : '提现'}
          </button>

        </form>
      </div>
    </div>
  );
};

export default AssetOperationModal;
