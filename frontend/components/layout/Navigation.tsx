"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/hooks/useLanguage";

interface NavItem {
  href: string;
  labelKey: string;
  icon: string;
}

const FARMER_NAV: NavItem[] = [
  { href: "/farmer/dashboard", labelKey: "nav.dashboard", icon: "🏠" },
  { href: "/farmer/market",    labelKey: "nav.market",    icon: "📊" },
  { href: "/farmer/buyers",    labelKey: "nav.buyers",    icon: "🤝" },
  { href: "/farmer/advisor",   labelKey: "nav.advisor",   icon: "💡" },
  { href: "/farmer/quality",   labelKey: "nav.quality",   icon: "🌾" },
  { href: "/farmer/income",    labelKey: "nav.income",    icon: "💰" },
  { href: "/farmer/chat",      labelKey: "nav.ai_chat",   icon: "🤖" },
];

export function BottomNav() {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 z-40 shadow-lg sm:hidden"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex">
        {FARMER_NAV.slice(0, 5).map((item) => (
          <Link
            key={item.href}
            href={item.href}
            aria-label={t(item.labelKey)}
            aria-current={pathname === item.href ? "page" : undefined}
            className={cn(
              "flex-1 flex flex-col items-center py-2.5 text-xs transition-colors min-h-[56px] justify-center",
              pathname === item.href
                ? "text-primary-600 font-semibold"
                : "text-gray-500 hover:text-primary-500"
            )}
          >
            <span className="text-xl mb-0.5" aria-hidden="true">{item.icon}</span>
            <span className="truncate max-w-[52px] text-center">{t(item.labelKey)}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}

export function SideNav() {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <aside
      className="hidden sm:flex flex-col w-56 bg-white border-r border-gray-100 min-h-screen py-6 px-3 gap-1 shrink-0"
      role="navigation"
      aria-label="Sidebar navigation"
    >
      <div className="px-3 mb-4">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          {t("nav.dashboard") !== "nav.dashboard" ? "—" : "Navigation"}
        </p>
      </div>
      {FARMER_NAV.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          aria-current={pathname === item.href ? "page" : undefined}
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
            pathname === item.href
              ? "bg-primary-50 text-primary-700"
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
          )}
        >
          <span className="text-lg" aria-hidden="true">{item.icon}</span>
          {t(item.labelKey)}
        </Link>
      ))}
    </aside>
  );
}
