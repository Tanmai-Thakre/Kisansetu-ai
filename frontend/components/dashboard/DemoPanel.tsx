"use client";

/**
 * Phase 9 — DemoPanel
 *
 * Hackathon demo mode panel that:
 *  1. Shows "DEMO MODE" badge
 *  2. Loads a demo farmer (one-click pre-population)
 *  3. Runs Full AI Analysis via the orchestrator
 *  4. Shows agent activity in real time
 *  5. Displays the Granite final answer
 *
 * Reuses Phase 8 postOrchestrate — no new AI system built.
 */

import { useState, useCallback } from "react";
import { postOrchestrate } from "@/lib/api";
import type { OrchestrateResponse } from "@/types";

const DEMO_QUERY_EN = "I have 100 quintals of cotton in Rajkot. Find the best buyer, predict the price for the next 15 days, tell me whether I should sell or store, and estimate my income.";
const DEMO_QUERY_GU = "100 ક્વિન્ટલ કપાસ રાજકોટમાં છે. શ્રેષ્ઠ ખરીદદાર, 15 દિવસ ભાવ, વેચો/સ્ટોર સલાહ અને આવક ગણો.";
const DEMO_QUERY_HI = "100 क्विंटल कपास राजकोट में है। सबसे अच्छा खरीदार, 15 दिन भाव, बेचें/रखें सलाह और आय की गणना करें।";

const AGENT_META: Record<string, { icon: string; label: string }> = {
  forecast: { icon: "📈", label: "Forecast Agent" },
  buyer:    { icon: "🤝", label: "Buyer Matching" },
  storage:  { icon: "📦", label: "Storage Advisor" },
  income:   { icon: "💰", label: "Income Agent" },
  quality:  { icon: "🔬", label: "Quality Agent" },
};

const STEP_LABELS: Record<string, string[]> = {
  en: [
    "Fetching market data...",
    "Finding suitable buyers...",
    "Comparing selling strategies...",
    "Calculating income scenarios...",
    "Generating AI recommendation...",
  ],
  gu: [
    "બજાર ડેટા મળી રહ્યો છે...",
    "ઉચિત ખરીદદારો શોધ...",
    "વ્યૂહ સરખામણી...",
    "આવક અંદાજ ગણ...",
    "AI ભલામણ તૈયાર...",
  ],
  hi: [
    "बाज़ार डेटा प्राप्त हो रहा है...",
    "उचित खरीदार खोज रहे हैं...",
    "बिक्री रणनीतियाँ तुलना...",
    "आय अनुमान गणना...",
    "AI सुझाव तैयार...",
  ],
};

function renderBold(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part.split("\n").map((line, j, arr) => (
          <span key={`${i}-${j}`}>{line}{j < arr.length - 1 && <br />}</span>
        ))
  );
}

interface DemoPanelProps {
  language?: "en" | "gu" | "hi";
  onLoad?: (data: { crop: string; quantity: number; mandi: string; farmerName: string }) => void;
}

