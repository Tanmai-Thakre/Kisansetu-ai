"use client";

/**
 * Phase 7 — /farmer/income
 * Farmer Income Dashboard: shows estimated net income for all selling scenarios.
 *
 * Sections:
 *   1. Input form (crop, quantity, mandi, costs)
 *   2. Top metric cards (Current Value / Best Buyer / Best Net Income / Potential Diff)
 *   3. Scenario comparison table (highlighted best scenario)
 *   4. Income & forecast value chart
 *   5. Cost breakdown list
 *   6. AI-generated deterministic summary
 *   7. Income history (empty until transaction data exists)
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { postIncomeDashboard } from "@/lib/api";
import type { IncomeResponse, IncomeScenario } from "@/types";

// ── Constants ─────────────────────────────────────────────────────────────────

const CROPS  = [{ value: "cotton", label: "🌿 Cotton" }, { value: "groundnut", label: "🥜 Groundnut" }];
const MANDIS = [
  "Rajkot APMC", "Amreli APMC", "Junagadh APMC",
  "Bhavnagar APMC", "Ahmedabad APMC", "Surendranagar APMC", "Jamnagar APMC",
];

// ── Formatting helpers ────────────────────────────────────────────────────────

function fmt(n: number) {
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

function fmtQ(n: number) {
  return `₹${Math.round(n).toLocaleString("en-IN")}/q`;
}

function pct(n: number) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MetricCard({ label, value, sub, accent = false }: {
  label: string; value: string; sub?: string; accent?: boolean;
}) {
  return (
    <div className={`rounded-2xl p-4 border ${accent
      ? "bg-primary-600 border-primary-600 text-white"
      : "bg-white border-gray-100 shadow-sm"}`}>
      <p className={`text-xs font-medium mb-1 ${accent ? "text-primary-100" : "text-gray-500"}`}>{label}</p>
      <p className={`text-xl font-black leading-tight ${accent ? "text-white" : "text-gray-900"}`}>{value}</p>
      {sub && <p className={`text-xs mt-0.5 ${accent ? "text-primary-200" : "text-gray-400"}`}>{sub}</p>}
    </div>
  );
}

function ScenarioRow({ scenario, isBest }: { scenario: IncomeScenario; isBest: boolean }) {
  return (
    <tr className={isBest ? "bg-green-50 border-l-4 border-l-green-500" : "hover:bg-gray-50"}>
      <td className="py-2.5 px-3 text-sm">
        <span className={`font-medium ${isBest ? "text-green-800" : "text-gray-800"}`}>
          {isBest && <span className="mr-1">★</span>}
          {scenario.name}
        </span>
        {isBest && (
          <span className="ml-2 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-semibold">
            Highest estimated
          </span>
        )}
      </td>
      <td className="py-2.5 px-3 text-sm text-right font-medium text-gray-700">
        {fmt(scenario.gross_revenue)}
      </td>
      <td className="py-2.5 px-3 text-sm text-right text-amber-600">
        {fmt(scenario.total_cost)}
      </td>
      <td className={`py-2.5 px-3 text-sm text-right font-bold ${
        isBest ? "text-green-700" : scenario.net_income < 0 ? "text-red-600" : "text-gray-900"
      }`}>
        {fmt(scenario.net_income)}
      </td>
      <td className="py-2.5 px-3 text-xs text-right text-gray-500">
        {fmtQ(scenario.net_income_per_quintal)}
      </td>
    </tr>
  );
}

function CostRow({ label, value }: { label: string; value: number | null | undefined }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-800">
        {value == null ? "Not provided" : fmt(value)}
      </span>
    </div>
  );
}

// ── Simple bar chart for scenarios ────────────────────────────────────────────

function IncomeBarChart({ scenarios, bestName }: {
  scenarios: IncomeScenario[]; bestName: string | null;
}) {
  if (scenarios.length === 0) return null;
  const maxVal = Math.max(...scenarios.map(s => Math.abs(s.net_income)), 1);

  return (
    <div className="space-y-2.5 mt-2">
      {scenarios.slice(0, 6).map(s => {
        const isBest = s.name === bestName;
        const widthPct = Math.max(5, Math.round((Math.max(0, s.net_income) / maxVal) * 100));
        return (
          <div key={s.name}>
            <div className="flex items-center justify-between text-xs mb-0.5">
              <span className={`font-medium ${isBest ? "text-green-700" : "text-gray-600"} truncate max-w-[180px]`}>
                {isBest && "★ "}{s.name}
              </span>
              <span className={`font-bold ${isBest ? "text-green-700" : "text-gray-700"}`}>
                {fmt(s.net_income)}
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${isBest ? "bg-green-500" : "bg-primary-400"}`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Value chart (forecast vs current) ────────────────────────────────────────

function ForecastValueCard({ result }: { result: IncomeResponse }) {
  const q = result.quantity;
  const rows = [
    { label: "Current (Mandi Now)", value: result.mandi_price * q, price: result.mandi_price, type: "current" },
    ...(result.buyer_price ? [{ label: "Direct Buyer", value: result.buyer_price * q, price: result.buyer_price, type: "buyer" }] : []),
    { label: "Forecast 7 days", value: result.forecast_7d * q, price: result.forecast_7d, type: "forecast" },
    { label: "Forecast 15 days", value: result.forecast_15d * q, price: result.forecast_15d, type: "forecast" },
    { label: "Forecast 30 days", value: result.forecast_30d * q, price: result.forecast_30d, type: "forecast" },
    ...(result.quality_adjusted_price ? [{
      label: "Quality-Adjusted",
      value: result.quality_adjusted_price * q,
      price: result.quality_adjusted_price,
      type: "quality",
    }] : []),
  ];
  const maxVal = Math.max(...rows.map(r => r.value), 1);

  const barColor = (type: string) => {
    switch (type) {
      case "buyer":   return "bg-blue-400";
      case "forecast": return "bg-indigo-400";
      case "quality":  return "bg-purple-400";
      default:         return "bg-primary-400";
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-400 mt-1">
        Gross value (before costs) • Quantity: {q} qtl
      </p>
      {rows.map(r => (
        <div key={r.label}>
          <div className="flex items-center justify-between text-xs mb-0.5">
            <span className="text-gray-600 truncate max-w-[180px]">{r.label}</span>
            <span className="font-medium text-gray-800">{fmt(r.value)}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full ${barColor(r.type)}`}
              style={{ width: `${Math.max(5, Math.round(r.value / maxVal * 100))}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-0.5">{fmtQ(r.price)}</p>
        </div>
      ))}
      <p className="text-xs text-amber-600 mt-1">
        ⚠️ Forecast values are estimated. Store scenarios include storage costs not shown above.
      </p>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function IncomePage() {
  const { language, t, changeLanguage } = useLanguage();

  // Inputs
  const [crop,          setCrop]         = useState("cotton");
  const [mandi,         setMandi]        = useState("Rajkot APMC");
  const [quantity,      setQuantity]     = useState(100);
  const [storageCost,   setStorageCost]  = useState(80);
  const [labourCost,    setLabourCost]   = useState(0);
  const [packagingCost, setPackagingCost] = useState(0);
  const [otherCost,     setOtherCost]    = useState(0);
  const [showOptional,  setShowOptional] = useState(false);

  // State
  const [result,  setResult]  = useState<IncomeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  // Auto-calculate on mount with defaults
  useEffect(() => {
    handleCalculate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCalculate = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await postIncomeDashboard({
        crop,
        quantity,
        mandi,
        storage_cost_per_quintal: storageCost,
        labour_total:    labourCost,
        packaging_total: packagingCost,
        other_total:     otherCost,
      });
      setResult(data);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Could not calculate income. Please ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Rameshbhai Patel" role="farmer" />
      <div className="flex">
        <SideNav />
        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">

          {/* Page header */}
          <div className="flex items-start justify-between flex-wrap gap-2">
            <div>
              <h1 className="text-xl font-bold text-gray-900">💰 Income Dashboard</h1>
              <p className="text-sm text-gray-500 mt-0.5">Compare estimated net income for all selling strategies</p>
            </div>
            <Badge variant="green">Phase 7 Active</Badge>
          </div>

          {/* ── Input form ─────────────────────────────────────────────────── */}
          <Card>
            <CardHeader><CardTitle>Crop & Quantity</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Crop</label>
                  <select value={crop} onChange={e => setCrop(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {CROPS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Mandi</label>
                  <select value={mandi} onChange={e => setMandi(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {MANDIS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Quantity (qtl)</label>
                  <input type="number" value={quantity} min={1}
                    onChange={e => setQuantity(Math.max(1, Number(e.target.value) || 1))}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Storage Cost (₹/qtl/mo)</label>
                  <input type="number" value={storageCost} min={0}
                    onChange={e => setStorageCost(Math.max(0, Number(e.target.value)))}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                </div>
              </div>

              {/* Optional expenses toggle */}
              <div>
                <button
                  onClick={() => setShowOptional(v => !v)}
                  className="text-xs text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1"
                >
                  {showOptional ? "▲ Hide" : "▼ Show"} Optional Expenses (Labour, Packaging, Other)
                </button>
              </div>

              {showOptional && (
                <div className="grid grid-cols-3 gap-3 pt-1">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5">Labour (₹)</label>
                    <input type="number" value={labourCost} min={0}
                      onChange={e => setLabourCost(Math.max(0, Number(e.target.value)))}
                      className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5">Packaging (₹)</label>
                    <input type="number" value={packagingCost} min={0}
                      onChange={e => setPackagingCost(Math.max(0, Number(e.target.value)))}
                      className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5">Other (₹)</label>
                    <input type="number" value={otherCost} min={0}
                      onChange={e => setOtherCost(Math.max(0, Number(e.target.value)))}
                      className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                  </div>
                </div>
              )}

              <Button variant="primary" size="lg" fullWidth onClick={handleCalculate} disabled={loading}>
                {loading ? "Calculating…" : "📊 Calculate Income Scenarios"}
              </Button>
            </CardContent>
          </Card>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-red-700">
              ⚠️ {error}
            </div>
          )}

          {/* ── Results ───────────────────────────────────────────────────── */}
          {result && (
            <>
              {/* ── Top metric cards ─────────────────────────────────────── */}
              <div className="grid grid-cols-2 gap-3">
                <MetricCard
                  label="Estimated Current Value"
                  value={fmt(result.current_estimated_income)}
                  sub={`Sell now at mandi • ${fmtQ(result.mandi_price)}`}
                />
                <MetricCard
                  label="Best Buyer Estimated Value"
                  value={result.best_buyer_income != null ? fmt(result.best_buyer_income) : "No buyer data"}
                  sub={result.buyer_price ? fmtQ(result.buyer_price) : undefined}
                />
                <MetricCard
                  label="Highest Estimated Net Income"
                  value={result.best_net_income != null ? fmt(result.best_net_income) : "—"}
                  sub={result.best_scenario || undefined}
                  accent
                />
                <MetricCard
                  label="Potential Difference"
                  value={fmt(result.income_difference)}
                  sub="Best vs lowest estimated"
                />
              </div>

              {/* ── Scenario comparison table ─────────────────────────── */}
              <Card>
                <CardHeader>
                  <CardTitle>📊 Scenario Comparison</CardTitle>
                  <p className="text-xs text-gray-400 mt-0.5">
                    ★ = Highest estimated net income — not a guaranteed best outcome
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto -mx-1">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-gray-100">
                          <th className="py-2 px-3 text-xs font-semibold text-gray-500">Strategy</th>
                          <th className="py-2 px-3 text-xs font-semibold text-gray-500 text-right">Gross Rev.</th>
                          <th className="py-2 px-3 text-xs font-semibold text-gray-500 text-right">Costs</th>
                          <th className="py-2 px-3 text-xs font-semibold text-gray-500 text-right">Net Income</th>
                          <th className="py-2 px-3 text-xs font-semibold text-gray-500 text-right">Per Qtl</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {result.scenarios.map(s => (
                          <ScenarioRow
                            key={s.name}
                            scenario={s}
                            isBest={s.name === result.best_scenario}
                          />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* ── Income bar chart ──────────────────────────────────── */}
              <Card>
                <CardHeader><CardTitle>📈 Net Income by Strategy</CardTitle></CardHeader>
                <CardContent>
                  <IncomeBarChart scenarios={result.scenarios} bestName={result.best_scenario} />
                </CardContent>
              </Card>

              {/* ── Value chart (gross, before costs) ────────────────── */}
              <Card>
                <CardHeader>
                  <CardTitle>💹 Price & Gross Value Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <ForecastValueCard result={result} />
                </CardContent>
              </Card>

              {/* ── Cost breakdown ───────────────────────────────────── */}
              <Card>
                <CardHeader><CardTitle>🔍 Cost Breakdown (Sell Now scenario)</CardTitle></CardHeader>
                <CardContent>
                  <CostRow label="Transport" value={result.cost_breakdown.transport} />
                  <CostRow label="Storage"   value={result.cost_breakdown.storage} />
                  <CostRow label="Labour"    value={result.cost_breakdown.labour} />
                  <CostRow label="Packaging" value={result.cost_breakdown.packaging} />
                  <CostRow label="Other"     value={result.cost_breakdown.other} />
                  <p className="text-xs text-gray-400 mt-2">
                    Storage cost varies per scenario — shown in table above.
                  </p>
                </CardContent>
              </Card>

              {/* ── Quality adjustment note ──────────────────────────── */}
              {result.quality_adjusted_price && (
                <Card className="border-l-4 border-l-purple-400">
                  <CardContent>
                    <p className="text-sm font-semibold text-purple-700 mb-1">
                      🔬 Quality Adjustment Applied
                    </p>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Market price</span>
                        <span className="font-medium">{fmtQ(result.mandi_price)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Quality impact</span>
                        <span className={`font-medium ${(result.quality_price_impact_pct ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
                          {pct(result.quality_price_impact_pct ?? 0)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm font-bold border-t border-purple-100 pt-1">
                        <span className="text-purple-700">Estimated quality price</span>
                        <span className="text-purple-700">{fmtQ(result.quality_adjusted_price)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                      Quality premium is estimated — not guaranteed. <Link href="/farmer/quality" className="text-purple-600 hover:underline">Update quality assessment →</Link>
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* ── AI summary ──────────────────────────────────────── */}
              <Card className="border-l-4 border-l-green-400">
                <CardHeader>
                  <CardTitle className="text-green-700">💡 Estimated Income Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-700 leading-relaxed">{result.deterministic_summary}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    IBM Granite AI will convert this into a personalised farmer-friendly explanation in Phase 8.
                  </p>
                </CardContent>
              </Card>

              {/* ── Disclaimer ───────────────────────────────────────── */}
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs text-amber-700 leading-relaxed">
                ⚠️ <strong>Estimated values only.</strong> {result.disclaimer}
              </div>

              {/* ── Income history placeholder ────────────────────────── */}
              <Card>
                <CardHeader><CardTitle>🗂 Income History</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-center py-6">
                    <p className="text-3xl mb-2">📋</p>
                    <p className="text-sm font-medium text-gray-600">No completed sale records yet</p>
                    <p className="text-xs text-gray-400 mt-1">
                      When you record completed sales, your history will appear here.
                    </p>
                  </div>
                  <div className="mt-2 border border-gray-100 rounded-xl overflow-hidden">
                    <table className="w-full text-xs text-gray-500">
                      <thead className="bg-gray-50">
                        <tr>
                          {["Date", "Crop", "Qty", "Sell Price", "Revenue", "Costs", "Net Income"].map(h => (
                            <th key={h} className="py-2 px-2 text-left font-medium">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td colSpan={7} className="py-4 text-center text-gray-400">No records</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* No result yet */}
          {!result && !loading && !error && (
            <Card>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-4xl mb-3">💰</p>
                  <p className="font-semibold text-gray-700">Enter crop details to see estimated income</p>
                  <p className="text-sm text-gray-400 mt-1">
                    The income dashboard compares all four selling strategies
                    using live market prices, forecasts, buyer offers, and your entered costs.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

        </main>
      </div>
      <BottomNav />
    </div>
  );
}
