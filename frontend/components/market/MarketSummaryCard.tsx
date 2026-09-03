"use client";

import { Card, CardContent } from "@/components/ui/Card";
import { TrendIndicator } from "./TrendIndicator";
import { cn, formatPrice } from "@/lib/utils";

interface MarketSummaryCardProps {
  crop: string;
  displayName: string;
  emoji: string;
  modalPrice: number;
  minPrice?: number;
  maxPrice?: number;
  trend?: string;
  changePct?: number;
  mandi?: string;
  source?: string;
  isHighlighted?: boolean;
}

export function MarketSummaryCard({
  crop,
  displayName,
  emoji,
  modalPrice,
  minPrice,
  maxPrice,
  trend = "STABLE",
  changePct,
  mandi,
  source,
  isHighlighted = false,
}: MarketSummaryCardProps) {
  const isUp = trend === "UP" || trend === "up";
  const isDown = trend === "DOWN" || trend === "down";
  const bg = isHighlighted
    ? isUp ? "bg-green-50 border-green-200" : isDown ? "bg-red-50 border-red-100" : "bg-amber-50 border-amber-100"
    : "bg-white border-gray-100";

  return (
    <div className={cn("rounded-2xl border p-5 flex flex-col gap-2", bg)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{emoji}</span>
          <span className="text-sm font-semibold text-gray-700">{displayName}</span>
        </div>
        {trend && (
          <TrendIndicator trend={trend} changePct={changePct} size="sm" />
        )}
      </div>
      <p className={cn(
        "text-3xl font-bold",
        isUp ? "text-green-700" : isDown ? "text-red-700" : "text-primary-700"
      )}>
        {formatPrice(modalPrice)}
      </p>
      <p className="text-xs text-gray-400">per quintal • modal</p>
      {(minPrice || maxPrice) && (
        <div className="flex gap-3 text-xs text-gray-500">
          {minPrice && <span>Min: {formatPrice(minPrice)}</span>}
          {maxPrice && <span>Max: {formatPrice(maxPrice)}</span>}
        </div>
      )}
      {mandi && <p className="text-xs text-gray-400 truncate">📍 {mandi}</p>}
      {source && <p className="text-xs text-amber-600 font-medium">{source}</p>}
    </div>
  );
}
