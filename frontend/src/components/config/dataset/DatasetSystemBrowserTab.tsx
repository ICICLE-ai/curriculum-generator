import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Folder, FileText, ArrowUp, RefreshCw } from 'lucide-react';
import {
  fetchAccessibleSystems,
  listSystemFiles,
  createTapisToTapisTransfer,
  fetchTransferStatus,
  TAPIS_DATASETS_DIR,
  type TapisSystem,
  type TapisFileItem,
  type TapisTransferResponse,
} from '../../../services/tapis';

interface DatasetSystemBrowserTabProps {
  token: string | null;
  username: string;
  systemRootDir: string;
  onChangeDatasetPath: (path: string) => void;
  onRefreshDatasets: () => void;
}

function formatBytes(bytes?: number): string {
  if (bytes === undefined || bytes === null || isNaN(bytes) || bytes < 0) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
}

function sanitizeFolderName(name: string): string {
  return name.trim().replace(/[^a-zA-Z0-9_\-.]/g, '_') || 'dataset';
}

export const DatasetSystemBrowserTab: React.FC<DatasetSystemBrowserTabProps> = ({
  token,
  username,
  systemRootDir,
  onChangeDatasetPath,
  onRefreshDatasets,
}) => {
  const [systems, setSystems] = useState<TapisSystem[]>([]);
  const [selectedSystemId, setSelectedSystemId] = useState<string>('');
  const [isLoadingSystems, setIsLoadingSystems] = useState<boolean>(false);
  const [systemsError, setSystemsError] = useState<string | null>(null);

  const [currentPath, setCurrentPath] = useState<string>('');
  const [pathInput, setPathInput] = useState<string>('');
  const [items, setItems] = useState<TapisFileItem[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(false);
  const [filesError, setFilesError] = useState<string | null>(null);

  const [selectedSource, setSelectedSource] = useState<{ systemId: string; path: string; name: string } | null>(null);
  const [targetFolderName, setTargetFolderName] = useState<string>('');

  const [isStartingTransfer, setIsStartingTransfer] = useState<boolean>(false);
  const [transferState, setTransferState] = useState<TapisTransferResponse | null>(null);
  const [transferError, setTransferError] = useState<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearPollTimer();
  }, [clearPollTimer]);

  const loadSystems = useCallback(async () => {
    if (!token) return;
    setIsLoadingSystems(true);
    setSystemsError(null);
    try {
      const list = await fetchAccessibleSystems(token);
      setSystems(list);
      if (list.length > 0 && !selectedSystemId) {
        const preferred =
          list.find((s) => s.id === 'cardinal-tapis') ||
          list.find((s) => s.id === 'ascend-static') ||
          list.find((s) => s.id !== 'expanse-tapis-static') ||
          list[0];
        setSelectedSystemId(preferred.id);
      }
    } catch (err) {
      setSystemsError(err instanceof Error ? err.message : 'Failed to load Tapis systems.');
    } finally {
      setIsLoadingSystems(false);
    }
  }, [token, selectedSystemId]);

  useEffect(() => {
    loadSystems();
  }, [loadSystems]);

  const loadDirectory = useCallback(
    async (systemId: string, path: string) => {
      if (!token || !systemId) return;
      setIsLoadingFiles(true);
      setFilesError(null);
      try {
        const result = await listSystemFiles(token, systemId, path);
        setItems(result);
      } catch (err) {
        setItems([]);
        setFilesError(err instanceof Error ? err.message : 'Failed to list directory.');
      } finally {
        setIsLoadingFiles(false);
      }
    },
    [token]
  );

  useEffect(() => {
    if (selectedSystemId) {
      setPathInput(currentPath);
      loadDirectory(selectedSystemId, currentPath);
    }
  }, [selectedSystemId, currentPath, loadDirectory]);

  const handleSelectSystem = (newSystemId: string) => {
    setSelectedSystemId(newSystemId);
    setCurrentPath('');
    setPathInput('');
    setSelectedSource(null);
    setTransferState(null);
    setTransferError(null);
  };

  const handleNavigateToPath = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPath(pathInput.trim().replace(/^\/+|\/+$/g, ''));
  };

  const handleOpenFolder = (folderName: string) => {
    setCurrentPath((prev) => (prev ? `${prev}/${folderName}` : folderName));
  };

  const handleNavigateUp = () => {
    if (!currentPath) return;
    const parts = currentPath.split('/').filter(Boolean);
    parts.pop();
    setCurrentPath(parts.join('/'));
  };

  const handleJumpBreadcrumb = (index: number) => {
    if (index < 0) {
      setCurrentPath('');
      return;
    }
    const parts = currentPath.split('/').filter(Boolean);
    setCurrentPath(parts.slice(0, index + 1).join('/'));
  };

  const handlePickSource = (path: string, name: string) => {
    const cleanPath = path.replace(/^\/+/, '');
    setSelectedSource({ systemId: selectedSystemId, path: cleanPath, name });
    setTargetFolderName(sanitizeFolderName(name));
    setTransferState(null);
    setTransferError(null);
  };

  const handleStartTransfer = async () => {
    if (!token || !username || !selectedSource) {
      setTransferError('Please select a source dataset folder and ensure you are signed in.');
      return;
    }

    const safeTarget = sanitizeFolderName(targetFolderName || selectedSource.name);
    setIsStartingTransfer(true);
    setTransferError(null);
    clearPollTimer();

    try {
      const initial = await createTapisToTapisTransfer(
        token,
        selectedSource.systemId,
        selectedSource.path,
        username,
        safeTarget
      );
      setTransferState(initial);

      const destClusterPath = systemRootDir
        ? `${systemRootDir}users/${username}/${TAPIS_DATASETS_DIR}/${safeTarget}`
        : `/users/${username}/${TAPIS_DATASETS_DIR}/${safeTarget}`;

      pollTimerRef.current = window.setInterval(async () => {
        try {
          const updated = await fetchTransferStatus(token, initial.uuid);
          setTransferState(updated);
          if (updated.status === 'COMPLETED') {
            clearPollTimer();
            onChangeDatasetPath(destClusterPath);
            onRefreshDatasets();
          } else if (updated.status === 'FAILED' || updated.status === 'CANCELLED') {
            clearPollTimer();
            setTransferError(updated.errorMessage || `Transfer ${updated.status.toLowerCase()}.`);
          }
        } catch {
          // Keep polling on transient network error
        }
      }, 2500);
    } catch (err) {
      setTransferError(err instanceof Error ? err.message : 'Failed to start Tapis transfer.');
    } finally {
      setIsStartingTransfer(false);
    }
  };

  const selectedSystemObj = systems.find((s) => s.id === selectedSystemId);
  const breadcrumbs = currentPath ? currentPath.split('/').filter(Boolean) : [];
  const isTransferActive =
    transferState && !['COMPLETED', 'FAILED', 'CANCELLED'].includes(transferState.status);

  return (
    <div className="stack">
      <div className="grid-2">
        <div>
          <label htmlFor="tapis-system-select" className="form-label">
            Source Tapis System
          </label>
          <div className="row">
            <select
              id="tapis-system-select"
              value={selectedSystemId}
              onChange={(e) => handleSelectSystem(e.target.value)}
              disabled={isLoadingSystems || systems.length === 0}
            >
              {systems.map((sys) => (
                <option key={sys.id} value={sys.id}>
                  {sys.id}{sys.host ? ` (${sys.host})` : ''}
                </option>
              ))}
              {systems.length === 0 && (
                <option value="">{isLoadingSystems ? 'Loading systems...' : 'No systems found'}</option>
              )}
            </select>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={loadSystems}
              disabled={isLoadingSystems}
              title="Refresh accessible Tapis systems"
              aria-label="Refresh accessible Tapis systems"
            >
              <RefreshCw size={14} className={isLoadingSystems ? 'spin' : undefined} aria-hidden="true" />
            </button>
          </div>
          {selectedSystemObj?.rootDir && (
            <div className="form-helper">
              System rootDir: <code>{selectedSystemObj.rootDir}</code>
            </div>
          )}
        </div>

        <form onSubmit={handleNavigateToPath}>
          <label htmlFor="tapis-system-path" className="form-label">
            Jump to Path
          </label>
          <div className="row">
            <input
              id="tapis-system-path"
              type="text"
              className="mono"
              value={pathInput}
              onChange={(e) => setPathInput(e.target.value)}
              placeholder="e.g. fs/ess/PAS2699"
            />
            <button type="submit" className="btn btn-sm btn-secondary" disabled={!selectedSystemId || isLoadingFiles}>
              Go
            </button>
          </div>
        </form>
      </div>

      {systemsError && (
        <div role="alert" className="alert alert-error">{systemsError}</div>
      )}

      {selectedSystemId && (
        <div className="breadcrumb-bar">
          <div className="breadcrumb-trail">
            <button
              type="button"
              onClick={() => handleJumpBreadcrumb(-1)}
              className={`breadcrumb-btn ${breadcrumbs.length === 0 ? 'is-current' : ''}`}
            >
              {selectedSystemId}:/
            </button>
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                <span className="muted">/</span>
                <button
                  type="button"
                  onClick={() => handleJumpBreadcrumb(idx)}
                  className={`breadcrumb-btn ${idx === breadcrumbs.length - 1 ? 'is-current' : ''}`}
                >
                  {crumb}
                </button>
              </React.Fragment>
            ))}
          </div>

          {currentPath && (
            <div className="row">
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => handlePickSource(currentPath, breadcrumbs[breadcrumbs.length - 1] || 'dataset')}
              >
                Select current folder
              </button>
              <button type="button" className="btn btn-sm btn-ghost" onClick={handleNavigateUp}>
                <ArrowUp size={13} aria-hidden="true" />
                <span>Up</span>
              </button>
            </div>
          )}
        </div>
      )}

      {isLoadingFiles ? (
        <p className="muted">Listing files on {selectedSystemId}...</p>
      ) : filesError ? (
        <div role="alert" className="alert alert-error">{filesError}</div>
      ) : items.length === 0 ? (
        <div className="empty-state">Empty directory.</div>
      ) : (
        <div className="table-wrap table-scroll">
          <table className="data-table">
            <tbody>
              {items.map((item) => {
                const isDir = item.type === 'dir';
                const isChosen =
                  selectedSource?.systemId === selectedSystemId &&
                  selectedSource?.path === item.path.replace(/^\/+/, '');
                return (
                  <tr key={item.name}>
                    <td>
                      {isDir ? (
                        <button
                          type="button"
                          className="dir-link"
                          onClick={() => handleOpenFolder(item.name)}
                        >
                          <Folder size={14} aria-hidden="true" />
                          <span>{item.name}/</span>
                        </button>
                      ) : (
                        <span className="row mono muted">
                          <FileText size={14} aria-hidden="true" />
                          <span>{item.name}</span>
                        </span>
                      )}
                    </td>
                    <td className="mono muted col-right" style={{ width: '90px' }}>
                      {isDir ? 'dir' : formatBytes(item.size)}
                    </td>
                    <td className="col-right" style={{ width: '100px' }}>
                      {isDir && (
                        <button
                          type="button"
                          className={`btn btn-sm ${isChosen ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => handlePickSource(item.path, item.name)}
                        >
                          {isChosen ? 'Selected' : 'Select'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedSource && (
        <div className="inset-panel stack-sm">
          <strong>Transfer to Expanse Dataset Storage</strong>
          <div className="muted">
            Source:{' '}
            <code>tapis://{selectedSource.systemId}/{selectedSource.path}</code>
          </div>
          <div className="form-group">
            <label htmlFor="tapis-target-folder" className="form-label">
              Destination folder name on Expanse
            </label>
            <input
              id="tapis-target-folder"
              type="text"
              value={targetFolderName}
              onChange={(e) => setTargetFolderName(e.target.value)}
              placeholder="e.g. soybeans_dataset"
            />
            <div className="form-helper">
              Saves to{' '}
              <code>users/{username}/{TAPIS_DATASETS_DIR}/{sanitizeFolderName(targetFolderName || selectedSource.name)}</code>
            </div>
          </div>

          <div className="col-end">
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() => setSelectedSource(null)}
              disabled={isStartingTransfer || Boolean(isTransferActive)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={handleStartTransfer}
              disabled={isStartingTransfer || Boolean(isTransferActive) || !username}
            >
              {isStartingTransfer
                ? 'Starting transfer...'
                : isTransferActive
                ? `Transferring (${transferState?.status})...`
                : 'Transfer to Expanse'}
            </button>
          </div>
        </div>
      )}

      {transferState && (
        <div
          className={`alert alert-col ${
            transferState.status === 'COMPLETED'
              ? 'alert-success'
              : transferState.status === 'FAILED' || transferState.status === 'CANCELLED'
              ? 'alert-error'
              : 'alert-info'
          }`}
        >
          <strong>Tapis Transfer {transferState.status}</strong>
          <span className="mono">
            ID: {transferState.uuid}
            {transferState.totalBytesTransferred != null &&
              ` · ${formatBytes(transferState.totalBytesTransferred)}${
                transferState.estimatedTotalBytes ? ` / ${formatBytes(transferState.estimatedTotalBytes)}` : ''
              }`}
          </span>
          {transferState.status === 'COMPLETED' && (
            <span>Dataset copied to Expanse and selected for your pipeline.</span>
          )}
        </div>
      )}

      {transferError && (
        <div role="alert" className="alert alert-error">{transferError}</div>
      )}
    </div>
  );
};
