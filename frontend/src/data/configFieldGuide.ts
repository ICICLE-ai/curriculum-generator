export interface FieldGuideEntry {
  key: string;
  title: string;
  yamlPath: string;
  summary: string;
  detailedDescription: string;
  recommendation?: string;
  example?: string;
  category: 'Project' | 'Dataset' | 'Pipeline' | 'Execution' | 'Curriculum';
}

export const CONFIG_FIELD_GUIDE: Record<string, FieldGuideEntry> = {
  'project.domain': {
    key: 'project.domain',
    title: 'Subject Area & Field of Study',
    yamlPath: 'project.domain',
    category: 'Project',
    summary: 'Tells the AI lesson builder what academic discipline your course belongs to.',
    detailedDescription:
      'This sets the background context for all generated course materials. When the AI creates slide decks, quizzes, and coding labs, it uses this subject area to ensure all vocabulary, examples, and discussions make sense for your field.\n\nFor example, if you choose "Precision Agriculture", the lessons will discuss crop yields, soil types, and farm equipment. If you choose "Medical Diagnostics", the lessons will focus on patient imaging, clinical workflows, and diagnostic safety.',
    recommendation: 'Pick the broad academic or vocational field your students are studying (e.g., "Precision Agriculture & Farming", "Medical Imaging & Health", "Environmental Science").',
    example: 'domain: "Medical Imaging & Diagnostics"',
  },
  'project.context_statement': {
    key: 'project.context_statement',
    title: 'Course Problem Statement',
    yamlPath: 'project.context_statement',
    category: 'Project',
    summary: 'Describes the real-world challenge your students will solve in class.',
    detailedDescription:
      'This is the "story" behind your curriculum. The AI lesson writer uses this description to build realistic student assignments, classroom discussions, and practical coding exercises around a meaningful goal.\n\nStudents stay more engaged when they understand the purpose of the code they write (e.g., "Helping doctors detect early-stage skin cancer" or "Helping farmers spot crop diseases before they spread").',
    recommendation: 'Write a simple 1-2 sentence description of what students are learning to recognize from images.',
    example: 'context_statement: "diagnosing skin lesions as benign or malignant from dermatoscopic images"',
  },
  'project.use_case': {
    key: 'project.use_case',
    title: 'Curriculum Purpose Tag',
    yamlPath: 'project.use_case',
    category: 'Project',
    summary: 'Labels this configuration as an educational classroom curriculum.',
    detailedDescription:
      'Tells the system that this configuration is designed for student learning and classroom instruction rather than pure benchmark testing.',
    recommendation: 'Keep as "educational curriculum".',
    example: 'use_case: "educational curriculum"',
  },
  'dataset.root_path': {
    key: 'dataset.root_path',
    title: 'Classroom Image Folder Location',
    yamlPath: 'dataset.root_path',
    category: 'Dataset',
    summary: 'The folder path on the cluster server where your teaching photos are stored.',
    detailedDescription:
      'This tells the system where to find the collection of images your students will learn from. To help the computer understand the categories, organize your images into separate folders named after each category.\n\nExample Folder Layout:\n  my_dataset/\n    |_ healthy_crops/\n    |_ diseased_crops/\n    |_ weeds/\n\nEnsure this path points to a valid folder path on your system.',
    recommendation: 'Use the shared folder path provided by your system administrator or university cluster manager.',
    example: 'root_path: "/fs/ess/PAS2699/digitalAgEdu_datasets/skin_cancer_dataset"',
  },
  'output.directory': {
    key: 'output.directory',
    title: 'Saved Materials & Output Folder',
    yamlPath: 'output.directory',
    category: 'Dataset',
    summary: 'Where all student notebooks, slide decks, and lesson files will be saved.',
    detailedDescription:
      'When the generator finishes building your course, all your teaching materials will be neatly organized inside this folder.\n\nThis includes ready-to-use teacher slide decks, student Jupyter coding notebooks, completed solution answer keys, accuracy charts, and highlighted visual image samples.',
    recommendation: 'Give it a clear, descriptive name like "./output/fall2026_biology_unit" so you can easily find your files later.',
    example: 'directory: "./output/skin_cancer_v1"',
  },
  'pipeline.classification': {
    key: 'pipeline.classification',
    title: 'Image Categorization Stage (DINOv2)',
    yamlPath: 'pipeline.stages[0]',
    category: 'Pipeline',
    summary: 'Enables the AI vision model to automatically recognize and sort images into categories.',
    detailedDescription:
      'This stage runs a modern vision model (DINOv2) that learns to tell categories apart (for example, recognizing whether a leaf is healthy or has rust fungus).\n\nThe model generates accuracy scores, confusion charts, and example predictions that your students will analyze in their data analytics and machine learning lessons.',
    recommendation: 'Leave this turned ON for any course teaching students how computers recognize or categorize images.',
    example: 'stages:\n  - name: "Classification"\n    active: true\n    task_type: "medical_classification"',
  },
  'pipeline.segmentation': {
    key: 'pipeline.segmentation',
    title: 'Object Highlighting & Outlining Stage (SAM)',
    yamlPath: 'pipeline.stages[1]',
    category: 'Pipeline',
    summary: 'Draws precise visual outlines around specific objects or regions in each photo.',
    detailedDescription:
      'Using the Segment Anything Model (SAM), the system pinpoints and draws a clean outline around the exact item of interest in each picture (such as circling a mole on skin or isolating a weed in a field).\n\nIn class, students use these outlines in hands-on coding labs to measure surface area, calculate boundaries, and build interactive point-and-click tools.',
    recommendation: 'Describe what you want outlined in simple everyday words (e.g., "the weed", "the spot on the leaf", "the mole on the skin").',
    example: 'stages:\n  - name: "Segmentation"\n    active: true\n    task_type: "object_extraction"\n    prompt: "the skin lesion or mole, the dark spot on the skin"',
  },
  'pipeline.visual_xai': {
    key: 'pipeline.visual_xai',
    title: 'Visual AI Heatmaps & Transparency (Grad-CAM)',
    yamlPath: 'pipeline.stages[2]',
    category: 'Pipeline',
    summary: 'Generates glowing visual heatmaps showing which parts of an image the AI focused on.',
    detailedDescription:
      'This creates visual "attention heatmaps" that show exactly where the AI looked before making a decision. Areas that influenced the AI glow brightly, while ignored areas stay dark.\n\nThis is an incredible teaching tool for helping students understand AI transparency, ethics, and debugging—such as checking whether an AI made a diagnosis by looking at the actual disease or by mistakenly looking at a ruler in the background.',
    recommendation: 'Turn this ON if you want to teach students about trustworthy AI, ethics, and model verification.',
    example: 'stages:\n  - name: "VisualXAI"\n    active: true\n    task_type: "visual_explainibility"',
  },
  'execution.device': {
    key: 'execution.device',
    title: 'Computer Hardware (GPU vs CPU)',
    yamlPath: 'execution.device',
    category: 'Execution',
    summary: 'Controls whether the program runs on fast graphics processors (GPU) or regular computer chips (CPU).',
    detailedDescription:
      'Graphics cards ("cuda" / GPU) process hundreds of classroom images in minutes, whereas standard desktop processors ("cpu") can take several hours.\n\nWhen running on school or university computing clusters, the system automatically uses graphics cards for fast results.',
    recommendation: 'Keep set to "cuda" when running on cluster computers for 20x to 50x faster speed.',
    example: 'device: "cuda"',
  },
  'execution.batch_size': {
    key: 'execution.batch_size',
    title: 'Image Processing Batch Size',
    yamlPath: 'execution.batch_size',
    category: 'Execution',
    summary: 'How many classroom images the computer looks at at the same time.',
    detailedDescription:
      'Analyzing multiple photos simultaneously speeds up the workflow. If the computer runs out of memory, lowering this number allows it to process images in smaller, manageable groups without crashing.',
    recommendation: '16 is standard. If the computer gives an "Out of Memory" message, lower this value to 8 or 4.',
    example: 'batch_size: 16',
  },
  'execution.image_size': {
    key: 'execution.image_size',
    title: 'Standard Image Resolution',
    yamlPath: 'execution.image_size',
    category: 'Execution',
    summary: 'The standard square pixel size all teaching images are scaled to.',
    detailedDescription:
      'All classroom photos are resized to this square format so the AI vision models can analyze them consistently and produce uniform charts for student assignments.',
    recommendation: 'Keep this set to 518. This is the optimal resolution recommended by modern AI vision models for clear results.',
    example: 'image_size: 518',
  },
  'execution.seed': {
    key: 'execution.seed',
    title: 'Classroom Reproducibility Number',
    yamlPath: 'execution.seed',
    category: 'Execution',
    summary: 'A number that ensures every student gets identical, repeatable results in lab exercises.',
    detailedDescription:
      'In data science, random steps (like shuffling photos) can make results vary slightly each time. Setting a fixed "seed" number guarantees that the lesson you demonstrate at the front of the classroom matches what every student sees on their own computer screen.',
    recommendation: 'Pick any favorite whole number (like 42 or 6767) and keep it the same across your assignments.',
    example: 'seed: 6767',
  },
  'execution.llm_model': {
    key: 'execution.llm_model',
    title: 'AI Lesson Writer & Code Synthesizer',
    yamlPath: 'execution.llm_model',
    category: 'Execution',
    summary: 'The intelligent language model that drafts your syllabus, coding exercises, and student quizzes.',
    detailedDescription:
      'This powers the automated 3-tier teaching assistant system:\n• Agent 0 designs the pedagogical structure and student learning goals.\n• Agent 1 writes clean, heavily-commented Python starter code and solution keys.\n• Agent 2 tests all code automatically to ensure students never encounter broken exercises or syntax bugs.',
    recommendation: 'The default Qwen2.5-Coder-32B model produces clear, beginner-friendly Python code with thorough explanations.',
    example: 'llm_model: "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"',
  },
  'curriculum.subject': {
    key: 'curriculum.subject',
    title: 'Course & Unit Title',
    yamlPath: 'curriculum.subject',
    category: 'Curriculum',
    summary: 'The main course or unit name printed on all student worksheets and slide decks.',
    detailedDescription:
      'This title is printed at the top of every generated slide deck, student Jupyter notebook, printable PDF worksheet, and laboratory assignment guide.',
    recommendation: 'Use a descriptive title like "Introduction to AI in Agriculture: Week 1" or "High School Computer Vision Lab".',
    example: 'subject: "Intro to Medical AI: Skin Cancer Diagnostics"',
  },
  'curriculum.target_level': {
    key: 'curriculum.target_level',
    title: 'Student Grade & Experience Level',
    yamlPath: 'curriculum.target_level',
    category: 'Curriculum',
    summary: 'Tells the AI how simple or advanced to make the math, explanations, and Python code.',
    detailedDescription:
      'The lesson writer automatically calibrates its difficulty to match your classroom:\n• High School STEM: Focuses on intuition, visual concepts, simple step-by-step code, and minimal advanced math.\n• Undergraduate: Introduces PyTorch neural network building, data science metrics, and matrix operations.\n• Graduate / Research: Includes formal loss functions, model evaluation theory, and advanced deployment.',
    recommendation: 'Choose the grade level that matches your students (e.g., "High School STEM (Grades 10-12)" or "Undergraduate CS/AI").',
    example: 'target_level: "Undergraduate / Grade 10"',
  },
  'curriculum.modules': {
    key: 'curriculum.modules',
    title: 'Weekly Syllabus & Hands-On Coding Labs',
    yamlPath: 'curriculum.modules',
    category: 'Curriculum',
    summary: 'The week-by-week roadmap of lessons, coding exercises, and student milestones.',
    detailedDescription:
      'Each module represents a specific lesson topic in your course (e.g., Week 1: Loading Photos with Python, Week 2: Building a Classifier, Week 3: Interactive Object Outlining).\n\nFor every module you add, the AI generates a complete student coding notebook, an educator solution answer key, and review questions.',
    recommendation: 'Click "+ Add Module" to build your custom syllabus. Set week numbers and choose beginner, intermediate, or advanced difficulty.',
    example: 'modules:\n  - id: "numpy_basics"\n    title: "NumPy Basics & Data Structures"\n    week: 1\n    difficulty: "Beginner"',
  },
  'curriculum.topics': {
    key: 'curriculum.topics',
    title: 'Capstone Project Topic',
    yamlPath: 'curriculum.topics',
    category: 'Curriculum',
    summary: 'The main real-world application project students build toward throughout the course.',
    detailedDescription:
      'Specifies the primary capstone project that ties all weekly coding exercises together (such as "Building a Smartphone Crop Disease Classifier" or "Creating an AI Assistant for Dermatology").\n\nHaving a clear project helps students stay motivated and see how their code applies to real careers.',
    recommendation: 'Give your project an engaging name and describe how it helps people or solves an industry problem.',
    example: 'topics:\n  - name: "Skin Lesion Classification"\n    description: "Learn to build a vision model that can classify skin lesions as benign or malignant."\n    project: "Skin Cancer Diagnostic AI"',
  },
  'curriculum.resources': {
    key: 'curriculum.resources',
    title: 'Recommended Student Resource Links',
    yamlPath: 'curriculum.resources',
    category: 'Curriculum',
    summary: 'Helpful website links, dataset sources, or tutorials embedded in student notebooks.',
    detailedDescription:
      'These clickable links are embedded directly inside student coding notebooks and slide decks so learners can look up extra explanations, explore original dataset sources, or read beginner tutorials.',
    recommendation: 'Include links to where the dataset photos came from or beginner-friendly Python guides.',
    example: 'resources:\n  - name: "Skin Cancer Dataset Source"\n    url: "https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign"',
  },
};
