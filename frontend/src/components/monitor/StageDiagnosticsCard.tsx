import React from 'react';
import type { PipelineStage } from '../../services/tapis';
import { StatusBadge } from '../ui';

export const StageDiagnosticsCard: React.FC<{ selectedStage: PipelineStage | null }> = ({ selectedStage }) => {
  if (!selectedStage) return null;
  return (
    <section className="card" style={{ marginBottom: 'var(--space-6)' }}>
      <div className="card-header">
        <h2 className="section-title">{selectedStage.name}</h2>
        <StatusBadge status={selectedStage.status} />
      </div>
      <div className="muted" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 'var(--text-base)' }}>
        {selectedStage.details && <p>{selectedStage.details}</p>}
        {selectedStage.duration_sec != null && <p>Took {Math.round(selectedStage.duration_sec)} s</p>}
        {selectedStage.error && <p style={{ color: 'var(--danger)' }}>{selectedStage.error}</p>}
      </div>
    </section>
  );
};
