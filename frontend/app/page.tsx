"use client";

import Link from "next/link";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";

export default function HomePage() {
  const { language, t, changeLanguage } = useLanguage();

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white">
      <Header language={language} onLanguageChange={changeLanguage} />

      {/* Hero */}
      <main className="max-w-2xl mx-auto px-4 pt-12 pb-24 text-center">
        <div className="mb-6">
          <span className="text-7xl">🌾</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-3 leading-tight">
          <span className="text-primary-700">KisanSetu</span>{" "}
          <span className="text-earth-500">AI</span>
        </h1>
        <p className="text-xl text-gray-600 mb-2">{t("app.tagline")}</p>
        <p className="text-sm text-gray-400 mb-10">
          AI-powered cotton &amp; groundnut market platform for Gujarat farmers
        </p>

        {/* Demo notice */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-10 text-sm text-amber-700">
          <strong>⚠️ Phase 1 Foundation</strong> — Demo data only. IBM Granite AI integration coming in Phase 2.
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Link
            href="/farmer/dashboard"
            className="bg-primary-600 text-white text-lg font-semibold px-8 py-4 rounded-2xl hover:bg-primary-700 active:scale-95 transition-all shadow-sm"
          >
            🌿 {t("auth.farmer")} Login
          </Link>
          <Link
            href="/login"
            className="border-2 border-primary-600 text-primary-700 text-lg font-semibold px-8 py-4 rounded-2xl hover:bg-primary-50 active:scale-95 transition-all"
          >
            {t("auth.login")}
          </Link>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-left">
          {[
            { icon: "📊", title: "Live Prices", desc: "Real-time mandi prices for cotton & groundnut" },
            { icon: "🤝", title: "Direct Buyers", desc: "Connect with verified buyers, skip middlemen" },
            { icon: "💡", title: "AI Advisor", desc: "IBM Granite-powered sell/store recommendations" },
            { icon: "🌾", title: "Quality Grading", desc: "AI-assisted crop quality assessment" },
            { icon: "💰", title: "Income Dashboard", desc: "See expected earnings before you sell" },
            { icon: "🗣️", title: "Multilingual", desc: "English, ગુજરાતી, हिन्दी support" },
          ].map((feature) => (
            <div key={feature.title} className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
              <span className="text-2xl">{feature.icon}</span>
              <p className="font-semibold text-gray-800 text-sm mt-2">{feature.title}</p>
              <p className="text-xs text-gray-500 mt-1 leading-snug">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Agent architecture teaser */}
        <div className="mt-12 bg-indigo-50 rounded-2xl p-6 border border-indigo-100 text-left">
          <h3 className="font-bold text-indigo-800 mb-3">🤖 AI Agent Architecture (Phase 2)</h3>
          <div className="space-y-2 text-sm text-indigo-700">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
              MandiForecastAgent — Price trend prediction
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
              BuyerMatchingAgent — Intelligent buyer matching
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
              StorageAdvisorAgent — Sell or store decisions
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
              QualityGradingAgent — Crop quality assessment
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
              IncomeDashboardAgent — Financial projections
            </div>
          </div>
          <p className="text-xs text-indigo-500 mt-3">All agents powered by IBM Granite on IBM Cloud</p>
        </div>
      </main>
    </div>
  );
}
