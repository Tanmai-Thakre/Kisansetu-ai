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
    id: "income",
    labelKey: "actions.view_income",
    icon: "💰",
    href: "/farmer/income",
    bg: "bg-emerald-600 hover:bg-emerald-700",
    text: "text-white",
  },
  {
    id: "ai",
    labelKey: "actions.ask_kisansetu_ai",
    icon: "🤖",
    href: "/farmer/chat",
    bg: "bg-indigo-600 hover:bg-indigo-700",
    text: "text-white",
    wide: true,
  },
];

export function QuickActions({ t }: QuickActionsProps) {
  return (
    <div>
      <h3 className="text-base font-semibold text-gray-800 mb-3">⚡ {t("actions.check_market_prices") !== "actions.check_market_prices" ? "" : "Quick "}Actions</h3>
      <div className="grid grid-cols-3 gap-2.5">
        {ACTIONS.map((action) => (
          <Link
            key={action.id}
            href={action.href}
            aria-label={t(action.labelKey)}
            className={cn(
              "flex flex-col items-center justify-center gap-1.5 p-3 rounded-2xl transition-all duration-200 active:scale-95 shadow-sm min-h-[80px]",
              action.bg,
              action.text,
              (action as { wide?: boolean }).wide ? "col-span-3" : ""
            )}
          >
            <span className="text-2xl" aria-hidden="true">{action.icon}</span>
            <span className="text-xs font-semibold text-center leading-snug">
              {t(action.labelKey)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
