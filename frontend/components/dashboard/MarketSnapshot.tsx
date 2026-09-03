"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatPrice } from "@/lib/utils";
import type { MarketSummary } from "@/types";

interface MarketSnapshotProps {
  cotton?: MarketSummary;
  groundnut?: MarketSummary;
  t: (key: string) => string;
}

function CropPriceCard({ data, label, emoji }: { data?: MarketSummary; label: string; emoji: string }) {
  if (!data) {
    return (
      <div className="bg-gray-50 rounded-xl p-4 flex-1">
        <p className="text-gray-400 text-sm">Loading...</p>
      </div>
    );
  }

  const isUp = data.trend === "up";
  const isDown = data.trend === "down";

  return (
    <div className={`rounded-2xl p-5 flex-1 ${isUp ? "bg-green-50" : isDown ? "bg-red-50" : "bg-amber-50"}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{emoji}</span>
          <span className="font-semibold text-gray-700 text-sm">{label}</span>
        </div>
        <Badge variant={isUp ? "green" : isDown ? "red" : "amber"}>
          {isUp ? "↑" : isDown ? "↓" : "→"}{" "}
          {data.change_percent !== undefined
            ? `${Math.abs(data.change_percent).toFixed(1)}%`
            : ""}
        </Badge>
      </div>
      <p className={`text-3xl font-bold mt-1 ${isUp ? "text-green-700" : isDown ? "text-red-700" : "text-amber-700"}`}>
        {formatPrice(data.latest_modal_price)}
      </p>
      <p className="text-xs text-gray-500 mt-1">per quintal • {data.mandi}</p>
      <p className="text-xs text-gray-400 mt-2 font-medium">{data.source}</p>
    </div>
  );
}

export function MarketSnapshot({ cotton, groundnut, t }: MarketSnapshotProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>📈 {t("market.title")}</CardTitle>
          <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full font-medium">
            DEMO DATA
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-3">
          <CropPriceCard data={cotton} label={t("market.cotton")} emoji="🌿" />
          <CropPriceCard data={groundnut} label={t("market.groundnut")} emoji="🥜" />
        </div>
        <p className="text-xs text-gray-400 mt-3 text-center">
          ⚠️ Demo data — not live market prices
        </p>
      </CardContent>
    </Card>
  );
}
