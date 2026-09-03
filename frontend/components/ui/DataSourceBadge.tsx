"use client";

/**
 * Phase 9 — DataSourceBadge
 * Shows DEMO DATA / LIVE / LATEST AVAILABLE + timestamp with correct styling.
 * Used across market, forecast, buyer, and income pages.
 */

interface DataSourceBadgeProps {
  status: "DEMO" | "LIVE" | "LATEST_AVAILABLE" | string;
  timestamp?: string | null;
  className?: string;
}

const STATUS_CONFIG = {
  LIVE:             { dot: "bg-green-500", bg: "bg-green-50",  text: "text-green-700",  border: "border-green-200", label: "● LIVE" },
  LATEST_AVAILABLE: { dot: "bg-blue-500",  bg: "bg-blue-50",   text: "text-blue-700",   border: "border-blue-200",  label: "◑ LATEST AVAILABLE" },
  DEMO:             { dot: "bg-amber-500", bg: "bg-amber-50",  text: "text-amber-700",  border: "border-amber-200", label: "○ DEMO DATA" },
} as const;

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

export function DataSourceBadge({ status, timestamp, className = "" }: DataSourceBadgeProps) {
  const cfg = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.DEMO;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.text} ${cfg.border} ${className}`}>
      {cfg.label}
      {timestamp && (
        <span className="opacity-70">· {formatTimestamp(timestamp)}</span>
      )}
    </span>
  );
}
