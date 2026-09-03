"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import type { PriceTrendPoint } from "@/types";

interface PriceTrendChartProps {
  data: PriceTrendPoint[];
  t: (key: string) => string;
}

// Merge cotton and groundnut data by date for recharts
function mergeByDate(data: PriceTrendPoint[]) {
  const map: Record<string, { date: string; cotton?: number; groundnut?: number }> = {};
  for (const point of data) {
    if (!map[point.date]) map[point.date] = { date: point.date };
    if (point.crop === "cotton") map[point.date].cotton = point.price;
    if (point.crop === "groundnut") map[point.date].groundnut = point.price;
  }
  return Object.values(map).slice(0, 30);
}

const CustomTooltip = ({ active, payload, label }: Record<string, unknown>) => {
  if (active && Array.isArray(payload) && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-3 shadow text-sm">
        <p className="font-semibold text-gray-700 mb-1">{String(label)}</p>
        {(payload as Array<{ color: string; name: string; value: number }>).map((entry) => (
          <p key={entry.name} style={{ color: entry.color }}>
            {entry.name === "cotton" ? "🌿 Cotton" : "🥜 Groundnut"}: ₹{entry.value.toLocaleString("en-IN")}
          </p>
        ))}
        <p className="text-xs text-gray-400 mt-1">DEMO DATA</p>
      </div>
    );
  }
  return null;
};

export function PriceTrendChart({ data, t }: PriceTrendChartProps) {
  const merged = mergeByDate(data);

  // Show every 5th label to avoid crowding
  const tickFormatter = (_: unknown, index: number) =>
    index % 5 === 0 ? (merged[index]?.date || "") : "";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>📉 {t("market.price_trend")}</CardTitle>
          <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full font-medium">
            DEMO DATA
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={merged} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#9ca3af" }}
                tickFormatter={tickFormatter}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#9ca3af" }}
                tickFormatter={(v) => `₹${(v / 1000).toFixed(1)}k`}
                width={48}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                formatter={(value) => value === "cotton" ? "🌿 Cotton" : "🥜 Groundnut"}
                wrapperStyle={{ fontSize: "13px" }}
              />
              <Line
                type="monotone"
                dataKey="cotton"
                stroke="#16a34a"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="groundnut"
                stroke="#d4851f"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          30-day price trend (₹/quintal) — Demo data only
        </p>
      </CardContent>
    </Card>
  );
}
