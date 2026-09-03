"use client";

// Phase 9 — /farmer/buyers: Ranked buyer marketplace (improved UX + translations)

import { useEffect, useState, useCallback } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { BuyerMatchCard } from "@/components/buyers/BuyerMatchCard";
import api, { endpoints } from "@/lib/api";
import type { BuyerMatch, BuyerMatchResponse } from "@/types";

const CROPS    = [
  { value: "cotton",    en: "🌿 Cotton",    gu: "🌿 કપાસ",   hi: "🌿 कपास" },
  { value: "groundnut", en: "🥜 Groundnut", gu: "🥜 મગફળી", hi: "🥜 मूंगफली" },
];
const GRADES   = ["", "A", "B", "C"];
const DISTRICTS = ["", "Rajkot", "Amreli", "Junagadh", "Bhavnagar", "Ahmedabad", "Surendranagar", "Jamnagar"];

// Demo farmer id for Phase 4 (no auth yet)
const DEMO_FARMER_ID = 1;

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map(i => (
        <div key={i} className="h-48 bg-gray-100 rounded-2xl" />
      ))}
    </div>
  );
}

export default function BuyersPage() {
  const { language, t, changeLanguage } = useLanguage();

  // Filters
  const [crop,     setCrop]     = useState("cotton");
  const [quantity, setQuantity] = useState(150);
  const [quality,  setQuality]  = useState("");
  const [district, setDistrict] = useState("");

  // Data
  const [result,   setResult]   = useState<BuyerMatchResponse | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  // Track which buyer_ids the farmer has already sent a request to
  const [requested, setRequested] = useState<Set<number>>(new Set());
  const [toast,     setToast]     = useState("");

  const fetchMatches = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params: Record<string, unknown> = { crop, quantity, top_n: 12 };
      if (quality)  params.quality  = quality;
      if (district) params.district = district;
      const res = await api.get(endpoints.buyerMatches, { params });
      setResult(res.data as BuyerMatchResponse);
    } catch {
      setError(t("errors.api_unavailable"));
    } finally {
      setLoading(false);
    }
  }, [crop, quantity, quality, district, t]);

  useEffect(() => { fetchMatches(); }, [fetchMatches]);

  const handleRequest = async (match: BuyerMatch) => {
    try {
      await api.post(endpoints.buyerRequest, {
        farmer_id:     DEMO_FARMER_ID,
        buyer_id:      match.buyer_id,
        crop:          crop,
        quantity:      quantity,
        offered_price: match.offered_price,
        match_score:   match.match_score,
        message:       `Interested in selling ${quantity} qtl of ${crop}. Grade: ${quality || "ungraded"}.`,
      });
      setRequested(prev => new Set(prev).add(match.buyer_id));
      setToast(`✓ ${t("buyers.request_sent")} — ${match.buyer_name}`);
      setTimeout(() => setToast(""), 3500);
    } catch {
      setToast(`⚠️ ${t("errors.api_unavailable")}`);
      setTimeout(() => setToast(""), 3500);
    }
  };

  const marketPrice = result?.market_price;

  const cropLabel = CROPS.find(c => c.value === crop)?.[language as "en"|"gu"|"hi"] ?? crop;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Rameshbhai Patel" role="farmer" />
      <div className="flex">
        <SideNav />
        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">

          {/* Header */}
          <div>
            <h1 className="text-xl font-bold text-gray-900">🤝 {t("buyers.title")}</h1>
            <p className="text-sm text-gray-500 mt-0.5">{t("buyers.match_score")} — 100 {language === "gu" ? "પોઈન્ટ" : language === "hi" ? "पॉइंट" : "point"}</p>
          </div>

          {/* Filters */}
          <Card>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="buyers-crop" className="block text-xs font-medium text-gray-500 mb-1.5">
                    {t("advisor.crop")}
                  </label>
                  <select id="buyers-crop" value={crop} onChange={e => setCrop(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {CROPS.map(c => (
                      <option key={c.value} value={c.value}>{c[language as "en"|"gu"|"hi"] ?? c.en}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="buyers-qty" className="block text-xs font-medium text-gray-500 mb-1.5">
                    {t("income.quantity")}
                  </label>
                  <input id="buyers-qty" type="number" value={quantity} min={1}
                    onChange={e => setQuantity(Number(e.target.value) || 100)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                </div>
                <div>
                  <label htmlFor="buyers-grade" className="block text-xs font-medium text-gray-500 mb-1.5">
                    {t("buyers.quality")}
                  </label>
                  <select id="buyers-grade" value={quality} onChange={e => setQuality(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {GRADES.map(g => (
                      <option key={g} value={g}>{g || (language === "gu" ? "ગ્રેડ નથી" : language === "hi" ? "ग्रेड नहीं" : "Not graded")}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="buyers-district" className="block text-xs font-medium text-gray-500 mb-1.5">
                    {t("buyers.location")}
                  </label>
                  <select id="buyers-district" value={district} onChange={e => setDistrict(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {DISTRICTS.map(d => (
                      <option key={d} value={d}>{d || (language === "gu" ? "કોઈ પણ" : language === "hi" ? "कोई भी" : "Any district")}</option>
                    ))}
                  </select>
                </div>
              </div>
              <Button variant="primary" size="md" fullWidth className="mt-3"
                onClick={fetchMatches} disabled={loading}>
                {loading
                  ? (language === "gu" ? "મળી રહ્યા છે..." : language === "hi" ? "खोज रहे हैं..." : "Finding matches…")
                  : `🔍 ${t("buyers.find")}`
                }
              </Button>
            </CardContent>
          </Card>

          {/* Market price context */}
          {marketPrice && (
            <div className="flex items-center gap-3 bg-white border border-gray-100 rounded-2xl px-4 py-3">
              <span className="text-xl" aria-hidden="true">{crop === "cotton" ? "🌿" : "🥜"}</span>
              <div>
                <p className="text-xs text-gray-500">{t("market.current_price")} — {cropLabel}</p>
                <p className="text-base font-bold text-gray-900">₹{marketPrice.toLocaleString("en-IN")}/{t("market.per_quintal")}</p>
              </div>
              <span className="ml-auto text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full font-medium border border-amber-200">
                ○ {t("status.demo")}
              </span>
            </div>
          )}

          {/* Results summary */}
          {result && !loading && (
            <p className="text-sm text-gray-500 font-medium">
              {result.total_found} {t("buyers.all_buyers").toLowerCase()}
              {district ? ` — ${district}` : ""}
            </p>
          )}

          {/* Error */}
          {error && (
            <Card>
              <CardContent>
                <div className="text-center py-6">
                  <p className="text-2xl mb-2" aria-hidden="true">⚠️</p>
                  <p className="text-sm text-gray-600">{error}</p>
                  <Button variant="outline" size="sm" className="mt-3" onClick={fetchMatches}>
                    {t("app.retry")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Loading */}
          {loading && <LoadingSkeleton />}

          {/* Match cards */}
          {!loading && result && result.matches.length > 0 && (
            <div className="space-y-4">
              {result.matches.map(match => (
                <BuyerMatchCard
                  key={match.buyer_id}
                  match={match}
                  farmerId={DEMO_FARMER_ID}
                  crop={crop}
                  quantity={quantity}
                  onRequest={handleRequest}
                  requested={requested.has(match.buyer_id)}
                />
              ))}
            </div>
          )}

          {/* No results */}
          {!loading && result && result.matches.length === 0 && (
            <Card>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-3xl mb-2" aria-hidden="true">🔍</p>
                  <p className="font-semibold text-gray-700">{t("buyers.no_buyers")}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {language === "gu" ? "ડિસ્ટ્રિક્ટ ફિલ્ટર હટાવો અથવા પાક બદલો." : language === "hi" ? "जिला फ़िल्टर हटाएं या फसल बदलें।" : "Try removing the district filter or changing crop."}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Responsible AI + DEMO notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-3 text-xs text-amber-700" role="note">
            ○ <strong>{t("status.demo")}</strong> — {t("buyers.disclaimer")}
          </div>

        </main>
      </div>

      {/* Toast */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className={`fixed bottom-24 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-2xl shadow-lg text-sm font-semibold animate-fade-in ${
            toast.startsWith("⚠️") ? "bg-amber-600 text-white" : "bg-green-600 text-white"
          }`}
        >
          {toast}
        </div>
      )}

      <BottomNav />
    </div>
  );
}
