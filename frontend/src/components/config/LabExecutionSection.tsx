import React from 'react';
import { DEFAULT_LLM_MODELS, type LlmModels, type LlmRole } from '../../utils/yamlGenerator';

interface LabExecutionSectionProps {
  llmModels: LlmModels;
  onChangeLlmModels: (models: LlmModels) => void;
  pedagogyEval: boolean;
  onChangePedagogyEval: (enabled: boolean) => void;
  batchSize: number;
  onChangeBatchSize: (size: number) => void;
  imageSize: number;
  onChangeImageSize: (size: number) => void;
  maxSamples: number | null;
  onChangeMaxSamples: (samples: number | null) => void;
  seed: number;
  onChangeSeed: (seed: number) => void;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
}

// NRP managed LLM chat models (https://nrp.ai/llms/)
const NRP_MODELS: [string, string][] = [
  ['deepseek-v4-flash', 'DeepSeek V4.1 Flash (strongest reasoning, fast)'],
  ['glm-5', 'GLM-5.3 (coding-focused)'],
  ['qwen3-small', 'Qwen3.8 27B (low latency)'],
  ['qwen3', 'Qwen3.8 Flash Next (flagship MoE)'],
  ['kimi', 'Kimi K2.7 Code (1T, slow, always thinks)'],
  ['gpt-oss', 'gpt-oss 120B (SDSC-hosted, stable)'],
  ['minimax', 'MiniMax M3.1 Flash'],
  ['gemma', 'Gemma 4 31B'],
];

const ROLES: [LlmRole, string][] = [
  ['planner', 'Planner (syllabus & contracts)'],
  ['coder', 'Coder (tests, solutions, repairs)'],
  ['arbiter', 'Arbiter (rules on failing tests)'],
  ['slides', 'Slides (presentation deck)'],
  ['slide_reviewer', 'Slide reviewer (sees screenshots; needs a vision model)'],
  ['judge', 'Pedagogy judge (scores weeks; vision model, not DeepSeek or GLM)'],
];

export const LabExecutionSection: React.FC<LabExecutionSectionProps> = ({
  llmModels,
  onChangeLlmModels,
  pedagogyEval,
  onChangePedagogyEval,
  batchSize,
  onChangeBatchSize,
  imageSize,
  onChangeImageSize,
  maxSamples,
  onChangeMaxSamples,
  seed,
  onChangeSeed,
  renderHelpBtn,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="form-group">
        <label className="form-label">
          <span>AI Lesson Writer Models</span>
          {renderHelpBtn('execution.llm_models')}
        </label>
        <div className="grid-2">
          {ROLES.filter(([role]) => role !== 'judge' || pedagogyEval).map(([role, label]) => (
            <div className="form-group" key={role}>
              <label className="form-label" htmlFor={`llm-model-${role}`}>
                <span>{label}</span>
              </label>
              <select
                id={`llm-model-${role}`}
                value={llmModels[role]}
                onChange={(e) => onChangeLlmModels({ ...llmModels, [role]: e.target.value })}
              >
                {NRP_MODELS.map(([value, name]) => (
                  <option key={value} value={value}>
                    {name}{value === DEFAULT_LLM_MODELS[role] ? ' (default)' : ''}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
        <div className="form-helper">Served by the NRP managed LLM API, so no GPU is spent on the LLM. Each role can use a different model.</div>
      </div>

      <div className="form-group">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input
              type="checkbox"
              id="pedagogy_eval"
              checked={pedagogyEval}
              onChange={(e) => onChangePedagogyEval(e.target.checked)}
              style={{ width: '18px', height: '18px' }}
            />
            <label htmlFor="pedagogy_eval" style={{ fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', color: 'var(--text-primary)' }}>
              Pedagogy Evaluation (pilot)
            </label>
          </div>
          {renderHelpBtn('execution.pedagogy_eval')}
        </div>
        <div className="form-helper">
          After the lessons are built, scores each week (rubric, Bloom alignment, simulated learner) into exercises/evaluation/. Log-only: it never changes the generated materials.
        </div>
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">
            <span>Batch Size</span>
            {renderHelpBtn('execution.batch_size')}
          </label>
          <input
            type="number"
            value={batchSize}
            onChange={(e) => onChangeBatchSize(Number(e.target.value))}
          />
        </div>
        <div className="form-group">
          <label className="form-label">
            <span>Image Size (px)</span>
            {renderHelpBtn('execution.image_size')}
          </label>
          <input
            type="number"
            value={imageSize}
            onChange={(e) => onChangeImageSize(Number(e.target.value))}
          />
        </div>
        <div className="form-group">
          <label className="form-label">
            <span>Max Samples (Subsampling)</span>
            {renderHelpBtn('execution.max_samples')}
          </label>
          <input
            type="number"
            min="1"
            placeholder="All images (no limit)"
            value={maxSamples ?? ''}
            onChange={(e) => {
              const val = e.target.value.trim();
              onChangeMaxSamples(val === '' ? null : Math.max(1, parseInt(val, 10)));
            }}
          />
          <div className="form-helper">Limit dataset size for fast test runs, or leave empty for full dataset.</div>
        </div>
        <div className="form-group">
          <label className="form-label">
            <span>Lab Seed Number</span>
            {renderHelpBtn('execution.seed')}
          </label>
          <input
            type="number"
            value={seed}
            onChange={(e) => onChangeSeed(Number(e.target.value))}
          />
        </div>
      </div>
    </div>
  );
};
