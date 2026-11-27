import React from 'react';

interface LabExecutionSectionProps {
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

export const LabExecutionSection: React.FC<LabExecutionSectionProps> = ({
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
    <div className="stack">
      <div>
        <h2 className="card-title">Lab Settings</h2>
        <p className="card-subtitle">Execution parameters for vision processing and evaluation.</p>
      </div>

      <div className="tool-card">
        <div className="row-between card-header-start">
          <div className="checkbox-row">
            <input
              type="checkbox"
              id="pedagogy_eval"
              checked={pedagogyEval}
              onChange={(e) => onChangePedagogyEval(e.target.checked)}
            />
            <div>
              <label htmlFor="pedagogy_eval" className="checkbox-label">
                Pedagogy Evaluation (pilot)
              </label>
              <p className="form-helper">
                After lessons are built, scores each week (rubric, Bloom alignment, simulated learner) into <code>exercises/evaluation/</code>. Log-only: never modifies the generated materials.
              </p>
            </div>
          </div>
          {renderHelpBtn('execution.pedagogy_eval')}
        </div>
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label htmlFor="exec-batch-size" className="form-label">
            <span>Batch Size</span>
            {renderHelpBtn('execution.batch_size')}
          </label>
          <input
            id="exec-batch-size"
            type="number"
            value={batchSize}
            onChange={(e) => onChangeBatchSize(Number(e.target.value))}
          />
        </div>
        <div className="form-group">
          <label htmlFor="exec-image-size" className="form-label">
            <span>Image Size (px)</span>
            {renderHelpBtn('execution.image_size')}
          </label>
          <input
            id="exec-image-size"
            type="number"
            value={imageSize}
            onChange={(e) => onChangeImageSize(Number(e.target.value))}
          />
        </div>
        <div className="form-group">
          <label htmlFor="exec-max-samples" className="form-label">
            <span>Max Samples (Subsampling)</span>
            {renderHelpBtn('execution.max_samples')}
          </label>
          <input
            id="exec-max-samples"
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
          <label htmlFor="exec-seed" className="form-label">
            <span>Lab Seed Number</span>
            {renderHelpBtn('execution.seed')}
          </label>
          <input
            id="exec-seed"
            type="number"
            value={seed}
            onChange={(e) => onChangeSeed(Number(e.target.value))}
          />
        </div>
      </div>
    </div>
  );
};
