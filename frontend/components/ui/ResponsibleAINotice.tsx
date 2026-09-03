"use client";

/**
 * Phase 9 — ResponsibleAINotice
 * Small, readable disclaimer for AI-generated estimates.
 * Type: forecast | quality | income | buyer | general
 */

interface ResponsibleAINoticeProps {
  type: "forecast" | "quality" | "income" | "buyer" | "general";
  language?: "en" | "gu" | "hi";
  compact?: boolean;
}

const NOTICES: Record<string, Record<string, string>> = {
  forecast: {
    en: "📊 Forecasts are estimates based on historical data and are not guaranteed future prices.",
    gu: "📊 ભાવ અનુમાન ઐતિહાસિક ડેટા પર આધારિત છે. ભવિષ્યના ભાવ ની ગેરંટી નથી.",
    hi: "📊 भाव अनुमान ऐतिहासिक डेटा पर आधारित हैं। भविष्य के भाव की गारंटी नहीं।",
  },
  quality: {
    en: "🔬 Preliminary AI-assisted assessment. Not a substitute for authorized quality testing.",
    gu: "🔬 AI-સહાયિત પ્રારંભિક અંદાજ. સત્તાવાર ગુણવત્તા પરીક્ષણ માટે નહીં.",
    hi: "🔬 AI-सहायक प्रारंभिक मूल्यांकन। अधिकृत गुणवत्ता परीक्षण का विकल्प नहीं।",
  },
  income: {
    en: "💰 Income values are estimates based on the data and costs provided. Actual income may vary.",
    gu: "💰 આવક ઉપલબ્ધ ડેટા અને ખર્ચ પર આધારિત અંદાજ છે. વાસ્તવિક આવક અલગ હોઈ શકે.",
    hi: "💰 आय मूल्य प्रदान किए गए डेटा पर आधारित अनुमान हैं। वास्तविक आय भिन्न हो सकती है।",
  },
  buyer: {
    en: "🤝 Buyer listings and verification status depend on available platform data.",
    gu: "🤝 ખરીદદારની યાદી અને ચકાસણી ઉપલબ્ধ ડેટા પર આધારિત છે.",
    hi: "🤝 खरीदार सूची और सत्यापन स्थिति उपलब्ध प्लेटफ़ॉर्म डेटा पर निर्भर है।",
  },
  general: {
    en: "⚠️ All estimates are based on available demo market data. Not financial advice.",
    gu: "⚠️ બધા અંદાજ ઉપલબ્ધ ડેમો ડેટા પર આધારિત છે. નાણાકીય સલાહ નથી.",
    hi: "⚠️ सभी अनुमान उपलब्ध डेमो डेटा पर आधारित हैं। वित्तीय सलाह नहीं।",
  },
};

export function ResponsibleAINotice({ type, language = "en", compact = false }: ResponsibleAINoticeProps) {
  const text = NOTICES[type]?.[language] ?? NOTICES[type]?.en ?? "";
  if (!text) return null;
  return (
    <p
      className={`text-gray-400 leading-relaxed ${compact ? "text-xs" : "text-xs"}`}
      role="note"
      aria-label={`Responsible AI notice: ${type}`}
    >
      {text}
    </p>
  );
}
