import type { AssessmentData } from '../types/assessment';

export type QuestionId =
  | 'Q1'
  | 'Q2'
  | 'Q3'
  | 'Q4'
  | 'Q5'
  | 'Q6'
  | 'REVIEW';

export type AssessmentSectionId =
  | 'location'
  | 'crop'
  | 'planting_date'
  | 'farm_size'
  | 'irrigation_method'
  | 'water_availability'
  | 'review';

export type InputType =
  | 'map_picker'
  | 'crop_selector'
  | 'date_picker'
  | 'radio'
  | 'review_summary';

export interface QuestionOption {
  value: string;
  label: string;
  description?: string;
  icon?: string;
}

export interface QuestionDefinition {
  id: QuestionId;
  section: AssessmentSectionId;
  title: string;
  subtitle?: string;
  helpText?: string;
  inputType: InputType;
  options?: QuestionOption[];
  required: boolean;
  dataPath: string;
  allowOther?: boolean;
  condition?: any;
}

export interface SectionMetadata {
  id: AssessmentSectionId;
  title: string;
  description: string;
  order: number;
}

export const ASSESSMENT_SECTIONS: Record<AssessmentSectionId, SectionMetadata> = {
  location: {
    id: 'location',
    title: 'Farm Location',
    description: 'Pinpoint your farmland coordinates using Google Maps',
    order: 1,
  },
  crop: {
    id: 'crop',
    title: 'Current Crop',
    description: 'Select your main crop for this cultivation cycle',
    order: 2,
  },
  planting_date: {
    id: 'planting_date',
    title: 'Planting Date',
    description: 'Sowing or transplanting timeline for this crop',
    order: 3,
  },
  farm_size: {
    id: 'farm_size',
    title: 'Farm Size',
    description: 'Total cultivated acreage of your farm plot',
    order: 4,
  },
  irrigation_method: {
    id: 'irrigation_method',
    title: 'Irrigation Method',
    description: 'How water is applied to your field',
    order: 5,
  },
  water_availability: {
    id: 'water_availability',
    title: 'Water Availability',
    description: 'Irrigation water supply reliability and volume',
    order: 6,
  },
  review: {
    id: 'review',
    title: 'Review Answers',
    description: 'Confirm your answers before completing setup',
    order: 7,
  },
};

export const ASSESSMENT_CONFIG: Record<QuestionId, QuestionDefinition> = {
  Q1: {
    id: 'Q1',
    section: 'location',
    title: 'Where is your farm located?',
    subtitle: 'Pinpoint your farm on the interactive Google Map or search for your village.',
    helpText: 'Search your area, drag the pin to your farm plot, and confirm the location coordinates.',
    inputType: 'map_picker',
    required: true,
    dataPath: 'location',
  },
  Q2: {
    id: 'Q2',
    section: 'crop',
    title: 'What crop are you currently growing?',
    subtitle: 'Select the primary crop you are growing in this field.',
    helpText: 'Use search or tap a category to quickly select your crop.',
    inputType: 'crop_selector',
    required: true,
    dataPath: 'crop',
  },
  Q3: {
    id: 'Q3',
    section: 'planting_date',
    title: 'When did you plant/sow this crop?',
    subtitle: 'Select the date when seeds were sown or seedlings were transplanted.',
    helpText: 'Use the quick preset chips or select the date from the calendar.',
    inputType: 'date_picker',
    required: true,
    dataPath: 'planting_date',
  },
  Q4: {
    id: 'Q4',
    section: 'farm_size',
    title: 'How large is your farm?',
    subtitle: 'Choose your total cultivated acreage.',
    inputType: 'radio',
    required: true,
    dataPath: 'farm_size',
    options: [
      {
        value: 'Less than 1 acre',
        label: 'Less than 1 acre',
        description: 'Smallholding / Marginal farm (< 0.4 ha)',
      },
      {
        value: '1–2 acres',
        label: '1–2 acres',
        description: 'Small family farm (0.4 – 0.8 ha)',
      },
      {
        value: '2–5 acres',
        label: '2–5 acres',
        description: 'Medium family farm (0.8 – 2.0 ha)',
      },
      {
        value: '5–10 acres',
        label: '5–10 acres',
        description: 'Semi-medium commercial farm (2.0 – 4.0 ha)',
      },
      {
        value: '10–25 acres',
        label: '10–25 acres',
        description: 'Medium to large farm (4.0 – 10 ha)',
      },
      {
        value: 'More than 25 acres',
        label: 'More than 25 acres',
        description: 'Large commercial farming operation (> 10 ha)',
      },
    ],
  },
  Q5: {
    id: 'Q5',
    section: 'irrigation_method',
    title: 'How do you currently irrigate your farm?',
    subtitle: 'Select the primary irrigation method used for this plot.',
    inputType: 'radio',
    required: true,
    dataPath: 'irrigation_method',
    options: [
      {
        value: 'Drip',
        label: 'Drip',
        description: 'Precision emitters / micro-irrigation at root zone',
        icon: '💧',
      },
      {
        value: 'Sprinkler',
        label: 'Sprinkler',
        description: 'Overhead spray nozzles mimicking rainfall',
        icon: '🌧️',
      },
      {
        value: 'Flood',
        label: 'Flood',
        description: 'Basin / surface flooding across the entire plot',
        icon: '🌊',
      },
      {
        value: 'Furrow',
        label: 'Furrow',
        description: 'Water channeled along trenches between ridges',
        icon: '〰️',
      },
      {
        value: 'Rain-fed',
        label: 'Rain-fed',
        description: 'No active irrigation; relies solely on rainfall',
        icon: '🌦️',
      },
      {
        value: 'Other',
        label: 'Other',
        description: 'Manual watering, portable pumps, or other custom methods',
        icon: '⚙️',
      },
    ],
  },
  Q6: {
    id: 'Q6',
    section: 'water_availability',
    title: 'How much water is usually available for irrigation?',
    subtitle: 'Choose the option that best describes your water security.',
    inputType: 'radio',
    required: true,
    dataPath: 'water_availability',
    options: [
      {
        value: 'Plenty',
        label: 'Plenty',
        description: 'Abundant water supply (canal, deep borewell, perennial river)',
        icon: '🟢',
      },
      {
        value: 'Limited',
        label: 'Limited',
        description: 'Adequate for scheduled turns, but requires careful water conservation',
        icon: '🟡',
      },
      {
        value: 'Very limited',
        label: 'Very limited',
        description: 'Scarcity; struggling to meet full crop water requirements',
        icon: '🔴',
      },
      {
        value: 'Depends mainly on rainfall',
        label: 'Depends mainly on rainfall',
        description: 'Open wells/ponds that fluctuate heavily with monsoon rains',
        icon: '🌧️',
      },
    ],
  },
  REVIEW: {
    id: 'REVIEW',
    section: 'review',
    title: 'Review Your Farm Setup',
    subtitle: 'Verify your 6 answers before completing your farm profile.',
    inputType: 'review_summary',
    required: false,
    dataPath: '',
  },
};

