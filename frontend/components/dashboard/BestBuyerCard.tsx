"use client";

// Phase 4 — BestBuyerCard: upgraded to show Phase 4 match score + price advantage.

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatPrice } from "@/lib/utils";
import { MatchScoreBar } from "@/components/buyers/MatchScoreBar";
import api, { endpoints } from "@/lib/api";
import type { BuyerListItem, BuyerMatch } from "@/types";

interface BestBuyerCardProps {
  buyer?: BuyerListItem;
  t: (key: string) => string;
}

export function BestBuyerCard({ buyer: fallbackBuyer, t }: BestBuyerCardProps) {
  const [topMatch, setTopMatch]   = useState<BuyerMatch | null>(null);
  const [loading,  setLoading]    = useState(true);

  useEffect(() => {
    api.get(endpoints.buyerMatches, {
      params: { crop: "cotton", quantity: 150, quality: "A", district: "Rajkot", top_n: 1 },
    })
      .then(res => {
        const matches: BuyerMatch[] = res.data?.matches ?? [];
        if (matches.length > 0) setTopMatch(matches[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Loading skeleton
  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>🤝 {t("buyers.best_buyer")}</CardTitle></CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            <div className="h-3 bg-gray-100 rounded w-3/4" />
            <div className="h-3 bg-gray-100 rounded w-1/2" />
            <div className="h-2 bg-gray-100 rounded mt-3" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Phase 4 match data available
  if (topMatch) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <CardTitle>🤝 Best Buyer Match</CardTitle>
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full font-medium">
              DEMO DATA
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Buyer info */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="font-semibold text-gray-900 text-sm truncate">{topMatch.buyer_name}</p>
                {topMatch.verified && <Badge variant="green">✓ Verified</Badge>}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                📍 {topMatch.location ?? "Gujarat"}
                {topMatch.distance_km != null ? ` · ~${topMatch.distance_km.toFixed(0)} km` : ""}
              </p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-xl font-bold text-primary-700">
                {topMatch.offered_price ? formatPrice(topMatch.offered_price) : "—"}
              </p>
              <p className="text-xs text-gray-400">per quintal</p>
            </div>
          </div>

          {/* Price vs market */}
          {topMatch.price_vs_market === "ABOVE_MARKET" && topMatch.price_advantage != null && (
            <div className="bg-green-50 rounded-xl px-3 py-2 border border-green-100 text-xs text-green-700 font-semibold">
              ↑ ₹{Math.abs(topMatch.price_advantage).toFixed(0)}/q above current market price
            </div>
          )}

          {/* Match score */}
          <MatchScoreBar score={topMatch.match_score} size="sm" />

          {/* CTA */}
          <Link href="/farmer/buyers">
            <Button variant="primary" size="sm" fullWidth className="mt-1">
              View All Buyers →
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  // Fallback: Phase 1 buyer data (API not running)
  if (!fallbackBuyer) {
    return (
      <Card>
        <CardHeader><CardTitle>🤝 {t("buyers.best_buyer")}</CardTitle></CardHeader>
        <CardContent>
          <p className="text-gray-400 text-sm">Start the backend to see matched buyers.</p>
          <Link href="/farmer/buyers">
            <Button variant="outline" size="sm" fullWidth className="mt-3">Find Buyers</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>🤝 {t("buyers.best_buyer")}</CardTitle>
          <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full font-medium">DEMO DATA</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-semibold text-gray-900 text-sm truncate">{fallbackBuyer.company_name}</p>
              {fallbackBuyer.verified && <Badge variant="green">✓ {t("buyers.verified")}</Badge>}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">📍 {fallbackBuyer.location}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-xl font-bold text-primary-700">
              {fallbackBuyer.offered_price ? formatPrice(fallbackBuyer.offered_price) : "—"}
            </p>
            <p className="text-xs text-gray-400">per quintal</p>
          </div>
        </div>
        <Link href="/farmer/buyers">
          <Button variant="outline" size="sm" fullWidth className="mt-4">
            {t("buyers.contact")}
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
