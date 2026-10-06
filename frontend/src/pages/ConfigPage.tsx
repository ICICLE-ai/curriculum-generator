import React, { useState, useEffect, useMemo } from 'react';
import { CONFIG_FIELD_GUIDE, type FieldGuideEntry } from '../data/configFieldGuide';
import { FieldHelpModal } from '../components/FieldHelpModal';
import { getStoredToken } from '../utils/storage';
import { parseJwt } from '../utils/jwt';
import {
  fetchAvailableDatasets,
  fetchSystemRootDir,
  type TapisDatasetItem,
} from '../utils/tapisJobs';
import {
  PRESETS,
  DEFAULT_PRESET_KEY,
  type CurriculumModule,
  type CurriculumResource,
} from '../presets';
import { generateCurriculumYaml } from '../utils/yamlGenerator';
import {
  CourseDataSection,
  PipelineToolsSection,
  CurriculumSyllabusSection,
  WeeklyModulesSection,
  LabExecutionSection,
  ConfigYamlPreview,
} from '../components/config';

interface ConfigPageProps {
  onNavigateToSubmit?: () => void;
}

export const ConfigPage: React.FC<ConfigPageProps> = ({ onNavigateToSubmit }) => {
  const token = getStoredToken();
  const decoded = token ? parseJwt(token) : null;
  const username = decoded?.payload['tapis/username'] || (decoded?.payload.sub as string) || '';
  const cleanUsername = username.includes('@') ? username.split('@')[0] : username;

  const [activeSection, setActiveSection] = useState<'project' | 'pipeline' | 'curriculum' | 'modules' | 'execution'>('project');
  const [activeHelpField, setActiveHelpField] = useState<FieldGuideEntry | null>(null);

  // Scanned cluster datasets & dynamic system root directory
  const [availableDatasets, setAvailableDatasets] = useState<TapisDatasetItem[]>([]);
  const [systemRootDir, setSystemRootDir] = useState<string>('');
  const [isLoadingDatasets, setIsLoadingDatasets] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    if (token) {
      setIsLoadingDatasets(true);
      fetchSystemRootDir(token, 'expanse-tapis-static')
        .then((root) => {
          if (active) setSystemRootDir(root);
        })
        .catch(() => {});

      fetchAvailableDatasets(token, cleanUsername, 'expanse-tapis-static')
        .then((items) => {
          if (active) {
            setAvailableDatasets(items);
          }
        })
        .catch(() => {})
        .finally(() => {
          if (active) setIsLoadingDatasets(false);
        });
    }
    return () => {
      active = false;
    };
  }, [token, cleanUsername]);

  const initialPreset = PRESETS[DEFAULT_PRESET_KEY];

  // 1. Course & Dataset
  const [selectedPreset, setSelectedPreset] = useState<string>(DEFAULT_PRESET_KEY);
  const [domain, setDomain] = useState<string>(initialPreset.domain);
  const [contextStatement, setContextStatement] = useState<string>(initialPreset.contextStatement);
  const [useCase] = useState<string>('educational_curriculum');
  const [datasetPath, setDatasetPath] = useState<string>(initialPreset.datasetPath);
  const [outputPath, setOutputPath] = useState<string>(initialPreset.outputPath);

  // 2. AI Vision Tools
  const [classificationActive, setClassificationActive] = useState<boolean>(true);
  const [classificationTask, setClassificationTask] = useState<string>(initialPreset.classificationTask);
  const [segmentationActive, setSegmentationActive] = useState<boolean>(true);
  const [segmentationPrompt, setSegmentationPrompt] = useState<string>(initialPreset.segmentationPrompt);
  const [xaiActive, setXaiActive] = useState<boolean>(false);

  // 3. Lab Execution Settings
  const [device] = useState<string>('cuda');
  const [batchSize, setBatchSize] = useState<number>(16);
  const [imageSize, setImageSize] = useState<number>(518);
  const [seed, setSeed] = useState<number>(6767);
  const [llmModel, setLlmModel] = useState<string>('Qwen/Qwen2.5-Coder-32B-Instruct-AWQ');

  // 4. Syllabus & Lessons
  const [subject, setSubject] = useState<string>(initialPreset.subject);
  const [targetLevel, setTargetLevel] = useState<string>(initialPreset.targetLevel || 'Undergraduate / Grade 10');
  const [modules, setModules] = useState<CurriculumModule[]>(initialPreset.modules);
  const [newObjectiveInputs, setNewObjectiveInputs] = useState<Record<number, string>>({});
  const [topicName, setTopicName] = useState<string>(initialPreset.topicName);
  const [topicDescription, setTopicDescription] = useState<string>(initialPreset.topicDescription);
  const [resources, setResources] = useState<CurriculumResource[]>(
    initialPreset.resources || [
      { name: 'Dataset Source', url: 'https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign' },
      { name: 'DINOv2 Documentation', url: 'https://huggingface.co/docs/transformers/en/model_doc/dinov2' },
    ]
  );

  // Preset Selection Handler
  const handleSelectPreset = (presetKey: string) => {
    setSelectedPreset(presetKey);

    if (presetKey === 'custom') {
      setDomain('');
      setContextStatement('');
      setDatasetPath('');
      setOutputPath('');
      setSubject('');
      setTargetLevel('');
      setClassificationTask('');
      setSegmentationPrompt('');
      setClassificationActive(true);
      setSegmentationActive(false);
      setXaiActive(false);
      setTopicName('');
      setTopicDescription('');
      setModules([]);
      setResources([]);
      setNewObjectiveInputs({});
      return;
    }

    const preset = PRESETS[presetKey];
    if (!preset) return;

    setDomain(preset.domain);
    setContextStatement(preset.contextStatement);

    let dynamicDatasetPath = preset.datasetPath;
    if (preset.datasetFolder) {
      const matched = availableDatasets.find((d) => d.name === preset.datasetFolder);
      if (matched) {
        dynamicDatasetPath = matched.clusterPath;
      } else if (systemRootDir) {
        dynamicDatasetPath = `${systemRootDir}shared/smart_curriculum_designer_datasets/${preset.datasetFolder}`;
      }
    }
    setDatasetPath(dynamicDatasetPath);

    setOutputPath(preset.outputPath);
    setSubject(preset.subject);
    setTargetLevel(preset.targetLevel || 'Undergraduate / Grade 10');
    setSegmentationPrompt(preset.segmentationPrompt);
    setClassificationTask(preset.classificationTask);
    setClassificationActive(true);
    setSegmentationActive(true);
    setXaiActive(false);
    setTopicName(preset.topicName);
    setTopicDescription(preset.topicDescription);
    setModules(JSON.parse(JSON.stringify(preset.modules)));
    setResources(JSON.parse(JSON.stringify(preset.resources || [])));
    setNewObjectiveInputs({});
  };

  // Field Help Modal Opener
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
        learning_outcomes: [
          'Analyze domain dataset features and implement Python processing milestones.',
          'Evaluate model performance metrics and interpret visual predictions.',
        ],
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

  const handleAddLearningOutcome = (moduleIndex: number, outcomeText: string) => {
    const trimmed = outcomeText.trim();
    if (!trimmed) return;
    setModules(
      modules.map((m, idx) => {
        if (idx !== moduleIndex) return m;
        const currentOutcomes = m.learning_outcomes || [];
        return {
          ...m,
          learning_outcomes: [...currentOutcomes, trimmed],
        };
      })
    );
  };

  const handleRemoveLearningOutcome = (moduleIndex: number, outcomeIndex: number) => {
    setModules(
      modules.map((m, idx) => {
        if (idx !== moduleIndex) return m;
        return {
          ...m,
          learning_outcomes: (m.learning_outcomes || []).filter((_, oIdx) => oIdx !== outcomeIndex),
        };
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

  // Memoized Live YAML Generation
  const yamlOutput = useMemo(() => {
    return generateCurriculumYaml({
      domain,
      contextStatement,
      useCase,
      datasetPath,
      outputPath,
      classificationActive,
      classificationTask,
      segmentationActive,
      segmentationPrompt,
      xaiActive,
      device,
      batchSize,
      imageSize,
      seed,
      llmModel,
      subject,
      targetLevel,
      modules,
      topicName,
      topicDescription,
      resources,
    });
  }, [
    domain,
    contextStatement,
    useCase,
    datasetPath,
    outputPath,
    classificationActive,
    classificationTask,
    segmentationActive,
    segmentationPrompt,
    xaiActive,
    device,
    batchSize,
    imageSize,
    seed,
    llmModel,
    subject,
    targetLevel,
    modules,
    topicName,
    topicDescription,
    resources,
  ]);

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Curriculum Designer Studio</h1>
        <p className="page-description">
          Configure an AI vision pipeline and multi-week curriculum. Preview and download the deployment YAML for SDSC Expanse.
        </p>
      </div>

      <div className="builder-grid-layout">
        {/* Left Column: Form Sections Workspace */}
        <div className="card">
          {/* Navigation Capsule Bar */}
          <div className="capsule-nav">
            <button
              type="button"
              className={`capsule-tab ${activeSection === 'project' ? 'active' : ''}`}
              onClick={() => setActiveSection('project')}
            >
              1. Course & Data
            </button>
            <button
              type="button"
              className={`capsule-tab ${activeSection === 'pipeline' ? 'active' : ''}`}
              onClick={() => setActiveSection('pipeline')}
            >
              2. AI Vision Tools
            </button>
            <button
              type="button"
              className={`capsule-tab ${activeSection === 'curriculum' ? 'active' : ''}`}
              onClick={() => setActiveSection('curriculum')}
            >
              3. Course Syllabus
            </button>
            <button
              type="button"
              className={`capsule-tab ${activeSection === 'modules' ? 'active' : ''}`}
              onClick={() => setActiveSection('modules')}
            >
              4. Weekly Labs & Modules ({modules.length})
            </button>
            <button
              type="button"
              className={`capsule-tab ${activeSection === 'execution' ? 'active' : ''}`}
              onClick={() => setActiveSection('execution')}
            >
              5. Lab Settings
            </button>
          </div>

          {/* Section 1: Course & Data */}
          {activeSection === 'project' && (
            <CourseDataSection
              selectedPreset={selectedPreset}
              onSelectPreset={handleSelectPreset}
              domain={domain}
              onChangeDomain={setDomain}
              contextStatement={contextStatement}
              onChangeContextStatement={setContextStatement}
              datasetPath={datasetPath}
              onChangeDatasetPath={setDatasetPath}
              outputPath={outputPath}
              onChangeOutputPath={setOutputPath}
              availableDatasets={availableDatasets}
              systemRootDir={systemRootDir}
              isLoadingDatasets={isLoadingDatasets}
              renderHelpBtn={renderHelpBtn}
            />
          )}

          {/* Section 2: AI Vision Tools */}
          {activeSection === 'pipeline' && (
            <PipelineToolsSection
              classificationActive={classificationActive}
              onChangeClassificationActive={setClassificationActive}
              classificationTask={classificationTask}
              onChangeClassificationTask={setClassificationTask}
              segmentationActive={segmentationActive}
              onChangeSegmentationActive={setSegmentationActive}
              segmentationPrompt={segmentationPrompt}
              onChangeSegmentationPrompt={setSegmentationPrompt}
              xaiActive={xaiActive}
              onChangeXaiActive={setXaiActive}
              renderHelpBtn={renderHelpBtn}
            />
          )}

          {/* Section 3: Course Syllabus & Resources */}
          {activeSection === 'curriculum' && (
            <CurriculumSyllabusSection
              subject={subject}
              onChangeSubject={setSubject}
              targetLevel={targetLevel}
              onChangeTargetLevel={setTargetLevel}
              topicName={topicName}
              onChangeTopicName={setTopicName}
              topicDescription={topicDescription}
              onChangeTopicDescription={setTopicDescription}
              resources={resources}
              onAddResource={handleAddResource}
              onRemoveResource={handleRemoveResource}
              onUpdateResource={handleUpdateResource}
              renderHelpBtn={renderHelpBtn}
            />
          )}

          {/* Section 4: Dedicated Weekly Labs & Modules Workspace */}
          {activeSection === 'modules' && (
            <WeeklyModulesSection
              modules={modules}
              onAddModule={handleAddModule}
              onRemoveModule={handleRemoveModule}
              onUpdateModule={handleUpdateModule}
              onAddLearningOutcome={handleAddLearningOutcome}
              onRemoveLearningOutcome={handleRemoveLearningOutcome}
              newObjectiveInputs={newObjectiveInputs}
              setNewObjectiveInputs={setNewObjectiveInputs}
              renderHelpBtn={renderHelpBtn}
            />
          )}

          {/* Section 5: Lab Execution Settings */}
          {activeSection === 'execution' && (
            <LabExecutionSection
              llmModel={llmModel}
              onChangeLlmModel={setLlmModel}
              batchSize={batchSize}
              onChangeBatchSize={setBatchSize}
              imageSize={imageSize}
              onChangeImageSize={setImageSize}
              seed={seed}
              onChangeSeed={setSeed}
              renderHelpBtn={renderHelpBtn}
            />
          )}
        </div>

        {/* Right Column: Live YAML Preview & Actions */}
        <ConfigYamlPreview
          yamlContent={yamlOutput}
          onNavigateToSubmit={onNavigateToSubmit}
        />
      </div>

      {/* Field Level Guided Documentation Modal */}
      {activeHelpField && (
        <FieldHelpModal
          entry={activeHelpField}
          onClose={() => setActiveHelpField(null)}
        />
      )}
    </div>
  );
};
