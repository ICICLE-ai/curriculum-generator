import React from 'react';
import type { PipelineStage } from '../../utils/tapisJobs';

interface StageDiagnosticsCardProps {
  selectedStage: PipelineStage | null;
}

export const StageDiagnosticsCard: React.FC<StageDiagnosticsCardProps> = ({ selectedStage }) => {
  if (!selectedStage) return null;

  const getStatusBadgeStyle = () => {
    switch (selectedStage.status) {
      case 'COMPLETED':
        return {
          background: 'var(--accent-emerald-subtle)',
          color: 'var(--accent-emerald)',
        };
      case 'IN_PROGRESS':
        return {
          background: 'var(--accent-amber-subtle)',
          color: 'var(--accent-amber)',
        };
      case 'FAILED':
        return {
          background: 'var(--accent-rose-subtle)',
          color: 'var(--accent-rose)',
        };
      default:
        return {
          background: 'var(--bg-card)',
          color: 'var(--text-secondary)',
        };
    }
  };

  const badgeStyle = getStatusBadgeStyle();

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
        <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
          Stage Diagnostics: {selectedStage.name}
        </h3>
        <span className="status-badge" style={badgeStyle}>
          <span className="status-dot" />
          {selectedStage.status}
        </span>
      </div>

      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
        <p style={{ margin: '0 0 0.5rem 0' }}>{selectedStage.details}</p>
        {selectedStage.duration_sec && (
          <div>
            Execution duration: <strong>{selectedStage.duration_sec} seconds</strong>
          </div>
        )}
        {selectedStage.error && (
          <div style={{ marginTop: '0.5rem', color: 'var(--accent-rose)' }}>
            Error details: {selectedStage.error}
          </div>
        )}
      </div>
    </div>
  );
};
