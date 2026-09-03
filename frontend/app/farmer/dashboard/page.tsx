"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { SideNav, BottomNav } from "@/components/layout/Navigation";
import { MarketSnapshot } from "@/components/dashboard/MarketSnapshot";
import { PriceTrendChart } from "@/components/dashboard/PriceTrendChart";
import { BestBuyerCard } from "@/components/dashboard/BestBuyerCard";
import { AIRecommendationCard } from "@/components/dashboard/AIRecommendationCard";
import { QuickActions } from "@/components/dashboard/QuickActions";
import api, { endpoints, fetchQualityHistory, fetchIncomePreview } from "@/lib/api";
import { AIChatWidget } from "@/components/dashboard/AIChatWidget";
import { DemoPanel } from "@/components/dashboard/DemoPanel";
import type { FarmerDashboardResponse, QualityHistoryItem, QualityGradeLevel, IncomeResponse } from "@/types";

// Demo fallback data (used if API is not running)
const DEMO_FALLBACK: FarmerDashboardResponse = {
  farmer_name: "Rameshbhai Patel",
  cotton: {
    crop: "cotton",
    latest_modal_price: 7200,
    latest_date: new Date().toISOString().split("T")[0],
    district: "Rajkot",
    mandi: "Rajkot APMC",
    change_percent: 1.4,
    trend: "up",
    source: "DEMO DATA",
  },
  groundnut: {
    crop: "groundnut",
    latest_modal_price: 6100,
    latest_date: new Date().toISOString().split("T")[0],
    district: "Rajkot",
    mandi: "Rajkot APMC",
    change_percent: -0.8,
    trend: "down",
    source: "DEMO DATA",
  },
  price_trend: Array.from({ length: 30 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (29 - i));
    const label = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return [
      { date: label, price: 7000 + Math.round(Math.sin(i / 3) * 200 + Math.random() * 100), crop: "cotton" as const },
      { date: label, price: 5900 + Math.round(Math.cos(i / 3) * 150 + Math.random() * 80), crop: "groundnut" as const },
    ];
  }).flat(),
  best_buyer: {
    id: 1,
    company_name: "Ahmedabad Textile Corp",
    location: "Ahmedabad, Gujarat",
    verified: true,
    crop: "cotton",
    offered_price: 7450,
    min_quantity: 300,
    max_quantity: 3000,
    quality_requirement: "A",
    note: "DEMO DATA",
  },
  ai_recommendation: {
    title: "AI Selling Advisor",
    message: "AI recommendations will appear here once IBM Granite integration is complete.",
    status: "pending_integration",
  },
  quick_actions: [],
  note: "⚠️ DEMO DATA — Phase 1 Foundation",
};

function gradeColor(grade: QualityGradeLevel) {
  switch (grade) {
    case "EXCELLENT": return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "GOOD":      return "text-blue-700    bg-blue-50    border-blue-200";
    case "AVERAGE":   return "text-amber-700   bg-amber-50   border-amber-200";
    case "POOR":      return "text-red-700     bg-red-50     border-red-200";
    default:          return "text-gray-700    bg-gray-50    border-gray-200";
  }
}

