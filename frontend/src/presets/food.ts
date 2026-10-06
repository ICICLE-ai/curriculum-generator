import type { CurriculumPreset } from './types';

export const foodPreset: CurriculumPreset = {
  id: 'food',
  label: 'Culinary Dish Categorization (Nutrition)',
  domain: 'Nutritional Computing & Food Analytics',
  contextStatement: 'categorizing culinary dishes and ingredients for dietary tracking',
  datasetPath: 'shared/smart_curriculum_designer_datasets/food_dataset_10k',
  datasetFolder: 'food_dataset_10k',
  outputPath: './output/food_v1',
  subject: 'Foundations of Visual AI: Food Classification',
  targetLevel: 'Undergraduate / Grade 10',
  segmentationPrompt: 'the main food dish or culinary item',
  classificationTask: 'food_classification',
  topicName: 'Culinary Image Classification',
  topicDescription: 'Train computer vision models to distinguish diverse dishes and estimate nutritional components.',
  resources: [
    { name: 'ETHZ Food-101 Benchmark', url: 'https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/' },
    { name: 'PyTorch Torchvision Models', url: 'https://pytorch.org/vision/stable/models.html' },
  ],
  modules: [
    {
      id: 'food_image_prep',
      title: 'Food Dataset Exploration & Color Profiling',
      week: 1,
      context: 'Examine culinary photography, color variations in ingredients, and data augmentation techniques.',
      difficulty: 'Beginner',
      learning_outcomes: [
        'Explore plate photography under diverse lighting and camera angles.',
        'Apply geometric and color augmentations to reflect real-world cafeteria settings.',
        'Group dishes into broad nutritional dietary categories.',
      ],
    },
    {
      id: 'ingredient_classifier',
      title: 'PyTorch Deep Classifier for Dish Types',
      week: 2,
      context: 'Train multi-class PyTorch neural networks to recognize meal categories from visual features.',
      difficulty: 'Intermediate',
      learning_outcomes: [
        'Fine-tune pre-trained vision backbones on culinary photo datasets.',
        'Optimize training with cross-entropy loss and AdamW optimization.',
        'Produce top-1 and top-5 accuracy evaluation metrics across all food categories.',
      ],
    },
    {
      id: 'portion_segmentation',
      title: 'Portion Boundary Outlining with Foundation Models',
      week: 3,
      context: 'Segment individual food items on a plate using interactive SAM prompts to estimate meal portions.',
      difficulty: 'Intermediate',
      learning_outcomes: [
        'Prompt SAM to delineate discrete food items sharing a plate.',
        'Extract individual dish masks to compute pixel area ratios.',
        'Correlate segmented plate area with estimated dietary portion sizes.',
      ],
    },
  ],
};
