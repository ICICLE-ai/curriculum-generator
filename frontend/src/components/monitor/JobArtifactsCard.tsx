import React, { useState, useEffect, useCallback } from 'react';
import type { TapisJob, TapisFileItem } from '../../services/tapis';
import { listJobDirectoryContents, fetchJobOutputFileText } from '../../services/tapis';

interface JobArtifactsCardProps {
  macroStatus: string;
  job: TapisJob | null;
  token: string | null;
  onDownloadArtifact: (filename: string) => void;
}

function formatBytes(bytes?: number): string {
  if (bytes === undefined || bytes === null || isNaN(bytes) || bytes < 0) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
}

function getFileIcon(name: string, isDir: boolean): string {
  if (isDir) return '📁';
  const lower = name.toLowerCase();
  if (lower.endsWith('.py')) return '🐍';
  if (lower.endsWith('.json')) return '📄';
  if (lower.endsWith('.yaml') || lower.endsWith('.yml')) return '⚙';
  if (lower.endsWith('.md') || lower.endsWith('.txt')) return '📝';
  if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return '🖼';
  if (lower.endsWith('.csv') || lower.endsWith('.tsv')) return '📊';
  if (lower.endsWith('.pptx')) return '📑';
  if (lower.endsWith('.pdf')) return '📕';
  if (lower.endsWith('.zip') || lower.endsWith('.tar') || lower.endsWith('.gz') || lower.endsWith('.tgz')) return '📦';
  if (lower.endsWith('.out') || lower.endsWith('.log')) return '📋';
  return '📄';
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

  // File Preview Modal State
  const [previewFile, setPreviewFile] = useState<{ name: string; path: string } | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState<boolean>(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [copiedPreview, setCopiedPreview] = useState<boolean>(false);

  const isFinished = macroStatus === 'FINISHED';
  const isRunning = macroStatus === 'RUNNING';

  // Fetch directory listing for the current subpath
  const loadDirectory = useCallback(async () => {
    if (!token || !job) {
      setItems([]);
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    try {
      const contents = await listJobDirectoryContents(token, job, currentSubpath);
      // Sort directories first, then alphabetical by name
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

  // Navigate deeper into a subfolder
  const handleOpenFolder = (folderName: string) => {
    setCurrentSubpath((prev) => (prev ? `${prev}/${folderName}` : folderName));
  };

  // Navigate up one level
  const handleNavigateUp = () => {
    if (!currentSubpath) return;
    const parts = currentSubpath.split('/').filter(Boolean);
    parts.pop();
    setCurrentSubpath(parts.join('/'));
  };

  // Jump to specific breadcrumb
  const handleJumpToBreadcrumb = (index: number) => {
    if (index === -1) {
      setCurrentSubpath('');
      return;
    }
    const parts = currentSubpath.split('/').filter(Boolean);
    const target = parts.slice(0, index + 1).join('/');
    setCurrentSubpath(target);
  };

  // Open Preview Modal
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
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
        <div>
          <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <span>🗂</span>
            <span>Job Output Filesystem</span>
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 0 }}>
            Navigate generated outputs, inspect subdirectories, and download results directly from cluster storage.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={loadDirectory}
            disabled={isLoading || !job}
            title="Refresh directory contents"
            style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: isLoading ? 'spin 1s linear infinite' : 'none' }}
            >
              <path d="M23 4v6h-6" />
              <path d="M1 20v-6h6" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Breadcrumb File Navigation Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.5rem 0.85rem',
          marginBottom: '1rem',
          fontSize: '0.8rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => handleJumpToBreadcrumb(-1)}
            style={{
              background: 'none',
              border: 'none',
              color: breadcrumbs.length === 0 ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              fontWeight: breadcrumbs.length === 0 ? 600 : 400,
              cursor: 'pointer',
              padding: '0.1rem 0.25rem',
              borderRadius: '3px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            📁 outputs
          </button>

          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1;
            return (
              <React.Fragment key={idx}>
                <span style={{ color: 'var(--text-muted)' }}>/</span>
                <button
                  type="button"
                  onClick={() => handleJumpToBreadcrumb(idx)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: isLast ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    fontWeight: isLast ? 600 : 400,
                    cursor: 'pointer',
                    padding: '0.1rem 0.25rem',
                    borderRadius: '3px',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {crumb}
                </button>
              </React.Fragment>
            );
          })}
        </div>

        {breadcrumbs.length > 0 && (
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={handleNavigateUp}
            style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem' }}
          >
            ⬆ Up one level
          </button>
        )}
      </div>

      {/* Directory Contents Table */}
      {isLoading ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ animation: 'spin 1s linear infinite' }}
          >
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          <span>Loading cluster directory contents...</span>
        </div>
      ) : errorMsg ? (
        <div className="alert alert-error" style={{ fontSize: '0.8rem' }}>
          {errorMsg}
        </div>
      ) : items.length === 0 ? (
        <div
          style={{
            padding: '2.5rem 1rem',
            textAlign: 'center',
            background: 'rgba(255, 255, 255, 0.01)',
            border: '1px dashed var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-muted)',
            fontSize: '0.825rem',
          }}
        >
          {isRunning ? (
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Job is currently executing</div>
              <div style={{ marginTop: '0.25rem' }}>Files will appear in this directory as stages write them to disk.</div>
            </div>
          ) : !isFinished ? (
            <div>
              <div style={{ fontSize: '1.25rem', marginBottom: '0.4rem' }}>📂</div>
              <div>No output files found in this directory.</div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: '1.25rem', marginBottom: '0.4rem' }}>✨</div>
              <div>This folder is empty.</div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', textAlign: 'left' }}>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 600 }}>Name</th>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 600, width: '110px' }}>Size</th>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 600, width: '180px' }}>Last Modified</th>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 600, textAlign: 'right', width: '170px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => {
                const isDir = it.type === 'dir';
                const icon = getFileIcon(it.name, isDir);
                const canPreview = !isDir && isPreviewable(it.name);

                return (
                  <tr
                    key={it.name}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      transition: 'background 0.15s ease',
                    }}
                    className="table-row-hover"
                  >
                    {/* Name column */}
                    <td style={{ padding: '0.65rem 0.75rem' }}>
                      {isDir ? (
                        <button
                          type="button"
                          onClick={() => handleOpenFolder(it.name)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--accent-cyan)',
                            fontWeight: 600,
                            fontFamily: 'var(--font-mono)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: 0,
                            textAlign: 'left',
                          }}
                        >
                          <span style={{ fontSize: '1.05rem' }}>{icon}</span>
                          <span>{it.name}/</span>
                        </button>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: 'var(--font-mono)' }}>
                          <span style={{ fontSize: '1rem' }}>{icon}</span>
                          <span style={{ color: 'var(--text-primary)' }}>{it.name}</span>
                        </div>
                      )}
                    </td>

                    {/* Size column */}
                    <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                      {isDir ? '—' : formatBytes(it.size)}
                    </td>

                    {/* Last Modified column */}
                    <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {it.lastModified ? new Date(it.lastModified).toLocaleString() : '—'}
                    </td>

                    {/* Actions column */}
                    <td style={{ padding: '0.65rem 0.75rem', textAlign: 'right' }}>
                      {isDir ? (
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleOpenFolder(it.name)}
                          style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem' }}
                        >
                          Open ➔
                        </button>
                      ) : (
                        <div style={{ display: 'inline-flex', gap: '0.35rem', justifyContent: 'flex-end' }}>
                          {canPreview && (
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={() => handlePreviewFile(it)}
                              title="Preview file contents"
                              style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem' }}
                            >
                              👁 View
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={() => onDownloadArtifact(it.path)}
                            title="Download file to computer"
                            style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem' }}
                          >
                            ⬇ Download
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

      {/* File Preview Modal */}
      {previewFile && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            backdropFilter: 'blur(4px)',
          }}
          onClick={() => setPreviewFile(null)}
        >
          <div
            className="card"
            style={{
              width: '90%',
              maxWidth: '850px',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              margin: '1rem',
              padding: 0,
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '1rem 1.25rem',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'var(--bg-card-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.1rem' }}>{getFileIcon(previewFile.name, false)}</span>
                <span style={{ fontWeight: 600, fontSize: '0.9rem', fontFamily: 'var(--font-mono)' }}>
                  {previewFile.name}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {previewContent && (
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={handleCopyPreview}
                    style={{ fontSize: '0.75rem' }}
                  >
                    {copiedPreview ? '✓ Copied' : 'Copy'}
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-sm btn-primary"
                  onClick={() => onDownloadArtifact(previewFile.path)}
                  style={{ fontSize: '0.75rem' }}
                >
                  ⬇ Download
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewFile(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    fontSize: '1.25rem',
                    cursor: 'pointer',
                    lineHeight: 1,
                    marginLeft: '0.5rem',
                  }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', background: '#090a0f' }}>
              {isPreviewLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  Loading file content from cluster...
                </div>
              ) : previewError ? (
                <div className="alert alert-error">{previewError}</div>
              ) : (
                <pre
                  style={{
                    margin: 0,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.78rem',
                    lineHeight: 1.5,
                    color: '#e2e8f0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                  }}
                >
                  {previewContent}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
