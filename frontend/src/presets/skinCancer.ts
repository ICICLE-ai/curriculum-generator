import type { CurriculumPreset } from './types';

export const skinCancerPreset: CurriculumPreset = {
  id: 'skin_cancer',
  label: 'Skin Lesion Diagnostics',
  domain: 'Medical Imaging & Diagnostics',
  contextStatement: 'diagnosing skin lesions as benign or malignant from dermatoscopic images',
  datasetPath: 'shared/smart_curriculum_designer_datasets/skin_cancer_dataset',
  datasetFolder: 'skin_cancer_dataset',
  outputPath: './output/skin_cancer_v1',
  subject: 'Intro to Medical AI: Skin Cancer Diagnostics',
  targetLevel: 'Undergraduate / Grade 10',
  segmentationPrompt: 'the skin lesion or mole, the dark spot on the skin',
  classificationTask: 'medical_classification',
  topicName: 'Skin Lesion Classification',
  topicDescription: 'Learn to build an AI vision model that can classify skin lesions as benign or malignant.',
  resources: [
    { name: 'Kaggle ISIC Skin Lesion Dataset', url: 'https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign' },
    { name: 'DINOv2 Foundation Docs', url: 'https://huggingface.co/docs/transformers/en/model_doc/dinov2' },
  ],
  modules: [
    {
      id: 'numpy_basics',
      title: 'NumPy Basics & Lesion Image Arrays',
      week: 1,
      context: 'Explore dermatoscopic lesion images, NumPy array representations, and pixel normalization.',
      difficulty: 'Beginner',
      learning_outcomes: [
        'Load and inspect 518x518 dermatoscopic RGB skin lesion photos.',
        'Normalize pixel values and calculate mean/std RGB distributions.',
        'Identify visual artifacts like skin markers, hair follicles, and lighting glares.',
      ],
    },
    {
      id: 'pandas_analytics',
      title: 'Pandas Diagnostic Analytics & Visualizations',
      week: 1,
      context: 'Analyze benign vs malignant class distributions, diagnostic metrics, and metadata in Pandas.',
      difficulty: 'Beginner',
      learning_outcomes: [
        'Compute melanoma class balance across diagnostic categories.',
        'Calculate sensitivity, specificity, and confusion matrix rates.',
        'Export structured diagnostic summary tables for clinical review.',
      ],
    },
    {
      id: 'pytorch_basics',
      title: 'PyTorch Lesion Classification Head',
      week: 2,
      context: 'Build a PyTorch classification head with Linear layers and Cross-Entropy loss for lesion diagnosis.',
      difficulty: 'Beginner',
      learning_outcomes: [
        'Construct a custom PyTorch linear classifier for foundation feature tokens.',
        'Implement gradient backpropagation with Adam optimizer and cross-entropy.',
        'Track training and validation accuracy across diagnostic epochs.',
      ],
    },
    {
      id: 'interactive_segmentation',
      title: 'Interactive Lesion Outlining with SAM',
      week: 3,
      context: 'Prompt Segment Anything Model (SAM) with coordinates to outline lesion borders and measure IoU overlap.',
      difficulty: 'Intermediate',
      learning_outcomes: [
        'Generate positive foreground prompt points on pigmented lesion borders.',
        'Extract binary segmentation masks isolating anomalous tissue.',
        'Calculate Intersection-over-Union (IoU) overlap metrics against expert clinical masks.',
      ],
    },
  ],
};
