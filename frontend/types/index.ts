// KisanSetu AI — TypeScript type definitions
// Phase 3: Extended with Forecast types

export type UserRole = "farmer" | "buyer" | "admin";
export type CropType = "cotton" | "groundnut";
export type QualityGrade = "A" | "B" | "C" | "ungraded";
export type Language = "en" | "gu" | "hi";
export type PriceTrend = "up" | "down" | "stable" | "UP" | "DOWN" | "STABLE";
export type SourceStatus = "LIVE" | "LATEST_AVAILABLE" | "DEMO";

export interface User {
  id: number;
  name: string;
  phone: string;
  email?: string;
  role: UserRole;
  language: Language;
  created_at: string;
  farmer_profile?: FarmerProfile;
}

export interface FarmerProfile {
  id: number;
  user_id: number;
  village?: string;
  district?: string;
  state: string;
  land_area?: number;
}

export interface Crop {
  id: number;
  farmer_id: number;
  crop_type: CropType;
  variety?: string;
  quantity?: number;
  expected_harvest_date?: string;
  quality_grade?: QualityGrade;
  created_at: string;
}

// ── Phase 1 market types (preserved) ─────────────────────────────────────────

export interface MarketSummary {
  crop: CropType;
  latest_modal_price: number;
  latest_date: string;
  district: string;
  mandi: string;
  change_percent?: number;
  trend?: PriceTrend;
  source: string;
}

export interface PriceTrendPoint {
  date: string;
  price: number;
  crop: CropType;
}

export interface MarketDashboard {
  cotton?: MarketSummary;
  groundnut?: MarketSummary;
  price_trend: PriceTrendPoint[];
  note: string;
}

// ── Phase 2 market types ──────────────────────────────────────────────────────

export interface MarketRecord {
  crop: string;
  variety?: string;
  mandi: string;
  district: string;
  state: string;
  date: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  arrival_quantity?: number;
  unit: string;
  source: string;
  source_status: SourceStatus;
}

export interface PaginatedMarketResponse {
  total: number;
  page: number;
  limit: number;
  source: string;
  source_status: SourceStatus;
  is_live: boolean;
  data: MarketRecord[];
}

export interface TrendIndicator {
  crop: string;
  mandi: string;
  current_price: number;
  previous_price?: number;
  change?: number;
  change_percent?: number;
  trend: "UP" | "DOWN" | "STABLE";
  source: string;
  source_status: SourceStatus;
  latest_date?: string;
}

export interface MandiComparisonEntry {
  mandi: string;
  district: string;
  modal_price: number;
  min_price: number;
  max_price: number;
  net_price: number;
  transport_cost_per_quintal: number;
  estimated_distance_km: number;
  trend: string;
  change_percent?: number;
  arrival_quantity?: number;
  source_status: SourceStatus;
  latest_date?: string;
  transport_note: string;
}

export interface MandiComparisonResponse {
  crop: string;
  quantity_quintals: number;
  mandis: MandiComparisonEntry[];
  count: number;
  source: string;
  source_status: SourceStatus;
  is_live: boolean;
  note: string;
}

export interface BestMandiResponse {
  crop: string;
  quantity_quintals: number;
  best_mandi?: MandiComparisonEntry;
  explanation: string;
  all_mandis: MandiComparisonEntry[];
  source_status: SourceStatus;
  note: string;
}

export interface HistoryPoint {
  date: string;
  modal_price: number;
  min_price: number;
  max_price: number;
  arrival_quantity?: number;
  mandi: string;
  crop: string;
}

export interface PriceHistoryResponse {
  crop: string;
  mandi?: string;
  district?: string;
  count: number;
  source: string;
  source_status: SourceStatus;
  is_live: boolean;
  data: HistoryPoint[];
}

export interface MandiMaster {
  name: string;
  short_name: string;
  district: string;
  state: string;
  latitude?: number;
  longitude?: number;
}

export interface CropMaster {
  name: string;
  display_name: string;
  unit: string;
  description?: string;
}

export interface DataSourceInfo {
  source: string;
  source_status: SourceStatus;
  is_live: boolean;
  tooltip: string;
}

// ── Phase 4 Buyer Matching types ─────────────────────────────────────────────

export interface ScoreBreakdown {
  crop:     number;
  quality:  number;
  price:    number;
  location: number;
  quantity: number;
  delivery: number;
}

