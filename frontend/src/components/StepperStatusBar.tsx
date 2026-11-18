import React from 'react';
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

const ICON: Record<PipelineStage['status'], React.ReactNode> = {
  COMPLETED: <polyline points="20 6 9 17 4 12" />,
  FAILED: (
    <>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </>
  ),
  IN_PROGRESS: <path d="M21 12a9 9 0 1 1-6.219-8.56" />,
  SKIPPED: <line x1="5" y1="12" x2="19" y2="12" />,
  READY: <circle cx="12" cy="12" r="7" />,
};

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
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          aria-hidden="true"
          style={stg.status === 'IN_PROGRESS' ? { animation: 'spin 1s linear infinite' } : undefined}
        >
          {ICON[stg.status] ?? ICON.READY}
        </svg>
        <span style={{ color: 'var(--text)' }}>{stg.name}</span>
        <span className="stage-phase">{statusLabel(stg.status)}</span>
      </button>
    ))}
  </div>
);
