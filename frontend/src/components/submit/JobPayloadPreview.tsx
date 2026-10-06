import React, { useState } from 'react';
import type { TapisJobSubmitPayload } from '../../utils/tapisJobs';

interface JobPayloadPreviewProps {
  payload: TapisJobSubmitPayload;
}

export const JobPayloadPreview: React.FC<JobPayloadPreviewProps> = ({ payload }) => {
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <div
      className="card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        position: 'sticky',
        top: '5.5rem',
        maxHeight: 'calc(100vh - 7rem)',
      }}
    >
      <div className="card-header">
        <div>
          <h2 className="card-title">Live Tapis Job Payload</h2>
          <p className="card-subtitle">Exact JSON dispatched to POST /v3/jobs/submit</p>
        </div>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          onClick={handleCopyJson}
        >
          {copiedJson ? 'Copied' : 'Copy JSON'}
        </button>
      </div>

      <pre
        style={{
          flex: 1,
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          lineHeight: 1.5,
          background: '#0c0c0e',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '1rem 1.25rem',
          overflowY: 'auto',
          maxHeight: 'calc(100vh - 14rem)',
          color: '#d4d4d8',
        }}
      >
        {JSON.stringify(payload, null, 2)}
      </pre>
    </div>
  );
};
