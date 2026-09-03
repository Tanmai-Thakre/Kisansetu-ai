"use client";

// Phase 4 — MatchScoreBar: visual 100-point score display component

interface MatchScoreBarProps {
  score: number;        // 0–100
  size?: "sm" | "md";
}

function scoreColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 60) return "bg-amber-400";
  if (score >= 40) return "bg-orange-400";
  return "bg-red-400";
}

function scoreLabel(score: number): string {
  if (score >= 85) return "Excellent Match";
  if (score >= 70) return "Good Match";
  if (score >= 50) return "Partial Match";
  return "Low Match";
}

export function MatchScoreBar({ score, size = "md" }: MatchScoreBarProps) {
  const color = scoreColor(score);
  const label = scoreLabel(score);
  const h = size === "sm" ? "h-1.5" : "h-2";

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-gray-600">
          Match Score
        </span>
        <span className={`text-xs font-bold ${score >= 70 ? "text-green-700" : score >= 50 ? "text-amber-700" : "text-red-600"}`}>
          {score.toFixed(0)}/100 — {label}
        </span>
      </div>
      <div className={`w-full ${h} bg-gray-100 rounded-full overflow-hidden`}>
        <div
          className={`${h} ${color} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    </div>
  );
}


interface ScoreBreakdown {
  crop: number;
  quality: number;
  price: number;
  location: number;
  quantity: number;
  delivery: number;
}

interface MatchScoreDetailProps {
  breakdown: ScoreBreakdown;
}

const SCORE_ITEMS = [
  { key: "crop",     label: "Crop",     max: 30, icon: "🌿" },
  { key: "quality",  label: "Quality",  max: 20, icon: "⭐" },
  { key: "price",    label: "Price",    max: 20, icon: "₹" },
  { key: "location", label: "Location", max: 15, icon: "📍" },
  { key: "quantity", label: "Quantity", max: 10, icon: "📦" },
  { key: "delivery", label: "Delivery", max:  5, icon: "📅" },
] as const;

export function MatchScoreDetail({ breakdown }: MatchScoreDetailProps) {
  return (
    <div className="space-y-1.5">
      {SCORE_ITEMS.map(item => {
        const val = breakdown[item.key];
        const pct = (val / item.max) * 100;
        const color = pct >= 80 ? "bg-green-400" : pct >= 50 ? "bg-amber-400" : "bg-red-300";
        return (
          <div key={item.key} className="flex items-center gap-2">
            <span className="text-xs w-4">{item.icon}</span>
            <span className="text-xs text-gray-500 w-14">{item.label}</span>
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs font-semibold text-gray-600 w-10 text-right">
              {val.toFixed(0)}/{item.max}
            </span>
          </div>
        );
      })}
    </div>
  );
}
