import React from 'react';
import type { PipelineStage } from '../../services/tapis';
import { StepperStatusBar } from '../StepperStatusBar';

interface PipelineProgressCardProps {
  displayedStages: PipelineStage[];
  selectedStageId?: string;
  onSelectStage: (stage: PipelineStage) => void;
  progressPercent: number;
  statusDescription: string;
  isActive: boolean;
}

export const PipelineProgressCard: React.FC<PipelineProgressCardProps> = ({
  displayedStages,
  selectedStageId,
  onSelectStage,
  progressPercent,
  statusDescription,
  isActive,
}) => (
  <section className="card" style={{ marginBottom: 'var(--space-6)' }}>
    <div className="card-header">
      <h2 className="section-title">Stages</h2>
      <span className="muted">Select a stage for details</span>
    </div>

    <StepperStatusBar stages={displayedStages} selectedStageId={selectedStageId} onSelectStage={onSelectStage} />

    <div style={{ marginTop: 'var(--space-4)' }}>
      <div className="muted" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
        <span>{statusDescription}</span>
        {isActive && <span style={{ color: 'var(--text)' }}>{progressPercent}%</span>}
      </div>
      {isActive && (
        <div className="progress-track" role="progressbar" aria-valuenow={progressPercent} aria-valuemin={0} aria-valuemax={100}>
          <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>
      )}
    </div>
  </section>
);
