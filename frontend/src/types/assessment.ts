/**
 * Assessment Domain Types — Milestone 5B-R Simplified Farmer Workflow
 * Focused 6-Question Assessment Schema + Real Google Maps Location
 */

export interface LocationData {
  latitude: number;
  longitude: number;
  place_name?: string;
  location_name?: string; // backwards compatibility alias
  location_confirmed: boolean;
}

export interface FarmDetails {
  size_range: string;
  size_exact?: number | null;
  experience_years_range: string;
}

export interface LandHistory {
  previous_crops: string[];
  historical_problems: string[];
}

export interface SoilGridsData {
  ph?: number | null;
  clay?: number | null;
  sand?: number | null;
  organic_carbon?: number | null;
  nitrogen?: number | null;
}

export interface FarmerSoilReport {
  n?: number | null;
  p?: number | null;
  k?: number | null;
  ph?: number | null;
  units: Record<string, string>;
}

export interface ResolvedSoilData {
  n?: number | null;
  p?: number | null;
  k?: number | null;
  ph?: number | null;
  clay?: number | null;
  sand?: number | null;
  organic_carbon?: number | null;
}

export interface SoilData {
  soilgrids?: SoilGridsData | null;
  farmer_report?: FarmerSoilReport | null;
  resolved?: ResolvedSoilData | null;
  source: Record<string, string | null>;
  soilgrids_confirmed: boolean;
  has_soil_report: boolean;
  observed_drainage: string;
  soil_choice?: 'looks_correct' | 'have_soil_report' | 'not_sure' | null;
}

export interface WeatherData {
  api_current: Record<string, any>;
  farmer_confirmed: boolean;
  farmer_reported_weather: Record<string, any>;
  user_selection?: 'yes' | 'no' | null;
}

export interface CropData {
  current_crop_id: string;
  planting_date: string;
  is_approximate_planting_date: boolean;
  calculated_stage: string;
  farmer_confirmed_stage: string;
  health_condition: string;
  stage_choice?: 'yes' | 'no' | null;
}

export interface IrrigationData {
  method: string;
  water_source: string;
  water_reliability: string;
  current_frequency: string;
  last_irrigation?: string | null;
}

export interface FarmInputs {
  fertilizers: string[];
  pest_control: string[];
}

export interface GoalsData {
  farmer_goals: string[];
}

export interface AssessmentData {
  location: LocationData;
  crop: any;
  planting_date: string; // ISO date string YYYY-MM-DD
  farm_size: string;
  irrigation_method: string;
  water_availability: string;

  // Flattened convenience fields for UI & quick access
  latitude?: number;
  longitude?: number;
  place_name?: string;

  // Legacy compatibility fields (retained for un-migrated reference components)
  farm: FarmDetails;
  crop_details?: Record<string, any>;
  land_history: LandHistory;
  soil: SoilData;
  weather: WeatherData;
  irrigation: IrrigationData;
  farm_inputs: FarmInputs;
  goals: GoalsData;
}

export interface AssessmentPayloadData {
  latitude: number;
  longitude: number;
  place_name: string;
  location: LocationData;
  crop: string;
  planting_date: string;
  farm_size: string;
  irrigation_method: string;
  water_availability: string;
}

export interface AssessmentCreate {
  farm_id: number;
  assessment_version?: string;
  latitude: number;
  longitude: number;
  place_name: string;
  crop: string;
  planting_date: string;
  farm_size: string;
  irrigation_method: string;
  water_availability: string;
  data: AssessmentPayloadData;
}

export interface AssessmentUpdate {
  assessment_version?: string;
  data?: Partial<AssessmentPayloadData>;
}

export interface AssessmentRead {
  id: number;
  farm_id: number;
  assessment_version: string;
  data: AssessmentPayloadData;
}
