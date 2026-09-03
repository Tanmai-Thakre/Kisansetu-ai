"use client";

import { cn } from "@/lib/utils";

interface TrendIndicatorProps {
  trend: string;
  changePct?: number;
  change?: number;
  size?: "sm" | "md" | "lg";
  showChange?: boolean;
}

export function TrendIndicator({ trend, changePct, change, size = "md", showChange = true }: TrendIndicatorProps) {
  const isUp = trend === "UP" || trend === "up";
  const isDown = trend === "DOWN" || trend === "down";
  const isStable = !isUp && !isDown;

  const colors = isUp
    ? "text-green-600"
    : isDown
    ? "text-red-600"
    : "text-gray-500";

  const arrow = isUp ? "↑" : isDown ? "↓" : "→";

  const sizes = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base font-semibold",
  };

  return (
    <span className={cn("inline-flex items-center gap-0.5", colors, sizes[size])}>
      <span>{arrow}</span>
      {showChange && changePct !== undefined && (
        <span>{Math.abs(changePct).toFixed(1)}%</span>
      )}
      {showChange && change !== undefined && changePct === undefined && (
        <span>{change > 0 ? "+" : ""}{change.toFixed(0)}</span>
      )}
    </span>
  );
}

interface TrendCardProps {
  currentPrice: number;
  previousPrice?: number;
  change?: number;
  changePct?: number;
  trend: string;
  label?: string;
}

export function TrendCard({ currentPrice, previousPrice, change, changePct, trend, label }: TrendCardProps) {
  const isUp = trend === "UP" || trend === "up";
  const isDown = trend === "DOWN" || trend === "down";
  const bgColor = isUp ? "bg-green-50 border-green-100" : isDown ? "bg-red-50 border-red-100" : "bg-gray-50 border-gray-100";

  return (
    <div className={cn("rounded-2xl border p-4", bgColor)}>
      {label && <p className="text-xs text-gray-500 mb-1">{label}</p>}
      <p className="text-2xl font-bold text-gray-900">₹{currentPrice.toLocaleString("en-IN")}/q</p>
      <div className="flex items-center gap-3 mt-2 flex-wrap">
        {change !== undefined && (
          <div className="text-sm">
            <span className="text-gray-500">Change: </span>
            <TrendIndicator trend={trend} change={change} changePct={undefined} showChange={true} />
          </div>
        )}
        {changePct !== undefined && (
          <div className="text-sm">
            <TrendIndicator trend={trend} changePct={changePct} size="md" />
          </div>
        )}
        {previousPrice && (
          <div className="text-xs text-gray-400">
            vs ₹{previousPrice.toLocaleString("en-IN")} (7d ago)
          </div>
        )}
      </div>
    </div>
  );
}
