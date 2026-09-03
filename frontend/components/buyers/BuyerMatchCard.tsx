"use client";

// Phase 4 — BuyerMatchCard: full buyer match card with score, reasons,
// price comparison, and Send Request button.

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { MatchScoreBar, MatchScoreDetail } from "./MatchScoreBar";
import { PriceVsMarketBadge } from "./PriceVsMarket";
import type { BuyerMatch } from "@/types";

interface BuyerMatchCardProps {
  match:       BuyerMatch;
  farmerId:    number;
  crop:        string;
  quantity:    number;
  onRequest:   (match: BuyerMatch) => Promise<void>;
  requested?:  boolean;
}

export function BuyerMatchCard({
  match, farmerId, crop, quantity, onRequest, requested = false,
}: BuyerMatchCardProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showReasons,   setShowReasons]   = useState(false);
  const [sending,       setSending]       = useState(false);
  const [sent,          setSent]          = useState(requested);

  const handleRequest = async () => {
    if (sent || sending) return;
    setSending(true);
    try {
      await onRequest(match);
      setSent(true);
    } catch {
      // error handled by parent
    } finally {
      setSending(false);
    }
  };

  const cropLabel = crop === "cotton" ? "🌿 Cotton" : "🥜 Groundnut";

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {/* Header strip */}
        <div className="flex items-start justify-between px-4 pt-4 pb-3 border-b border-gray-50 gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-bold text-gray-900 text-base leading-tight">{match.buyer_name}</p>
              {match.verified && (
                <Badge variant="green" className="text-xs">✓ Verified</Badge>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              📍 {match.location ?? "Gujarat"} {match.distance_km != null ? `· ~${match.distance_km.toFixed(0)} km` : ""}
            </p>
          </div>
          <div className="text-right shrink-0">
            <span className={`text-xl font-black ${match.match_score >= 75 ? "text-green-700" : match.match_score >= 55 ? "text-amber-700" : "text-gray-600"}`}>
              {match.match_score.toFixed(0)}
            </span>
            <span className="text-xs text-gray-400">/100</span>
          </div>
        </div>

        {/* Body */}
        <div className="px-4 py-3 space-y-3">
          {/* Price */}
          <div className="flex items-start justify-between gap-3">
            <div>
              {match.offered_price ? (
                <PriceVsMarketBadge
                  offeredPrice={match.offered_price}
                  marketPrice={match.market_price ?? null}
                  priceVsMarket={match.price_vs_market}
                  priceAdvantage={match.price_advantage ?? null}
                />
              ) : (
                <span className="text-gray-400 text-sm">Price TBD</span>
              )}
            </div>
            <div className="text-right text-xs text-gray-500">
              <p>{cropLabel}</p>
              {(match.min_quantity || match.max_quantity) && (
                <p>{match.min_quantity ?? 0}–{match.max_quantity ?? "∞"} qtl</p>
              )}
              {match.quality_requirement && (
                <p>Grade {match.quality_requirement}+</p>
              )}
            </div>
          </div>

          {/* Match score bar */}
          <MatchScoreBar score={match.match_score} />

          {/* Score breakdown toggle */}
          <button
            onClick={() => setShowBreakdown(p => !p)}
            className="text-xs text-indigo-600 font-medium hover:underline"
          >
            {showBreakdown ? "▲ Hide breakdown" : "▼ Score breakdown"}
          </button>
          {showBreakdown && (
            <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
              <MatchScoreDetail breakdown={match.breakdown} />
            </div>
          )}

          {/* Why this buyer toggle */}
          <button
            onClick={() => setShowReasons(p => !p)}
            className="text-xs text-indigo-600 font-medium hover:underline"
          >
            {showReasons ? "▲ Hide reasons" : "💡 Why this buyer?"}
          </button>
          {showReasons && (
            <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100 space-y-1">
              {match.reasons.map((r, i) => (
                <p key={i} className="text-xs text-indigo-700">• {r}</p>
              ))}
            </div>
          )}

          {/* Send request button */}
          <Button
            variant={sent ? "outline" : "primary"}
            size="md"
            fullWidth
            disabled={sent || sending}
            onClick={handleRequest}
          >
            {sent ? "✓ Request Sent" : sending ? "Sending…" : "Send Request"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
