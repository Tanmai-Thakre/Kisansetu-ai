"use client";

/**
 * Phase 8/9 — KisanSetu AI Chat Widget (updated)
 *
 * Phase 9 improvements:
 * - Language-aware placeholder text from translation files
 * - Voice button placeholder ("coming soon")
 * - Better fallback notice using translation
 * - Improved agent activity display
 * - Granite availability indicator
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { postChat, fetchChatStatus } from "@/lib/api";
import type { ChatResponse, GraniteStatusResponse } from "@/types";

const AGENT_META: Record<string, { icon: string; label: string }> = {
  forecast: { icon: "📈", label: "Forecast" },
  buyer:    { icon: "🤝", label: "Buyer Matching" },
  storage:  { icon: "📦", label: "Storage Advisor" },
  income:   { icon: "💰", label: "Income" },
  quality:  { icon: "🔬", label: "Quality" },
};

const LOADING_STEPS: Record<string, string[]> = {
  en: ["Analyzing market data...", "Finding suitable buyers...", "Comparing strategies...", "Generating recommendation..."],
  gu: ["બજાર ડેટા વિશ્લેષણ...", "ખરીદદારો શોધ...", "વ્યૂહ સરખામણી...", "ભલામણ તૈયાર..."],
  hi: ["बाज़ार डेटा विश्लेषण...", "खरीदार खोज रहे हैं...", "रणनीतियाँ तुलना...", "सुझाव तैयार कर रहे हैं..."],
};

const EXAMPLES: Record<string, string[]> = {
  en: [
    "Should I sell my cotton now or wait?",
    "Find the best buyer for 100 quintals.",
    "What is the 15-day price forecast?",
    "I have 100 quintals of cotton in Rajkot. Find best buyer, predict price, estimate my income.",
  ],
  gu: [
    "શું મારે હવે કપાસ વેચવો જોઈએ?",
    "100 ક્વિન્ટલ માટે ખરીદદાર શોધો.",
    "15 દિવસ ભાવ અનુમાન શું છે?",
    "100 ક્વિન્ટલ કપાસ છે. ખરીદદાર, ભાવ, આવક ગણો.",
  ],
  hi: [
    "क्या मुझे अभी कपास बेचनी चाहिए?",
    "100 क्विंटल के लिए खरीदार खोजें।",
    "15 दिन भाव अनुमान क्या है?",
    "100 क्विंटल कपास है। खरीदार, भाव, आय गणना करें।",
  ],
};

const PLACEHOLDER: Record<string, string> = {
  en: "Ask anything about your crop... (Enter to send)",
  gu: "તમારો સવાલ અહીં લખો... (Enter દબાવો)",
  hi: "अपना सवाल यहाँ लिखें... (Enter दबाएँ)",
};

const ASK_BTN: Record<string, string> = { en: "Ask", gu: "પૂછો", hi: "पूछें" };

function renderAnswer(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part.split("\n").map((line, j, arr) => (
      <span key={`${i}-${j}`}>{line}{j < arr.length - 1 && <br />}</span>
    ));
  });
}

interface AIChatWidgetProps {
  language?: "en" | "gu" | "hi";
  farmerId?: number;
  crop?:     string;
  mandi?:    string;
  quantity?: number;
  compact?:  boolean;
}

export function AIChatWidget({
  language = "en",
  farmerId = 1,
  crop     = "cotton",
  mandi    = "Rajkot APMC",
  quantity = 100,
  compact  = false,
}: AIChatWidgetProps) {
  const [query,    setQuery]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error,    setError]    = useState<string | null>(null);
  const [step,     setStep]     = useState(0);
  const [granite,  setGranite]  = useState<GraniteStatusResponse | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const timerRef    = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    fetchChatStatus()
      .then(s => setGranite(s))
      .catch(() => setGranite({ available: false, mode: "fallback", model: null, region: null }));
  }, []);

  const startTimer = useCallback(() => {
    setStep(0);
    let s = 0;
    const steps = LOADING_STEPS[language] ?? LOADING_STEPS.en;
    timerRef.current = setInterval(() => {
      s = (s + 1) % steps.length;
      setStep(s);
    }, 1400);
  }, [language]);

  const stopTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const handleSubmit = useCallback(async () => {
    const q = query.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setResponse(null);
    startTimer();
    try {
      const res = await postChat({ message: q, language, farmer_id: farmerId, crop, mandi, quantity });
      setResponse(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      stopTimer();
      setLoading(false);
    }
  }, [query, loading, language, farmerId, crop, mandi, quantity, startTimer, stopTimer]);

  const examples = (EXAMPLES[language] ?? EXAMPLES.en).slice(0, compact ? 2 : 3);
  const steps    = LOADING_STEPS[language] ?? LOADING_STEPS.en;

  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-gray-100 ${compact ? "p-4" : "p-5"}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">🤖</span>
          <h3 className={`font-semibold text-gray-800 ${compact ? "text-sm" : "text-base"}`}>
            KisanSetu AI
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {/* Granite availability indicator */}
          {granite && (
            <span
              title={granite.available ? `IBM Granite: ${granite.model ?? "configured"}` : "Fallback mode active"}
              className={`text-xs px-2 py-0.5 rounded-full font-medium cursor-help ${
                granite.available
                  ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                  : "bg-gray-100 text-gray-500 border border-gray-200"
              }`}
            >
              {granite.available ? "● Granite" : "○ Fallback"}
            </span>
          )}
        </div>
      </div>

      {/* Fallback notice */}
      {granite && !granite.available && (
        <div className="mb-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          {language === "gu"
            ? "IBM Granite ઉપલબ્ધ નથી — નિયમ-આધારિત વિશ્લેષણ"
            : language === "hi"
            ? "IBM Granite उपलब्ध नहीं — नियम-आधारित विश्लेषण"
            : "IBM Granite not configured — showing rule-based analysis."}
        </div>
      )}

      {/* Input row */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          rows={compact ? 2 : 3}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
          placeholder={PLACEHOLDER[language]}
          disabled={loading}
          className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 pr-20 resize-none
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:bg-gray-50 disabled:text-gray-400 placeholder-gray-300"
          aria-label="Ask KisanSetu AI"
        />
        {/* Action buttons */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1">
          {/* Voice placeholder */}
          <button
            title={
              language === "gu" ? "વૉઇસ ટૂંક સમયમાં"
              : language === "hi" ? "वॉइस जल्द आएगा"
              : "Voice support coming soon"
            }
            className="p-1.5 rounded-lg text-gray-300 cursor-not-allowed"
            aria-label="Voice input (coming soon)"
            disabled
          >
            🎤
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            className="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg font-medium
                       hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Send message"
          >
            {loading ? "…" : ASK_BTN[language] ?? "Ask"}
          </button>
        </div>
      </div>

      {/* Example chips */}
      {!loading && !response && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {examples.map((ex, i) => (
            <button
              key={i}
              onClick={() => setQuery(ex)}
              className="text-xs text-blue-600 bg-blue-50 border border-blue-100 rounded-full px-2.5 py-1
                         hover:bg-blue-100 transition-colors text-left"
            >
              {ex.length > 50 ? ex.slice(0, 50) + "…" : ex}
            </button>
          ))}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="mt-3 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse inline-block" />
            <span className="text-xs text-blue-600 font-medium">{steps[step]}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1">
            <div
              className="bg-blue-500 h-1 rounded-full transition-all duration-700"
              style={{ width: `${((step + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="mt-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
          ⚠️ {error}
        </div>
      )}

      {/* Response */}
      {response && !loading && (
        <div className="mt-3 space-y-3">
          <div className="text-sm text-gray-700 bg-gray-50 rounded-xl p-3 leading-relaxed">
            {renderAnswer(response.answer)}
          </div>

          {/* Agent activity */}
          {response.agents_used.length > 0 && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-3">
              <p className="text-xs font-semibold text-blue-700 mb-1.5">
                {language === "gu" ? "ઉપયોગ કરેલ" : language === "hi" ? "उपयोग किया गया" : "Agents used"}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {response.agents_used.map(a => {
                  const m = AGENT_META[a];
                  return (
                    <span key={a} className="flex items-center gap-1 text-xs text-blue-700 bg-white border border-blue-200 rounded-full px-2 py-0.5">
                      {m?.icon} ✓ {m?.label ?? a}
                    </span>
                  );
                })}
                {response.agents_failed?.map(a => (
                  <span key={a} className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
                    {AGENT_META[a]?.icon} ✗ {AGENT_META[a]?.label ?? a}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Confidence + Granite indicator */}
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>
              {language === "gu" ? "વિશ્વાસ" : language === "hi" ? "विश्वास" : "Confidence"}:
              <strong className="text-gray-600 ml-1">{response.confidence}%</strong>
            </span>
            <span className={response.granite_used ? "text-emerald-600 font-medium" : "text-gray-400"}>
              {response.granite_used ? "🤖 IBM Granite" : "⚙️ Rule-based"}
            </span>
          </div>

          <p className="text-xs text-gray-400 leading-relaxed">
            {language === "gu"
              ? "⚠️ આ અંદાજ ડેમો ડેટા પર આધારિત છે. નાણાકીય સલાહ નથી."
              : language === "hi"
              ? "⚠️ यह डेमो डेटा पर आधारित अनुमान है। वित्तीय सलाह नहीं।"
              : "⚠️ Estimates based on demo data. Not financial advice."}
          </p>

          <button
            onClick={() => { setResponse(null); setQuery(""); textareaRef.current?.focus(); }}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            {language === "gu" ? "← નવો સવાલ" : language === "hi" ? "← नया सवाल" : "← Ask another question"}
          </button>
        </div>
      )}
    </div>
  );
}
