import React, { useState } from 'react';
import { CONFIG_FIELD_GUIDE, type FieldGuideEntry } from '../data/configFieldGuide';
import { FieldHelpModal } from '../components/FieldHelpModal';

export interface CurriculumModule {
  id: string;
  title: string;
  week: number;
  context: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
}

export interface CurriculumResource {
  name: string;
  url: string;
}

export const ConfigPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'project' | 'pipeline' | 'curriculum' | 'execution'>('project');
  const [activeHelpField, setActiveHelpField] = useState<FieldGuideEntry | null>(null);

  // 1. Course & Dataset
  const [domain, setDomain] = useState<string>('Medical Imaging & Diagnostics');
  const [contextStatement, setContextStatement] = useState<string>('diagnosing skin lesions as benign or malignant from dermatoscopic images');
  const [useCase] = useState<string>('educational curriculum');
  const [datasetPath, setDatasetPath] = useState<string>('/fs/ess/PAS2699/digitalAgEdu_datasets/skin_cancer_dataset');
  const [outputPath, setOutputPath] = useState<string>('./output/skin_cancer_v1');

  // 2. AI Vision Tools
  const [classificationActive, setClassificationActive] = useState<boolean>(true);
  const [classificationTask, setClassificationTask] = useState<string>('medical_classification');
  
  const [segmentationActive, setSegmentationActive] = useState<boolean>(true);
  const [segmentationPrompt, setSegmentationPrompt] = useState<string>('the skin lesion or mole, the dark spot on the skin');

  const [xaiActive, setXaiActive] = useState<boolean>(false);

  // 3. Lab Execution Settings
  const [device] = useState<string>('cuda');
  const [batchSize, setBatchSize] = useState<number>(16);
  const [imageSize, setImageSize] = useState<number>(518);
  const [seed, setSeed] = useState<number>(6767);
  const [llmModel, setLlmModel] = useState<string>('Qwen/Qwen2.5-Coder-32B-Instruct-AWQ');

  // 4. Syllabus & Lessons
  const [subject, setSubject] = useState<string>('Intro to Medical AI: Skin Cancer Diagnostics');
  const [targetLevel, setTargetLevel] = useState<string>('Undergraduate / Grade 10');
  
  // Dynamic Modules List
  const [modules, setModules] = useState<CurriculumModule[]>([
    {
      id: 'numpy_basics',
      title: 'NumPy Basics & Image Arrays',
      week: 1,
      context: 'Explore dataset images, NumPy array operations, and pixel normalization.',
      difficulty: 'Beginner',
    },
    {
      id: 'pandas_analytics',
      title: 'Pandas Data Analytics & Visualizations',
      week: 1,
      context: 'Analyze accuracy metrics, loss curves, and diagnostic distributions.',
      difficulty: 'Beginner',
    },
    {
      id: 'pytorch_basics',
      title: 'PyTorch Neural Networks',
      week: 2,
      context: 'Build a Multi-Layer Perceptron (MLP) image classifier with Cross-Entropy Loss.',
      difficulty: 'Beginner',
    },
    {
      id: 'interactive_segmentation',
      title: 'Interactive Object Outlining with SAM',
      week: 3,
      context: 'Build an interactive image segmentation tool and calculate IoU overlap metrics.',
      difficulty: 'Intermediate',
    },
  ]);

  // Topics & Capstone
  const [topicName, setTopicName] = useState<string>('Skin Lesion Classification');
  const [topicDescription, setTopicDescription] = useState<string>('Learn to build an AI vision model that can classify skin lesions as benign or malignant.');
  const [projectName, setProjectName] = useState<string>('Skin Cancer Diagnostic AI');

  // Dynamic Multiple Resources
  const [resources, setResources] = useState<CurriculumResource[]>([
    { name: 'Dataset Source', url: 'https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign' },
    { name: 'DINOv2 Documentation', url: 'https://huggingface.co/docs/transformers/en/model_doc/dinov2' },
  ]);

  const [copied, setCopied] = useState<boolean>(false);

  // Help Button Helper
  const renderHelpBtn = (key: string) => {
    const entry = CONFIG_FIELD_GUIDE[key];
    if (!entry) return null;
    return (
      <button
        type="button"
        className="help-icon-btn"
        onClick={() => setActiveHelpField(entry)}
        title={`Learn about ${entry.title}`}
        aria-label={`Help for ${entry.title}`}
      >
        ?
      </button>
    );
  };

  // Dynamic Module Actions
  const handleAddModule = () => {
    const nextWeek = modules.length > 0 ? Math.max(...modules.map((m) => m.week)) + 1 : 1;
    const newModuleId = `custom_module_${modules.length + 1}`;
    setModules([
      ...modules,
      {
        id: newModuleId,
        title: `Custom Lesson ${modules.length + 1}`,
        week: nextWeek,
        context: 'Implement hands-on coding exercise and analyze model outputs.',
        difficulty: 'Intermediate',
      },
    ]);
  };

  const handleRemoveModule = (index: number) => {
    setModules(modules.filter((_, idx) => idx !== index));
  };

  const handleUpdateModule = (index: number, field: keyof CurriculumModule, value: string | number) => {
    setModules(
      modules.map((m, idx) => {
        if (idx !== index) return m;
        const updated = { ...m, [field]: value };
        if (field === 'title') {
          const autoId = String(value)
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '');
          if (autoId) updated.id = autoId;
        }
        return updated;
      })
    );
  };

  // Dynamic Resource Actions
  const handleAddResource = () => {
    setResources([
      ...resources,
      { name: `Resource ${resources.length + 1}`, url: 'https://' },
    ]);
  };

  const handleRemoveResource = (index: number) => {
    setResources(resources.filter((_, idx) => idx !== index));
  };

  const handleUpdateResource = (index: number, field: keyof CurriculumResource, value: string) => {
    setResources(
      resources.map((r, idx) => (idx === index ? { ...r, [field]: value } : r))
    );
  };

  const generateYaml = (): string => {
    let yaml = `# ==============================================================================
# DIGITALAGEDU EXPERIMENT CONFIGURATION
# Auto-generated by DigitalAgEdu Curriculum Builder
# ==============================================================================

# ===============
# Project Context
# ===============
project:
  domain: "${domain}"
  context_statement: "${contextStatement}"
  use_case: "${useCase}"

# ================
# Dataset Settings
# ================
dataset:
  root_path: "${datasetPath}"

output:
  directory: "${outputPath}"

# ================
# Pipeline Stages
# ================
pipeline:
  stages:
    - name: "Classification"
      active: ${classificationActive}
      task_type: "${classificationTask}"

    - name: "Segmentation"
      active: ${segmentationActive}
      task_type: "object_extraction"
      prompt: "${segmentationPrompt}"

    - name: "VisualXAI"
      active: ${xaiActive}
      task_type: "visual_explainibility"

# ============
# Execution
# ============
execution:
  device: "${device}"
  batch_size: ${batchSize}
  image_size: ${imageSize}
  max_samples: null
  seed: ${seed}

  # Phase 2 LLM Setup
  use_llm: true
  llm_model: "${llmModel}"

# ==================
# Curriculum Config
# ==================
curriculum:
  subject: "${subject}"
  target_level: "${targetLevel}"
  model: "${llmModel}"

  modules:
`;

    modules.forEach((m) => {
      yaml += `    - id: "${m.id}"
      title: "${m.title}"
      week: ${m.week}
      context: "${m.context}"
      difficulty: "${m.difficulty}"
`;
    });

    yaml += `
  topics:
    - name: "${topicName}"
      description: "${topicDescription}"
      project: "${projectName}"

  resources:
`;

    resources.forEach((r) => {
      yaml += `    - name: "${r.name}"
      url: "${r.url}"
`;
    });

    return yaml;
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generateYaml());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const yaml = generateYaml();
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'config.yaml';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page-container">
      {/* Help Modal Component */}
      <FieldHelpModal entry={activeHelpField} onClose={() => setActiveHelpField(null)} />

      <div style={{ marginBottom: '0.75rem' }}>
        <h1 className="page-title">Curriculum & Lesson Builder</h1>
        <p className="page-description" style={{ marginBottom: '0.75rem' }}>
          Design custom AI lesson plans, slide decks, and student coding exercises tailored to your subject area.
        </p>
      </div>

      <div className="grid-2" style={{ alignItems: 'stretch' }}>
        {/* Left Column: Config Builder Controls */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', marginBottom: 0 }}>
          {/* Sub-navigation Tabs */}
          <div style={{ display: 'flex', gap: '0.25rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem', marginBottom: '0.75rem' }}>
            <button
              type="button"
              className={`nav-tab ${activeSection === 'project' ? 'active' : ''}`}
              onClick={() => setActiveSection('project')}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.775rem' }}
            >
              1. Course & Data
            </button>
            <button
              type="button"
              className={`nav-tab ${activeSection === 'pipeline' ? 'active' : ''}`}
              onClick={() => setActiveSection('pipeline')}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.775rem' }}
            >
              2. AI Vision Tools
            </button>
            <button
              type="button"
              className={`nav-tab ${activeSection === 'curriculum' ? 'active' : ''}`}
              onClick={() => setActiveSection('curriculum')}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.775rem' }}
            >
              3. Syllabus & Labs
            </button>
            <button
              type="button"
              className={`nav-tab ${activeSection === 'execution' ? 'active' : ''}`}
              onClick={() => setActiveSection('execution')}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.775rem' }}
            >
              4. Lab Settings
            </button>
          </div>

          {/* Section 1: Course & Data */}
          {activeSection === 'project' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>
                  Subject Area / Field of Study {renderHelpBtn('project.domain')}
                </label>
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="e.g. Precision Agriculture, Medical Diagnostics"
                  style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>
                  Course Problem Statement {renderHelpBtn('project.context_statement')}
                </label>
                <input
                  type="text"
                  value={contextStatement}
                  onChange={(e) => setContextStatement(e.target.value)}
                  placeholder="e.g. identifying crop diseases from drone photos"
                  style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>
                  Classroom Image Folder Path {renderHelpBtn('dataset.root_path')}
                </label>
                <input
                  type="text"
                  value={datasetPath}
                  onChange={(e) => setDatasetPath(e.target.value)}
                  placeholder="/fs/ess/PAS2699/my_classroom_dataset"
                  style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem', fontFamily: 'var(--font-mono)' }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>
                  Saved Materials & Output Folder {renderHelpBtn('output.directory')}
                </label>
                <input
                  type="text"
                  value={outputPath}
                  onChange={(e) => setOutputPath(e.target.value)}
                  placeholder="./output/fall2026_biology_unit"
                  style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem', fontFamily: 'var(--font-mono)' }}
                />
              </div>
            </div>
          )}

          {/* Section 2: AI Vision Tools */}
          {activeSection === 'pipeline' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ padding: '0.65rem', background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                      type="checkbox"
                      id="stage_classification"
                      checked={classificationActive}
                      onChange={(e) => setClassificationActive(e.target.checked)}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <label htmlFor="stage_classification" style={{ fontWeight: 600, fontSize: '0.825rem', cursor: 'pointer' }}>
                      Image Categorization (DINOv2)
                    </label>
                  </div>
                  {renderHelpBtn('pipeline.classification')}
                </div>
                {classificationActive && (
                  <input
                    type="text"
                    value={classificationTask}
                    onChange={(e) => setClassificationTask(e.target.value)}
                    placeholder="Task Type (e.g. crop_disease_classification)"
                    style={{ padding: '0.35rem 0.5rem', fontSize: '0.775rem' }}
                  />
                )}
              </div>

              <div style={{ padding: '0.65rem', background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                      type="checkbox"
                      id="stage_segmentation"
                      checked={segmentationActive}
                      onChange={(e) => setSegmentationActive(e.target.checked)}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <label htmlFor="stage_segmentation" style={{ fontWeight: 600, fontSize: '0.825rem', cursor: 'pointer' }}>
                      Object Highlighting & Outlining (SAM)
                    </label>
                  </div>
                  {renderHelpBtn('pipeline.segmentation')}
                </div>
                {segmentationActive && (
                  <input
                    type="text"
                    value={segmentationPrompt}
                    onChange={(e) => setSegmentationPrompt(e.target.value)}
                    placeholder="Describe object to outline (e.g. the weed, the lesion, the crop leaf)"
                    style={{ padding: '0.35rem 0.5rem', fontSize: '0.775rem' }}
                  />
                )}
              </div>

              <div style={{ padding: '0.65rem', background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="stage_xai"
                    checked={xaiActive}
                    onChange={(e) => setXaiActive(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <label htmlFor="stage_xai" style={{ fontSize: '0.825rem', fontWeight: 600, cursor: 'pointer' }}>
                    Visual AI Heatmaps & Transparency (Grad-CAM)
                  </label>
                </div>
                {renderHelpBtn('pipeline.visual_xai')}
              </div>
            </div>
          )}

          {/* Section 3: Syllabus & Dynamic Modules & Multiple Resources */}
          {activeSection === 'curriculum' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div className="grid-2" style={{ gap: '0.5rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Course / Unit Title {renderHelpBtn('curriculum.subject')}
                  </label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="e.g. Intro to Agricultural AI"
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Student Grade Level {renderHelpBtn('curriculum.target_level')}
                  </label>
                  <input
                    type="text"
                    value={targetLevel}
                    onChange={(e) => setTargetLevel(e.target.value)}
                    placeholder="e.g. High School STEM or Undergraduate CS"
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
              </div>

              {/* Dynamic Module Builder with + Add Button */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: 0 }}>
                    Curriculum Modules & Weekly Labs ({modules.length}) {renderHelpBtn('curriculum.modules')}
                  </label>
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={handleAddModule}
                    style={{ padding: '0.2rem 0.55rem', fontSize: '0.75rem' }}
                  >
                    + Add Module
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', maxHeight: '130px', overflowY: 'auto', paddingRight: '0.25rem' }}>
                  {modules.map((m, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.3rem',
                        padding: '0.45rem 0.65rem',
                        background: 'var(--bg-card-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.775rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <input
                          type="text"
                          value={m.title}
                          onChange={(e) => handleUpdateModule(idx, 'title', e.target.value)}
                          placeholder="Lesson Title (e.g. Intro to Image Data)..."
                          style={{ flex: 1, padding: '0.25rem 0.45rem', fontSize: '0.775rem', fontWeight: 600 }}
                        />
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Wk</span>
                          <input
                            type="number"
                            min="1"
                            max="52"
                            value={m.week}
                            onChange={(e) => handleUpdateModule(idx, 'week', Number(e.target.value))}
                            style={{ width: '42px', padding: '0.25rem 0.35rem', fontSize: '0.75rem', textAlign: 'center' }}
                          />
                        </div>
                        <select
                          value={m.difficulty}
                          onChange={(e) => handleUpdateModule(idx, 'difficulty', e.target.value as 'Beginner' | 'Intermediate' | 'Advanced')}
                          style={{ padding: '0.25rem 0.4rem', fontSize: '0.725rem', width: '95px' }}
                        >
                          <option value="Beginner">Beginner</option>
                          <option value="Intermediate">Intermediate</option>
                          <option value="Advanced">Advanced</option>
                        </select>
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleRemoveModule(idx)}
                          style={{ padding: '0.2rem 0.45rem', fontSize: '0.75rem', color: 'var(--accent-rose)' }}
                          title="Remove lesson module"
                        >
                          Remove
                        </button>
                      </div>

                      <input
                        type="text"
                        value={m.context}
                        onChange={(e) => handleUpdateModule(idx, 'context', e.target.value)}
                        placeholder="What will students learn/build in this lab? (e.g. write Python code to load and normalize photos)..."
                        style={{ padding: '0.25rem 0.45rem', fontSize: '0.725rem', color: 'var(--text-secondary)' }}
                      />
                    </div>
                  ))}
                  {modules.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: '0.775rem' }}>
                      No modules added yet. Click "+ Add Module" to build your custom weekly syllabus.
                    </div>
                  )}
                </div>
              </div>

              <div className="grid-2" style={{ gap: '0.5rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Capstone Project Title {renderHelpBtn('curriculum.topics')}
                  </label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="e.g. Smart Crop Disease Assistant"
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Core Topic Name {renderHelpBtn('curriculum.topics')}
                  </label>
                  <input
                    type="text"
                    value={topicName}
                    onChange={(e) => setTopicName(e.target.value)}
                    placeholder="e.g. Leaf Classification"
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>
                  Topic Description {renderHelpBtn('curriculum.topics')}
                </label>
                <input
                  type="text"
                  value={topicDescription}
                  onChange={(e) => setTopicDescription(e.target.value)}
                  placeholder="Explain the real-world purpose of this project for students..."
                  style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                />
              </div>

              {/* Dynamic Multiple Resources Section */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: 0 }}>
                    Recommended Student Resource Links ({resources.length}) {renderHelpBtn('curriculum.resources')}
                  </label>
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={handleAddResource}
                    style={{ padding: '0.2rem 0.55rem', fontSize: '0.75rem' }}
                  >
                    + Add Resource
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '110px', overflowY: 'auto', paddingRight: '0.25rem' }}>
                  {resources.map((r, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        padding: '0.35rem 0.5rem',
                        background: 'var(--bg-card-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <input
                        type="text"
                        value={r.name}
                        onChange={(e) => handleUpdateResource(idx, 'name', e.target.value)}
                        placeholder="Resource Title (e.g. Kaggle Dataset, PyTorch Docs)..."
                        style={{ width: '160px', padding: '0.25rem 0.45rem', fontSize: '0.75rem', fontWeight: 600 }}
                      />
                      <input
                        type="text"
                        value={r.url}
                        onChange={(e) => handleUpdateResource(idx, 'url', e.target.value)}
                        placeholder="https://..."
                        style={{ flex: 1, padding: '0.25rem 0.45rem', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
                      />
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleRemoveResource(idx)}
                        style={{ padding: '0.2rem 0.45rem', fontSize: '0.75rem', color: 'var(--accent-rose)' }}
                        title="Remove resource"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  {resources.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '0.75rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      No resources attached. Click "+ Add Resource" to embed links for students.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Section 4: Lab Settings */}
          {activeSection === 'execution' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>
                  AI Lesson Writer Model {renderHelpBtn('execution.llm_model')}
                </label>
                <select
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                >
                  <option value="Qwen/Qwen2.5-Coder-32B-Instruct-AWQ">Qwen2.5-Coder-32B (Recommended / High Quality)</option>
                  <option value="Qwen/Qwen2.5-Coder-14B-Instruct-AWQ">Qwen2.5-Coder-14B (Fast)</option>
                  <option value="Qwen/Qwen2.5-Coder-7B-Instruct">Qwen2.5-Coder-7B (Lightweight)</option>
                </select>
              </div>

              <div className="grid-3" style={{ gap: '0.5rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Batch Size {renderHelpBtn('execution.batch_size')}
                  </label>
                  <input
                    type="number"
                    value={batchSize}
                    onChange={(e) => setBatchSize(Number(e.target.value))}
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Image Size {renderHelpBtn('execution.image_size')}
                  </label>
                  <input
                    type="number"
                    value={imageSize}
                    onChange={(e) => setImageSize(Number(e.target.value))}
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>
                    Lab Seed Number {renderHelpBtn('execution.seed')}
                  </label>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(Number(e.target.value))}
                    style={{ padding: '0.45rem 0.65rem', fontSize: '0.825rem' }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live YAML Preview & Actions */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', marginBottom: 0, padding: '1rem 1.25rem' }}>
          <div className="card-header" style={{ marginBottom: '0.5rem' }}>
            <div>
              <h2 className="card-title">Live YAML Preview</h2>
              <p className="card-subtitle">Ready to run on your cluster or download</p>
            </div>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <button type="button" className="btn btn-sm btn-secondary" onClick={handleCopy} style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}>
                {copied ? 'Copied' : 'Copy'}
              </button>
              <button type="button" className="btn btn-sm btn-primary" onClick={handleDownload} style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}>
                Download .yaml
              </button>
            </div>
          </div>

          <pre
            style={{
              flex: 1,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.725rem',
              lineHeight: 1.4,
              background: 'var(--bg-card-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.75rem',
              overflowY: 'auto',
              maxHeight: '380px',
            }}
          >
            {generateYaml()}
          </pre>
        </div>
      </div>
    </div>
  );
};
