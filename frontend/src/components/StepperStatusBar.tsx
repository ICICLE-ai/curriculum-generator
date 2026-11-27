import React from 'react';
import { Check, X, Loader2, Minus, Circle } from 'lucide-react';
import { type PipelineStage } from '../services/tapis';
import { statusLabel } from '../utils/status';

interface StepperStatusBarProps {
  stages: PipelineStage[];
  selectedStageId?: string;
  onSelectStage?: (stage: PipelineStage) => void;
}

const STATE_CLASS: Partial<Record<PipelineStage['status'], string>> = {
  COMPLETED: 'is-completed',
  IN_PROGRESS: 'is-running',
  FAILED: 'is-failed',
};

function renderStageIcon(status: PipelineStage['status']): React.ReactNode {
  if (status === 'COMPLETED') return <Check size={14} aria-hidden="true" />;
  if (status === 'FAILED') return <X size={14} aria-hidden="true" />;
  if (status === 'IN_PROGRESS') return <Loader2 size={14} className="spin" aria-hidden="true" />;
  if (status === 'SKIPPED') return <Minus size={14} aria-hidden="true" />;
  return <Circle size={12} aria-hidden="true" />;
}

/** One chip per stage: icon, name and status in text (status is never conveyed by color alone). */
export const StepperStatusBar: React.FC<StepperStatusBarProps> = ({ stages, selectedStageId, onSelectStage }) => (
  <div className="stage-strip">
    {stages.map((stg) => (
      <button
        key={stg.id}
        type="button"
        className={`stage-chip ${STATE_CLASS[stg.status] ?? ''}`}
        aria-pressed={selectedStageId === stg.id}
        onClick={() => onSelectStage?.(stg)}
      >
        {renderStageIcon(stg.status)}
        <span style={{ color: 'var(--text)' }}>{stg.name}</span>
        <span className="stage-phase">{statusLabel(stg.status)}</span>
      </button>
    ))}
  </div>
);
