"use client";

// Phase 3 — /farmer/market updated with AI Forecast section (ForecastCard + ForecastChart)

import { useEffect, useState, useCallback } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { MarketSummaryCard } from "@/components/market/MarketSummaryCard";
import { PriceTable } from "@/components/market/PriceTable";
import { HistoricalPriceChart } from "@/components/market/HistoricalPriceChart";
import { BestMandiCard, MandiComparisonCard } from "@/components/market/MandiComparison";
import { DataFreshnessBadge } from "@/components/market/DataFreshnessBadge";
import { TrendCard } from "@/components/market/TrendIndicator";
import { ForecastCard } from "@/components/market/ForecastCard";
import { ForecastChart } from "@/components/market/ForecastChart";
import api, { endpoints, fetchForecast, fetchForecastChart } from "@/lib/api";
import type {
  MandiComparisonResponse, BestMandiResponse,
  HistoryPoint, MandiComparisonEntry, TrendIndicator,
  ForecastResponse, ForecastChartResponse,
} from "@/types";

const DISTRICTS = ["Rajkot", "Amreli", "Junagadh", "Bhavnagar", "Ahmedabad", "Surendranagar", "Jamnagar", "Mehsana", "Banaskantha"];
const CROPS = [
  { value: "cotton", label: "🌿 Cotton" },
  { value: "groundnut", label: "🥜 Groundnut" },
];

// ── Error / Empty states ──────────────────────────────────────────────────────

function MarketErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card>
      <CardContent>
        <div className="text-center py-8">
          <p className="text-3xl mb-3">⚠️</p>
          <p className="font-semibold text-gray-700">Market data temporarily unavailable</p>
          <p className="text-sm text-gray-500 mt-1">Showing latest available data. Start the backend to load live demo prices.</p>
          <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
            Try Again
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map(i => (
        <div key={i} className="h-24 bg-gray-100 rounded-2xl" />
      ))}
    </div>
  );
}

// ── Market Filters ────────────────────────────────────────────────────────────

interface FiltersProps {
  crop: string;
  district: string;
  quantity: number;
  onCropChange: (c: string) => void;
  onDistrictChange: (d: string) => void;
  onQuantityChange: (q: number) => void;
  onRefresh: () => void;
  loading: boolean;
}

