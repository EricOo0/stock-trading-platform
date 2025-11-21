import React from 'react';

interface FedWatchTableProps {
    currentRate: number; // Effective Fed Funds Rate (e.g., 4.58)
    impliedRate: number; // Implied Rate from Futures (e.g., 3.61)
}

export const FedWatchTable: React.FC<FedWatchTableProps> = ({ currentRate, impliedRate }) => {
    // CME Methodology:
    // 1. Assume Effective Fed Funds Rate (EFFR) trades at Lower Bound + 0.08%
    // 2. Find the two Target Ranges whose "Effective Rates" bracket the Implied Rate.

    const EFFR_SPREAD = 0.08;

    // Find the lower bound of the bracket
    // Formula: floor((Implied - Spread) / 0.25) * 0.25
    const bracketLower = Math.floor((impliedRate - EFFR_SPREAD) / 0.25) * 0.25;

    // Define the two effective rates for interpolation
    const effRate1 = bracketLower + EFFR_SPREAD;
    const effRate2 = effRate1 + 0.25;

    // Calculate probabilities
    // Prob(Range 1) = (Rate2 - Implied) / 0.25
    let prob1 = (effRate2 - impliedRate) / 0.25;
    let prob2 = 1 - prob1;

    // Clamp probabilities (in case of rounding errors or extreme values)
    prob1 = Math.max(0, Math.min(1, prob1));
    prob2 = Math.max(0, Math.min(1, prob2));

    const rows = [
        {
            rangeLower: bracketLower,
            rangeUpper: bracketLower + 0.25,
            prob: prob1 * 100
        },
        {
            rangeLower: bracketLower + 0.25,
            rangeUpper: bracketLower + 0.50,
            prob: prob2 * 100
        }
    ];

    // Determine Current Target Range for comparison
    const currentTargetLower = Math.floor((currentRate - 0.01) / 0.25) * 0.25; // Use -0.01 to handle exact boundary cases safely
    const currentTargetUpper = currentTargetLower + 0.25;

    return (
        <div className="mt-4 bg-slate-900/50 rounded-lg border border-slate-700/50 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
                <h3 className="text-sm font-semibold text-slate-300">Fed Rate Probabilities (Estimated)</h3>
            </div>
            <table className="w-full text-sm">
                <thead>
                    <tr className="bg-slate-800/30 text-slate-400">
                        <th className="px-4 py-2 text-left font-medium">Target Rate (bps)</th>
                        <th className="px-4 py-2 text-right font-medium">Probability</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                    {rows.map((row, index) => {
                        const isCurrent = Math.abs(row.rangeLower - currentTargetLower) < 0.01;
                        const label = `${(row.rangeLower * 100).toFixed(0)}-${(row.rangeUpper * 100).toFixed(0)}`;
                        const status = isCurrent ? '(Current)' : '';

                        return (
                            <tr key={index} className={isCurrent ? 'bg-blue-500/10' : ''}>
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <span className="font-mono text-slate-200">{label}</span>
                                        {status && <span className="text-xs text-blue-400">{status}</span>}
                                    </div>
                                </td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center justify-end gap-3">
                                        <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-500 rounded-full"
                                                style={{ width: `${row.prob}%` }}
                                            />
                                        </div>
                                        <span className="font-mono font-medium w-12 text-right">{row.prob.toFixed(1)}%</span>
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <div className="px-4 py-2 bg-slate-800/30 border-t border-slate-700/30">
                <p className="text-xs text-slate-500">
                    * Calculated using linear interpolation between effective rate assumptions (Lower Bound + 8bps).
                    Implied Rate: {impliedRate.toFixed(3)}%.
                </p>
            </div>
        </div>
    );
};
