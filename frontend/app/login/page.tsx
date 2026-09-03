"use client";

import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  const { language, t, changeLanguage } = useLanguage();
  const [role, setRole] = useState<"farmer" | "buyer">("farmer");

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} />
      <main className="max-w-md mx-auto px-4 pt-10 pb-20">
        <div className="text-center mb-8">
          <span className="text-5xl">{role === "farmer" ? "🌾" : "🏢"}</span>
          <h1 className="text-2xl font-bold text-gray-900 mt-3">{t("auth.login")}</h1>
          <p className="text-gray-500 text-sm mt-1">Welcome back to KisanSetu AI</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          {/* Role selector */}
          <div className="flex rounded-xl overflow-hidden border border-gray-200 mb-6">
            {(["farmer", "buyer"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRole(r)}
                className={`flex-1 py-2.5 text-sm font-semibold transition-colors ${
                  role === r ? "bg-primary-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                {r === "farmer" ? "🌾 " : "🏢 "}
                {t(`auth.${r}`)}
              </button>
            ))}
          </div>

          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                {t("auth.phone")}
              </label>
              <input
                type="tel"
                placeholder="9876543210"
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                {t("auth.password")}
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>

            <Link
              href={role === "farmer" ? "/farmer/dashboard" : "/buyer/dashboard"}
              className="block"
            >
              <Button variant="primary" size="lg" fullWidth>
                {t("auth.login")}
              </Button>
            </Link>
          </form>

          <p className="text-center text-sm text-gray-500 mt-5">
            {t("auth.no_account")}{" "}
            <Link href="/register" className="text-primary-600 font-semibold hover:underline">
              {t("auth.register")}
            </Link>
          </p>

          <div className="mt-5 p-3 bg-amber-50 rounded-xl border border-amber-100">
            <p className="text-xs text-amber-700">
              <strong>Demo:</strong> Use any phone/password to access the dashboard.
              Authentication will be fully implemented in Phase 2.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
