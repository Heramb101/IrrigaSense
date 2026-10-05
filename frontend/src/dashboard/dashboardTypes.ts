/**
 * IrrigaSense Milestone 10 — Farmer Dashboard Types & Mappings
 * ============================================================
 * Provides clean, strongly-typed contracts for the post-assessment dashboard.
 * Encapsulates farmer-friendly status conversions, confidence classifications,
 * and operational contexts without leaking internal ML or ANFIS technicalities.
 */

export type IrrigationDecision =
  | 'NO_IRRIGATION'
  | 'MONITOR'
  | 'IRRIGATION_RECOMMENDED'
  | 'IRRIGATION_URGENT'
  | 'INSUFFICIENT_CONFIDENCE';

export type DecisionConfidence =
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'UNAVAILABLE';

export interface DecisionContext {
  irrigation_method: string;
  water_availability: string;
  farm_size: string;
}

export interface WeatherSummary {
  temperature_c?: number;
  humidity_percent?: number;
  et0_mm?: number;
  precipitation_mm?: number;
  wind_speed_kmh?: number;
}

export interface DashboardRecommendation {
  decision: IrrigationDecision;
  confidence: DecisionConfidence;
  current_moisture: number | null;
  predicted_moisture_24h: number | null;
  field_capacity: number | null;
  mad_threshold: number | null;
  depletion_fraction: number | null;
  moisture_state: string | null;
  crop: string;
  crop_stage: string;
  dap: number | null;
  reason: string;
  domain_status: string;
  warnings: string[];
  context: DecisionContext;
  weather_summary?: WeatherSummary | null;
  last_updated?: string | null;
}

export interface FarmLocationInfo {
  latitude: number;
  longitude: number;
  place_name: string;
}

export type StatusTheme = 'success' | 'warning' | 'alert' | 'urgent' | 'neutral';

export interface FarmerFriendlyStatus {
  label: string;
  icon: string;
  theme: StatusTheme;
  headline: string;
  badgeText: string;
}

/**
 * Translates raw backend decision enum values into clear, farmer-actionable language.
 * Guarantees zero raw enum values or technical ML jargon are shown to farmers.
 */
export function getFarmerFriendlyStatus(decision: IrrigationDecision): FarmerFriendlyStatus {
  switch (decision) {
    case 'NO_IRRIGATION':
      return {
        label: '🌱 No irrigation needed now',
        icon: '🌱',
        theme: 'success',
        headline: 'No Irrigation Needed Now',
        badgeText: 'Optimal Moisture',
      };
    case 'MONITOR':
      return {
        label: '👀 Monitor your field',
        icon: '👀',
        theme: 'warning',
        headline: 'Monitor Field Conditions',
        badgeText: 'Approaching Threshold',
      };
    case 'IRRIGATION_RECOMMENDED':
      return {
        label: '💧 Irrigation recommended',
        icon: '💧',
        theme: 'alert',
        headline: 'Irrigation Recommended',
        badgeText: 'Moisture Below Allowable Level',
      };
    case 'IRRIGATION_URGENT':
      return {
        label: '⚠️ Irrigation urgently recommended',
        icon: '⚠️',
        theme: 'urgent',
        headline: 'Urgent Irrigation Required',
        badgeText: 'Critical Soil Deficit',
      };
    case 'INSUFFICIENT_CONFIDENCE':
    default:
      return {
        label: 'ℹ️ More information is needed',
        icon: 'ℹ️',
        theme: 'neutral',
        headline: 'More Information Needed',
        badgeText: 'Guidance Pending Telemetry',
      };
  }
}

export interface FarmerFriendlyConfidence {
  label: string;
  tip?: string;
  badgeClass: string;
}

/**
 * Translates decision reliability classification into understandable phrasing.
 */
export function getFarmerFriendlyConfidence(
  confidence: DecisionConfidence,
  domainStatus?: string
): FarmerFriendlyConfidence {
  switch (confidence) {
    case 'HIGH':
      return {
        label: 'Recommendation confidence: High',
        tip: 'Verified against validated soil and atmospheric conditions.',
        badgeClass: 'conf-high',
      };
    case 'MEDIUM':
      return {
        label: 'Recommendation confidence: Medium',
        tip: 'Reliable guidance based on interpolated growth stage or regional soil baseline.',
        badgeClass: 'conf-medium',
      };
    case 'LOW':
      return {
        label: 'Recommendation confidence: Low',
        tip: 'Interpret with caution. Telemetry has missing secondary factors.',
        badgeClass: 'conf-low',
      };
    case 'UNAVAILABLE':
    default:
      return {
        label: 'Recommendation confidence: Unavailable',
        tip: domainStatus === 'GUARDRAIL_TRIGGERED'
          ? 'Current field observations fall outside our validated operating conditions.'
          : 'Unable to safely verify confidence.',
        badgeClass: 'conf-unavailable',
      };
  }
}
