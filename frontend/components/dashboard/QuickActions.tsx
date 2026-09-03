"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

interface QuickActionsProps {
  t: (key: string) => string;
}

const ACTIONS = [
  {
    id: "market",
    labelKey: "actions.check_market_prices",
    icon: "📊",
    href: "/farmer/market",
    bg: "bg-green-500 hover:bg-green-600",
    text: "text-white",
  },
  {
    id: "buyers",
    labelKey: "actions.find_buyers",
    icon: "🤝",
    href: "/farmer/buyers",
    bg: "bg-blue-500 hover:bg-blue-600",
    text: "text-white",
  },
  {
    id: "advisor",
    labelKey: "actions.sell_or_store",
    icon: "💡",
    href: "/farmer/advisor",
    bg: "bg-amber-500 hover:bg-amber-600",
    text: "text-white",
  },
  {
    id: "quality",
    labelKey: "actions.check_crop_quality",
    icon: "🌾",
    href: "/farmer/quality",
    bg: "bg-purple-500 hover:bg-purple-600",
    text: "text-white",
  },
  {
    id: "ai",
    labelKey: "actions.ask_kisansetu_ai",
    icon: "🤖",
    href: "/farmer/advisor",
    bg: "bg-indigo-600 hover:bg-indigo-700",
    text: "text-white",
  },
];

export function QuickActions({ t }: QuickActionsProps) {
  return (
    <div>
      <h3 className="text-base font-semibold text-gray-800 mb-3">⚡ Quick Actions</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {ACTIONS.map((action) => (
          <Link
            key={action.id}
            href={action.href}
            className={cn(
              "flex flex-col items-center justify-center gap-2 p-4 rounded-2xl transition-all duration-200 active:scale-95 shadow-sm",
              action.bg,
              action.text,
              action.id === "ai" ? "col-span-2 sm:col-span-1" : ""
            )}
          >
            <span className="text-3xl">{action.icon}</span>
            <span className="text-sm font-semibold text-center leading-snug">
              {t(action.labelKey)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
