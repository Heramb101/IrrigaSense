import type { AssessmentCreate, AssessmentRead, AssessmentUpdate } from '../types/assessment';

/**
 * Backend API Client Service
 * Configured for communication with FastAPI backend endpoints:
 * - POST /api/assessments
 * - GET  /api/assessments/{id}
 * - PUT  /api/assessments/{id}
 *
 * NOTE: Architecture stub only. Live API integration will be wired in subsequent milestones.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const assessmentApi = {
  /**
   * Submit a new completed farm assessment
   */
  async createAssessment(payload: AssessmentCreate): Promise<AssessmentRead> {
    const response = await fetch(`${API_BASE_URL}/assessments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Failed to create assessment: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Fetch an existing assessment by ID
   */
  async getAssessment(id: number): Promise<AssessmentRead> {
    const response = await fetch(`${API_BASE_URL}/assessments/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to retrieve assessment ${id}: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Update an in-progress or existing assessment by ID
   */
  async updateAssessment(id: number, payload: AssessmentUpdate): Promise<AssessmentRead> {
    const response = await fetch(`${API_BASE_URL}/assessments/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Failed to update assessment ${id}: ${response.statusText}`);
    }

    return response.json();
  },
};

export interface WeatherProfile {
  temperature_c: number;
  humidity_percent: number;
  precipitation_mm: number;
  wind_speed_kmh: number;
  et0_mm: number;
}

export interface EnvironmentalResponse {
  latitude: number;
  longitude: number;
  weather: WeatherProfile;
  source: string;
}

export const environmentApi = {
  /**
   * Fetch current normalized environmental weather data for confirmed coordinates
   */
  async getWeather(latitude: number, longitude: number): Promise<EnvironmentalResponse> {
    const params = new URLSearchParams({
      latitude: latitude.toString(),
      longitude: longitude.toString(),
    });
    const response = await fetch(`${API_BASE_URL}/environment/weather?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText;
      throw new Error(`Failed to fetch environmental weather: ${detail}`);
    }

    return response.json();
  },

  /**
   * Fetch normalized environmental soil profile from ISRIC SoilGrids for confirmed coordinates
   */
  async getSoil(latitude: number, longitude: number): Promise<SoilResponse> {
    const params = new URLSearchParams({
      latitude: latitude.toString(),
      longitude: longitude.toString(),
    });
    const response = await fetch(`${API_BASE_URL}/environment/soil?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText;
      throw new Error(`Failed to fetch environmental soil: ${detail}`);
    }

    return response.json();
  },
};

export interface SoilProfile {
  ph: number | null;
  nitrogen: number | null;
  organic_carbon: number | null;
  sand_percent: number | null;
  silt_percent: number | null;
  clay_percent: number | null;
  bulk_density: number | null;
}

export interface SoilResponse {
  latitude: number;
  longitude: number;
  soil: SoilProfile;
  depth: string;
  source: string;
}

export interface RecommendationRequest {
  crop_name: string;
  planting_date: string;
  current_soil_moisture?: number | null;
  predicted_moisture_24h?: number | null;
  clay_content?: number | null;
  temperature_2m?: number | null;
  relative_humidity_2m?: number | null;
  et0_fao?: number | null;
  irrigation_method?: string | null;
  water_availability?: string | null;
  farm_size?: string | null;
  evaluation_date?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface DecisionContext {
  irrigation_method: string;
  water_availability: string;
  farm_size: string;
}

export interface RecommendationResponse {
  decision: 'NO_IRRIGATION' | 'MONITOR' | 'IRRIGATION_RECOMMENDED' | 'IRRIGATION_URGENT' | 'INSUFFICIENT_CONFIDENCE';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'UNAVAILABLE';
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
  weather_summary?: {
    temperature_c?: number;
    humidity_percent?: number;
    et0_mm?: number;
    precipitation_mm?: number;
  } | null;
  last_updated?: string | null;
}

export const decisionApi = {
  /**
   * Fetches adaptive irrigation recommendation from the backend decision engine.
   */
  async getRecommendation(request: RecommendationRequest): Promise<RecommendationResponse> {
    const response = await fetch(`${API_BASE_URL}/decision/recommendation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText;
      throw new Error(`Failed to fetch irrigation recommendation: ${detail}`);
    }

    return response.json();
  },
};



