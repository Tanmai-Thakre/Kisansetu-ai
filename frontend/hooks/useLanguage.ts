"use client";

import { useState, useCallback } from "react";
import type { Language } from "@/types";
import en from "@/locales/en.json";
import gu from "@/locales/gu.json";
import hi from "@/locales/hi.json";

const translations = { en, gu, hi };

type TranslationKeys = typeof en;

function getNestedValue(obj: Record<string, unknown>, path: string): string {
  const keys = path.split(".");
  let current: unknown = obj;
  for (const key of keys) {
    if (typeof current !== "object" || current === null) return path;
    current = (current as Record<string, unknown>)[key];
  }
  return typeof current === "string" ? current : path;
}

export function useLanguage() {
  const [language, setLanguage] = useState<Language>("en");

  const t = useCallback(
    (key: string): string => {
      const dict = translations[language] as unknown as Record<string, unknown>;
      return getNestedValue(dict, key);
    },
    [language]
  );

  const changeLanguage = useCallback((lang: Language) => {
    setLanguage(lang);
  }, []);

  return { language, t, changeLanguage };
}
