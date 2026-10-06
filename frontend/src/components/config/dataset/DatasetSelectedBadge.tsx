import React from 'react';
import type { TapisDatasetItem } from '../../../services/tapis';

interface DatasetSelectedBadgeProps {
  datasetPath: string;
  matchedDataset?: TapisDatasetItem;
}

export const DatasetSelectedBadge: React.FC<DatasetSelectedBadgeProps> = ({
  datasetPath,
  matchedDataset,
}) => {
  if (!datasetPath) {
    return (
      <div
        style={{
          padding: '0.65rem 0.9rem',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px dashed var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '1rem',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
        }}
      >
        No dataset selected yet. Select a curated dataset below, upload a <code>.zip</code> file, or link a direct download URL.
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '0.75rem 1rem',
        background: 'rgba(6, 182, 212, 0.08)',
        border: '1px solid rgba(6, 182, 212, 0.3)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.1rem' }}>✓</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
            {matchedDataset ? matchedDataset.name : datasetPath.split('/').filter(Boolean).pop()}
          </span>
          <span
            style={{
              fontSize: '0.65rem',
              padding: '0.1rem 0.4rem',
              borderRadius: '3px',
              background: matchedDataset?.source === 'user' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(255, 255, 255, 0.1)',
              color: matchedDataset?.source === 'user' ? 'var(--accent-emerald)' : 'var(--text-secondary)',
              fontWeight: 600,
            }}
          >
            {matchedDataset?.source === 'user' ? 'Personal Dataset' : 'Verified Cluster Dataset'}
          </span>
        </div>
        <div
          style={{
            fontSize: '0.72rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            marginTop: '0.2rem',
            wordBreak: 'break-all',
          }}
        >
          {datasetPath}
        </div>
      </div>
    </div>
  );
};

