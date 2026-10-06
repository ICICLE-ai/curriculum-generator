import type { CurriculumPreset } from './types';

export const plantDiseasesPreset: CurriculumPreset = {
  id: 'plant_diseases',
  label: 'Crop Leaf Disease Detection (Agriculture)',
  domain: 'Agricultural Crop Health',
  contextStatement: 'identifying crop leaf blight and foliar pathogens in agricultural fields',
  datasetPath: 'shared/smart_curriculum_designer_datasets/plant_dataset',
  datasetFolder: 'plant_dataset',
  outputPath: './output/plant_diseases_v1',
  subject: 'Intro to Agricultural AI: Plant Disease Detection',
  targetLevel: 'Undergraduate / Grade 10',
  segmentationPrompt: 'the diseased leaf spot or infected foliage',
  classificationTask: 'crop_disease_classification',
  topicName: 'Crop Foliage Pathology',
  topicDescription: 'Learn to identify foliar crop infections and train vision transformers on drone farm photography.',
  resources: [
    { name: 'PlantVillage Benchmark Dataset', url: 'https://github.com/spMohanty/PlantVillage-Dataset' },
    { name: 'Segment Anything (SAM) Repository', url: 'https://github.com/facebookresearch/segment-anything' },
  ],
  modules: [
    {
      id: 'leaf_image_exploration',
      title: 'Agricultural Imaging & Foliar Symptom Exploration',
      week: 1,
      context: 'Inspect foliar lesion patterns, color channel distributions (chlorophyll green vs chlorosis/necrosis yellow-brown), and class balance in plant pathology datasets.',
      difficulty: 'Beginner',
      learning_outcomes: [
        'Analyze multispectral and RGB leaf imagery across healthy and infected crop specimens.',
        'Calculate pathogen class distributions, identifying minority blight classes and class imbalance.',
        'Build exploratory image processing pipelines to compute greenness indices and color channel histograms.',
      ],
    },
    {
      id: 'morphological_feature_extraction',
      title: 'Handcrafted Morphological Descriptors & Baseline Classifiers',
      week: 2,
      context: 'Extract handcrafted textural (GLCM), color moment, and morphological lesion contours to train classical machine learning baselines for foliar disease classification.',
      difficulty: 'Intermediate',
      learning_outcomes: [
        'Extract gray-level co-occurrence matrix (GLCM) texture features and color moments from leaf lesions.',
        'Train classical baseline models (support vector machines, random forests) on extracted tabular features.',
        'Evaluate baseline classification performance across crop species using precision, recall, and multi-class F1-scores.',
      ],
    },
    {
      id: 'dinov2_representation_learning',
      title: 'Self-Supervised Feature Embeddings with DINOv2',
      week: 3,
      context: 'Extract high-dimensional visual embeddings from pre-trained DINOv2 foundation models and implement PyTorch classification heads for fine-grained leaf pathology.',
      difficulty: 'Intermediate',
      learning_outcomes: [
        'Extract 768-dimensional visual patch tokens using pre-trained DINOv2 ViT backbones.',
        'Design and train lightweight PyTorch classification adapters on frozen foundation embeddings.',
        'Analyze t-SNE and PCA embedding clusters to visualize semantic separation between foliar pathogen variants.',
      ],
    },
    {
      id: 'sam_zero_shot_segmentation',
      title: 'Zero-Shot Foliar Lesion Segmentation with SAM',
      week: 4,
      context: 'Deploy Segment Anything Model (SAM) with point and bounding box prompts to delineate necrosis boundaries on infected leaves and quantify damaged surface area.',
      difficulty: 'Intermediate',
      learning_outcomes: [
        'Formulate automated point and bounding box prompt coordinates over infected foliar regions.',
        'Generate binary segmentation masks with SAM to measure necrotic tissue percentage across the leaf surface.',
        'Benchmark mask precision against ground-truth pathology annotations using Intersection-over-Union (IoU).',
      ],
    },
  ],
};