function MarketFilters({ crop, district, quantity, onCropChange, onDistrictChange, onQuantityChange, onRefresh, loading }: FiltersProps) {
  return (
    <Card>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Crop</label>
            <select
              value={crop}
              onChange={e => onCropChange(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              {CROPS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">District</label>
            <select
              value={district}
              onChange={e => onDistrictChange(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              <option value="">All Districts</option>
              {DISTRICTS.map(d => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Quantity (qtl)</label>
            <input
              type="number"
              value={quantity}
              min={1}
              onChange={e => onQuantityChange(Number(e.target.value) || 100)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>
          <div className="flex items-end">
            <Button
              variant="primary"
              size="md"
              fullWidth
              onClick={onRefresh}
              disabled={loading}
            >
              {loading ? "Loading..." : "🔄 Refresh"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function MarketPage() {
  const { language, t, changeLanguage } = useLanguage();

  // Filters
  const [crop, setCrop] = useState("cotton");
  const [district, setDistrict] = useState("");
  const [quantity, setQuantity] = useState(100);
  const [selectedMandi, setSelectedMandi] = useState("Rajkot APMC");

  // Chart mandi tab
  const [chartTab, setChartTab] = useState<"cotton" | "groundnut">("cotton");

  // Phase 2 data states
  const [comparison, setComparison]     = useState<MandiComparisonResponse | null>(null);
  const [bestMandi, setBestMandi]       = useState<BestMandiResponse | null>(null);
  const [cottonHistory, setCottonHistory] = useState<HistoryPoint[]>([]);
  const [gnHistory, setGnHistory]       = useState<HistoryPoint[]>([]);
  const [trends, setTrends]             = useState<TrendIndicator[]>([]);
  const [sourceInfo, setSourceInfo]     = useState({ source: "KisanSetu Demo Dataset", source_status: "DEMO" as const, is_live: false });

  // Phase 3 forecast states
  const [forecast, setForecast]           = useState<ForecastResponse | null>(null);
  const [forecastChart, setForecastChart] = useState<ForecastChartResponse | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const params: Record<string, unknown> = { crop, quantity };
      if (district) params.district = district;

      const [cmpRes, bestRes, cottonHistRes, gnHistRes, trendsRes, srcRes] = await Promise.allSettled([
        api.get(endpoints.marketCompare, { params }),
        api.get(endpoints.marketBestMandi, { params: { crop, quantity, ...(district && { district }) } }),
        api.get(endpoints.marketHistory, { params: { crop: "cotton", mandi: selectedMandi, limit: 60 } }),
        api.get(endpoints.marketHistory, { params: { crop: "groundnut", mandi: selectedMandi.replace("APMC", "").trim() + " APMC", limit: 60 } }),
        api.get(endpoints.marketTrends, { params: { crop, ...(district && { district }) } }),
        api.get(endpoints.marketSourceInfo),
      ]);

      if (cmpRes.status === "fulfilled") setComparison(cmpRes.value.data);
      if (bestRes.status === "fulfilled") setBestMandi(bestRes.value.data);
      if (cottonHistRes.status === "fulfilled") setCottonHistory(cottonHistRes.value.data.data || []);
      if (gnHistRes.status === "fulfilled") setGnHistory(gnHistRes.value.data.data || []);
      if (trendsRes.status === "fulfilled") setTrends(trendsRes.value.data || []);
      if (srcRes.status === "fulfilled") setSourceInfo(srcRes.value.data);

      // If all critical requests failed, show error
      if (cmpRes.status === "rejected" && bestRes.status === "rejected") {
        setError(true);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [crop, district, quantity, selectedMandi]);

  // Phase 3: fetch forecast when crop or selectedMandi changes
  const fetchForecastData = useCallback(async () => {
    setForecastLoading(true);
    try {
      const [fc, fChart] = await Promise.allSettled([
        fetchForecast(crop, selectedMandi),
        fetchForecastChart(crop, selectedMandi, 45, 30),
      ]);
      if (fc.status === "fulfilled")     setForecast(fc.value);
      if (fChart.status === "fulfilled") setForecastChart(fChart.value);
    } catch {
      // forecast is optional — fail silently
    } finally {
      setForecastLoading(false);
    }
  }, [crop, selectedMandi]);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  useEffect(() => { fetchForecastData(); }, [fetchForecastData]);

  // Summary cards from comparison data
  const cottonEntry = comparison?.mandis?.find(m => m.mandi.toLowerCase().includes("rajkot"));
  const gnComparison = comparison?.crop === "groundnut" ? comparison : null;

  // Top trend card for selected crop
  const topTrend = trends.find(tr => tr.mandi === selectedMandi) || trends[0];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Rameshbhai Patel" role="farmer" />
      <div className="flex">
        <SideNav />
        <main className="flex-1 max-w-3xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">

          {/* Header row */}
          <div className="flex items-start justify-between flex-wrap gap-2">
            <div>
              <h1 className="text-xl font-bold text-gray-900">📈 Market Intelligence</h1>
              <p className="text-sm text-gray-500 mt-0.5">Gujarat Mandi Prices — Cotton & Groundnut</p>
            </div>
            <DataFreshnessBadge
              source={sourceInfo.source}
              sourceStatus={sourceInfo.source_status}
              isLive={sourceInfo.is_live}
              tooltip="This prototype uses synthetic demonstration data. Live market integration available via MarketDataProvider."
            />
          </div>

          {/* Filters */}
          <MarketFilters
            crop={crop}
            district={district}
            quantity={quantity}
            onCropChange={setCrop}
            onDistrictChange={setDistrict}
            onQuantityChange={setQuantity}
            onRefresh={fetchAll}
            loading={loading}
          />

          {error && <MarketErrorState onRetry={fetchAll} />}
          {loading && !comparison && <LoadingState />}

          {/* Summary cards */}
          {comparison && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {/* Cotton summary */}
              {(() => {
                const best = comparison.mandis?.[0];
                if (!best) return null;
                return (
                  <MarketSummaryCard
                    crop={comparison.crop}
                    displayName={comparison.crop === "cotton" ? "Cotton" : "Groundnut"}
                    emoji={comparison.crop === "cotton" ? "🌿" : "🥜"}
                    modalPrice={best.modal_price}
                    minPrice={best.min_price}
                    maxPrice={best.max_price}
                    trend={best.trend}
                    changePct={best.change_percent ?? undefined}
                    mandi={best.mandi}
                    source="DEMO DATA"
                    isHighlighted
                  />
                );
              })()}
              {/* Best mandi summary */}
              {bestMandi?.best_mandi && (
                <div className="rounded-2xl bg-primary-50 border border-primary-100 p-5 flex flex-col gap-1">
                  <p className="text-xs font-semibold text-primary-500">Best Mandi (Net)</p>
                  <p className="font-bold text-primary-900 text-sm truncate">{bestMandi.best_mandi.mandi}</p>
                  <p className="text-2xl font-bold text-primary-700">₹{bestMandi.best_mandi.net_price.toLocaleString("en-IN")}</p>
                  <p className="text-xs text-primary-400">net / quintal</p>
                </div>
              )}
              {/* Trend card */}
              {topTrend && (
                <div className="rounded-2xl bg-white border border-gray-100 p-5 flex flex-col gap-1">
                  <p className="text-xs font-semibold text-gray-400">Price Trend (7d)</p>
                  <p className="text-xs text-gray-500 truncate">{topTrend.mandi}</p>
                  <p className="text-2xl font-bold text-gray-900">₹{(topTrend.current_price || 0).toLocaleString("en-IN")}</p>
                  <div className="text-sm">
                    {topTrend.change !== undefined && (
                      <span className={topTrend.trend === "UP" ? "text-green-600" : topTrend.trend === "DOWN" ? "text-red-600" : "text-gray-500"}>
                        {topTrend.trend === "UP" ? "↑" : topTrend.trend === "DOWN" ? "↓" : "→"}
                        {" "}{topTrend.change_percent !== undefined ? `${Math.abs(topTrend.change_percent).toFixed(1)}%` : ""}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Best mandi recommendation */}
          {bestMandi && <BestMandiCard data={bestMandi} />}

          {/* ── Phase 3: AI Price Forecast section ─────────────────────────── */}
          <div className="rounded-2xl bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 px-4 py-3">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🔮</span>
              <h2 className="font-bold text-indigo-800 text-base">AI Price Forecast</h2>
              <span className="text-xs bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full font-medium ml-auto">
                Phase 3 Active
              </span>
            </div>
            <p className="text-xs text-indigo-500 mb-3">
              Select a crop and mandi above — the RandomForest model will forecast 7, 15, and 30-day prices.
            </p>

            {/* Mandi selector for forecast */}
            <div className="mb-3">
              <label className="block text-xs font-medium text-indigo-600 mb-1.5">Forecast Mandi</label>
              <select
                value={selectedMandi}
                onChange={e => setSelectedMandi(e.target.value)}
                className="w-full border border-indigo-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
              >
                {["Rajkot APMC","Amreli APMC","Junagadh APMC","Bhavnagar APMC","Ahmedabad APMC","Surendranagar APMC","Jamnagar APMC","Gondal APMC","Morbi APMC","Botad APMC","Dhrangadhra APMC","Anand APMC","Surat APMC","Mehsana APMC","Palanpur APMC","Vadodara APMC"].map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Forecast Card */}
          {(forecast || forecastLoading) && (
            <ForecastCard data={forecast!} loading={forecastLoading} />
          )}

          {/* Forecast Chart */}
          {(forecastChart || forecastLoading) && (
            <ForecastChart data={forecastChart!} loading={forecastLoading} />
          )}

          {/* Forecast not available state */}
          {!forecastLoading && !forecast && (
            <Card>
              <CardContent>
                <div className="text-center py-6">
                  <p className="text-3xl mb-2">🔮</p>
                  <p className="font-semibold text-gray-700 text-sm">Forecast unavailable</p>
                  <p className="text-xs text-gray-400 mt-1">Start the backend to generate AI price forecasts.</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Historical chart — tab between crops */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>📉 Historical Price Chart</CardTitle>
                <div className="flex rounded-xl overflow-hidden border border-gray-200">
                  {(["cotton", "groundnut"] as const).map(c => (
                    <button
                      key={c}
                      onClick={() => setChartTab(c)}
                      className={`px-3 py-1.5 text-xs font-semibold transition-colors ${
                        chartTab === c ? "bg-primary-600 text-white" : "bg-white text-gray-500 hover:bg-gray-50"
                      }`}
                    >
                      {c === "cotton" ? "🌿 Cotton" : "🥜 Groundnut"}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent className="-mx-1">
              <HistoricalPriceChart
                data={chartTab === "cotton" ? cottonHistory : gnHistory}
                crop={chartTab}
                mandi={selectedMandi}
                t={t}
                source={sourceInfo.source}
                sourceStatus={sourceInfo.source_status}
              />
            </CardContent>
          </Card>

          {/* Mandi comparison table */}
          {comparison && comparison.mandis.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <CardTitle>
                    🏪 Mandi Comparison — {comparison.crop === "cotton" ? "Cotton" : "Groundnut"}
                  </CardTitle>
                  <span className="text-xs text-gray-400">
                    {quantity} qtl • Sorted by net price
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <PriceTable rows={comparison.mandis} showNetPrice highlightBest />
                <p className="text-xs text-gray-400 mt-3 text-center">
                  Net price = Modal − Estimated transport cost. Not official rates.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Mobile mandi cards */}
          {comparison && (
            <div className="sm:hidden">
              <h3 className="font-semibold text-gray-800 mb-3 text-sm">Compare Mandis</h3>
              <MandiComparisonCard entries={comparison.mandis.slice(0, 5)} crop={comparison.crop} />
            </div>
          )}

        </main>
      </div>
      <BottomNav />
    </div>
  );
}
