"use client";

/**
 * Phase 9 — /farmer/chat: KisanSetu AI Chat Page (fully translated)
 */

import { useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { AIChatWidget } from "@/components/dashboard/AIChatWidget";

const CROPS_LABELS: Record<string, { value: string; label: Record<string, string> }[]> = {
  en: [{ value: "cotton", label: { en: "🌿 Cotton", gu: "🌿 કપાસ", hi: "🌿 कपास" } }, { value: "groundnut", label: { en: "🥜 Groundnut", gu: "🥜 મગફળી", hi: "🥜 मूंगफली" } }],
};

const CROP_OPTIONS = [
  { value: "cotton",    en: "🌿 Cotton",    gu: "🌿 કપાસ",   hi: "🌿 कपास" },
  { value: "groundnut", en: "🥜 Groundnut", gu: "🥜 મગફળી", hi: "🥜 मूंगफली" },
];

const MANDIS = [
  "Rajkot APMC", "Amreli APMC", "Junagadh APMC",
  "Bhavnagar APMC", "Ahmedabad APMC", "Surendranagar APMC", "Jamnagar APMC",
];

const CONTEXT_LABELS: Record<string, { title: string; crop: string; qty: string; mandi: string }> = {
  en: { title: "Your Crop Context",   crop: "Crop",     qty: "Quantity (quintals)", mandi: "Nearest Mandi" },
  gu: { title: "તમારી પાક વિગત",     crop: "પાક",      qty: "જથ્થો (ક્વિન્ટલ)",   mandi: "નજીકની મંડી" },
  hi: { title: "आपकी फसल जानकारी",   crop: "फसल",     qty: "मात्रा (क्विंटल)",    mandi: "नज़दीकी मंडी" },
};

export default function AIChatPage() {
  const { language, t, changeLanguage } = useLanguage();
  const [crop,     setCrop]     = useState("cotton");
  const [mandi,    setMandi]    = useState("Rajkot APMC");
  const [quantity, setQuantity] = useState(100);

  const ctx = CONTEXT_LABELS[language] ?? CONTEXT_LABELS.en;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        language={language}
        onLanguageChange={changeLanguage}
        farmerName="Rameshbhai Patel"
        role="farmer"
      />

      <div className="flex">
        <SideNav />

        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-4">

          {/* Page title */}
          <div>
            <h2 className="text-xl font-bold text-gray-900">🤖 {t("chat.title")}</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {language === "gu"
                ? "ગુજરાતી, હિન્દી અથવા English — ગમે તે ભાષામાં સવાલ કરો"
                : language === "hi"
                ? "हिन्दी, गुजराती या English — किसी भी भाषा में सवाल करें"
                : "Ask any question in English, Gujarati, or Hindi."}
            </p>
          </div>

          {/* Context panel */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">{ctx.title}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="chat-crop" className="block text-xs text-gray-500 mb-1">
                  {ctx.crop}
                </label>
                <select
                  id="chat-crop"
                  value={crop}
                  onChange={e => setCrop(e.target.value)}
                  className="w-full text-sm border border-gray-200 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CROP_OPTIONS.map(c => (
                    <option key={c.value} value={c.value}>
                      {c[language as keyof typeof c] ?? c.en}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="chat-qty" className="block text-xs text-gray-500 mb-1">
                  {ctx.qty}
                </label>
                <input
                  id="chat-qty"
                  type="number"
                  min={1}
                  value={quantity}
                  onChange={e => setQuantity(Number(e.target.value))}
                  className="w-full text-sm border border-gray-200 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label htmlFor="chat-mandi" className="block text-xs text-gray-500 mb-1">
                {ctx.mandi}
              </label>
              <select
                id="chat-mandi"
                value={mandi}
                onChange={e => setMandi(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {MANDIS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>

          {/* AI Chat widget */}
          <AIChatWidget
            language={language}
            farmerId={1}
            crop={crop}
            mandi={mandi}
            quantity={quantity}
          />

          {/* Responsible AI disclaimer */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs text-amber-700" role="note">
            <strong>⚠️ {t("status.demo")}</strong> — {t("errors.ai_unavailable").replace("AI service is temporarily unavailable. ", "")}
          </div>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