export function DemoPanel({ language = "en", onLoad }: DemoPanelProps) {
  const [phase,    setPhase]    = useState<"idle" | "loading" | "done" | "error">("idle");
  const [step,     setStep]     = useState(0);
  const [result,   setResult]   = useState<OrchestrateResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [loaded,   setLoaded]   = useState(false);

  const demoData = { crop: "cotton", quantity: 100, mandi: "Rajkot APMC", farmerName: "Rameshbhai Patel" };
  const steps = STEP_LABELS[language] ?? STEP_LABELS.en;

  const handleLoad = useCallback(() => {
    setLoaded(true);
    onLoad?.(demoData);
  }, [onLoad]);

  const handleRunAnalysis = useCallback(async () => {
    setPhase("loading");
    setResult(null);
    setErrorMsg("");
    setStep(0);

    const query = language === "gu" ? DEMO_QUERY_GU : language === "hi" ? DEMO_QUERY_HI : DEMO_QUERY_EN;
    const stepList = STEP_LABELS[language] ?? STEP_LABELS.en;

    // Advance step text while waiting
    const timer = setInterval(() => setStep(s => Math.min(s + 1, stepList.length - 1)), 1200);

    try {
      const res = await postOrchestrate({
        farmer_id: 1,
        message:   query,
        language,
        crop:      "cotton",
        mandi:     "Rajkot APMC",
        quantity:  100,
      });
      setResult(res);
      setPhase("done");
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Analysis failed");
      setPhase("error");
    } finally {
      clearInterval(timer);
    }
  }, [language]);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 bg-indigo-600">
        <div className="flex items-center gap-2">
          <span className="text-white font-black text-xs tracking-widest uppercase">
            {language === "gu" ? "ડેમો મોડ" : language === "hi" ? "डेमो मोड" : "DEMO MODE"}
          </span>
          <span className="bg-white bg-opacity-20 text-white text-xs px-2 py-0.5 rounded-full">
            {language === "gu" ? "કૃત્રિમ ડેટા" : language === "hi" ? "सिंथेटिक डेटा" : "Synthetic data"}
          </span>
        </div>
        <span className="text-white opacity-70 text-xs">KisanSetu AI</span>
      </div>

      <div className="p-5 space-y-4">
        {/* Demo farmer card */}
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-sm font-bold text-indigo-800">
                👨‍🌾 {language === "gu" ? "રમેશભાઈ પટેલ" : language === "hi" ? "रमेशभाई पटेल" : "Rameshbhai Patel"}
              </p>
              <p className="text-xs text-indigo-600 mt-0.5">
                🌿 {language === "gu" ? "કપાસ · 100 ક્વિન્ટલ · રાજકોટ, ગુજરાત" : language === "hi" ? "कपास · 100 क्विंटल · राजकोट, गुजरात" : "Cotton · 100 quintals · Rajkot, Gujarat"}
              </p>
            </div>
            <button
              onClick={handleLoad}
              className={`text-xs px-4 py-2.5 rounded-xl font-semibold transition-colors min-h-[36px] ${
                loaded
                  ? "bg-green-100 text-green-700 border border-green-200"
                  : "bg-indigo-600 text-white hover:bg-indigo-700"
              }`}
            >
              {loaded
                ? (language === "gu" ? "✓ લોડ થઈ ગયું" : language === "hi" ? "✓ लोड हो गया" : "✓ Loaded")
                : (language === "gu" ? "ડેમો ખેડૂત લોડ" : language === "hi" ? "डेमो किसान लोड" : "Load Demo Farmer")
              }
            </button>
          </div>
        </div>

        {/* Full analysis button */}
        <button
          onClick={handleRunAnalysis}
          disabled={phase === "loading"}
          className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-blue-600 text-white text-sm font-bold rounded-xl
                     hover:from-indigo-700 hover:to-blue-700 disabled:opacity-60 disabled:cursor-not-allowed
                     transition-all active:scale-99 shadow-sm"
          aria-busy={phase === "loading"}
        >
          {phase === "loading"
            ? (language === "gu" ? "⏳ વિશ્લેષણ..." : language === "hi" ? "⏳ विश्लेषण..." : "⏳ Analyzing...")
            : (language === "gu" ? "🚀 સંપૂર્ણ AI વિશ્લેષણ" : language === "hi" ? "🚀 पूर्ण AI विश्लेषण" : "🚀 Run Full AI Analysis")
          }
        </button>

        {/* Loading progress */}
        {phase === "loading" && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5 bg-indigo-500 rounded-full animate-pulse" aria-hidden="true" />
              <span className="text-xs text-indigo-600 font-medium">{steps[step]}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5" role="progressbar" aria-valuenow={step + 1} aria-valuemax={steps.length}>
              <div
                className="bg-indigo-500 h-1.5 rounded-full transition-all duration-700"
                style={{ width: `${((step + 1) / steps.length) * 100}%` }}
              />
            </div>
            <div className="text-xs text-gray-400">
              {language === "gu"
                ? "📈 ભાવ → 🤝 ખરીદદાર → 📦 સ્ટોરેજ → 💰 આવક → 🤖 IBM Granite"
                : language === "hi"
                ? "📈 भाव → 🤝 खरीदार → 📦 स्टोरेज → 💰 आय → 🤖 IBM Granite"
                : "📈 Forecast → 🤝 Buyer → 📦 Storage → 💰 Income → 🤖 IBM Granite"
              }
            </div>
          </div>
        )}

        {/* Error */}
        {phase === "error" && (
          <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2" role="alert">
            ⚠️ {errorMsg}
          </div>
        )}

        {/* Result */}
        {phase === "done" && result && (
          <div className="space-y-3">
            {/* Agent activity */}
            <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3">
              <p className="text-xs font-semibold text-indigo-700 mb-2">
                {language === "gu" ? "ઉપયોગ કરેલ" : language === "hi" ? "उपयोग किए गए" : "Agents used"}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.agents_used.map(a => {
                  const m = AGENT_META[a];
                  return (
                    <span key={a} className="flex items-center gap-1 text-xs text-indigo-700 bg-white border border-indigo-200 rounded-full px-2 py-0.5">
                      {m?.icon} ✓ {m?.label ?? a}
                    </span>
                  );
                })}
                {result.agents_failed.map(a => (
                  <span key={a} className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
                    {AGENT_META[a]?.icon} ✗ {AGENT_META[a]?.label ?? a}
                  </span>
                ))}
              </div>
            </div>

            {/* Granite answer */}
            <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {renderBold(result.final_answer)}
            </div>

            {/* Meta row */}
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>
                {language === "gu" ? "વિશ્વાસ" : language === "hi" ? "विश्वास" : "Confidence"}:{" "}
                <strong className="text-gray-600">{result.confidence}%</strong>
              </span>
              <span className={result.granite_used ? "text-emerald-600 font-medium" : "text-gray-400"}>
                {result.granite_used ? "🤖 IBM Granite" : "⚙️ Rule-based"}
              </span>
            </div>

            <p className="text-xs text-gray-400 text-center leading-relaxed">
              {language === "gu"
                ? "⚠️ બધા આંકડા ડેમો ડેટા પર આધારિત અંદાજ. નાણાકીય સલાહ નથી."
                : language === "hi"
                ? "⚠️ सभी अनुमान डेमो डेटा पर आधारित। वित्तीय सलाह नहीं।"
                : "⚠️ All figures are estimates based on demo data. Not financial advice."
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
