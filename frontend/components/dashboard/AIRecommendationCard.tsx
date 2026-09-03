"use client";

// Phase 5 — AIRecommendationCard: upgraded from Phase 3 forecast summary
// to a compact StorageAdvisor card.
//
// Shows: recommendation badge, current vs forecast price, sell/store split,
// gain/loss, risk pill, confidence bar, quick reason snippet, and a CTA
// button to the full /farmer/advisor page.
//
// Falls back gracefully to the Phase 3 forecast card if the advisor API is
// unavailable.

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { storageAdvisorPreview } from "@/lib/api";
import type { AIRecommendation, AdvisorResponse } from "@/types";

// ── Sub-components ────────────────────────────────────────────────────────────

function RiskPill({ risk }: { risk: string }) {
  const map: Record<string, string> = {
    LOW:    "bg-green-100 text-green-700",
    MEDIUM: "bg-amber-100 text-amber-700",
    HIGH:   "bg-red-100   text-red-700",
  };
  const icon = risk === "LOW" ? "🟢" : risk === "HIGH" ? "🔴" : "🟡";
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${map[risk] ?? map.MEDIUM}`}>
      {icon} {risk} Risk
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const color =
    value >= 70 ? "bg-green-400" : value >= 50 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8 text-right">{value.toFixed(0)}%</span>
    </div>
  );
}

// ── Recommendation badge (compact) ────────────────────────────────────────────

type Rec = "SELL_NOW" | "STORE" | "PARTIAL_SELL";

function RecBadge({ rec, sellPct, storePct }: { rec: Rec; sellPct: number; storePct: number }) {
  if (rec === "SELL_NOW") {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-3 flex items-center gap-3">
        <span className="text-2xl">💰</span>
        <div>
          <p className="text-sm font-bold text-green-700">Sell Now</p>
          <p className="text-xs text-green-600">Best price available today</p>
        </div>
      </div>
    );
  }
  if (rec === "STORE") {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 flex items-center gap-3">
        <span className="text-2xl">🏭</span>
        <div>
          <p className="text-sm font-bold text-blue-700">Store &amp; Wait</p>
          <p className="text-xs text-blue-600">Prices forecast to rise</p>
        </div>
      </div>
    );
  }
  // PARTIAL_SELL
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center gap-3">
      <span className="text-2xl">⚖️</span>
      <div>
        <p className="text-sm font-bold text-amber-700">Partial Sell</p>
        <p className="text-xs text-amber-600">
          Sell {sellPct}% now · Store {storePct}%
        </p>
      </div>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n: number) {
  return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function AdvisorSkeleton() {
  return (
    <Card className="border-l-4 border-l-indigo-400">
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="text-xl">🤖</span>
          <CardTitle className="text-indigo-700">AI Selling Advisor</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="animate-pulse space-y-2">
          <div className="h-12 bg-gray-100 rounded-xl" />
          <div className="h-3 bg-gray-100 rounded w-3/4" />
          <div className="h-3 bg-gray-100 rounded w-1/2" />
          <div className="h-8 bg-gray-100 rounded-xl mt-3" />
        </div>
      </CardContent>
    </Card>
  );
}

// ── Fallback card (Phase 3 style — no advisor data) ───────────────────────────

function FallbackCard({ recommendation }: { recommendation: AIRecommendation }) {
  return (
    <Card className="border-l-4 border-l-indigo-400">
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="text-xl">🤖</span>
          <CardTitle className="text-indigo-700">{recommendation.title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-500 text-sm">{recommendation.message}</p>
        <div className="mt-3 bg-indigo-50 rounded-xl p-3 border border-indigo-100">
          <p className="text-xs text-indigo-600 font-semibold mb-1">Phase 5 Advisor Active:</p>
          <ul className="text-xs text-indigo-500 space-y-1">
            <li>💡 SELL_NOW / STORE / PARTIAL_SELL decision</li>
            <li>📊 7/15/30-day price forecasts</li>
            <li>🤝 Best buyer vs mandi comparison</li>
            <li>💰 Net gain &amp; storage cost analysis</li>
          </ul>
        </div>
        <Link href="/farmer/advisor">
          <button className="mt-3 w-full text-xs text-indigo-600 font-semibold bg-indigo-50 rounded-xl py-2 hover:bg-indigo-100 transition-colors">
            Open Sell or Store Advisor →
          </button>
        </Link>
      </CardContent>
    </Card>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface AIRecommendationCardProps {
  recommendation: AIRecommendation;
  t: (key: string) => string;
}

export function AIRecommendationCard({
  recommendation,
  t,
}: AIRecommendationCardProps) {
  const [advisor, setAdvisor] = useState<AdvisorResponse | null>(null);
  const [loading, setLoading]  = useState(true);

  useEffect(() => {
    storageAdvisorPreview("cotton", "Rajkot APMC")
      .then((data) => setAdvisor(data as AdvisorResponse))
      .catch(() => setAdvisor(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <AdvisorSkeleton />;
  if (!advisor) return <FallbackCard recommendation={recommendation} />;

  // ── Derived values ─────────────────────────────────────────────────────────
  const gainColor =
    advisor.potential_net_gain > 0 ? "text-green-600" : "text-red-500";
  const trendColor =
    advisor.forecast_price > advisor.current_best_price
      ? "text-green-600"
      : advisor.forecast_price < advisor.current_best_price
      ? "text-red-500"
      : "text-gray-500";
  const trendArrow =
    advisor.forecast_price > advisor.current_best_price ? "↑"
    : advisor.forecast_price < advisor.current_best_price ? "↓"
    : "→";

  // First reason snippet (keep short)
  const reasonSnippet =
    advisor.reasons.length > 0 ? advisor.reasons[0] : advisor.explanation;

  return (
    <Card className="border-l-4 border-l-indigo-400">
      {/* Header */}
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">🤖</span>
            <CardTitle className="text-indigo-700">AI Selling Advisor</CardTitle>
          </div>
          <RiskPill risk={advisor.risk} />
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Recommendation badge */}
        <RecBadge
          rec={advisor.recommendation as Rec}
          sellPct={advisor.sell_percentage}
          storePct={advisor.store_percentage}
        />

        {/* Price pair: now → forecast */}
        <div className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-3">
          <div className="text-center">
            <p className="text-xs text-gray-400">Today (Cotton)</p>
            <p className="text-lg font-bold text-gray-900">
              {fmt(advisor.current_best_price)}
            </p>
            <p className="text-xs text-gray-400">/q</p>
          </div>
          <div className={`text-2xl font-bold ${trendColor}`}>{trendArrow}</div>
          <div className="text-center">
            <p className="text-xs text-gray-400">
              {advisor.recommended_horizon_days}d Forecast
            </p>
            <p className={`text-lg font-bold ${trendColor}`}>
              {fmt(advisor.forecast_price)}
            </p>
            <p className={`text-xs font-semibold ${gainColor}`}>
              {advisor.gain_percent >= 0 ? "+" : ""}
              {advisor.gain_percent.toFixed(1)}% net
            </p>
          </div>
        </div>

        {/* Confidence bar */}
        <div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>Forecast Confidence</span>
            <span className="capitalize">{advisor.crop}</span>
          </div>
          <ConfidenceBar value={advisor.confidence} />
        </div>

        {/* Key reason */}
        <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
          <p className="text-xs font-semibold text-indigo-700 line-clamp-2">
            💡 {reasonSnippet}
          </p>
        </div>

        {/* Potential gain pill */}
        <div
          className={`rounded-xl p-2.5 text-center border ${
            advisor.potential_net_gain > 0
              ? "bg-green-50 border-green-200"
              : "bg-red-50 border-red-200"
          }`}
        >
          <p className="text-xs text-gray-500">
            Potential net gain if storing{" "}
            {advisor.recommended_horizon_days}d
          </p>
          <p
            className={`text-base font-black ${
              advisor.potential_net_gain > 0 ? "text-green-700" : "text-red-600"
            }`}
          >
            {advisor.potential_net_gain >= 0 ? "+" : ""}
            {fmt(advisor.potential_net_gain)}
          </p>
        </div>

        {/* CTA */}
        <Link href="/farmer/advisor">
          <button className="w-full text-xs text-indigo-600 font-semibold bg-indigo-50 rounded-xl py-2.5 hover:bg-indigo-100 transition-colors border border-indigo-100">
            Full Sell / Store Analysis →
          </button>
        </Link>

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 text-center leading-relaxed">
          AI-assisted estimate. Not a guaranteed future price.
        </p>
      </CardContent>
    </Card>
  );
}