export const QUESTION_SEQUENCE: QuestionId[] = [
  'Q1',
  'Q2',
  'Q3',
  'Q4',
  'Q5',
  'Q6',
  'REVIEW',
];

export function isQuestionActive(
  questionId: QuestionId,
  _data: AssessmentData,
  _config?: Record<QuestionId, QuestionDefinition>
): boolean {
  return QUESTION_SEQUENCE.includes(questionId);
}

export function getNextActiveQuestionId(
  currentId: QuestionId,
  _data: AssessmentData,
  _config?: Record<QuestionId, QuestionDefinition>
): QuestionId | null {
  const currentIndex = QUESTION_SEQUENCE.indexOf(currentId);
  if (currentIndex === -1 || currentIndex >= QUESTION_SEQUENCE.length - 1) {
    return null;
  }
  return QUESTION_SEQUENCE[currentIndex + 1];
}

export function getPreviousActiveQuestionId(
  currentId: QuestionId,
  _data: AssessmentData,
  _config?: Record<QuestionId, QuestionDefinition>
): QuestionId | null {
  const currentIndex = QUESTION_SEQUENCE.indexOf(currentId);
  if (currentIndex <= 0) {
    return null;
  }
  return QUESTION_SEQUENCE[currentIndex - 1];
}

export function validateAssessmentStep(
  questionId: QuestionId,
  data: AssessmentData
): { isValid: boolean; errorMessage?: string } {
  switch (questionId) {
    case 'Q1': {
      if (!data.location || !data.location.latitude || !data.location.longitude) {
        return {
          isValid: false,
          errorMessage: 'Please select and pin your farm location on the map.',
        };
      }
      if (!data.location.location_confirmed) {
        return {
          isValid: false,
          errorMessage: 'Please confirm your farm location by clicking "Confirm Location".',
        };
      }
      return { isValid: true };
    }
    case 'Q2': {
      const crop = typeof data.crop === 'string' ? data.crop : (data.crop as any)?.current_crop_id;
      if (!crop || crop.trim() === '') {
        return {
          isValid: false,
          errorMessage: 'Please select the crop you are currently growing.',
        };
      }
      return { isValid: true };
    }
    case 'Q3': {
      const date = data.planting_date || (data.crop as any)?.planting_date;
      if (!date || date.trim() === '') {
        return {
          isValid: false,
          errorMessage: 'Please specify the planting or sowing date.',
        };
      }
      return { isValid: true };
    }
    case 'Q4': {
      const size = data.farm_size || (data.farm as any)?.size_range;
      if (!size || size.trim() === '') {
        return {
          isValid: false,
          errorMessage: 'Please select the size of your farm.',
        };
      }
      return { isValid: true };
    }
    case 'Q5': {
      const method = data.irrigation_method || (data.irrigation as any)?.method;
      if (!method || method.trim() === '') {
        return {
          isValid: false,
          errorMessage: 'Please select your current irrigation method.',
        };
      }
      return { isValid: true };
    }
    case 'Q6': {
      const avail = data.water_availability || (data.irrigation as any)?.water_reliability;
      if (!avail || avail.trim() === '') {
        return {
          isValid: false,
          errorMessage: 'Please indicate water availability for irrigation.',
        };
      }
      return { isValid: true };
    }
    case 'REVIEW':
      return { isValid: true };
    default:
      return { isValid: true };
  }
}