export default function FarmerDashboardPage() {
  const { language, t, changeLanguage } = useLanguage();
  const [data, setData] = useState<FarmerDashboardResponse>(DEMO_FALLBACK);
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<"connected" | "demo">("demo");

  // Phase 6 — Quality snapshot
  const [qualityLatest, setQualityLatest] = useState<QualityHistoryItem | null>(null);

  // Phase 7 — Income snapshot
  const [incomeSnap, setIncomeSnap] = useState<IncomeResponse | null>(null);

  useEffect(() => {
    api
      .get(endpoints.farmerDashboard)
      .then((res) => {
        setData(res.data);
        setApiStatus("connected");
      })
      .catch(() => {
        // API not running — use demo fallback silently
        setApiStatus("demo");
      })
      .finally(() => setLoading(false));

    // Fetch latest quality assessment for dashboard widget
    fetchQualityHistory(1, 1)
      .then(res => {
        if (res.items.length > 0) setQualityLatest(res.items[0]);
      })
      .catch(() => {/* quality data optional */});

    // Fetch income snapshot for dashboard widget (cotton, 100 qtl default)
    fetchIncomePreview("cotton", 100)
      .then(res => setIncomeSnap(res))
      .catch(() => {/* income data optional */});
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        language={language}
        onLanguageChange={changeLanguage}
        farmerName={data.farmer_name}
        role="farmer"
      />

      <div className="flex">
        <SideNav />

        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">
          {/* Greeting */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {language === "gu" ? "નમસ્તે" : language === "hi" ? "नमस्ते" : "Hello"}, {data.farmer_name.split(" ")[0]}! 👋
              </h2>
              <p className="text-sm text-gray-500">Gujarat • {new Date().toLocaleDateString(language === "en" ? "en-IN" : "hi-IN", { weekday: "long", day: "numeric", month: "long" })}</p>
            </div>
            {apiStatus === "demo" && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full font-medium border border-amber-200">
                ○ {t("status.demo")}
              </span>
            )}
          </div>

          {/* Market Snapshot */}
          <MarketSnapshot
            cotton={data.cotton}
            groundnut={data.groundnut}
            t={t}
          />

          {/* Quick Actions */}
          <QuickActions t={t} />

          {/* AI Recommendation */}
          <AIRecommendationCard recommendation={data.ai_recommendation} t={t} />

          {/* Best Buyer */}
          <BestBuyerCard buyer={data.best_buyer} t={t} />

          {/* Price Trend Chart */}
          <PriceTrendChart data={data.price_trend} t={t} />

          {/* Phase 6 — Crop Quality widget */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-800">🔬 {t("quality.title")}</h3>
              <Link
                href="/farmer/quality"
                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                {t("quality.assess")} →
              </Link>
            </div>
            {qualityLatest ? (
              <div className={`rounded-xl border p-3 ${gradeColor(qualityLatest.grade)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold capitalize">{qualityLatest.crop}</p>
                    <p className="text-xs mt-0.5 opacity-80">
                      {t("quality.grade")}: <strong>{qualityLatest.grade}</strong> &nbsp;·&nbsp; {t("quality.score")}: {qualityLatest.quality_score}/100
                    </p>
                  </div>
                  <Link
                    href="/farmer/quality"
                    className="text-xs px-3 py-1.5 rounded-lg bg-white bg-opacity-60 font-medium border border-current hover:bg-opacity-80 transition-colors"
                  >
                    {t("quality.history")}
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-center py-3">
                <p className="text-sm text-gray-400">{t("quality.no_assessment")}</p>
                <Link
                  href="/farmer/quality"
                  className="mt-2 inline-block text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  {t("quality.assess")} →
                </Link>
              </div>
            )}
          </div>

          {/* Phase 7 — Income Snapshot widget */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-800">💰 {t("income.title")}</h3>
              <Link
                href="/farmer/income"
                className="text-xs text-green-600 hover:text-green-800 font-medium"
              >
                {t("actions.view_income")} →
              </Link>
            </div>
            {incomeSnap ? (
              <div>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-400">{t("income.net_income")}</p>
                    <p className="text-lg font-black text-gray-900">
                      ₹{Math.round(incomeSnap.best_net_income ?? incomeSnap.current_estimated_income).toLocaleString("en-IN")}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{t("market.cotton")} · 100 {language === "gu" ? "ક્વિ" : language === "hi" ? "क्वि" : "qtl"}</p>
                  </div>
                  <div className="bg-green-50 rounded-xl p-3 border border-green-100">
                    <p className="text-xs text-green-600">{t("income.best_scenario")}</p>
                    <p className="text-sm font-bold text-green-800 leading-tight mt-0.5">
                      {incomeSnap.best_scenario ?? "—"}
                    </p>
                    <p className="text-xs text-green-600 mt-0.5">
                      {t("income.diff_vs_now")}: ₹{Math.round(incomeSnap.income_difference).toLocaleString("en-IN")}
                    </p>
                  </div>
                </div>
                <Link
                  href="/farmer/income"
                  className="block w-full text-center text-xs text-green-700 font-semibold bg-green-50 border border-green-200 rounded-xl py-2 hover:bg-green-100 transition-colors"
                >
                  📊 {t("actions.view_income")}
                </Link>
              </div>
            ) : (
              <div className="text-center py-3">
                <p className="text-sm text-gray-400">{t("income.no_income")}</p>
                <Link
                  href="/farmer/income"
                  className="mt-2 inline-block text-xs text-green-600 hover:text-green-800 font-medium"
                >
                  {t("actions.view_income")} →
                </Link>
              </div>
            )}
          </div>

          {/* Phase 8 — AI Chat widget */}
          <AIChatWidget
            language={language}
            farmerId={1}
            crop="cotton"
            mandi="Rajkot APMC"
            quantity={100}
            compact
          />

          {/* Phase 9 — Demo Panel */}
          <DemoPanel language={language} />

          {/* Demo notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-sm text-amber-700" role="status">
            <strong>⚠️ {t("status.demo")}</strong> — {t("demo.notice")}
          </div>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
