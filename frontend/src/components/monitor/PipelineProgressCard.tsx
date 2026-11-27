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
  <section className="card">
    <div className="card-header">
      <h2 className="section-title">Stages</h2>
      <span className="muted">Select a stage for details</span>
    </div>

    <StepperStatusBar stages={displayedStages} selectedStageId={selectedStageId} onSelectStage={onSelectStage} />

    <div className="mt-4 stack-sm">
      <div className="row-between muted">
        <span>{statusDescription}</span>
        {isActive && <strong>{progressPercent}%</strong>}
      </div>
      {isActive && (
        <div className="progress-track" role="progressbar" aria-valuenow={progressPercent} aria-valuemin={0} aria-valuemax={100}>
          <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>
      )}
    </div>
  </section>
);
