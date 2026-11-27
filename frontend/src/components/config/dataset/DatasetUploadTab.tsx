import React, { useState } from 'react';
import { Package } from 'lucide-react';
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
      setSelectedFile(e.dataTransfer.files[0]);
      setFileUploadError(null);
      setFileUploadSuccess(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
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
      setFileUploadSuccess(`Extracted and uploaded into "${folderName}/" on Tapis storage.`);
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
    <div className="stack">
      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleFileDrop}
        onClick={() => document.getElementById('dataset-file-input')?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            document.getElementById('dataset-file-input')?.click();
          }
        }}
        className={`dropzone ${isDragging ? 'is-dragging' : ''}`}
      >
        <input
          id="dataset-file-input"
          type="file"
          accept=".zip,.tar,.gz,.tgz"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />
        <Package size={24} className="muted" aria-hidden="true" />
        <strong>{selectedFile ? selectedFile.name : 'Drag and drop your dataset archive here'}</strong>
        <span className="muted">
          {selectedFile
            ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB — ready to upload to Tapis`
            : 'Supports .zip, .tar, .tar.gz containing class folders of images (e.g. Kaggle download)'}
        </span>
      </div>

      {selectedFile && (
        <div className="col-end">
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
        <div className="alert alert-info">{uploadProgressText}</div>
      )}

      {fileUploadSuccess && (
        <div className="alert alert-success">{fileUploadSuccess}</div>
      )}

      {fileUploadError && (
        <div role="alert" className="alert alert-error">{fileUploadError}</div>
      )}
    </div>
  );
};
