export interface CurriculumModule {
  id: string;
  title: string;
  week: number;
  context: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  learning_outcomes: string[];
}

export interface CurriculumResource {
  name: string;
  url: string;
}

export interface CurriculumPreset {
  id: string;
  label: string;
  domain: string;
  contextStatement: string;
  datasetPath: string;
  datasetFolder?: string;
  outputPath: string;
  subject: string;
  targetLevel?: string;
  segmentationPrompt: string;
  classificationTask: string;
  topicName: string;
  topicDescription: string;
  modules: CurriculumModule[];
  resources?: CurriculumResource[];
}

export interface PresetOption {
  value: string;
  label: string;
}
