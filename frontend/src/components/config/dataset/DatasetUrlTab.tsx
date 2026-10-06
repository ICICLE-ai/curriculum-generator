import React, { useState } from 'react';
import { extractAndUploadArchive } from '../../../utils/archiveExtractor';
import { createTapisDatasetTransfer, TAPIS_DATASETS_DIR } from '../../../services/tapis';

interface DatasetUrlTabProps {
  token: string | null;
  username: string;
  systemRootDir: string;
  onChangeDatasetPath: (path: string) => void;
  onRefreshDatasets: () => void;
}

export const DatasetUrlTab: React.FC<DatasetUrlTabProps> = ({
  token,
  username,
  systemRootDir,
  onChangeDatasetPath,
  onRefreshDatasets,
}) => {
  const [sourceUrl, setSourceUrl] = useState<string>('');
  const [urlDatasetName, setUrlDatasetName] = useState<string>('');
  const [isUrlSubmitting, setIsUrlSubmitting] = useState<boolean>(false);
  const [urlProgressText, setUrlProgressText] = useState<string | null>(null);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [urlWarning, setUrlWarning] = useState<string | null>(null);
  const [urlSuccess, setUrlSuccess] = useState<string | null>(null);

  const handleUrlInputChange = (val: string) => {
    setSourceUrl(val);
    setUrlError(null);
    setUrlSuccess(null);

    if (val.toLowerCase().includes('kaggle.com/datasets') || val.toLowerCase().includes('kaggle.com/')) {
      setUrlWarning(
        '⚠️ Kaggle web links require browser login and will download an HTML page rather than the dataset files. Please download the dataset zip from Kaggle first and drop it into the "Upload Archive (.zip)" tab, or use a direct link (e.g. Hugging Face raw file, GitHub release, or direct S3 link).'
      );
    } else {
      setUrlWarning(null);
    }

    if (!urlDatasetName && val) {
      try {
        const parsed = new URL(val);
        const segments = parsed.pathname.split('/').filter(Boolean);
        const last = segments[segments.length - 1];
        if (last && !last.includes('?') && !last.includes('=')) {
          const stripped = last.replace(/\.(zip|tar|gz|tgz)$/i, '');
          setUrlDatasetName(stripped.replace(/[^a-zA-Z0-9_\-.]/g, '_'));
        }
      } catch {
        const parts = val.split('/');
        const last = parts[parts.length - 1];
        if (last && last.length < 50) {
          const stripped = last.replace(/\.(zip|tar|gz|tgz)$/i, '');
          setUrlDatasetName(stripped.replace(/[^a-zA-Z0-9_\-.]/g, '_'));
        }
      }
    }
  };

  const handleStartUrlTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !username) {
      setUrlError('You must be logged in to transfer datasets to Tapis.');
      return;
    }
    if (!sourceUrl.trim()) {
      setUrlError('Please provide a valid direct dataset URL.');
      return;
    }

    setIsUrlSubmitting(true);
    setUrlError(null);
    setUrlSuccess(null);
    setUrlProgressText('Downloading and checking archive...');

    const safeTarget = (urlDatasetName.trim() || `dataset_${Date.now()}`).replace(/\.(zip|tar|gz|tgz)$/i, '');

    try {
      // Try fetching the archive through browser to auto-unzip
      let downloadedBlob: Blob | null = null;
      let filename = 'archive.zip';
      try {
        const resp = await fetch(sourceUrl.trim());
        if (resp.ok) {
          const blob = await resp.blob();
          downloadedBlob = blob;
          const urlSegments = sourceUrl.trim().split('/').filter(Boolean);
          if (urlSegments.length > 0) {
            filename = urlSegments[urlSegments.length - 1];
          }
        }
      } catch {
        // Fall back to server-side transfer if CORS blocked
      }

      if (downloadedBlob) {
        setUrlProgressText('Extracting archive folders and images...');
        const clusterPath = await extractAndUploadArchive({
          archiveData: downloadedBlob,
          archiveName: filename,
          datasetFolderName: safeTarget,
          token,
          username,
          systemRootDir,
          onProgress: (msg) => setUrlProgressText(msg),
        });
        onChangeDatasetPath(clusterPath);
        setUrlSuccess(`Successfully extracted & uploaded into "${safeTarget}/" on Tapis!`);
        onRefreshDatasets();
      } else {
        // Fallback to Tapis backend transfer
        setUrlProgressText('Dispatching server-to-server transfer via Tapis...');
        await createTapisDatasetTransfer(token, username, sourceUrl.trim(), safeTarget);
        const clusterPath = systemRootDir
          ? `${systemRootDir}users/${username}/${TAPIS_DATASETS_DIR}/${safeTarget}`
          : `/users/${username}/${TAPIS_DATASETS_DIR}/${safeTarget}`;
        onChangeDatasetPath(clusterPath);
        setUrlSuccess(`Server transfer dispatched for "${safeTarget}"!`);
        onRefreshDatasets();
      }
    } catch (err) {
      setUrlError(err instanceof Error ? err.message : 'Failed to process dataset.');
    } finally {
      setIsUrlSubmitting(false);
      setUrlProgressText(null);
    }
  };

  return (
    <form onSubmit={handleStartUrlTransfer}>
      <div className="form-group" style={{ marginBottom: '0.65rem' }}>
        <label className="form-label" style={{ fontSize: '0.78rem' }}>
          Direct Download URL
        </label>
        <input
          type="url"
          value={sourceUrl}
          onChange={(e) => handleUrlInputChange(e.target.value)}
          placeholder="https://huggingface.co/datasets/.../resolve/main/dataset.zip"
          required
        />
        <div className="form-helper" style={{ fontSize: '0.7rem' }}>
          Must be a direct link to a file (Hugging Face direct files, Zenodo, GitHub Releases, S3).
        </div>
      </div>

      {urlWarning && (
        <div
          className="alert"
          style={{
            background: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            color: '#facc15',
            padding: '0.6rem 0.85rem',
            fontSize: '0.725rem',
            marginBottom: '0.75rem',
            lineHeight: 1.45,
          }}
        >
          {urlWarning}
        </div>
      )}

      <div className="form-group" style={{ marginBottom: '0.85rem' }}>
        <label className="form-label" style={{ fontSize: '0.78rem' }}>
          Target Folder Name in Tapis (unzipped directory)
        </label>
        <input
          type="text"
          value={urlDatasetName}
          onChange={(e) => setUrlDatasetName(e.target.value)}
          placeholder="e.g. plant_diseases"
          required
        />
      </div>

      {urlProgressText && (
        <div
          className="alert"
          style={{
            marginBottom: '0.75rem',
            fontSize: '0.75rem',
            background: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
            color: 'var(--accent-cyan)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: 'var(--accent-cyan)',
              display: 'inline-block',
            }}
          />
          <span>{urlProgressText}</span>
        </div>
      )}

      {urlSuccess && (
        <div className="alert alert-success" style={{ marginBottom: '0.75rem', fontSize: '0.75rem' }}>
          ✓ {urlSuccess}
        </div>
      )}
      {urlError && (
        <div className="alert alert-error" style={{ marginBottom: '0.75rem', fontSize: '0.75rem' }}>
          {urlError}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          type="submit"
          className="btn btn-sm btn-primary"
          disabled={isUrlSubmitting || !sourceUrl.trim()}
        >
          {isUrlSubmitting ? 'Transferring...' : 'Transfer to Tapis'}
        </button>
      </div>
    </form>
  );
};

