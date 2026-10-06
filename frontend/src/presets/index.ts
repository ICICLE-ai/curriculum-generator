import type { CurriculumPreset, PresetOption } from './types';
import { skinCancerPreset } from './skinCancer';
import { plantDiseasesPreset } from './plantDiseases';
import { foodPreset } from './food';

export * from './types';
export { skinCancerPreset } from './skinCancer';
export { plantDiseasesPreset } from './plantDiseases';
export { foodPreset } from './food';

export const PRESETS: Record<string, CurriculumPreset> = {
  skin_cancer: skinCancerPreset,
  plant_diseases: plantDiseasesPreset,
  food: foodPreset,
};

export const PRESET_OPTIONS: PresetOption[] = [
  { value: 'skin_cancer', label: skinCancerPreset.label },
  { value: 'plant_diseases', label: plantDiseasesPreset.label },
  { value: 'food', label: foodPreset.label },
  { value: 'custom', label: 'Custom (User-Defined / Blank)' },
];

export const DEFAULT_PRESET_KEY = 'skin_cancer';
