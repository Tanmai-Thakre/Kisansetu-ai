"use client";

// Phase 3 — ForecastChart: renders combined historical + forecast line chart
// using Recharts with a vertical "today" reference line.

import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import type { ForecastChartResponse } from "@/types";

interface ForecastChartProps {
  data: ForecastChartResponse;
  loading?: boolean;
}

// Merge history + forecast into a single series for seamless display
function buildChartData(data: ForecastChartResponse) {
  const hist = data.history.map(p => ({
    date:       p.date,
    historical: p.price,
    forecast:   null as number | null,
  }));
  const fcast = data.forecast_points.map(p => ({
    date:       p.date,
    historical: null as number | null,
    forecast:   p.price,
  }));
  // Overlap the last historical point as forecast start for continuity
  if (hist.length > 0 && fcast.length > 0) {
    fcast[0].historical = hist[hist.length - 1].historical;
  }
  return [...hist, ...fcast];
}

function formatPrice(v: number) {
  return `₹${v.toLocaleString("en-IN")}`;
}

function formatDate(str: string) {
  // Show only month-day for axis labels
  try {
    const d = new Date(str);
    return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
  } catch {
    return str;
  }
}

// Custom tooltip
function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number | null; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const date = label ? formatDate(label) : "";
  return (
    <div className="bg-white border border-gray-200 rounded-xl px-3 py-2 shadow-sm text-xs">
      <p className="font-semibold text-gray-700 mb-1">{date}</p>
      {payload.map(p => p.value !== null && (
        <p key={p.name} style={{ color: p.color }}>
          {p.name === "historical" ? "📊 Historical" : "🔮 Forecast"}: {formatPrice(p.value)}
        </p>
      ))}
    </div>
  );
}

export function ForecastChart({ data, loading }: ForecastChartProps) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <div className="animate-pulse h-48 bg-gray-100 rounded-xl" />
        </CardContent>
      </Card>
    );
  }

  const chartData = buildChartData(data);
  // Find today's date string to place the reference line
  const todayStr = new Date().toISOString().split("T")[0];
  // Y-axis domain with padding
  const allPrices = chartData.flatMap(d => [d.historical, d.forecast]).filter((v): v is number => v !== null);
  const minP = Math.min(...allPrices) * 0.98;
  const maxP = Math.max(...allPrices) * 1.02;

  // Thin out x-axis ticks for readability
  const step = Math.max(1, Math.floor(chartData.length / 8));
  const xTicks = chartData.filter((_, i) => i % step === 0).map(d => d.date);

  const cropLabel = data.crop === "cotton" ? "🌿 Cotton" : "🥜 Groundnut";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle>📉 Historical + Forecast — {cropLabel}</CardTitle>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-0.5 bg-primary-500 rounded" />
              Historical
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-0.5 bg-indigo-500 rounded border-dashed border border-indigo-300" />
              Forecast
            </span>
          </div>
        </div>
        <p className="text-xs text-gray-400">{data.mandi} — current ₹{data.current_price.toLocaleString("en-IN")}/qtl</p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              ticks={xTicks}
              tickFormatter={formatDate}
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[minP, maxP]}
              tickFormatter={v => `₹${(v / 1000).toFixed(1)}k`}
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              axisLine={false}
              tickLine={false}
              width={48}
            />
            <Tooltip content={<CustomTooltip />} />
            {/* Today reference line */}
            <ReferenceLine
              x={todayStr}
              stroke="#6366f1"
              strokeDasharray="4 4"
              label={{ value: "Today", position: "top", fontSize: 10, fill: "#6366f1" }}
            />
            <Line
              type="monotone"
              dataKey="historical"
              name="historical"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="forecast"
              name="forecast"
              stroke="#6366f1"
              strokeWidth={2.5}
              strokeDasharray="6 3"
              dot={{ r: 3, fill: "#6366f1", strokeWidth: 0 }}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-400 text-center mt-2">
          AI forecast is an estimate based on historical market data and is not a guaranteed future price.
        </p>
      </CardContent>
    </Card>
  );
}
