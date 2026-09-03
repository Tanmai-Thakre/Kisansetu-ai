"use client";

import { cn } from "@/lib/utils";
import type { SourceStatus } from "@/types";

interface DataFreshnessBadgeProps {
  source: string;
  sourceStatus: SourceStatus;
  isLive?: boolean;
  tooltip?: string;
  className?: string;
}

export function DataFreshnessBadge({
  source,
  sourceStatus,
  isLive = false,
  tooltip,
  className,
}: DataFreshnessBadgeProps) {
  const dotColor = isLive ? "bg-green-500" : sourceStatus === "DEMO" ? "bg-amber-400" : "bg-blue-400";
  const badgeColor = isLive
    ? "bg-green-50 text-green-700 border-green-200"
    : sourceStatus === "DEMO"
    ? "bg-amber-50 text-amber-700 border-amber-200"
    : "bg-blue-50 text-blue-700 border-blue-200";
  const label = isLive ? "LIVE" : sourceStatus === "DEMO" ? "DEMO DATA" : "LATEST AVAILABLE";

  return (
    <div className={cn("relative group inline-flex", className)}>
      <div className={cn("inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border", badgeColor)}>
        <span className={cn("w-1.5 h-1.5 rounded-full", dotColor)} />
        {label}
        {!isLive && (
          <span className="ml-0.5 cursor-help opacity-60">ⓘ</span>
        )}
      </div>
      {/* Tooltip */}
      {tooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 hidden group-hover:block z-50">
          <div className="bg-gray-800 text-white text-xs rounded-xl p-3 leading-relaxed shadow-lg">
            <p className="font-semibold mb-1">Data Source: {source}</p>
            <p>{tooltip}</p>
          </div>
          <div className="w-2 h-2 bg-gray-800 rotate-45 mx-auto -mt-1" />
        </div>
      )}
    </div>
  );
}
