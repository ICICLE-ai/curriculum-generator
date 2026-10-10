import React from 'react';
import type { PipelineStage } from '../../services/tapis';
import { StepperStatusBar } from '../StepperStatusBar';

interface PipelineProgressCardProps {
  displayedStages: PipelineStage[];
  currentStageId?: string;
  selectedStageId?: string;
  onSelectStage: (stage: PipelineStage) => void;
  onViewLogs: () => void;
  progressPercent: number;
  statusDescription: string;
  macroStatus: string;
}

export const PipelineProgressCard: React.FC<PipelineProgressCardProps> = ({
  displayedStages,
  currentStageId,
  selectedStageId,
  onSelectStage,
  onViewLogs,
  progressPercent,
  statusDescription,
  macroStatus,
}) => {
  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.75rem',
        }}
      >
        <h2 className="card-title" style={{ margin: 0 }}>
          Pipeline Stage Progression
        </h2>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          Select any stage for diagnostic inspection
        </span>
      </div>

      <StepperStatusBar
        stages={displayedStages}
        currentStageId={currentStageId}
        selectedStageId={selectedStageId}
        onSelectStage={onSelectStage}
        onViewLogs={onViewLogs}
      />

      {/* Progress Bar */}
      <div style={{ marginTop: '1.25rem' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            marginBottom: '0.4rem',
          }}
        >
          <span>{statusDescription}</span>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{progressPercent}%</span>
        </div>
        <div
          style={{
            height: '8px',
            borderRadius: '999px',
            background: 'var(--bg-card-subtle)',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progressPercent}%`,
              background:
                macroStatus === 'FAILED'
                  ? 'var(--accent-rose)'
                  : 'linear-gradient(90deg, var(--accent-primary), var(--accent-emerald))',
              transition: 'width 0.4s ease',
            }}
          />
        </div>
      </div>
    </div>
  );
};
