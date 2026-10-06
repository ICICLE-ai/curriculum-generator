import React from 'react';

interface LabExecutionSectionProps {
  llmModel: string;
  onChangeLlmModel: (model: string) => void;
  batchSize: number;
  onChangeBatchSize: (size: number) => void;
  imageSize: number;
  onChangeImageSize: (size: number) => void;
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
          <option value="Qwen/Qwen2.5-Coder-32B-Instruct-AWQ">Qwen2.5-Coder-32B (Recommended / High Quality)</option>
          <option value="Qwen/Qwen2.5-Coder-14B-Instruct-AWQ">Qwen2.5-Coder-14B (Fast)</option>
          <option value="Qwen/Qwen2.5-Coder-7B-Instruct">Qwen2.5-Coder-7B (Lightweight)</option>
        </select>
        <div className="form-helper">Inference backbone used to synthesize lessons, markdown slides, and coding exercises.</div>
      </div>

      <div className="grid-3">
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
