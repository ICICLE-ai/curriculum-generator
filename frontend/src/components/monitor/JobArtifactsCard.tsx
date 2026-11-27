import React, { useState, useEffect, useCallback } from 'react';
import {
  Folder,
  FileCode,
  FileJson,
  FileText,
  Image,
  FileSpreadsheet,
  Archive,
  File,
  RefreshCw,
  ArrowUp,
  Eye,
  Download,
  Copy,
  Check,
  ChevronRight,
} from 'lucide-react';
import type { TapisJob, TapisFileItem } from '../../services/tapis';
import { listJobDirectoryContents, fetchJobOutputFileText } from '../../services/tapis';
import { formatBytes } from '../../utils/format';
import { Dialog } from '../ui';

interface JobArtifactsCardProps {
  macroStatus: string;
  job: TapisJob | null;
  token: string | null;
  onDownloadArtifact: (filename: string) => void;
}

function renderFileIcon(name: string, isDir: boolean): React.ReactNode {
  if (isDir) return <Folder size={15} aria-hidden="true" />;
  const lower = name.toLowerCase();
  if (lower.endsWith('.py') || lower.endsWith('.yaml') || lower.endsWith('.yml')) {
    return <FileCode size={15} aria-hidden="true" />;
  }
  if (lower.endsWith('.json')) return <FileJson size={15} aria-hidden="true" />;
  if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg')) {
    return <Image size={15} aria-hidden="true" />;
  }
  if (lower.endsWith('.csv') || lower.endsWith('.tsv')) {
    return <FileSpreadsheet size={15} aria-hidden="true" />;
  }
  if (lower.endsWith('.zip') || lower.endsWith('.tar') || lower.endsWith('.gz') || lower.endsWith('.tgz')) {
    return <Archive size={15} aria-hidden="true" />;
  }
  if (lower.endsWith('.md') || lower.endsWith('.txt') || lower.endsWith('.out') || lower.endsWith('.log')) {
    return <FileText size={15} aria-hidden="true" />;
  }
  return <File size={15} aria-hidden="true" />;
}

function isPreviewable(name: string): boolean {
  const lower = name.toLowerCase();
  return (
    lower.endsWith('.json') ||
    lower.endsWith('.py') ||
    lower.endsWith('.md') ||
    lower.endsWith('.txt') ||
    lower.endsWith('.csv') ||
    lower.endsWith('.tsv') ||
    lower.endsWith('.yaml') ||
    lower.endsWith('.yml') ||
    lower.endsWith('.out') ||
    lower.endsWith('.log')
  );
}

