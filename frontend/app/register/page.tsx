"use client";

import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";

export default function RegisterPage() {
  const { language, t, changeLanguage } = useLanguage();
  const [role, setRole] = useState<"farmer" | "buyer">("farmer");

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} />
      <main className="max-w-md mx-auto px-4 pt-10 pb-20">
        <div className="text-center mb-8">
          <span className="text-5xl">{role === "farmer" ? "🌾" : "🏢"}</span>
          <h1 className="text-2xl font-bold text-gray-900 mt-3">{t("auth.register")}</h1>
          <p className="text-gray-500 text-sm mt-1">Join KisanSetu AI today</p>
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
              <label className="block text-sm font-medium text-gray-700 mb-1.5">{t("auth.name")}</label>
              <input
                type="text"
                placeholder={role === "farmer" ? "Rameshbhai Patel" : "Company Name"}
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">{t("auth.phone")}</label>
              <input
                type="tel"
                placeholder="9876543210"
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
            {role === "farmer" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">{t("profile.district")}</label>
                <select className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-400">
                  {["Rajkot", "Amreli", "Junagadh", "Bhavnagar", "Surendranagar", "Jamnagar", "Ahmedabad"].map(d => (
                    <option key={d}>{d}</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">{t("auth.password")}</label>
              <input
                type="password"
                placeholder="Create a password"
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>

            <Link href={role === "farmer" ? "/farmer/dashboard" : "/buyer/dashboard"} className="block">
              <Button variant="primary" size="lg" fullWidth>
                {t("auth.register")}
              </Button>
            </Link>
          </form>

          <p className="text-center text-sm text-gray-500 mt-5">
            {t("auth.already_have_account")}{" "}
            <Link href="/login" className="text-primary-600 font-semibold hover:underline">
              {t("auth.login")}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
