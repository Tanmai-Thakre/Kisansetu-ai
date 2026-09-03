"use client";

// Phase 4 — /farmer/buyers: Ranked buyer marketplace with match scores,
// price comparison, "Why this buyer?", and Send Request flow.

import { useEffect, useState, useCallback } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { BuyerMatchCard } from "@/components/buyers/BuyerMatchCard";
import api, { endpoints } from "@/lib/api";
import type { BuyerMatch, BuyerMatchResponse } from "@/types";

const CROPS    = [{ value: "cotton", label: "🌿 Cotton" }, { value: "groundnut", label: "🥜 Groundnut" }];
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
      setError("Could not load buyers. Start the backend to see matching results.");
    } finally {
      setLoading(false);
    }
  }, [crop, quantity, quality, district]);

  useEffect(() => { fetchMatches(); }, [fetchMatches]);

  const handleRequest = async (match: BuyerMatch) => {
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
    setToast(`✓ Request sent to ${match.buyer_name}`);
    setTimeout(() => setToast(""), 3500);
  };

  const marketPrice = result?.market_price;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Rameshbhai Patel" role="farmer" />
      <div className="flex">
        <SideNav />
        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">

          {/* Header */}
          <div className="flex items-start justify-between flex-wrap gap-2">
            <div>
              <h1 className="text-xl font-bold text-gray-900">🤝 Find Buyers</h1>
              <p className="text-sm text-gray-500 mt-0.5">Ranked by 100-point match score</p>
            </div>
            <Badge variant="purple">Phase 4 Active</Badge>
          </div>

          {/* Filters */}
          <Card>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Crop</label>
                  <select value={crop} onChange={e => setCrop(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {CROPS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Quantity (qtl)</label>
                  <input type="number" value={quantity} min={1}
                    onChange={e => setQuantity(Number(e.target.value) || 100)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Your Grade</label>
                  <select value={quality} onChange={e => setQuality(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {GRADES.map(g => <option key={g} value={g}>{g || "Not graded"}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Your District</label>
                  <select value={district} onChange={e => setDistrict(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
                    {DISTRICTS.map(d => <option key={d} value={d}>{d || "Any district"}</option>)}
                  </select>
                </div>
              </div>
              <Button variant="primary" size="md" fullWidth className="mt-3"
                onClick={fetchMatches} disabled={loading}>
                {loading ? "Finding matches…" : "🔍 Find Buyers"}
              </Button>
            </CardContent>
          </Card>

          {/* Market price context */}
          {marketPrice && (
            <div className="flex items-center gap-3 bg-white border border-gray-100 rounded-2xl px-4 py-3">
              <span className="text-xl">{crop === "cotton" ? "🌿" : "🥜"}</span>
              <div>
                <p className="text-xs text-gray-500">Current Market Price — {crop === "cotton" ? "Cotton" : "Groundnut"}</p>
                <p className="text-base font-bold text-gray-900">₹{marketPrice.toLocaleString("en-IN")}/qtl</p>
              </div>
              <span className="ml-auto text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full font-medium">
                ⚠️ DEMO DATA
              </span>
            </div>
          )}

          {/* Results summary */}
          {result && !loading && (
            <p className="text-sm text-gray-500 font-medium">
              {result.total_found} buyer{result.total_found !== 1 ? "s" : ""} matched
              {district ? ` near ${district}` : " in Gujarat"}
            </p>
          )}

          {/* Error */}
          {error && (
            <Card>
              <CardContent>
                <div className="text-center py-6">
                  <p className="text-2xl mb-2">⚠️</p>
                  <p className="text-sm text-gray-600">{error}</p>
                  <Button variant="outline" size="sm" className="mt-3" onClick={fetchMatches}>
                    Try Again
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
                <div className="text-center py-6">
                  <p className="text-3xl mb-2">🔍</p>
                  <p className="font-semibold text-gray-700">No buyers found</p>
                  <p className="text-xs text-gray-400 mt-1">Try removing the district filter or changing crop.</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* DEMO notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-3 text-xs text-amber-700">
            ⚠️ <strong>DEMO DATA</strong> — Match scores are deterministic estimates.
            Distance calculated from district centroids — not actual routes.
          </div>

        </main>
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 bg-green-600 text-white px-5 py-3 rounded-2xl shadow-lg text-sm font-semibold animate-fade-in">
          {toast}
        </div>
      )}

      <BottomNav />
    </div>
  );
}
