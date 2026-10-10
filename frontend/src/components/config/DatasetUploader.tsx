import React, { useState } from 'react';
import type { TapisDatasetItem } from '../../services/tapis';
import { getStoredToken } from '../../utils/storage';
import { parseJwt } from '../../utils/jwt';
import {
  DatasetSelectedBadge,
  DatasetBrowseTab,
  DatasetUploadTab,
  DatasetUrlTab,
} from './dataset';

export interface DatasetUploaderProps {
  datasetPath: string;
  onChangeDatasetPath: (path: string) => void;
  availableDatasets: TapisDatasetItem[];
  systemRootDir: string;
  isLoadingDatasets: boolean;
  onRefreshDatasets: () => void;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
}

export const DatasetUploader: React.FC<DatasetUploaderProps> = ({
  datasetPath,
  onChangeDatasetPath,
  availableDatasets,
  systemRootDir,
  isLoadingDatasets,
  onRefreshDatasets,
  renderHelpBtn,
}) => {
  const [activeTab, setActiveTab] = useState<'browse' | 'upload' | 'url'>('browse');
  const [showManualPath, setShowManualPath] = useState<boolean>(false);

  const token = getStoredToken();
  const decoded = token ? parseJwt(token) : null;
  const username = decoded?.payload['tapis/username'] || (decoded?.payload.sub as string) || '';
  const cleanUsername = username.includes('@') ? username.split('@')[0] : username;

  // Find currently selected dataset label if any
  const matchedDataset = availableDatasets.find(
    (d) => d.clusterPath === datasetPath || (d.name && datasetPath.endsWith(d.name))
  );

  return (
    <div
      style={{
        background: 'var(--bg-card-subtle)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
        marginBottom: '1.5rem',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
        <div>
          <label className="form-label" style={{ marginBottom: 0, fontWeight: 600 }}>
            <span>Dataset</span>
            {renderHelpBtn('project.dataset_path')}
          </label>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Choose a verified dataset or add your own via upload or URL link.
          </div>
        </div>

        {datasetPath && (
          <button
            type="button"
            onClick={() => onChangeDatasetPath('')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            Clear Selected
          </button>
        )}
      </div>

      {/* Selected Dataset Summary Card */}
      <DatasetSelectedBadge
        datasetPath={datasetPath}
        matchedDataset={matchedDataset}
      />

      {/* Dataset Input Options Tabs */}
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1rem' }}>
        <button
          type="button"
          onClick={() => setActiveTab('browse')}
          className={`btn btn-sm ${activeTab === 'browse' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.76rem' }}
        >
          📂 Available Datasets ({availableDatasets.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('upload')}
          className={`btn btn-sm ${activeTab === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.76rem' }}
        >
          ⬆ Upload Archive (.zip, .tar.gz)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('url')}
          className={`btn btn-sm ${activeTab === 'url' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.76rem' }}
        >
          🔗 Import via URL
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'browse' && (
        <DatasetBrowseTab
          isLoadingDatasets={isLoadingDatasets}
          availableDatasets={availableDatasets}
          datasetPath={datasetPath}
          onSelectDatasetPath={onChangeDatasetPath}
        />
      )}

      {activeTab === 'upload' && (
        <DatasetUploadTab
          token={token}
          username={cleanUsername}
          systemRootDir={systemRootDir}
          onChangeDatasetPath={onChangeDatasetPath}
          onRefreshDatasets={onRefreshDatasets}
        />
      )}

      {activeTab === 'url' && (
        <DatasetUrlTab
          token={token}
          username={cleanUsername}
          systemRootDir={systemRootDir}
          onChangeDatasetPath={onChangeDatasetPath}
          onRefreshDatasets={onRefreshDatasets}
        />
      )}

      {/* Manual Cluster Path Override Toggle */}
      <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.65rem' }}>
        <button
          type="button"
          onClick={() => setShowManualPath(!showManualPath)}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '0.72rem',
            cursor: 'pointer',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <span>{showManualPath ? '▼' : '▶'}</span>
          <span>Manual cluster directory path (advanced)</span>
        </button>

        {showManualPath && (
          <div style={{ marginTop: '0.5rem' }}>
            <input
              type="text"
              value={datasetPath}
              onChange={(e) => onChangeDatasetPath(e.target.value)}
              placeholder="/scratch/shared/smart_curriculum_designer_datasets/..."
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}
            />
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Raw filesystem path on the HPC execution cluster.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
