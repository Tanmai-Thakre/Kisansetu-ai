"use client";

import Link from "next/link";
import { useState } from "react";
import type { Language } from "@/types";

interface HeaderProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  farmerName?: string;
  role?: "farmer" | "buyer" | "admin" | "public";
}

const LANGUAGES: { code: Language; label: string; flag: string }[] = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "gu", label: "ગુજરાતી", flag: "🇮🇳" },
  { code: "hi", label: "हिन्दी",  flag: "🇮🇳" },
];

export function Header({ language, onLanguageChange, farmerName, role = "public" }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 select-none">
          <span className="text-2xl">🌾</span>
          <div>
            <span className="text-lg font-bold text-primary-700 leading-none">KisanSetu</span>
            <span className="text-lg font-bold text-earth-500 leading-none"> AI</span>
          </div>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Language Selector */}
          <div className="relative">
            <select
              value={language}
              onChange={(e) => onLanguageChange(e.target.value as Language)}
              className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg px-3 py-1.5 pr-7 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.flag} {l.label}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-gray-400">
              ▾
            </div>
          </div>

          {/* Farmer Avatar */}
          {farmerName && (
            <div className="hidden sm:flex items-center gap-2 bg-primary-50 rounded-full px-3 py-1.5">
              <div className="w-7 h-7 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                {farmerName.charAt(0)}
              </div>
              <span className="text-sm font-medium text-primary-800 max-w-[120px] truncate">
                {farmerName}
              </span>
            </div>
          )}

          {!farmerName && (
            <Link
              href="/login"
              className="text-sm font-medium text-primary-700 hover:text-primary-900 bg-primary-50 px-3 py-1.5 rounded-lg"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
