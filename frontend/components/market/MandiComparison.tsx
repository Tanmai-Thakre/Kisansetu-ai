"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { formatPrice } from "@/lib/utils";
import { TrendIndicator } from "./TrendIndicator";
import type { BestMandiResponse, MandiComparisonEntry } from "@/types";

interface BestMandiCardProps {
  data?: BestMandiResponse;
  loading?: boolean;
}

export function BestMandiCard({ data, loading }: BestMandiCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <div className="animate-pulse space-y-2 py-4">
            <div className="h-4 bg-gray-100 rounded w-2/3" />
            <div className="h-8 bg-gray-100 rounded w-1/2" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data?.best_mandi) {
    return (
      <Card>
        <CardContent>
          <p className="text-gray-400 text-sm py-4 text-center">Best mandi data unavailable</p>
        </CardContent>
      </Card>
    );
  }

  const best = data.best_mandi;

  return (
    <Card className="border-l-4 border-l-primary-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>🏆 Best Mandi — Net Price</CardTitle>
          <span className="text-xs bg-amber-50 text-amber-600 px-2 py-1 rounded-full">DEMO DATA</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="bg-primary-50 rounded-2xl p-4 border border-primary-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-bold text-primary-900 text-lg">{best.mandi}</p>
              <p className="text-sm text-primary-600">📍 {best.district}</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-primary-700">{formatPrice(best.net_price)}</p>
              <p className="text-xs text-primary-500">net / quintal</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-primary-700">
            <div>
              <p className="text-primary-400">Modal Price</p>
              <p className="font-semibold">{formatPrice(best.modal_price)}</p>
            </div>
            <div>
              <p className="text-primary-400">Est. Transport</p>
              <p className="font-semibold">−{formatPrice(best.transport_cost_per_quintal)}/q</p>
            </div>
            <div>
              <p className="text-primary-400">Distance (est.)</p>
              <p className="font-semibold">~{best.estimated_distance_km} km</p>
            </div>
            <div>
              <p className="text-primary-400">Trend</p>
              <TrendIndicator trend={best.trend} changePct={best.change_percent ?? undefined} size="sm" />
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div className="mt-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
          <p className="text-xs text-gray-500 font-medium mb-1">Why this mandi?</p>
          <p className="text-sm text-gray-700">{data.explanation}</p>
        </div>

        <p className="text-xs text-gray-400 mt-2 text-center">{best.transport_note}</p>
      </CardContent>
    </Card>
  );
}

interface MandiComparisonCardProps {
  entries: MandiComparisonEntry[];
  crop: string;
}

export function MandiComparisonCard({ entries, crop }: MandiComparisonCardProps) {
  if (entries.length === 0) return null;
  const bestNet = Math.max(...entries.map(e => e.net_price));

  return (
    <div className="space-y-3">
      {entries.slice(0, 6).map(entry => {
        const isBest = entry.net_price === bestNet;
        return (
          <div
            key={entry.mandi}
            className={`rounded-2xl border p-4 ${isBest ? "border-primary-300 bg-primary-50" : "border-gray-100 bg-white"}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-gray-900 text-sm">{entry.mandi}</p>
                  {isBest && (
                    <span className="text-xs bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded-full font-semibold">
                      Best Net
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500">📍 {entry.district}</p>
              </div>
              <TrendIndicator trend={entry.trend} changePct={entry.change_percent ?? undefined} size="sm" />
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
              <div>
                <p className="text-gray-400">Modal</p>
                <p className="font-semibold text-gray-900">{formatPrice(entry.modal_price)}</p>
              </div>
              <div>
                <p className="text-gray-400">Transport</p>
                <p className="font-semibold text-red-500">−{formatPrice(entry.transport_cost_per_quintal)}</p>
              </div>
              <div>
                <p className="text-gray-400">Net</p>
                <p className={`font-bold ${isBest ? "text-primary-700" : "text-gray-900"}`}>
                  {formatPrice(entry.net_price)}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
