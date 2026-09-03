"use client";

// Phase 5 — /farmer/advisor: Storage & Selling Timing Advisor
// Fully functional: inputs → POST /api/agents/storage-advisor → rich result UI

import { useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { RecommendationBadge } from "@/components/advisor/RecommendationBadge";
import { ComparisonTable } from "@/components/advisor/ComparisonTable";
import api, { endpoints } from "@/lib/api";
import type { AdvisorResponse } from "@/types";

const CROPS    = [{ value: "cotton", label: "🌿 Cotton" }, { value: "groundnut", label: "🥜 Groundnut" }];
const MANDIS   = ["Rajkot APMC","Amreli APMC","Junagadh APMC","Bhavnagar APMC","Ahmedabad APMC","Surendranagar APMC","Jamnagar APMC"];
const URGENCIES: { value: "LOW"|"MEDIUM"|"HIGH", label: string, icon: string }[] = [
  { value: "LOW",    label: "Low — I can wait",         icon: "😌" },
  { value: "MEDIUM", label: "Medium — Need income soon", icon: "🕐" },
  { value: "HIGH",   label: "High — Need cash now",      icon: "⚡" },
];

function fmt(n: number) {
  return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function MetricRow({ label, value, sub, color = "text-gray-900" }: {
  label: string; value: string; sub?: string; color?: string;
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <div className="text-right">
        <span className={`text-sm font-bold ${color}`}>{value}</span>
        {sub && <p className="text-xs text-gray-400">{sub}</p>}
      </div>
    </div>
  );
}

export default function AdvisorPage() {
  const { language, t, changeLanguage } = useLanguage();

  // Inputs
  const [crop,     setCrop]     = useState("cotton");
  const [mandi,    setMandi]    = useState("Rajkot APMC");
  const [quantity, setQuantity] = useState(100);
  const [storeCost,setStoreCost] = useState(80);
  const [urgency,  setUrgency]  = useState<"LOW"|"MEDIUM"|"HIGH">("MEDIUM");

  // State
  const [result,   setResult]   = useState<AdvisorResponse | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const [showBreakdown, setShowBreakdown] = useState(false);

  const handleAdvise = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.post(endpoints.storageAdvisor, {
        crop,
        mandi,
        quantity,
        storage_cost_per_quintal: storeCost,
        cash_urgency: urgency,
      });
      setResult(res.data as AdvisorResponse);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Could not get recommendation. Please start the backend.");
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
          <div>
            <h1 className="text-xl font-bold text-gray-900">💡 {t("advisor.title")}</h1>
            <p className="text-sm text-gray-500 mt-0.5">{t("advisor.ai_recommendation")}</p>
          </div>

          {/* Input form */}
          <Card>
            <CardHeader>
              <CardTitle>
                {language === "gu" ? "તમારી પાક વિગત" : language === "hi" ? "आपकी फसल जानकारी" : "Your Crop Details"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="advisor-crop" className="block text-xs font-medium text-gray-500 mb-1.5">{t("advisor.crop")}</label>
                  <select id="advisor-crop" value={crop} onChange={e => setCrop(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {CROPS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="advisor-mandi" className="block text-xs font-medium text-gray-500 mb-1.5">{t("advisor.mandi")}</label>
                  <select id="advisor-mandi" value={mandi} onChange={e => setMandi(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {MANDIS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="advisor-qty" className="block text-xs font-medium text-gray-500 mb-1.5">{t("income.quantity")}</label>
                  <input id="advisor-qty" type="number" value={quantity} min={1}
                    onChange={e => setQuantity(Number(e.target.value) || 1)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                </div>
                <div>
                  <label htmlFor="advisor-storecost" className="block text-xs font-medium text-gray-500 mb-1.5">{t("advisor.storage_cost")}</label>
                  <input id="advisor-storecost" type="number" value={storeCost} min={0}
                    onChange={e => setStoreCost(Number(e.target.value))}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                </div>
              </div>

              {/* Cash urgency */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-2">{t("advisor.cash_urgency")}</label>
                <div className="flex gap-2">
                  {URGENCIES.map(u => (
                    <button
                      key={u.value}
                      onClick={() => setUrgency(u.value)}
                      aria-pressed={urgency === u.value}
                      className={`flex-1 py-2.5 rounded-xl text-xs font-semibold transition-colors border min-h-[44px] ${
                        urgency === u.value
                          ? "bg-primary-600 text-white border-primary-600"
                          : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                      }`}>
                      <div aria-hidden="true">{u.icon}</div>
                      <div className="mt-0.5 hidden sm:block">{u.label.split("—")[0].trim()}</div>
                    </button>
                  ))}
                </div>
              </div>

              <Button variant="primary" size="lg" fullWidth onClick={handleAdvise} disabled={loading} aria-busy={loading}>
                {loading
                  ? (language === "gu" ? "વિશ્લેષણ..." : language === "hi" ? "विश्लेषण..." : "Analysing…")
                  : `🤖 ${t("advisor.get_advice")}`
                }
              </Button>
            </CardContent>
          </Card>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-red-700" role="alert">
              ⚠️ {error}
            </div>
          )}

          {/* ── Results ───────────────────────────────────────────────────── */}
          {result && (
            <>
              {/* Main recommendation */}
              <RecommendationBadge
                recommendation={result.recommendation}
                sellPct={result.sell_percentage}
                storePct={result.store_percentage}
                horizonDays={result.recommended_horizon_days}
                risk={result.risk}
                confidence={result.confidence}
              />

              {/* Price comparison cards */}
              <div className="grid grid-cols-2 gap-3">
                <Card>
                  <CardContent>
                    <p className="text-xs text-gray-400 mb-1">Best Current Price</p>
                    <p className="text-xl font-black text-gray-900">{fmt(result.current_best_price)}<span className="text-xs text-gray-400 font-normal">/q</span></p>
                    {result.buyer_is_best
                      ? <p className="text-xs text-green-600 font-semibold mt-0.5">↑ Direct buyer (vs mandi {fmt(result.current_mandi_price)}/q)</p>
                      : <p className="text-xs text-gray-400 mt-0.5">Mandi price</p>
                    }
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <p className="text-xs text-gray-400 mb-1">Forecast ({result.recommended_horizon_days}d)</p>
                    <p className="text-xl font-black text-indigo-700">{fmt(result.forecast_price)}<span className="text-xs text-gray-400 font-normal">/q</span></p>
                    <p className={`text-xs font-semibold mt-0.5 ${result.gain_percent >= 0 ? "text-green-600" : "text-red-500"}`}>
                      {result.gain_percent >= 0 ? "+" : ""}{result.gain_percent.toFixed(1)}% net gain
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <p className="text-xs text-gray-400 mb-1">Sell Now Total</p>
                    <p className="text-xl font-black text-green-700">{fmt(result.sell_now_value)}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{quantity} qtl × {fmt(result.current_best_price)}/q</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <p className="text-xs text-gray-400 mb-1">Storage Cost</p>
                    <p className="text-xl font-black text-amber-600">{fmt(result.estimated_storage_cost)}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{result.recommended_horizon_days}d at ₹{storeCost}/qtl/mo</p>
                  </CardContent>
                </Card>
              </div>

              {/* Potential gain */}
              <div className={`rounded-2xl p-4 border ${
                result.potential_net_gain > 0
                  ? "bg-green-50 border-green-200"
                  : "bg-red-50 border-red-200"
              }`}>
                <p className="text-xs font-semibold text-gray-500 mb-1">Potential Net Gain (Store vs Sell Now)</p>
                <p className={`text-2xl font-black ${result.potential_net_gain > 0 ? "text-green-700" : "text-red-600"}`}>
                  {result.potential_net_gain >= 0 ? "+" : ""}{fmt(result.potential_net_gain)}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {fmt(result.gain_per_quintal)}/qtl · {result.gain_percent >= 0 ? "+" : ""}{result.gain_percent.toFixed(1)}%
                </p>
              </div>

              {/* Comparison table */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>📊 Sell vs Store Comparison</CardTitle>
                    <button onClick={() => setShowBreakdown(p => !p)}
                      className="text-xs text-indigo-600 font-medium hover:underline">
                      {showBreakdown ? "▲ Hide" : "▼ Show"}
                    </button>
                  </div>
                </CardHeader>
                {showBreakdown && (
                  <CardContent>
                    <ComparisonTable
                      sellNowValue={result.sell_now_value}
                      horizons={result.horizons}
                      quantity={quantity}
                    />
                  </CardContent>
                )}
              </Card>

              {/* Why this recommendation */}
              <Card className="border-l-4 border-l-indigo-400">
                <CardHeader>
                  <CardTitle className="text-indigo-700">💡 Why this recommendation?</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-gray-600 leading-relaxed">{result.explanation}</p>
                  <div className="space-y-1.5">
                    {result.reasons.map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-gray-600">
                        <span className="text-indigo-400 mt-0.5 shrink-0">•</span>
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Disclaimer */}
              <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 text-xs text-gray-500 leading-relaxed">
                ⚠️ <strong>AI-assisted recommendation:</strong> {result.disclaimer}
              </div>
            </>
          )}

          {/* No result yet */}
          {!result && !loading && !error && (
            <Card>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-4xl mb-3" aria-hidden="true">🌾</p>
                  <p className="font-semibold text-gray-700">{t("advisor.pending")}</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {language === "gu"
                      ? "ઉપર ફસલ વિગત ભરો — AI ભલામણ આવશે."
                      : language === "hi"
                      ? "ऊपर फसल जानकारी भरें — AI सुझाव मिलेगा।"
                      : "Fill in your crop details above to get a personalised recommendation."}
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
