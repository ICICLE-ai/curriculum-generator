import React, { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { extractAndUploadArchive } from '../../../utils/archiveExtractor';
import { sanitizeTapisName } from '../../../utils/format';

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
        'Kaggle web links require browser login and download an HTML page rather than the dataset files. Download the .zip from Kaggle first and use "Upload Archive", or paste a direct file URL.'
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
          setUrlDatasetName(sanitizeTapisName(stripped));
        }
      } catch {
        const parts = val.split('/');
        const last = parts[parts.length - 1];
        if (last && last.length < 50) {
          const stripped = last.replace(/\.(zip|tar|gz|tgz)$/i, '');
          setUrlDatasetName(sanitizeTapisName(stripped));
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
      let downloadedBlob: Blob | null = null;
      let filename = 'archive.zip';
      try {
        const resp = await fetch(sourceUrl.trim());
        if (resp.ok) {
          downloadedBlob = await resp.blob();
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
        setUrlSuccess(`Extracted and uploaded into "${safeTarget}/" on Tapis storage.`);
        onRefreshDatasets();
      } else {
        // The server-side transfer only copies the archive file, unextracted, which the pipeline can't read, so don't do it.
        throw new Error(
          'Your browser is not allowed to download that link, so the files cannot be unpacked here. Use a direct-download link that allows browser downloads, download the archive and use "Upload Archive", or for Hugging Face ask the Assistant to "find a dataset online".'
        );
      }
    } catch (err) {
      setUrlError(err instanceof Error ? err.message : 'Failed to process dataset.');
    } finally {
      setIsUrlSubmitting(false);
      setUrlProgressText(null);
    }
  };

  return (
    <form onSubmit={handleStartUrlTransfer} className="stack">
      <div className="form-group">
        <label htmlFor="dataset-url-input" className="form-label">
          Direct Download URL
        </label>
        <input
          id="dataset-url-input"
          type="url"
          value={sourceUrl}
          onChange={(e) => handleUrlInputChange(e.target.value)}
          placeholder="https://huggingface.co/datasets/.../resolve/main/dataset.zip"
          required
        />
        <div className="form-helper">
          Must be a direct link to a file (Hugging Face raw files, Zenodo, GitHub Releases, S3).
        </div>
      </div>

      {urlWarning && (
        <div className="callout-warning">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} aria-hidden="true" />
          <span>{urlWarning}</span>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="dataset-url-folder" className="form-label">
          Target Folder Name in Tapis
        </label>
        <input
          id="dataset-url-folder"
          type="text"
          value={urlDatasetName}
          onChange={(e) => setUrlDatasetName(e.target.value)}
          placeholder="e.g. plant_diseases"
          required
        />
      </div>

      {urlProgressText && (
        <div className="alert alert-info">{urlProgressText}</div>
      )}

      {urlSuccess && (
        <div className="alert alert-success">{urlSuccess}</div>
      )}

      {urlError && (
        <div role="alert" className="alert alert-error">{urlError}</div>
      )}

      <div className="col-end">
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
