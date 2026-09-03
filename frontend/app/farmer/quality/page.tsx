"use client";

/**
 * Phase 6 — /farmer/quality
 *
 * Step flow:
 *   Step 1 — Select crop (Cotton / Groundnut)
 *   Step 2 — Choose: Upload Image OR Enter Parameters (or both)
 *   Step 3 — Fill crop-specific quality parameters + optional image
 *   Step 4 — Analyze Quality → show result
 */

import { useState, useRef } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { postQualityAssess, postQualityUpload, fetchQualityHistory } from "@/lib/api";
import type {
  QualityAssessmentResponse,
  QualityHistoryItem,
  CottonQualityParams,
  GroundnutQualityParams,
  FactorRating,
  QualityGradeLevel,
} from "@/types";

// ── constants ─────────────────────────────────────────────────────────────────

const DEMO_FARMER_ID = 1;

function fmt(n: number) {
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

// ── grade colours ─────────────────────────────────────────────────────────────

function gradeColor(grade: QualityGradeLevel) {
  switch (grade) {
    case "EXCELLENT": return { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-800", badge: "bg-emerald-600" };
    case "GOOD":      return { bg: "bg-blue-50",    border: "border-blue-200",    text: "text-blue-800",    badge: "bg-blue-600" };
    case "AVERAGE":   return { bg: "bg-amber-50",   border: "border-amber-200",   text: "text-amber-800",   badge: "bg-amber-500" };
    case "POOR":      return { bg: "bg-red-50",     border: "border-red-200",     text: "text-red-800",     badge: "bg-red-500" };
    default:          return { bg: "bg-gray-50",    border: "border-gray-200",    text: "text-gray-800",    badge: "bg-gray-500" };
  }
}

function ratingColor(rating: FactorRating) {
  switch (rating) {
    case "good":          return "text-emerald-600 bg-emerald-50";
    case "moderate":      return "text-amber-600   bg-amber-50";
    case "poor":          return "text-red-600     bg-red-50";
    case "not_available": return "text-gray-400    bg-gray-50";
    default:              return "text-gray-500    bg-gray-50";
  }
}

function ratingLabel(rating: FactorRating) {
  switch (rating) {
    case "good":          return "Good";
    case "moderate":      return "Moderate";
    case "poor":          return "Poor";
    case "not_available": return "Not available";
    default:              return rating;
  }
}

function paramLabel(key: string) {
  const labels: Record<string, string> = {
    moisture:          "Moisture",
    staple_length:     "Staple Length",
    micronaire:        "Micronaire",
    foreign_matter:    "Foreign Matter",
    color:             "Color",
    uniformity:        "Uniformity",
    kernel_appearance: "Kernel Appearance",
    damaged_kernels:   "Damaged Kernels",
    kernel_size:       "Kernel Size",
  };
  return labels[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// ── sub-components ─────────────────────────────────────────────────────────────

function NumberInput({
  label, unit, value, onChange, min, max, step = 0.1, placeholder,
}: {
  label: string; unit: string; value: string;
  onChange: (v: string) => void;
  min: number; max: number; step?: number; placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-gray-700">
        {label} <span className="text-xs text-gray-400 font-normal">({unit})</span>
      </label>
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        placeholder={placeholder ?? `${min}–${max}`}
        onChange={e => onChange(e.target.value)}
        className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
      />
    </div>
  );
}

function CottonFields({
  params,
  setParams,
}: {
  params: Partial<Record<string, string>>;
  setParams: (p: Partial<Record<string, string>>) => void;
}) {
  const set = (k: string) => (v: string) => setParams({ ...params, [k]: v });
  return (
    <div className="grid grid-cols-2 gap-3">
      <NumberInput label="Moisture"       unit="%"       value={params.moisture ?? ""}       onChange={set("moisture")}       min={0}    max={30}  step={0.1} placeholder="0–30" />
      <NumberInput label="Staple Length"  unit="mm"      value={params.staple_length ?? ""}  onChange={set("staple_length")}  min={10}   max={50}  step={0.5} placeholder="20–45" />
      <NumberInput label="Micronaire"     unit="µg/inch" value={params.micronaire ?? ""}     onChange={set("micronaire")}     min={1}    max={8}   step={0.1} placeholder="3.5–5" />
      <NumberInput label="Foreign Matter" unit="%"       value={params.foreign_matter ?? ""}  onChange={set("foreign_matter")} min={0}    max={20}  step={0.1} placeholder="0–10" />
      <NumberInput label="Color Score"    unit="1–5"     value={params.color ?? ""}           onChange={set("color")}          min={1}    max={5}   step={0.5} placeholder="1–5" />
      <NumberInput label="Uniformity"     unit="%"       value={params.uniformity ?? ""}      onChange={set("uniformity")}     min={60}   max={100} step={0.5} placeholder="76–90" />
    </div>
  );
}

function GroundnutFields({
  params,
  setParams,
}: {
  params: Partial<Record<string, string>>;
  setParams: (p: Partial<Record<string, string>>) => void;
}) {
  const set = (k: string) => (v: string) => setParams({ ...params, [k]: v });
  return (
    <div className="grid grid-cols-2 gap-3">
      <NumberInput label="Moisture"           unit="%"   value={params.moisture ?? ""}           onChange={set("moisture")}           min={0}  max={20}  step={0.1} placeholder="0–15" />
      <NumberInput label="Kernel Appearance"  unit="1–5" value={params.kernel_appearance ?? ""}  onChange={set("kernel_appearance")}  min={1}  max={5}   step={0.5} placeholder="1–5" />
      <NumberInput label="Damaged Kernels"    unit="%"   value={params.damaged_kernels ?? ""}    onChange={set("damaged_kernels")}    min={0}  max={50}  step={0.1} placeholder="0–20" />
      <NumberInput label="Foreign Matter"     unit="%"   value={params.foreign_matter ?? ""}     onChange={set("foreign_matter")}     min={0}  max={20}  step={0.1} placeholder="0–10" />
      <NumberInput label="Kernel Size"        unit="1–5" value={params.kernel_size ?? ""}        onChange={set("kernel_size")}        min={1}  max={5}   step={0.5} placeholder="1–5" />
      <NumberInput label="Color Score"        unit="1–5" value={params.color ?? ""}              onChange={set("color")}              min={1}  max={5}   step={0.5} placeholder="1–5" />
    </div>
  );
}

// ── Result UI ─────────────────────────────────────────────────────────────────

function QualityResult({ result }: { result: QualityAssessmentResponse }) {
  const gc = gradeColor(result.grade);
  const impactSign = result.price_impact_percent >= 0 ? "+" : "";

  return (
    <div className="space-y-4">
      {/* Grade card */}
      <div className={`rounded-2xl border p-5 ${gc.bg} ${gc.border}`}>
        <div className="flex items-center gap-4">
          <div className={`w-16 h-16 rounded-2xl ${gc.badge} flex items-center justify-center text-white text-xl font-bold`}>
            {result.grade === "EXCELLENT" ? "⭐" : result.grade === "GOOD" ? "✓" : result.grade === "AVERAGE" ? "~" : "⚠"}
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-0.5">AI Quality Assessment</p>
            <p className={`text-2xl font-bold ${gc.text}`}>{result.grade}</p>
            <div className="flex gap-3 mt-1">
              <span className="text-sm text-gray-600">Score: <strong>{result.quality_score}/100</strong></span>
              <span className="text-sm text-gray-600">Confidence: <strong>{result.confidence}%</strong></span>
            </div>
          </div>
        </div>
        {result.image_used && (
          <div className="mt-3 flex items-center gap-1.5 text-xs text-gray-500">
            <span>📷</span>
            <span>Image analysis included</span>
          </div>
        )}
      </div>

      {/* Quality Factors */}
      <Card>
        <CardHeader><CardTitle>Quality Factors</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(result.factors).map(([key, rating]) => {
              const detail = result.parameter_details?.[key];
              return (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <div>
                    <span className="text-sm text-gray-700">{paramLabel(key)}</span>
                    {detail?.source === "estimated" && (
                      <span className="ml-1.5 text-xs text-blue-500 italic">(estimated)</span>
                    )}
                    {detail?.value !== null && detail?.value !== undefined && (
                      <span className="ml-1.5 text-xs text-gray-400">{detail.value}</span>
                    )}
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ratingColor(rating as FactorRating)}`}>
                    {ratingLabel(rating as FactorRating)}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Price Impact */}
      {result.reference_price !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Estimated Price Impact</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Reference market price</span>
                <span className="font-medium">{fmt(result.reference_price!)}/q</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Estimated quality impact</span>
                <span className={`font-bold ${result.price_impact_percent >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                  {impactSign}{result.price_impact_percent}%
                </span>
              </div>
              {result.estimated_quality_price !== null && (
                <div className="flex justify-between text-sm border-t border-gray-100 pt-2 mt-1">
                  <span className="font-medium text-gray-700">Estimated value</span>
                  <span className="font-bold text-gray-900">{fmt(result.estimated_quality_price!)}/q</span>
                </div>
              )}
              {result.price_impact_range && (
                <p className="text-xs text-gray-400 mt-1">Range for {result.grade}: {result.price_impact_range}</p>
              )}
            </div>
            <p className="mt-3 text-xs text-amber-700 bg-amber-50 rounded-lg p-2.5">
              ⚠️ Estimated quality-related price impact. Not a guaranteed buyer price.
            </p>
          </CardContent>
        </Card>
      )}
      {result.reference_price === null && (
        <Card>
          <CardContent>
            <p className="text-sm text-gray-500 text-center py-2">
              Reference market price unavailable. Quality assessment completed without price estimation.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <Card>
          <CardHeader><CardTitle>💡 Improvement Suggestions</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {result.suggestions.map((s, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-700">
                  <span className="text-amber-500 mt-0.5 shrink-0">•</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Limitations */}
      {result.limitations.length > 0 && (
        <Card>
          <CardHeader><CardTitle>⚠️ Limitations</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-1.5">
              {result.limitations.map((l, i) => (
                <li key={i} className="text-xs text-gray-500 flex gap-2">
                  <span className="shrink-0">ℹ</span>
                  <span>{l}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
        <p className="text-xs text-amber-800 leading-relaxed">
          <strong>⚠️ {result.disclaimer}</strong>
        </p>
      </div>
    </div>
  );
}

// ── History table ──────────────────────────────────────────────────────────────

function HistoryTable({ items }: { items: QualityHistoryItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-center text-gray-400 py-4">No previous assessments found.</p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left py-2 pr-3 font-medium text-gray-500">Date</th>
            <th className="text-left py-2 pr-3 font-medium text-gray-500">Crop</th>
            <th className="text-left py-2 pr-3 font-medium text-gray-500">Grade</th>
            <th className="text-right py-2 font-medium text-gray-500">Score</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => {
            const gc = gradeColor(item.grade);
            const d = item.created_at
              ? new Date(item.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })
              : "—";
            return (
              <tr key={item.id} className="border-b border-gray-50 last:border-0">
                <td className="py-2 pr-3 text-gray-500 text-xs">{d}</td>
                <td className="py-2 pr-3 capitalize text-gray-800">{item.crop}</td>
                <td className="py-2 pr-3">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gc.bg} ${gc.text}`}>
                    {item.grade}
                  </span>
                </td>
                <td className="py-2 text-right font-bold text-gray-900">{item.quality_score}/100</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function QualityPage() {
  const { language, t, changeLanguage } = useLanguage();

  // Step 1 — crop selection
  const [crop, setCrop] = useState<"cotton" | "groundnut">("cotton");

  // Step 2 — input mode
  const [mode, setMode] = useState<"params" | "image" | "both">("params");

  // Step 3 — parameters (raw strings from inputs, parsed on submit)
  const [params, setParams] = useState<Partial<Record<string, string>>>({});

  // Image
  const [image, setImage]   = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Result state
  const [result,  setResult]  = useState<QualityAssessmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  // History
  const [history, setHistory] = useState<QualityHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // ── Image handler ──────────────────────────────────────────────────────────
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      setError("Please upload a JPG, PNG, or WebP image.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Image must be under 10 MB.");
      return;
    }
    setError("");
    setImage(file);
    const reader = new FileReader();
    reader.onload = ev => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  // ── Parse float from string, return undefined if blank/invalid ────────────
  const parseNum = (s: string | undefined): number | undefined => {
    if (!s || s.trim() === "") return undefined;
    const n = parseFloat(s);
    return isNaN(n) ? undefined : n;
  };

  // ── Build typed params ─────────────────────────────────────────────────────
  const buildCottonParams = (): CottonQualityParams => ({
    moisture:       parseNum(params.moisture),
    staple_length:  parseNum(params.staple_length),
    micronaire:     parseNum(params.micronaire),
    foreign_matter: parseNum(params.foreign_matter),
    color:          parseNum(params.color),
    uniformity:     parseNum(params.uniformity),
  });

  const buildGroundnutParams = (): GroundnutQualityParams => ({
    moisture:          parseNum(params.moisture),
    kernel_appearance: parseNum(params.kernel_appearance),
    damaged_kernels:   parseNum(params.damaged_kernels),
    foreign_matter:    parseNum(params.foreign_matter),
    kernel_size:       parseNum(params.kernel_size),
    color:             parseNum(params.color),
  });

  // ── Submit handler ─────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      let data: QualityAssessmentResponse;

      if (mode === "params") {
        // JSON endpoint — no image
        const payload =
          crop === "cotton"
            ? { farmer_id: DEMO_FARMER_ID, crop, cotton_params: buildCottonParams() }
            : { farmer_id: DEMO_FARMER_ID, crop, groundnut_params: buildGroundnutParams() };
        data = await postQualityAssess(payload);
      } else {
        // Multipart endpoint — with or without image
        const p = crop === "cotton" ? buildCottonParams() : buildGroundnutParams();
        data = await postQualityUpload(
          DEMO_FARMER_ID,
          crop,
          p,
          mode === "both" || mode === "image" ? (image ?? undefined) : undefined,
        );
      }
      setResult(data);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Quality analysis failed. Please check your inputs and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // ── History loader ─────────────────────────────────────────────────────────
  const handleLoadHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetchQualityHistory(DEMO_FARMER_ID, 20);
      setHistory(res.items);
      setShowHistory(true);
    } catch {
      setHistory([]);
      setShowHistory(true);
    } finally {
      setHistoryLoading(false);
    }
  };

  // ── Crop change ────────────────────────────────────────────────────────────
  const handleCropChange = (c: "cotton" | "groundnut") => {
    setCrop(c);
    setParams({});
    setResult(null);
    setError("");
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Rameshbhai Patel" role="farmer" />
      <div className="flex">
        <SideNav />
        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">

          {/* Header */}
          <div>
            <h1 className="text-xl font-bold text-gray-900">🔬 {t("quality.title")}</h1>
            <p className="text-sm text-gray-500 mt-0.5">{t("quality.disclaimer")}</p>
          </div>

          {/* Step 1 — Crop selection */}
          <Card>
            <CardHeader><CardTitle>Step 1 — Select Crop</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: "cotton" as const,    label: "🌿 Cotton",   desc: "Bt Cotton / Desi Cotton" },
                  { value: "groundnut" as const, label: "🥜 Groundnut", desc: "Bold / Java varieties"  },
                ].map(c => (
                  <button
                    key={c.value}
                    onClick={() => handleCropChange(c.value)}
                    className={`rounded-2xl border-2 p-4 text-left transition-all cursor-pointer ${
                      crop === c.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                  >
                    <p className="font-semibold text-gray-800">{c.label}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{c.desc}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Step 2 — Input mode */}
          <Card>
            <CardHeader><CardTitle>Step 2 — How to Assess</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: "params" as const, label: "📝 Enter Details",  desc: "Manual parameters" },
                  { value: "image"  as const, label: "📷 Upload Image",   desc: "Visual analysis" },
                  { value: "both"   as const, label: "📝+📷 Both",        desc: "Best accuracy" },
                ].map(m => (
                  <button
                    key={m.value}
                    onClick={() => setMode(m.value)}
                    className={`rounded-xl border-2 p-3 text-center transition-all cursor-pointer ${
                      mode === m.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                  >
                    <p className="font-semibold text-sm text-gray-800">{m.label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{m.desc}</p>
                  </button>
                ))}
              </div>
              {mode === "image" && (
                <p className="text-xs text-amber-700 bg-amber-50 rounded-lg p-2.5 mt-3">
                  ℹ️ Image analysis is visual only. Lab parameters (moisture, micronaire) cannot be confirmed from images.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Step 3 — Parameters */}
          {(mode === "params" || mode === "both") && (
            <Card>
              <CardHeader>
                <CardTitle>
                  Step 3 — {crop === "cotton" ? "Cotton" : "Groundnut"} Quality Parameters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-gray-400 mb-3">All fields are optional. Fill what you know.</p>
                {crop === "cotton"
                  ? <CottonFields params={params} setParams={setParams} />
                  : <GroundnutFields params={params} setParams={setParams} />
                }
              </CardContent>
            </Card>
          )}

          {/* Image upload */}
          {(mode === "image" || mode === "both") && (
            <Card>
              <CardHeader>
                <CardTitle>{mode === "both" ? "Upload Crop Image (optional)" : "Upload Crop Image"}</CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className="border-2 border-dashed border-gray-200 rounded-2xl p-6 text-center cursor-pointer hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {imagePreview ? (
                    <div className="space-y-2">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={imagePreview} alt="Crop preview" className="max-h-48 mx-auto rounded-xl object-cover" />
                      <p className="text-xs text-gray-500">{image?.name}</p>
                      <p className="text-xs text-blue-500">Tap to change image</p>
                    </div>
                  ) : (
                    <>
                      <span className="text-4xl">📷</span>
                      <p className="mt-2 text-sm font-medium text-gray-700">Tap to upload crop photo</p>
                      <p className="text-xs text-gray-400 mt-1">JPG, PNG, WebP • Max 10 MB</p>
                    </>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleImageChange}
                />
                {mode === "image" && !image && (
                  <p className="text-xs text-gray-400 mt-2 text-center">
                    Image not uploaded yet — you can still analyze using default parameters.
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-red-700">
              ❌ {error}
            </div>
          )}

          {/* Step 4 — Analyze button */}
          <Button
            fullWidth
            size="lg"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "🔬 Analyzing crop quality…" : "🔬 Analyze Quality"}
          </Button>

          {/* Loading state */}
          {loading && (
            <Card>
              <CardContent>
                <div className="text-center py-6 space-y-2">
                  <div className="text-3xl animate-spin inline-block">⏳</div>
                  <p className="text-sm text-gray-600 font-medium">Analyzing crop image…</p>
                  <p className="text-xs text-gray-400">Running quality grading analysis</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Result */}
          {result && !loading && (
            <QualityResult result={result} />
          )}

          {/* Image failure notice */}
          {result && !loading && result.limitations.some(l =>
            l.toLowerCase().includes("image") || l.toLowerCase().includes("pillow")
          ) && !result.image_used && (mode === "image" || mode === "both") && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-sm text-amber-800">
              📷 Image analysis was unavailable. You can continue using manual quality parameters.
            </div>
          )}

          {/* History */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Assessment History</CardTitle>
                <button
                  onClick={handleLoadHistory}
                  disabled={historyLoading}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
                >
                  {historyLoading ? "Loading…" : showHistory ? "Refresh" : "Load History"}
                </button>
              </div>
            </CardHeader>
            <CardContent>
              {showHistory
                ? <HistoryTable items={history} />
                : <p className="text-sm text-center text-gray-400 py-2">Tap "Load History" to see past assessments.</p>
              }
            </CardContent>
          </Card>

          {/* Demo notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-sm text-amber-700">
            <strong>⚠️ DEMO DATA</strong> — Farmer ID 1. In production, use authenticated farmer session.
          </div>

        </main>
      </div>
      <BottomNav />
    </div>
  );
}
