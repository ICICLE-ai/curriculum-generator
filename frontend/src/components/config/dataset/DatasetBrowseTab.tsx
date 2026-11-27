import React from 'react';
import { Folder } from 'lucide-react';
import type { TapisDatasetItem } from '../../../services/tapis';

interface DatasetBrowseTabProps {
  isLoadingDatasets: boolean;
  availableDatasets: TapisDatasetItem[];
  datasetPath: string;
  onSelectDatasetPath: (path: string) => void;
}

export const DatasetBrowseTab: React.FC<DatasetBrowseTabProps> = ({
  isLoadingDatasets,
  availableDatasets,
  datasetPath,
  onSelectDatasetPath,
}) => {
  if (isLoadingDatasets) {
    return <p className="muted">Scanning Tapis storage for available datasets...</p>;
  }

  if (availableDatasets.length === 0) {
    return (
      <div className="empty-state">
        No dataset directories found in storage yet. Upload an archive, import via URL, or transfer from another Tapis system.
      </div>
    );
  }

  return (
    <div className="pill-list">
      {availableDatasets.map((item) => {
        const isSelected = datasetPath === item.clusterPath || (item.name && datasetPath.endsWith(item.name));
        return (
          <button
            key={item.name}
            type="button"
            onClick={() => onSelectDatasetPath(item.clusterPath)}
            className={`pill ${isSelected ? 'is-selected' : ''}`}
          >
            <Folder size={14} aria-hidden="true" />
            <span>{item.name}</span>
            <span className={`pill-tag ${item.source === 'user' ? 'is-personal' : ''}`}>
              {item.source === 'user' ? 'Personal' : 'Shared'}
            </span>
          </button>
        );
      })}
    </div>
  );
};
