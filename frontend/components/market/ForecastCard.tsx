"use client";

// Phase 3 — ForecastCard: displays 7/15/30-day price forecasts with
// trend, confidence, risk level, and AI explanation.

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { ForecastResponse } from "@/types";

interface ForecastCardProps {
  data: ForecastResponse;
  loading?: boolean;
}

function RiskBadge({ risk }: { risk: string }) {
  const styles: Record<string, string> = {
    LOW:    "bg-green-100 text-green-700 border-green-200",
    MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
    HIGH:   "bg-red-100 text-red-700 border-red-200",
  };
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${styles[risk] ?? styles.MEDIUM}`}>
      {risk === "LOW" ? "🟢 Low Risk" : risk === "HIGH" ? "🔴 High Risk" : "🟡 Med Risk"}
    </span>
  );
}

function TrendBadge({ trend }: { trend: string }) {
  if (trend === "UP")     return <span className="text-green-600 font-bold">↑ Rising</span>;
  if (trend === "DOWN")   return <span className="text-red-600 font-bold">↓ Falling</span>;
  return <span className="text-gray-500 font-bold">→ Stable</span>;
}

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 70 ? "bg-green-400" : value >= 50 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-600 w-10 text-right">{value.toFixed(0)}%</span>
    </div>
  );
}

function ForecastPill({ label, price, current }: { label: string; price: number; current: number }) {
  const diff = price - current;
  const pct  = current > 0 ? (diff / current) * 100 : 0;
  const up   = diff >= 0;
  return (
    <div className="flex flex-col items-center bg-gray-50 rounded-xl p-3 border border-gray-100">
      <span className="text-xs text-gray-400 font-medium mb-1">{label}</span>
      <span className="text-lg font-bold text-gray-900">₹{price.toLocaleString("en-IN")}</span>
      <span className={`text-xs font-semibold mt-0.5 ${up ? "text-green-600" : "text-red-600"}`}>
        {up ? "+" : ""}{pct.toFixed(1)}%
      </span>
    </div>
  );
}

export function ForecastCard({ data, loading }: ForecastCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <div className="animate-pulse space-y-3 py-2">
            <div className="h-4 bg-gray-100 rounded w-1/3" />
            <div className="h-10 bg-gray-100 rounded" />
            <div className="h-10 bg-gray-100 rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-l-4 border-l-indigo-400">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔮</span>
            <CardTitle className="text-indigo-700">AI Price Forecast</CardTitle>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <TrendBadge trend={data.trend} />
            <RiskBadge risk={data.risk} />
            <Badge variant="gray" className="text-xs">{data.model_name}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Confidence */}
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Forecast Confidence</span>
            <span>Current: ₹{data.current_price.toLocaleString("en-IN")}/qtl</span>
          </div>
          <ConfidenceBar value={data.confidence} />
        </div>

        {/* Forecast pills */}
        <div className="grid grid-cols-3 gap-2">
          <ForecastPill label="7 Days"  price={data.forecast_7d}  current={data.current_price} />
          <ForecastPill label="15 Days" price={data.forecast_15d} current={data.current_price} />
          <ForecastPill label="30 Days" price={data.forecast_30d} current={data.current_price} />
        </div>

        {/* AI explanation */}
        <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
          <p className="text-xs font-semibold text-indigo-700 mb-1">📊 Analysis</p>
          <p className="text-xs text-indigo-600">{data.explanation}</p>
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 text-center leading-relaxed">{data.disclaimer}</p>
      </CardContent>
    </Card>
  );
}
