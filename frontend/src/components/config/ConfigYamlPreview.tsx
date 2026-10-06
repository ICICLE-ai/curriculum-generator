import React, { useState } from 'react';

interface ConfigYamlPreviewProps {
  yamlContent: string;
  onNavigateToSubmit?: () => void;
}

export const ConfigYamlPreview: React.FC<ConfigYamlPreviewProps> = ({
  yamlContent,
  onNavigateToSubmit,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(yamlContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([yamlContent], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'config.yaml';
    a.click();
    URL.revokeObjectURL(url);
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
          <h2 className="card-title">Live YAML Preview</h2>
          <p className="card-subtitle">Ready to run on HPC cluster or export</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={handleCopy}
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={handleDownload}
          >
            Download .yaml
          </button>
          {onNavigateToSubmit && (
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={onNavigateToSubmit}
              title="Proceed to Job Launch tab"
            >
              Submit Job →
            </button>
          )}
        </div>
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
        {yamlContent}
      </pre>
    </div>
  );
};
