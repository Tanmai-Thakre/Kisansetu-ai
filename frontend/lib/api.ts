import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Phase 1 endpoints (preserved)
// Phase 2 endpoints added
// Phase 3 forecast endpoints added
export const endpoints = {
  // System
  health:               "/health",

  // Market — Phase 1 backward-compat
  marketPrices:         "/api/market/prices",

  // Market — Phase 2
  marketLatest:         "/api/market/prices/latest",
  marketHistory:        "/api/market/prices/history",
  marketCompare:        "/api/market/prices/compare",
  marketMandis:         "/api/market/mandis",
  marketCrops:          "/api/market/crops",
  marketDistricts:      "/api/market/districts",
  marketTrends:         "/api/market/trends",
  marketBestMandi:      "/api/market/best-mandi",
  marketForecastInput:  "/api/market/forecast-input",
  marketSourceInfo:     "/api/market/source-info",

  // Market — Phase 3 Forecasting
  marketForecast:       "/api/market/forecast",
  marketForecastChart:  "/api/market/forecast/chart",

  // Buyers — Phase 1 (preserved)
  buyers:               "/api/buyers",
  bestBuyer:            "/api/buyers/best",

  // Buyers — Phase 4 Matching
  buyerMatches:         "/api/buyers/matches",
  buyerRequest:         "/api/buyers/request",
  buyerRequests:        "/api/buyers/requests",

  // Farmer
  farmerDashboard:      "/api/farmer/dashboard",

  // Agents — Phase 5
  storageAdvisor:       "/api/agents/storage-advisor",
  storageAdvisorPreview:"/api/agents/storage-advisor/preview",

  // Quality Grading — Phase 6
  qualityAssess:        "/api/agents/quality",
  qualityUpload:        "/api/agents/quality/upload",
  qualityHistory:       "/api/agents/quality/history",
  qualityPreview:       "/api/agents/quality/preview",

  // Income Dashboard — Phase 7
  incomeDashboard:      "/api/agents/income",
  incomePreview:        "/api/agents/income/preview",
  incomeHistory:        "/api/agents/income/history",
};

// ── Typed forecast helpers ────────────────────────────────────────────────────

import type { ForecastResponse, ForecastChartResponse, AdvisorResponse } from "@/types";

export async function fetchForecast(
  crop: string,
  mandi: string,
  horizon?: number,
): Promise<ForecastResponse> {
  const res = await api.get(endpoints.marketForecast, {
    params: { crop, mandi, ...(horizon ? { horizon } : {}) },
  });
  return res.data as ForecastResponse;
}

export async function fetchForecastChart(
  crop: string,
  mandi: string,
  historyDays?: number,
  forecastDays?: number,
): Promise<ForecastChartResponse> {
  const res = await api.get(endpoints.marketForecastChart, {
    params: {
      crop,
      mandi,
      ...(historyDays  ? { history_days:  historyDays  } : {}),
      ...(forecastDays ? { forecast_days: forecastDays } : {}),
    },
  });
  return res.data as ForecastChartResponse;
}

// ── Phase 5 Storage Advisor helpers ──────────────────────────────────────────

/**
 * GET /api/agents/storage-advisor/preview
 * Convenience endpoint — no request body needed.
 */
export async function storageAdvisorPreview(
  crop: string = "cotton",
  mandi: string = "Rajkot APMC",
  quantity: number = 100,
  storageCost: number = 80,
): Promise<AdvisorResponse> {
  const res = await api.get(endpoints.storageAdvisorPreview, {
    params: { crop, mandi, quantity, storage_cost_per_quintal: storageCost },
  });
  return res.data as AdvisorResponse;
}

/**
 * POST /api/agents/storage-advisor
 * Full advisor call with all parameters.
 */
export async function postStorageAdvisor(payload: {
  crop: string;
  mandi?: string;
  quantity: number;
  storage_cost_per_quintal?: number;
  cash_urgency?: "LOW" | "MEDIUM" | "HIGH";
  current_price_override?: number;
  buyer_price_override?: number;
}): Promise<AdvisorResponse> {
  const res = await api.post(endpoints.storageAdvisor, payload);
  return res.data as AdvisorResponse;
}

// ── Phase 6 Quality Grading helpers ──────────────────────────────────────────

import type {
  QualityAssessmentResponse,
  QualityHistoryResponse,
  CottonQualityParams,
  GroundnutQualityParams,
} from "@/types";

/**
 * POST /api/agents/quality  — JSON params, no image
 */
export async function postQualityAssess(payload: {
  farmer_id: number;
  crop: string;
  crop_id?: number;
  cotton_params?: CottonQualityParams;
  groundnut_params?: GroundnutQualityParams;
}): Promise<QualityAssessmentResponse> {
  const res = await api.post(endpoints.qualityAssess, payload);
  return res.data as QualityAssessmentResponse;
}

/**
 * POST /api/agents/quality/upload  — multipart with optional image
 */
export async function postQualityUpload(
  farmerId: number,
  crop: string,
  params: CottonQualityParams | GroundnutQualityParams,
  image?: File,
): Promise<QualityAssessmentResponse> {
  const form = new FormData();
  form.append("farmer_id", String(farmerId));
  form.append("crop", crop);
  form.append("params_json", JSON.stringify(params));
  if (image) form.append("image", image);
  const res = await api.post(endpoints.qualityUpload, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data as QualityAssessmentResponse;
}

/**
 * GET /api/agents/quality/history
 */
export async function fetchQualityHistory(
  farmerId: number,
  limit = 20,
): Promise<QualityHistoryResponse> {
  const res = await api.get(endpoints.qualityHistory, {
    params: { farmer_id: farmerId, limit },
  });
  return res.data as QualityHistoryResponse;
}

// ── Phase 7 Income Dashboard helpers ─────────────────────────────────────────

import type { IncomeResponse, IncomeRequest } from "@/types";

/**
 * POST /api/agents/income — full income calculation with all parameters.
 */
export async function postIncomeDashboard(
  payload: IncomeRequest,
): Promise<IncomeResponse> {
  const res = await api.post(endpoints.incomeDashboard, payload);
  return res.data as IncomeResponse;
}

/**
 * GET /api/agents/income/preview — quick calculation without request body.
 */
export async function fetchIncomePreview(
  crop: string = "cotton",
  quantity: number = 100,
  mandi: string = "Rajkot APMC",
  storageCost: number = 80,
): Promise<IncomeResponse> {
  const res = await api.get(endpoints.incomePreview, {
    params: { crop, quantity, mandi, storage_cost_per_quintal: storageCost },
  });
  return res.data as IncomeResponse;
}

export default api;
