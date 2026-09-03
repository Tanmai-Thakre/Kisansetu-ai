"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const FARMER_NAV: NavItem[] = [
  { href: "/farmer/dashboard", label: "Dashboard", icon: "🏠" },
  { href: "/farmer/market",    label: "Market",    icon: "📊" },
  { href: "/farmer/buyers",    label: "Buyers",    icon: "🤝" },
  { href: "/farmer/advisor",   label: "Advisor",   icon: "💡" },
  { href: "/farmer/quality",   label: "Quality",   icon: "🌾" },
  { href: "/farmer/income",    label: "Income",    icon: "💰" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 z-40 shadow-lg sm:hidden">
      <div className="flex">
        {FARMER_NAV.slice(0, 5).map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex-1 flex flex-col items-center py-2 text-xs transition-colors",
              pathname === item.href
                ? "text-primary-600 font-semibold"
                : "text-gray-500 hover:text-primary-500"
            )}
          >
            <span className="text-lg mb-0.5">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}

export function SideNav() {
  const pathname = usePathname();

  return (
    <aside className="hidden sm:flex flex-col w-56 bg-white border-r border-gray-100 min-h-screen py-6 px-3 gap-1">
      <div className="px-3 mb-4">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Navigation</p>
      </div>
      {FARMER_NAV.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
            pathname === item.href
              ? "bg-primary-50 text-primary-700"
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
          )}
        >
          <span className="text-lg">{item.icon}</span>
          {item.label}
        </Link>
      ))}
    </aside>
  );
}