export interface BuyerMatch {
  buyer_id:            number;
  buyer_name:          string;
  location:            string | null;
  verified:            boolean;
  crop:                string;
  offered_price:       number | null;
  min_quantity:        number | null;
  max_quantity:        number | null;
  quality_requirement: string | null;
  match_score:         number;
  breakdown:           ScoreBreakdown;
  reasons:             string[];
  price_vs_market:     "ABOVE_MARKET" | "AT_MARKET" | "BELOW_MARKET" | "UNKNOWN";
  price_advantage:     number | null;
  distance_km:         number | null;
  market_price:        number | null;
}

export interface BuyerMatchResponse {
  crop:         string;
  quantity:     number | null;
  district:     string | null;
  market_price: number | null;
  total_found:  number;
  matches:      BuyerMatch[];
  note:         string;
}

// ── Phase 5 Storage Advisor types ────────────────────────────────────────────

export interface HorizonResult {
  horizon_days:     number;
  forecast_price:   number;
  gross_future:     number;
  storage_cost:     number;
  net_future:       number;
  sell_now_value:   number;
  potential_gain:   number;
  gain_per_quintal: number;
  gain_percent:     number;
}

export type AdvisorRecommendation = "SELL_NOW" | "STORE" | "PARTIAL_SELL";

export interface AdvisorResponse {
  recommendation:           AdvisorRecommendation;
  sell_percentage:          number;
  store_percentage:         number;
  recommended_horizon_days: number;
  current_best_price:       number;
  current_mandi_price:      number;
  buyer_price:              number | null;
  buyer_is_best:            boolean;
  forecast_price:           number;
  sell_now_value:           number;
  estimated_storage_cost:   number;
  potential_net_gain:       number;
  gain_per_quintal:         number;
  gain_percent:             number;
  risk:                     "LOW" | "MEDIUM" | "HIGH";
  risk_score:               number;
  confidence:               number;
  cash_urgency:             "LOW" | "MEDIUM" | "HIGH";
  crop:                     string;
  mandi:                    string;
  quantity:                 number;
  source_status:            string;
  horizons:                 HorizonResult[];
  reasons:                  string[];
  explanation:              string;
  disclaimer:               string;
}

export interface AdvisorRequest {
  crop:                     string;
  mandi?:                   string;
  quantity:                 number;
  storage_cost_per_quintal?: number;
  cash_urgency?:            "LOW" | "MEDIUM" | "HIGH";
  current_price_override?:  number;
  buyer_price_override?:    number;
}

export interface ConnectionRequest {
  id:            number;
  farmer_id:     number;
  buyer_id:      number;
  crop:          string;
  quantity:      number;
  offered_price: number | null;
  message:       string | null;
  status:        "PENDING" | "ACCEPTED" | "REJECTED" | "COMPLETED";
  match_score:   number | null;
  created_at:    string;
  updated_at:    string;
}

// ── Phase 3 Forecast types ────────────────────────────────────────────────────

export interface ForecastChartPoint {
  date:  string;
  price: number;
  type:  "historical" | "forecast";
}

export interface ForecastResponse {
  crop:                string;
  mandi:               string;
  current_price:       number;
  forecast_7d:         number;
  forecast_15d:        number;
  forecast_30d:        number;
  trend:               "UP" | "DOWN" | "STABLE";
  confidence:          number;          // 0–100
  risk:                "LOW" | "MEDIUM" | "HIGH";
  expected_change:     number;
  expected_change_pct: number;
  explanation:         string;
  disclaimer:          string;
  generated_at:        string;
  model_name:          string;
  mae:                 number | null;
  rmse:                number | null;
  n_history:           number;
  source_status:       SourceStatus;
  insufficient_data:   boolean;
  error_message:       string | null;
}

export interface ForecastChartResponse {
  crop:            string;
  mandi:           string;
  current_price:   number;
  history:         ForecastChartPoint[];
  forecast_points: ForecastChartPoint[];
  trend:           "UP" | "DOWN" | "STABLE";
  source_status:   SourceStatus;
}

// ── Shared types ──────────────────────────────────────────────────────────────

export interface BuyerListItem {
  id: number;
  company_name: string;
  location?: string;
  verified: boolean;
  crop: CropType;
  offered_price?: number;
  min_quantity?: number;
  max_quantity?: number;
  quality_requirement?: string;
  note: string;
}

