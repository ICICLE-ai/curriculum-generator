import React from 'react';

interface LabExecutionSectionProps {
  llmModel: string;
  onChangeLlmModel: (model: string) => void;
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

export const LabExecutionSection: React.FC<LabExecutionSectionProps> = ({
  llmModel,
  onChangeLlmModel,
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
          <span>AI Lesson Writer Model</span>
          {renderHelpBtn('execution.llm_model')}
        </label>
        <select
          value={llmModel}
          onChange={(e) => onChangeLlmModel(e.target.value)}
        >
          <option value="Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4">Qwen2.5-Coder-32B GPTQ-Int4 (Quantized - Best for 2× V100 32GB)</option>
          <option value="Qwen/Qwen2.5-Coder-14B-Instruct">Qwen2.5-Coder-14B (Full Precision - Recommended for 2 GPUs)</option>
          <option value="Qwen/Qwen2.5-Coder-32B-Instruct">Qwen2.5-Coder-32B (Full Precision - Recommended for 4 GPUs)</option>
          <option value="Qwen/Qwen2.5-Coder-7B-Instruct">Qwen2.5-Coder-7B (Lightweight - Recommended for 1 GPU)</option>
        </select>
        <div className="form-helper">Inference backbone used to synthesize lessons, markdown slides, and coding exercises. Multi-GPU nodes automatically parallelize serving across all available GPUs.</div>
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
