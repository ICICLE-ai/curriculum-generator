import React, { useState } from 'react';
import { extractAndUploadArchive } from '../../../utils/archiveExtractor';

interface DatasetUploadTabProps {
  token: string | null;
  username: string;
  systemRootDir: string;
  onChangeDatasetPath: (path: string) => void;
  onRefreshDatasets: () => void;
}

export const DatasetUploadTab: React.FC<DatasetUploadTabProps> = ({
  token,
  username,
  systemRootDir,
  onChangeDatasetPath,
  onRefreshDatasets,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isFileUploading, setIsFileUploading] = useState<boolean>(false);
  const [uploadProgressText, setUploadProgressText] = useState<string | null>(null);
  const [fileUploadError, setFileUploadError] = useState<string | null>(null);
  const [fileUploadSuccess, setFileUploadSuccess] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setFileUploadError(null);
      setFileUploadSuccess(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setFileUploadError(null);
      setFileUploadSuccess(null);
    }
  };

  const handleUploadFile = async () => {
    if (!selectedFile || !token || !username) {
      setFileUploadError('Please select a file and ensure you are logged in.');
      return;
    }

    setIsFileUploading(true);
    setFileUploadError(null);
    setFileUploadSuccess(null);
    setUploadProgressText('Opening archive...');

    const folderName = selectedFile.name.replace(/\.(zip|tar|gz|tgz)$/i, '').replace(/[^a-zA-Z0-9_-]/g, '_');

    try {
      const clusterPath = await extractAndUploadArchive({
        archiveData: selectedFile,
        archiveName: selectedFile.name,
        datasetFolderName: folderName,
        token,
        username,
        systemRootDir,
        onProgress: (msg) => setUploadProgressText(msg),
      });

      onChangeDatasetPath(clusterPath);
      setFileUploadSuccess(`Extracted and uploaded into "${folderName}/" directory on Tapis!`);
      setSelectedFile(null);
      onRefreshDatasets();
    } catch (err) {
      setFileUploadError(err instanceof Error ? err.message : 'Failed to extract and upload archive.');
    } finally {
      setIsFileUploading(false);
      setUploadProgressText(null);
    }
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleFileDrop}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '1.75rem 1.5rem',
          textAlign: 'center',
          background: isDragging ? 'rgba(6, 182, 212, 0.08)' : 'rgba(255, 255, 255, 0.02)',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
        onClick={() => document.getElementById('dataset-file-input')?.click()}
      >
        <input
          id="dataset-file-input"
          type="file"
          accept=".zip,.tar,.gz,.tgz"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />
        <div style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>📦</div>
        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
          {selectedFile ? selectedFile.name : 'Drag & drop your dataset archive here'}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          {selectedFile
            ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to upload to Tapis`
            : 'Supports .zip, .tar, .tar.gz containing class folders of images (e.g. Kaggle download)'}
        </div>
      </div>

      {selectedFile && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.85rem' }}>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={() => setSelectedFile(null)}
            disabled={isFileUploading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={handleUploadFile}
            disabled={isFileUploading}
          >
            {isFileUploading ? 'Unpacking & Uploading...' : 'Unpack & Upload to Tapis'}
          </button>
        </div>
      )}

      {uploadProgressText && (
        <div
          className="alert"
          style={{
            marginTop: '0.75rem',
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
          <span>{uploadProgressText}</span>
        </div>
      )}

      {fileUploadSuccess && (
        <div className="alert alert-success" style={{ marginTop: '0.75rem', fontSize: '0.75rem' }}>
          ✓ {fileUploadSuccess}
        </div>
      )}
      {fileUploadError && (
        <div className="alert alert-error" style={{ marginTop: '0.75rem', fontSize: '0.75rem' }}>
          {fileUploadError}
        </div>
      )}
    </div>
  );
};

