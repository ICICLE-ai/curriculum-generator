import React, { useState } from 'react';
import { FolderOpen, Upload, Link2, Globe, ChevronDown, ChevronRight } from 'lucide-react';
import type { TapisDatasetItem } from '../../services/tapis';
import { getStoredToken } from '../../utils/storage';
import { parseJwt } from '../../utils/jwt';
import { cleanTapisUsername } from '../../utils/format';
import { Dialog } from '../ui';
import {
  DatasetSelectedBadge,
  DatasetBrowseTab,
  DatasetUploadTab,
  DatasetUrlTab,
  DatasetSystemBrowserTab,
} from './dataset';

interface DatasetUploaderProps {
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
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'browse' | 'upload' | 'url' | 'systems'>('browse');
  const [showManualPath, setShowManualPath] = useState<boolean>(false);

  const token = getStoredToken();
  const decoded = token ? parseJwt(token) : null;
  const username = decoded?.payload['tapis/username'] || (decoded?.payload.sub as string) || '';
  const cleanUsername = cleanTapisUsername(username);

  const matchedDataset = availableDatasets.find(
    (d) => d.clusterPath === datasetPath || (d.name && datasetPath.endsWith(d.name))
  );

  return (
    <div className="form-group">
      <div className="inset-panel stack-sm">
        <div className="row-between">
          <div>
            <div className="inline-label-pair">
              <span className="form-label mb-0">Dataset</span>
              {renderHelpBtn('dataset.root_path')}
            </div>
            <div className="form-helper">
              Choose a cluster dataset, upload an archive, or transfer from another Tapis system.
            </div>
          </div>

          <div className="row">
            {datasetPath && (
              <button
                type="button"
                className="btn btn-sm btn-ghost"
                onClick={() => onChangeDatasetPath('')}
              >
                Clear
              </button>
            )}
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => setIsModalOpen(true)}
            >
              {datasetPath ? 'Change Dataset' : 'Choose Dataset'}
            </button>
          </div>
        </div>

        <DatasetSelectedBadge
          datasetPath={datasetPath}
          matchedDataset={matchedDataset}
        />
      </div>

      {isModalOpen && (
        <Dialog
          title="Select or Import Dataset"
          onClose={() => setIsModalOpen(false)}
          width={840}
          footer={
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setIsModalOpen(false)}
            >
              Done
            </button>
          }
        >
          <div className="stack">
            <DatasetSelectedBadge
              datasetPath={datasetPath}
              matchedDataset={matchedDataset}
            />

            <div className="callout-info">
              <strong>Expected Dataset Format:</strong> Organize your images into one subfolder per category/class
              (for example, <code>my_dataset/healthy/*.jpg</code> and <code>my_dataset/diseased/*.png</code>).
              Archives should unpack to that folder structure.
            </div>

            <div className="tab-strip" role="tablist" aria-label="Dataset Source Tabs">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'browse'}
                onClick={() => setActiveTab('browse')}
                className={`btn btn-sm ${activeTab === 'browse' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <FolderOpen size={14} aria-hidden="true" />
                <span>Available Datasets ({availableDatasets.length})</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'upload'}
                onClick={() => setActiveTab('upload')}
                className={`btn btn-sm ${activeTab === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Upload size={14} aria-hidden="true" />
                <span>Upload Archive</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'url'}
                onClick={() => setActiveTab('url')}
                className={`btn btn-sm ${activeTab === 'url' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Link2 size={14} aria-hidden="true" />
                <span>Import via URL</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'systems'}
                onClick={() => setActiveTab('systems')}
                className={`btn btn-sm ${activeTab === 'systems' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Globe size={14} aria-hidden="true" />
                <span>Tapis Systems</span>
              </button>
            </div>

            {activeTab === 'browse' && (
              <DatasetBrowseTab
                isLoadingDatasets={isLoadingDatasets}
                availableDatasets={availableDatasets}
                datasetPath={datasetPath}
                onSelectDatasetPath={(path) => {
                  onChangeDatasetPath(path);
                  setIsModalOpen(false);
                }}
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

            {activeTab === 'systems' && (
              <DatasetSystemBrowserTab
                token={token}
                username={cleanUsername}
                systemRootDir={systemRootDir}
                onChangeDatasetPath={onChangeDatasetPath}
                onRefreshDatasets={onRefreshDatasets}
              />
            )}

            <div className="divider-top">
              <button
                type="button"
                className="disclosure-btn"
                onClick={() => setShowManualPath(!showManualPath)}
                aria-expanded={showManualPath}
              >
                {showManualPath ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
                <span>Manual cluster directory path (advanced)</span>
              </button>

              {showManualPath && (
                <div className="form-group mt-2">
                  <input
                    type="text"
                    className="mono"
                    value={datasetPath}
                    onChange={(e) => onChangeDatasetPath(e.target.value)}
                    placeholder="/scratch/shared/smart_curriculum_designer_datasets/..."
                  />
                  <div className="form-helper">
                    Raw filesystem path on the HPC execution cluster.
                  </div>
                </div>
              )}
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
};
