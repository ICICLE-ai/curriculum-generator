import React from 'react';
import { type PipelineStage } from '../utils/tapisJobs';

interface StepperStatusBarProps {
  stages: PipelineStage[];
  currentStageId?: string;
  selectedStageId?: string;
  onSelectStage?: (stage: PipelineStage) => void;
  onViewLogs?: () => void;
}

const statusStyles: Record<
  PipelineStage['status'],
  { color: string; bg: string; border: string }
> = {
  READY: {
    color: 'var(--text-secondary)',
    bg: 'var(--bg-card)',
    border: 'var(--border-subtle)',
  },
  IN_PROGRESS: {
    color: 'var(--accent-amber)',
    bg: 'var(--accent-amber-subtle)',
    border: 'var(--accent-amber-border)',
  },
  COMPLETED: {
    color: 'var(--accent-emerald)',
    bg: 'var(--accent-emerald-subtle)',
    border: 'var(--accent-emerald-border)',
  },
  FAILED: {
    color: 'var(--accent-rose)',
    bg: 'var(--accent-rose-subtle)',
    border: 'var(--accent-rose)',
  },
  SKIPPED: {
    color: 'var(--text-muted)',
    bg: 'var(--bg-card-subtle)',
    border: 'var(--border-subtle)',
  },
};

export const StepperStatusBar: React.FC<StepperStatusBarProps> = ({
  stages,
  selectedStageId,
  onSelectStage,
  onViewLogs,
}) => {
  const renderStatusIcon = (status: PipelineStage['status']) => {
    switch (status) {
      case 'IN_PROGRESS':
        return (
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            style={{
              animation: 'spin 1s linear infinite',
            }}
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
        );
      case 'COMPLETED':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        );
      case 'FAILED':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        );
      case 'SKIPPED':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        );
      case 'READY':
      default:
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="8" />
          </svg>
        );
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        overflowX: 'auto',
        padding: '0.5rem 0',
        scrollbarWidth: 'thin',
      }}
    >
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>

      {stages.map((stg, index) => {
        const style = statusStyles[stg.status] || statusStyles.READY;
        const isSelected = selectedStageId === stg.id;

        return (
          <React.Fragment key={stg.id}>
            <button
              type="button"
              onClick={() => onSelectStage?.(stg)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.45rem 0.85rem',
                borderRadius: '999px',
                background: style.bg,
                border: `1.5px solid ${isSelected ? 'var(--accent-primary)' : style.border}`,
                color: style.color,
                fontSize: '0.8rem',
                fontWeight: isSelected ? 700 : 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                boxShadow: isSelected ? '0 0 0 2px var(--accent-primary-subtle)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center' }}>{renderStatusIcon(stg.status)}</span>
              <span>{stg.name}</span>
              {stg.duration_sec && (
                <span
                  style={{
                    fontSize: '0.7rem',
                    opacity: 0.8,
                    background: 'rgba(0,0,0,0.06)',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '4px',
                  }}
                >
                  {stg.duration_sec}s
                </span>
              )}
            </button>

            {index < stages.length - 1 && (
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--border-strong)"
                strokeWidth="2"
                style={{ flexShrink: 0 }}
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            )}
          </React.Fragment>
        );
      })}

      {onViewLogs && (
        <button
          type="button"
          onClick={onViewLogs}
          className="btn btn-secondary"
          style={{
            marginLeft: 'auto',
            padding: '0.4rem 0.75rem',
            fontSize: '0.78rem',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="4 17 10 11 4 5" />
            <line x1="12" y1="19" x2="20" y2="19" />
          </svg>
          Logs
        </button>
      )}
    </div>
  );
};
