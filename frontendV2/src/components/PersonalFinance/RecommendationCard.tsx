import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

export type RecommendationAction = 'buy' | 'sell' | 'hold' | 'monitor';

export interface RecommendationCardProps {
  title: string;
  description: string;
  asset_id?: string;
  action: RecommendationAction;
  confidence_score: number;
  risk_level: 'low' | 'medium' | 'high';
  suggested_symbol?: string | null;
  suggested_price?: number | null;
  suggested_quantity?: number | null;
  reasoning?: string | null;
}

const actionColors = {
  buy: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  sell: 'bg-red-500/10 text-red-400 border-red-500/20',
  hold: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  monitor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
};

const riskColors = {
  low: 'text-emerald-400',
  medium: 'text-amber-400',
  high: 'text-red-400',
};

const RecommendationCard: React.FC<RecommendationCardProps> = ({
  title,
  description,
  asset_id,
  action,
  confidence_score,
  risk_level,
  suggested_symbol,
  suggested_price,
  suggested_quantity,
  reasoning
}) => {
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 shadow-lg hover:border-slate-600 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2">
          {action === 'buy' && <TrendingUp size={18} className="text-emerald-400" />}
          {action === 'sell' && <TrendingDown size={18} className="text-red-400" />}
          {action === 'hold' && <ShieldCheck size={18} className="text-blue-400" />}
          {action === 'monitor' && <Activity size={18} className="text-amber-400" />}
          <h4 className="font-bold text-white">{title}</h4>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-bold uppercase border ${actionColors[action]}`}>
          {action}
        </span>
      </div>
      
      <p className="text-slate-300 text-sm mb-4 leading-relaxed">
        {description}
      </p>

      {/* Execution Strategy Block */}
      {(suggested_symbol || suggested_quantity) && (
        <div className="mb-4 p-3 bg-slate-900/50 rounded-lg text-xs border border-slate-700/50">
           <div className="text-slate-500 mb-2 font-medium">执行策略 (AI Execution Strategy)</div>
           <div className="grid grid-cols-2 gap-2">
               <div>
                  <span className="text-slate-400 block mb-0.5">标的 (Symbol)</span>
                  <span className="text-white font-mono font-medium">{suggested_symbol || asset_id || '-'}</span>
               </div>
               <div>
                  <span className="text-slate-400 block mb-0.5">数量 (Qty)</span>
                  <span className="text-white font-mono font-medium">{suggested_quantity || '-'}</span>
               </div>
               {suggested_price && (
                   <div className="col-span-2">
                      <span className="text-slate-400 block mb-0.5">建议价格 (Price)</span>
                      <span className="text-white font-mono font-medium">¥{suggested_price}</span>
                   </div>
               )}
           </div>
           {reasoning && (
             <div className="mt-2 pt-2 border-t border-slate-700/30">
                <span className="text-slate-400 block mb-0.5">策略理由</span>
                <span className="text-slate-300 italic">{reasoning}</span>
             </div>
           )}
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-700/50">
        <div className="flex items-center gap-1.5 text-slate-400">
          <span>置信度:</span>
          <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${confidence_score * 100}%` }}
            />
          </div>
          <span>{(confidence_score * 100).toFixed(0)}%</span>
        </div>
        
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">风险等级:</span>
          <span className={`font-medium flex items-center gap-1 ${riskColors[risk_level]}`}>
            {risk_level === 'high' && <AlertTriangle size={12} />}
            {risk_level === 'medium' ? '中 (Medium)' : risk_level === 'high' ? '高 (High)' : '低 (Low)'}
          </span>
        </div>
      </div>
      
      {asset_id && (
        <div className="mt-2 text-xs text-slate-500 font-mono">
          Asset: {asset_id}
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;