export interface AIRecommendation {
  title: string;
  message: string;
  recommendation?: string;
  confidence?: number;
  status: string;
}

// ── Phase 6 Quality Grading types ────────────────────────────────────────────

export type QualityGradeLevel = "EXCELLENT" | "GOOD" | "AVERAGE" | "POOR";
export type FactorRating = "good" | "moderate" | "poor" | "not_available";

export interface ParameterDetail {
  value:  number | null;
  rating: FactorRating;
  source: "measured" | "estimated" | "unavailable";
  note:   string;
}

export interface QualityAssessmentResponse {
  id:                      number;
  crop:                    string;
  grade:                   QualityGradeLevel;
  quality_score:           number;
  confidence:              number;
  factors:                 Record<string, FactorRating>;
  parameter_details:       Record<string, ParameterDetail>;
  price_impact_percent:    number;
  reference_price:         number | null;
  estimated_quality_price: number | null;
  price_impact_range?:     string | null;
  price_note?:             string | null;
  observations:            string[];
  suggestions:             string[];
  limitations:             string[];
  image_used:              boolean;
  disclaimer:              string;
  source_status:           string;
  created_at:              string;
}

export interface QualityHistoryItem {
  id:                      number;
  crop:                    string;
  grade:                   QualityGradeLevel;
  quality_score:           number;
  confidence:              number;
  price_impact_percent:    number | null;
  reference_price:         number | null;
  estimated_quality_price: number | null;
  image_used:              boolean;
  suggestions:             string[];
  created_at:              string | null;
}

export interface QualityHistoryResponse {
  farmer_id: number;
  count:     number;
  items:     QualityHistoryItem[];
}

export interface CottonQualityParams {
  moisture?:       number;
  staple_length?:  number;
  micronaire?:     number;
  foreign_matter?: number;
  color?:          number;
  uniformity?:     number;
}

export interface GroundnutQualityParams {
  moisture?:          number;
  kernel_appearance?: number;
  damaged_kernels?:   number;
  foreign_matter?:    number;
  kernel_size?:       number;
  color?:             number;
}

// ── Phase 7 Income Dashboard types ───────────────────────────────────────────

export interface IncomeScenario {
  name:                       string;
  selling_price_per_quintal:  number;
  gross_revenue:              number;
  transport_cost:             number;
  storage_cost:               number;
  labour_cost:                number;
  packaging_cost:             number;
  other_cost:                 number;
  total_cost:                 number;
  net_income:                 number;
  net_income_per_quintal:     number;
  notes:                      string[];
}

export interface IncomeCostBreakdown {
  transport:  number | null;
  storage:    number | null;
  labour:     number | null;
  packaging:  number | null;
  other:      number | null;
}

export interface IncomeResponse {
  crop:                       string;
  mandi:                      string;
  quantity:                   number;
  mandi_price:                number;
  transport_per_quintal:      number;
  buyer_price:                number | null;
  forecast_7d:                number;
  forecast_15d:               number;
  forecast_30d:               number;
  forecast_confidence:        number;
  quality_price_impact_pct:   number | null;
  quality_adjusted_price:     number | null;
  scenarios:                  IncomeScenario[];
  best_scenario:              string | null;
  best_net_income:            number | null;
  income_difference:          number;
  deterministic_summary:      string;
  current_estimated_income:   number;
  best_buyer_income:          number | null;
  partial_sell_income:        number;
  cost_breakdown:             IncomeCostBreakdown;
  source_status:              string;
  disclaimer:                 string;
}

export interface IncomeRequest {
  crop:                           string;
  quantity:                       number;
  mandi?:                         string;
  storage_cost_per_quintal?:      number;
  transport_per_quintal_override?: number;
  labour_total?:                  number;
  packaging_total?:               number;
  other_total?:                   number;
  mandi_price_override?:          number;
  buyer_price_override?:          number;
  quality_price_impact_pct?:      number;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  href: string;
  color: string;
}

export interface FarmerDashboardResponse {
  farmer_name: string;
  cotton?: MarketSummary;
  groundnut?: MarketSummary;
  price_trend: PriceTrendPoint[];
  best_buyer?: BuyerListItem;
  ai_recommendation: AIRecommendation;
  quick_actions: QuickAction[];
  note: string;
}
