import React from 'react';
import { CheckCircle2 } from 'lucide-react';
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
      <div className="empty-state" style={{ padding: 'var(--space-3)' }}>
        No dataset selected yet. Click <strong>Choose Dataset</strong> to pick or import one.
      </div>
    );
  }

  return (
    <div className="dataset-badge-card">
      <div className="row-wrap">
        <CheckCircle2 size={16} className="text-info" aria-hidden="true" />
        <strong>
          {matchedDataset ? matchedDataset.name : datasetPath.split('/').filter(Boolean).pop()}
        </strong>
        <span className={`pill-tag ${matchedDataset?.source === 'user' ? 'is-personal' : ''}`}>
          {matchedDataset?.source === 'user' ? 'Personal Dataset' : 'Verified Cluster Dataset'}
        </span>
      </div>
      <div className="mono muted break-all">
        {datasetPath}
      </div>
    </div>
  );
};
