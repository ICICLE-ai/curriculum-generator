import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import type { TapisJobSubmitPayload } from '../../services/tapis';

interface JobPayloadPreviewProps {
  payload: TapisJobSubmitPayload;
}

export const JobPayloadPreview: React.FC<JobPayloadPreviewProps> = ({ payload }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <div className="card card-compact">
      <div className="row-between">
        <button
          type="button"
          className="disclosure-btn"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
        >
          {isOpen ? <ChevronDown size={16} aria-hidden="true" /> : <ChevronRight size={16} aria-hidden="true" />}
          <span>Job request (JSON)</span>
        </button>

        {isOpen && (
          <button type="button" className="btn btn-sm btn-secondary" onClick={handleCopyJson}>
            {copiedJson ? <Check size={13} aria-hidden="true" /> : <Copy size={13} aria-hidden="true" />}
            <span>{copiedJson ? 'Copied' : 'Copy JSON'}</span>
          </button>
        )}
      </div>

      {isOpen && (
        <pre className="code-box" style={{ marginTop: 'var(--space-3)', maxHeight: '420px' }}>
          {JSON.stringify(payload, null, 2)}
        </pre>
      )}
    </div>
  );
};
