"use client";

// Phase 5 — ComparisonTable: sell-now vs store-7/15/30 side-by-side

import type { HorizonResult } from "@/types";

interface Props {
  sellNowValue: number;
  horizons:     HorizonResult[];
  quantity:     number;
  currency?:    string;
}

function fmt(n: number) {
  return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function GainCell({ gain }: { gain: number }) {
  if (gain > 0) return <span className="text-green-600 font-semibold">{fmt(gain)} ↑</span>;
  if (gain < 0) return <span className="text-red-500 font-semibold">{fmt(gain)} ↓</span>;
  return <span className="text-gray-400">—</span>;
}

export function ComparisonTable({ sellNowValue, horizons, quantity }: Props) {
  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-xs min-w-[420px]">
        <thead>
          <tr className="text-gray-400 border-b border-gray-100">
            <th className="text-left py-2 px-2 font-semibold">Option</th>
            <th className="text-right py-2 px-2 font-semibold">Gross Value</th>
            <th className="text-right py-2 px-2 font-semibold">Storage Cost</th>
            <th className="text-right py-2 px-2 font-semibold">Net Value</th>
            <th className="text-right py-2 px-2 font-semibold">vs Sell Now</th>
          </tr>
        </thead>
        <tbody>
          {/* Sell Now row */}
          <tr className="border-b border-gray-50 bg-green-50">
            <td className="py-2.5 px-2 font-semibold text-gray-800">💰 Sell Now</td>
            <td className="text-right py-2.5 px-2 font-bold text-gray-900">{fmt(sellNowValue)}</td>
            <td className="text-right py-2.5 px-2 text-gray-400">—</td>
            <td className="text-right py-2.5 px-2 font-bold text-green-700">{fmt(sellNowValue)}</td>
            <td className="text-right py-2.5 px-2 text-gray-400">—</td>
          </tr>
          {/* Horizon rows */}
          {horizons.map(h => (
            <tr key={h.horizon_days} className="border-b border-gray-50">
              <td className="py-2.5 px-2 font-medium text-gray-700">
                📦 Store {h.horizon_days}d
              </td>
              <td className="text-right py-2.5 px-2 text-gray-700">{fmt(h.gross_future)}</td>
              <td className="text-right py-2.5 px-2 text-amber-600">−{fmt(h.storage_cost)}</td>
              <td className="text-right py-2.5 px-2 font-semibold text-gray-800">{fmt(h.net_future)}</td>
              <td className="text-right py-2.5 px-2">
                <GainCell gain={h.potential_gain} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-gray-400 mt-2">
        ⚠️ DEMO estimates — storage costs proportional, transport costs included.
      </p>
    </div>
  );
}