export const JobArtifactsCard: React.FC<JobArtifactsCardProps> = ({
  macroStatus,
  job,
  token,
  onDownloadArtifact,
}) => {
  const [currentSubpath, setCurrentSubpath] = useState<string>('');
  const [items, setItems] = useState<TapisFileItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [previewFile, setPreviewFile] = useState<{ name: string; path: string } | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState<boolean>(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [copiedPreview, setCopiedPreview] = useState<boolean>(false);

  const isFinished = macroStatus === 'FINISHED';
  const isRunning = macroStatus === 'RUNNING';

  const loadDirectory = useCallback(async () => {
    if (!token || !job) {
      setItems([]);
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    try {
      const contents = await listJobDirectoryContents(token, job, currentSubpath);
      const sorted = [...contents].sort((a, b) => {
        if (a.type === 'dir' && b.type !== 'dir') return -1;
        if (a.type !== 'dir' && b.type === 'dir') return 1;
        return a.name.localeCompare(b.name);
      });
      setItems(sorted);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to list directory contents.');
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  }, [token, job, currentSubpath]);

  useEffect(() => {
    loadDirectory();
  }, [loadDirectory]);

  const handleOpenFolder = (folderName: string) => {
    setCurrentSubpath((prev) => (prev ? `${prev}/${folderName}` : folderName));
  };

  const handleNavigateUp = () => {
    if (!currentSubpath) return;
    const parts = currentSubpath.split('/').filter(Boolean);
    parts.pop();
    setCurrentSubpath(parts.join('/'));
  };

  const handleJumpToBreadcrumb = (index: number) => {
    if (index === -1) {
      setCurrentSubpath('');
      return;
    }
    const parts = currentSubpath.split('/').filter(Boolean);
    setCurrentSubpath(parts.slice(0, index + 1).join('/'));
  };

  const handlePreviewFile = async (item: TapisFileItem) => {
    if (!token || !job) return;
    setPreviewFile({ name: item.name, path: item.path });
    setIsPreviewLoading(true);
    setPreviewContent(null);
    setPreviewError(null);
    setCopiedPreview(false);

    try {
      const text = await fetchJobOutputFileText(token, job.uuid, item.path);
      setPreviewContent(text);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : 'Unable to preview file.');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleCopyPreview = () => {
    if (previewContent) {
      navigator.clipboard.writeText(previewContent);
      setCopiedPreview(true);
      setTimeout(() => setCopiedPreview(false), 2000);
    }
  };

  const breadcrumbs = currentSubpath ? currentSubpath.split('/').filter(Boolean) : [];

  return (
    <section className="card stack">
      <div className="card-header mb-0">
        <div>
          <h2 className="section-title">Outputs</h2>
          <p className="card-subtitle">
            Browse generated slides, notebooks, and metrics from cluster storage.
          </p>
        </div>

        <button
          type="button"
          className="btn btn-sm btn-secondary"
          onClick={loadDirectory}
          disabled={isLoading || !job}
        >
          <RefreshCw size={13} className={isLoading ? 'spin' : undefined} aria-hidden="true" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="breadcrumb-bar">
        <div className="breadcrumb-trail">
          <button
            type="button"
            onClick={() => handleJumpToBreadcrumb(-1)}
            className={`breadcrumb-btn ${breadcrumbs.length === 0 ? 'is-current' : ''}`}
          >
            <Folder size={13} aria-hidden="true" />
            <span>outputs</span>
          </button>

          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              <span className="muted">/</span>
              <button
                type="button"
                onClick={() => handleJumpToBreadcrumb(idx)}
                className={`breadcrumb-btn ${idx === breadcrumbs.length - 1 ? 'is-current' : ''}`}
              >
                {crumb}
              </button>
            </React.Fragment>
          ))}
        </div>

        {breadcrumbs.length > 0 && (
          <button type="button" className="btn btn-sm btn-secondary" onClick={handleNavigateUp}>
            <ArrowUp size={13} aria-hidden="true" />
            <span>Up</span>
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="row muted">
          <RefreshCw size={14} className="spin" aria-hidden="true" />
          <span>Loading directory contents...</span>
        </div>
      ) : errorMsg ? (
        <div role="alert" className="alert alert-error">{errorMsg}</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          {isRunning
            ? 'Job is running. Output files will appear here as stages write them.'
            : isFinished
            ? 'This folder is empty.'
            : 'No output files found in this directory.'}
        </div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th style={{ width: '110px' }}>Size</th>
                <th style={{ width: '190px' }}>Modified</th>
                <th className="col-right" style={{ width: '190px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => {
                const isDir = it.type === 'dir';
                const canPreview = !isDir && isPreviewable(it.name);

                return (
                  <tr key={it.name}>
                    <td>
                      {isDir ? (
                        <button
                          type="button"
                          className="dir-link"
                          onClick={() => handleOpenFolder(it.name)}
                        >
                          {renderFileIcon(it.name, true)}
                          <span>{it.name}/</span>
                        </button>
                      ) : (
                        <div className="row mono">
                          <span className="muted">
                            {renderFileIcon(it.name, false)}
                          </span>
                          <span>{it.name}</span>
                        </div>
                      )}
                    </td>
                    <td className="mono muted">{isDir ? '—' : formatBytes(it.size)}</td>
                    <td className="muted">
                      {it.lastModified ? new Date(it.lastModified).toLocaleString() : '—'}
                    </td>
                    <td className="col-right">
                      {isDir ? (
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleOpenFolder(it.name)}
                        >
                          <span>Open</span>
                          <ChevronRight size={13} aria-hidden="true" />
                        </button>
                      ) : (
                        <div className="col-end">
                          {canPreview && (
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={() => handlePreviewFile(it)}
                            >
                              <Eye size={13} aria-hidden="true" />
                              <span>View</span>
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={() => onDownloadArtifact(it.path)}
                          >
                            <Download size={13} aria-hidden="true" />
                            <span>Download</span>
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {previewFile && (
        <Dialog
          title={
            <span className="row mono">
              {renderFileIcon(previewFile.name, false)}
              <span>{previewFile.name}</span>
            </span>
          }
          onClose={() => setPreviewFile(null)}
          width={860}
          height="82vh"
          headerActions={
            <>
              {previewContent && (
                <button type="button" className="btn btn-sm btn-secondary" onClick={handleCopyPreview}>
                  {copiedPreview ? <Check size={13} aria-hidden="true" /> : <Copy size={13} aria-hidden="true" />}
                  <span>{copiedPreview ? 'Copied' : 'Copy'}</span>
                </button>
              )}
              <button
                type="button"
                className="btn btn-sm btn-primary"
                onClick={() => onDownloadArtifact(previewFile.path)}
              >
                <Download size={13} aria-hidden="true" />
                <span>Download</span>
              </button>
            </>
          }
        >
          {isPreviewLoading ? (
            <p className="muted">Loading file content from cluster...</p>
          ) : previewError ? (
            <div role="alert" className="alert alert-error">{previewError}</div>
          ) : (
            <pre className="code-box mb-0">{previewContent}</pre>
          )}
        </Dialog>
      )}
    </section>
  );
};
