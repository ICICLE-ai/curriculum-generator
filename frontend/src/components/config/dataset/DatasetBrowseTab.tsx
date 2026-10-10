import React from 'react';
import type { TapisDatasetItem } from '../../../services/tapis';

interface DatasetBrowseTabProps {
  isLoadingDatasets: boolean;
  availableDatasets: TapisDatasetItem[];
  datasetPath: string;
  onSelectDatasetPath: (path: string) => void;
}

function getDatasetIcon(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes('skin') || lower.includes('cancer')) return '🩺';
  if (lower.includes('plant') || lower.includes('crop') || lower.includes('greenhouse')) return '🌾';
  if (lower.includes('food') || lower.includes('dish')) return '🍲';
  return '📁';
}

export const DatasetBrowseTab: React.FC<DatasetBrowseTabProps> = ({
  isLoadingDatasets,
  availableDatasets,
  datasetPath,
  onSelectDatasetPath,
}) => {
  if (isLoadingDatasets) {
    return (
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '0.5rem 0' }}>
        Scanning Tapis storage for available datasets...
      </div>
    );
  }

  if (availableDatasets.length === 0) {
    return (
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '0.5rem 0' }}>
        No dataset directories found in storage yet. Upload a .zip or provide a URL above.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
      {availableDatasets.map((item) => {
        const isSelected = datasetPath === item.clusterPath || (item.name && datasetPath.endsWith(item.name));
        return (
          <button
            key={item.name}
            type="button"
            onClick={() => onSelectDatasetPath(item.clusterPath)}
            style={{
              background: isSelected ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
              color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              padding: '0.45rem 0.8rem',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
            }}
          >
            <span>{getDatasetIcon(item.name)}</span>
            <span style={{ fontWeight: isSelected ? 600 : 400 }}>{item.name}</span>
            <span
              style={{
                fontSize: '0.625rem',
                padding: '0.1rem 0.35rem',
                borderRadius: '3px',
                background: item.source === 'user' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(255, 255, 255, 0.08)',
                color: item.source === 'user' ? 'var(--accent-emerald)' : 'var(--text-muted)',
              }}
            >
              {item.source === 'user' ? 'Personal' : 'Shared'}
            </span>
          </button>
        );
      })}
    </div>
  );
};

