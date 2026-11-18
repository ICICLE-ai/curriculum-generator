import React, { useState, useEffect, useRef } from 'react';
import { Dialog } from './ui';

interface LogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  logs: string;
  jobUuid: string;
  isLoading?: boolean;
  onRefresh?: () => void;
}

export const LogsModal: React.FC<LogsModalProps> = ({ isOpen, onClose, logs, jobUuid, isLoading = false, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);
  const logContainerRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll, isOpen]);

  if (!isOpen) return null;

  const filteredLogs = searchTerm.trim()
    ? logs
        .split('\n')
        .filter((line) => line.toLowerCase().includes(searchTerm.toLowerCase()))
        .join('\n')
    : logs;

  const handleCopy = () => {
    navigator.clipboard.writeText(logs);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog
      title={
        <>
          Job log <span className="muted mono" style={{ fontWeight: 400 }}>{jobUuid}</span>
        </>
      }
      onClose={onClose}
      width={1040}
      height="85vh"
      headerActions={
        <>
          {onRefresh && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={onRefresh} disabled={isLoading}>
              {isLoading ? 'Loading…' : 'Refresh'}
            </button>
          )}
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleCopy}>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <input
            type="search"
            aria-label="Filter log lines"
            placeholder="Filter lines (e.g. Error, Week 3)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1 }}
          />
          <label className="muted" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', whiteSpace: 'nowrap' }}>
            <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} />
            Follow end
          </label>
        </div>
        <pre
          ref={logContainerRef}
          className="code-box"
          style={{ flex: 1, minHeight: 0, margin: 0, overflowY: 'auto', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}
        >
          {isLoading && !logs
            ? 'Loading the log from the cluster…'
            : filteredLogs.trim().length === 0
            ? searchTerm
              ? 'No lines match.'
              : 'No log output yet.'
            : filteredLogs}
        </pre>
      </div>
    </Dialog>
  );
};
