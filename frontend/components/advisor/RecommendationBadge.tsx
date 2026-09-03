"use client";

// Phase 5 — RecommendationBadge: prominent visual for SELL_NOW / STORE / PARTIAL_SELL

import type { AdvisorRecommendation } from "@/types";

interface Props {
  recommendation: AdvisorRecommendation;
  sellPct:        number;
  storePct:       number;
  horizonDays:    number;
  risk:           "LOW" | "MEDIUM" | "HIGH";
  confidence:     number;
}

const CONFIG = {
  SELL_NOW: {
    bg:     "bg-green-500",
    light:  "bg-green-50 border-green-200",
    text:   "text-green-700",
    label:  "SELL NOW",
    icon:   "💰",
    sub:    "Get the best current price today",
  },
  STORE: {
    bg:     "bg-indigo-500",
    light:  "bg-indigo-50 border-indigo-200",
    text:   "text-indigo-700",
    label:  "STORE",
    icon:   "📦",
    sub:    "Wait for a better price",
  },
  PARTIAL_SELL: {
    bg:     "bg-amber-500",
    light:  "bg-amber-50 border-amber-200",
    text:   "text-amber-700",
    label:  "PARTIAL SELL",
    icon:   "⚖️",
    sub:    "Balance immediate income with future upside",
  },
};

const RISK_STYLE: Record<string, string> = {
  LOW:    "bg-green-100 text-green-700",
  MEDIUM: "bg-amber-100 text-amber-700",
  HIGH:   "bg-red-100   text-red-700",
};

export function RecommendationBadge({ recommendation, sellPct, storePct, horizonDays, risk, confidence }: Props) {
  const cfg = CONFIG[recommendation];
  return (
    <div className={`rounded-2xl border p-5 ${cfg.light}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-12 h-12 ${cfg.bg} rounded-2xl flex items-center justify-center text-2xl text-white shadow-sm`}>
          {cfg.icon}
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Recommendation</p>
          <p className={`text-2xl font-black ${cfg.text}`}>{cfg.label}</p>
        </div>
      </div>
      <p className={`text-sm font-medium ${cfg.text} mb-4`}>{cfg.sub}</p>

      {/* Split pills */}
      {recommendation === "PARTIAL_SELL" && (
        <div className="flex gap-2 mb-4">
          <div className="flex-1 bg-green-500 rounded-xl py-2.5 text-center text-white font-bold text-sm">
            Sell {sellPct}%
          </div>
          <div className="flex-1 bg-indigo-500 rounded-xl py-2.5 text-center text-white font-bold text-sm">
            Store {storePct}%
          </div>
        </div>
      )}

      {recommendation === "STORE" && (
        <div className="bg-indigo-100 rounded-xl py-2.5 text-center text-indigo-700 font-bold text-sm mb-4">
          Store for {horizonDays} days
        </div>
      )}

      {/* Meta row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${RISK_STYLE[risk]}`}>
          {risk === "LOW" ? "🟢" : risk === "HIGH" ? "🔴" : "🟡"} {risk} Risk
        </span>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">
          {confidence.toFixed(0)}% Confidence
        </span>
        {horizonDays > 0 && recommendation !== "SELL_NOW" && (
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-100 text-blue-600">
            📅 {horizonDays}d horizon
          </span>
        )}
      </div>
    </div>
  );
}
