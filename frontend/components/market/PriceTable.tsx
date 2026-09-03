"use client";

import { useState, useMemo } from "react";
import { cn, formatPrice } from "@/lib/utils";
import { TrendIndicator } from "./TrendIndicator";
import type { MandiComparisonEntry } from "@/types";

interface PriceTableProps {
  rows: MandiComparisonEntry[];
  showNetPrice?: boolean;
  highlightBest?: boolean;
  className?: string;
}

type SortKey = "modal_price" | "net_price" | "transport_cost_per_quintal" | "mandi";
type SortDir = "asc" | "desc";

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  return (
    <span className={cn("ml-1 text-xs", active ? "text-primary-600" : "text-gray-300")}>
      {active ? (dir === "asc" ? "▲" : "▼") : "⇅"}
    </span>
  );
}

export function PriceTable({ rows, showNetPrice = true, highlightBest = true, className }: PriceTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("net_price");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filter, setFilter] = useState("");

  const sorted = useMemo(() => {
    let data = [...rows];
    if (filter) {
      const f = filter.toLowerCase();
      data = data.filter(r =>
        r.mandi.toLowerCase().includes(f) || r.district.toLowerCase().includes(f)
      );
    }
    data.sort((a, b) => {
      let av: string | number = 0, bv: string | number = 0;
      if (sortKey === "mandi") { av = a.mandi; bv = b.mandi; }
      else { av = a[sortKey] ?? 0; bv = b[sortKey] ?? 0; }
      if (typeof av === "string") return sortDir === "asc" ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
      return sortDir === "asc" ? av - (bv as number) : (bv as number) - av;
    });
    return data;
  }, [rows, sortKey, sortDir, filter]);

  const bestNetPrice = rows.length > 0 ? Math.max(...rows.map(r => r.net_price)) : 0;

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("desc"); }
  }

  if (rows.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400">
        <p className="text-3xl mb-2">📊</p>
        <p>No market data available</p>
      </div>
    );
  }

  return (
    <div className={cn("", className)}>
      {/* Filter */}
      <div className="mb-3">
        <input
          type="text"
          placeholder="Filter by mandi or district..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
        />
      </div>

      {/* Desktop table */}
      <div className="hidden sm:block overflow-x-auto rounded-2xl border border-gray-100">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-3 font-semibold cursor-pointer" onClick={() => toggleSort("mandi")}>
                Mandi <SortIcon active={sortKey === "mandi"} dir={sortDir} />
              </th>
              <th className="text-left px-4 py-3 font-semibold text-gray-500">District</th>
              <th className="text-right px-4 py-3 font-semibold cursor-pointer" onClick={() => toggleSort("modal_price")}>
                Modal ₹/q <SortIcon active={sortKey === "modal_price"} dir={sortDir} />
              </th>
              <th className="text-right px-4 py-3 font-semibold text-gray-500">Min</th>
              <th className="text-right px-4 py-3 font-semibold text-gray-500">Max</th>
              <th className="text-center px-4 py-3 font-semibold">Trend</th>
              {showNetPrice && (
                <th className="text-right px-4 py-3 font-semibold cursor-pointer" onClick={() => toggleSort("net_price")}>
                  Net ₹/q <SortIcon active={sortKey === "net_price"} dir={sortDir} />
                </th>
              )}
              {showNetPrice && (
                <th className="text-right px-4 py-3 font-semibold cursor-pointer text-gray-500" onClick={() => toggleSort("transport_cost_per_quintal")}>
                  Transport <SortIcon active={sortKey === "transport_cost_per_quintal"} dir={sortDir} />
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-50">
            {sorted.map((row, i) => {
              const isBest = highlightBest && row.net_price === bestNetPrice;
              return (
                <tr key={row.mandi} className={cn("hover:bg-gray-50", isBest && "bg-green-50")}>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {row.mandi}
                    {isBest && (
                      <span className="ml-2 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Best</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{row.district}</td>
                  <td className="px-4 py-3 text-right font-semibold">{formatPrice(row.modal_price)}</td>
                  <td className="px-4 py-3 text-right text-gray-500 text-xs">{formatPrice(row.min_price)}</td>
                  <td className="px-4 py-3 text-right text-gray-500 text-xs">{formatPrice(row.max_price)}</td>
                  <td className="px-4 py-3 text-center">
                    <TrendIndicator trend={row.trend} changePct={row.change_percent ?? undefined} size="sm" />
                  </td>
                  {showNetPrice && (
                    <td className={cn("px-4 py-3 text-right font-bold", isBest ? "text-green-700" : "text-primary-700")}>
                      {formatPrice(row.net_price)}
                    </td>
                  )}
                  {showNetPrice && (
                    <td className="px-4 py-3 text-right text-gray-400 text-xs">
                      -{formatPrice(row.transport_cost_per_quintal)}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="sm:hidden space-y-3">
        {sorted.map(row => {
          const isBest = highlightBest && row.net_price === bestNetPrice;
          return (
            <div key={row.mandi} className={cn("rounded-2xl border p-4", isBest ? "border-green-300 bg-green-50" : "border-gray-100 bg-white")}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold text-gray-900 text-sm">
                    {row.mandi}
                    {isBest && <span className="ml-1.5 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Best</span>}
                  </p>
                  <p className="text-xs text-gray-500">{row.district}</p>
                </div>
                <TrendIndicator trend={row.trend} changePct={row.change_percent ?? undefined} size="sm" />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="text-gray-400">Modal</p>
                  <p className="font-bold text-gray-900">{formatPrice(row.modal_price)}</p>
                </div>
                {showNetPrice && (
                  <div>
                    <p className="text-gray-400">Net (after transport)</p>
                    <p className={cn("font-bold", isBest ? "text-green-700" : "text-primary-700")}>
                      {formatPrice(row.net_price)}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-gray-400">Min / Max</p>
                  <p className="text-gray-600">{formatPrice(row.min_price)} / {formatPrice(row.max_price)}</p>
                </div>
                {showNetPrice && (
                  <div>
                    <p className="text-gray-400">Transport est.</p>
                    <p className="text-gray-600">{formatPrice(row.transport_cost_per_quintal)}/q</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {filter && sorted.length === 0 && (
        <p className="text-center text-gray-400 py-6 text-sm">No mandis match "{filter}"</p>
      )}
    </div>
  );
}
