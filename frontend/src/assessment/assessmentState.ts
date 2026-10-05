import type { AssessmentData } from '../types/assessment';
import type { QuestionId } from './assessmentConfig';

export interface AssessmentState {
  currentQuestionId: QuestionId;
  history: QuestionId[];
  data: AssessmentData;
  isSubmitting: boolean;
  isCompleted: boolean;
  hasReachedReview?: boolean;
  lastSavedAt?: string;
}

export const INITIAL_ASSESSMENT_DATA: AssessmentData = {
  location: {
    latitude: 0,
    longitude: 0,
    place_name: '',
    location_name: '',
    location_confirmed: false,
  },
  crop: '',
  planting_date: '',
  farm_size: '',
  irrigation_method: '',
  water_availability: '',
  latitude: 0,
  longitude: 0,
  place_name: '',

  // Retained defaults for legacy reference components
  farm: {
    size_range: '',
    size_exact: null,
    experience_years_range: '',
  },
  soil: {
    soilgrids: {
      ph: null,
      clay: null,
      sand: null,
      organic_carbon: null,
      nitrogen: null,
    },
    farmer_report: {
      n: null,
      p: null,
      k: null,
      ph: null,
      units: {},
    },
    resolved: {
      n: null,
      p: null,
      k: null,
      ph: null,
      clay: null,
      sand: null,
      organic_carbon: null,
    },
    source: {},
    soilgrids_confirmed: false,
    has_soil_report: false,
    observed_drainage: '',
    soil_choice: null,
  },
  weather: {
    api_current: {},
    farmer_confirmed: false,
    farmer_reported_weather: {},
    user_selection: null,
  },
  irrigation: {
    method: '',
    water_source: '',
    water_reliability: '',
    current_frequency: '',
    last_irrigation: null,
  },
  land_history: {
    previous_crops: [],
    historical_problems: [],
  },
  farm_inputs: {
    fertilizers: [],
    pest_control: [],
  },
  goals: {
    farmer_goals: [],
  },
};

export const INITIAL_ASSESSMENT_STATE: AssessmentState = {
  currentQuestionId: 'Q1',
  history: [],
  data: INITIAL_ASSESSMENT_DATA,
  isSubmitting: false,
  isCompleted: false,
  hasReachedReview: false,
};
