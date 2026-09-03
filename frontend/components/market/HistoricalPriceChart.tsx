"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { DataFreshnessBadge } from "./DataFreshnessBadge";
import type { HistoryPoint } from "@/types";

interface HistoricalPriceChartProps {
  data: HistoryPoint[];
  crop: string;
  mandi?: string;
  t: (key: string) => string;
  source?: string;
  sourceStatus?: "LIVE" | "LATEST_AVAILABLE" | "DEMO";
}

function mergeByDate(data: HistoryPoint[]) {
  // Group by date, average modal price if multiple mandis
  const map: Record<string, { date: string; sum: number; count: number }> = {};
  for (const point of data) {
    if (!map[point.date]) map[point.date] = { date: point.date, sum: 0, count: 0 };
    map[point.date].sum += point.modal_price;
    map[point.date].count += 1;
  }
  return Object.values(map)
    .map(d => ({ date: d.date.slice(5), price: Math.round(d.sum / d.count) }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

const CustomTooltip = ({ active, payload, label }: Record<string, unknown>) => {
  if (active && Array.isArray(payload) && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-md text-sm">
        <p className="font-semibold text-gray-700 mb-1">{String(label)}</p>
        {(payload as Array<{ color: string; value: number; name: string }>).map(entry => (
          <p key={entry.name} style={{ color: entry.color }}>
            Modal: ₹{entry.value.toLocaleString("en-IN")}/q
          </p>
        ))}
        <p className="text-xs text-gray-400 mt-1">DEMO DATA</p>
      </div>
    );
  }
  return null;
};

export function HistoricalPriceChart({
  data,
  crop,
  mandi,
  t,
  source = "KisanSetu Demo Dataset",
  sourceStatus = "DEMO",
}: HistoricalPriceChartProps) {
  const chartData = mergeByDate(data);
  const color = crop === "cotton" ? "#16a34a" : "#d4851f";
  const emoji = crop === "cotton" ? "🌿" : "🥜";
  const cropLabel = crop === "cotton" ? "Cotton" : "Groundnut";

  // Calculate avg for reference line
  const avg = chartData.length
    ? Math.round(chartData.reduce((s, d) => s + d.price, 0) / chartData.length)
    : 0;

  const tickFormatter = (_: unknown, idx: number) => idx % Math.max(1, Math.floor(chartData.length / 7)) === 0
    ? chartData[idx]?.date || ""
    : "";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle>
            {emoji} {cropLabel} Price Trend
            {mandi && <span className="text-sm font-normal text-gray-500 ml-1">— {mandi}</span>}
          </CardTitle>
          <DataFreshnessBadge
            source={source}
            sourceStatus={sourceStatus}
            tooltip="This prototype uses synthetic demonstration data. Live market integration coming in Phase 3."
          />
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-3xl mb-2">📉</p>
              <p className="text-sm">No historical data available</p>
            </div>
          </div>
        ) : (
          <>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "#9ca3af" }}
                    tickFormatter={tickFormatter}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "#9ca3af" }}
                    tickFormatter={v => `₹${(v / 1000).toFixed(1)}k`}
                    width={48}
                    domain={["auto", "auto"]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={avg} stroke="#e5e7eb" strokeDasharray="4 4" label={{
                    value: `Avg ₹${avg.toLocaleString("en-IN")}`,
                    fill: "#9ca3af",
                    fontSize: 10,
                    position: "right",
                  }} />
                  <Line
                    type="monotone"
                    dataKey="price"
                    name={cropLabel}
                    stroke={color}
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5, fill: color }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              Daily modal price (₹/quintal) — {chartData.length} trading days
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
