/**
 * Mock Environmental and External Data Service Types and Stubs
 * Used during local development and testing prior to live external API integration in Milestone 6.
 */

export interface MockLocationResponse {
  latitude: number;
  longitude: number;
  location_name: string;
  region: string;
}

export interface MockWeatherResponse {
  temperature_c: number;
  humidity_percent: number;
  precipitation_mm: number;
  condition: string;
  et0_mm_day: number;
  icon: string;
}

export interface MockSoilGridsResponse {
  ph: number;
  clay: number;
  sand: number;
  organic_carbon: number;
  nitrogen: number;
}

export interface MockCropStageResponse {
  calculated_stage: string;
  estimated_days_after_planting: number;
  confidence: 'high' | 'medium' | 'low';
}

export interface MockCropItem {
  id: string;
  name: string;
  category: string;
  typicalDurationDays: number;
  stages: string[];
}

export const PRESET_MOCK_LOCATIONS: MockLocationResponse[] = [
  {
    latitude: 18.5204,
    longitude: 73.8567,
    location_name: 'Pune District, Maharashtra',
    region: 'Western Maharashtra',
  },
  {
    latitude: 19.9975,
    longitude: 73.7898,
    location_name: 'Nashik Agricultural Zone, Maharashtra',
    region: 'Northern Maharashtra',
  },
  {
    latitude: 19.0948,
    longitude: 74.7480,
    location_name: 'Ahmednagar Farmlands, Maharashtra',
    region: 'Central Maharashtra',
  },
  {
    latitude: 21.1458,
    longitude: 79.0882,
    location_name: 'Nagpur Cotton Belt, Maharashtra',
    region: 'Vidarbha',
  },
];

export const MOCK_LOCATION_DATA: MockLocationResponse = PRESET_MOCK_LOCATIONS[0];

export const MOCK_WEATHER_DATA: MockWeatherResponse = {
  temperature_c: 28,
  humidity_percent: 78,
  precipitation_mm: 2.5,
  condition: 'Light rain',
  et0_mm_day: 4.2,
  icon: '🌦️',
};

export const MOCK_SOILGRIDS_DATA: MockSoilGridsResponse = {
  ph: 6.6,
  clay: 32.0,
  sand: 40.0,
  organic_carbon: 0.8,
  nitrogen: 0.15,
};

export const MOCK_CROPS_LIST: MockCropItem[] = [
  {
    id: 'wheat',
    name: 'Wheat (गेहूं)',
    category: 'Cereals & Grains',
    typicalDurationDays: 120,
    stages: ['Newly planted', 'Germination', 'Vegetative growth', 'Flowering', 'Fruiting / grain formation', 'Maturity'],
  },
  {
    id: 'rice_paddy',
    name: 'Rice / Paddy (चावल / धान)',
    category: 'Cereals & Grains',
    typicalDurationDays: 135,
    stages: ['Nursery / Seedling', 'Tillering', 'Panicle initiation', 'Flowering', 'Grain filling', 'Maturity'],
  },
  {
    id: 'cotton',
    name: 'Cotton (कपास)',
    category: 'Fiber & Commercial',
    typicalDurationDays: 165,
    stages: ['Seedling', 'Square formation', 'Flowering & Boll development', 'Boll opening', 'Maturity'],
  },
  {
    id: 'sugarcane',
    name: 'Sugarcane (गन्ना)',
    category: 'Commercial Crop',
    typicalDurationDays: 365,
    stages: ['Germination', 'Tillering', 'Grand growth phase', 'Ripening & Maturity'],
  },
  {
    id: 'maize',
    name: 'Maize / Corn (मक्का)',
    category: 'Cereals & Grains',
    typicalDurationDays: 100,
    stages: ['Emergence', 'Vegetative growth', 'Tasseling / Silking', 'Grain formation', 'Maturity'],
  },
  {
    id: 'soybean',
    name: 'Soybean (सोयाबीन)',
    category: 'Oilseeds & Legumes',
    typicalDurationDays: 95,
    stages: ['Emergence', 'Vegetative growth', 'Flowering', 'Pod development', 'Maturity'],
  },
  {
    id: 'chickpea',
    name: 'Chickpea / Bengal Gram (चना)',
    category: 'Pulses & Legumes',
    typicalDurationDays: 110,
    stages: ['Vegetative stage', 'Branching', 'Flowering', 'Pod filling', 'Maturity'],
  },
  {
    id: 'tomato',
    name: 'Tomato (टमाटर)',
    category: 'Vegetables',
    typicalDurationDays: 90,
    stages: ['Transplanting', 'Vegetative growth', 'Flowering', 'Fruit development', 'Ripening & Harvest'],
  },
  {
    id: 'onion',
    name: 'Onion (प्याज)',
    category: 'Vegetables',
    typicalDurationDays: 120,
    stages: ['Seedling establishment', 'Vegetative growth', 'Bulb initiation', 'Bulb enlargement', 'Maturity'],
  },
  {
    id: 'potato',
    name: 'Potato (आलू)',
    category: 'Vegetables',
    typicalDurationDays: 105,
    stages: ['Sprouting', 'Vegetative growth', 'Tuber initiation', 'Tuber bulking', 'Maturation'],
  },
  {
    id: 'chilli',
    name: 'Chilli (हरी मिर्च)',
    category: 'Spices & Vegetables',
    typicalDurationDays: 150,
    stages: ['Seedling', 'Vegetative branching', 'Flowering', 'Fruit development', 'Harvesting'],
  },
  {
    id: 'banana',
    name: 'Banana (केला)',
    category: 'Fruits & Plantation',
    typicalDurationDays: 330,
    stages: ['Shooting / Early vegetative', 'Stem elongation', 'Shooting / Inflorescence', 'Bunch development', 'Maturity'],
  },
];

/**
 * Calculates an estimated crop stage given planting date and crop type.
 */
export function calculateMockCropStage(
  _cropId: string,
  plantingDateStr: string
): MockCropStageResponse {
  if (!plantingDateStr) {
    return {
      calculated_stage: 'Vegetative growth',
      estimated_days_after_planting: 30,
      confidence: 'medium',
    };
  }

  const plantingDate = new Date(plantingDateStr);
  const now = new Date();
  const diffTime = Math.max(0, now.getTime() - plantingDate.getTime());
  const days = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  let calculatedStage = 'Vegetative growth';

  if (days <= 10) {
    calculatedStage = 'Newly planted / Germination';
  } else if (days <= 30) {
    calculatedStage = 'Early growth';
  } else if (days <= 60) {
    calculatedStage = 'Vegetative growth';
  } else if (days <= 90) {
    calculatedStage = 'Flowering & Fruit formation';
  } else if (days <= 120) {
    calculatedStage = 'Maturity';
  } else {
    calculatedStage = 'Near harvest';
  }

  return {
    calculated_stage: calculatedStage,
    estimated_days_after_planting: days,
    confidence: 'high',
  };
}
