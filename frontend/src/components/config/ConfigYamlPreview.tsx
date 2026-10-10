import React, { useState } from 'react';
import { exportConfigToTapis, TAPIS_CONFIGS_DIR } from '../../services/tapis';
import { getStoredToken } from '../../utils/storage';
import { parseJwt } from '../../utils/jwt';

interface ConfigYamlPreviewProps {
  yamlContent: string;
  defaultConfigName?: string;
  onNavigateToSubmit?: () => void;
}

export const ConfigYamlPreview: React.FC<ConfigYamlPreviewProps> = ({
  yamlContent,
  defaultConfigName = 'curriculum_config',
  onNavigateToSubmit,
}) => {
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportSuccessPath, setExportSuccessPath] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [configFilename, setConfigFilename] = useState<string>(defaultConfigName);
  const [showExportModal, setShowExportModal] = useState<boolean>(false);

  const token = getStoredToken();
  const decoded = token ? parseJwt(token) : null;
  const username = decoded?.payload['tapis/username'] || (decoded?.payload.sub as string) || '';

  const handleDownload = () => {
    const blob = new Blob([yamlContent], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = configFilename.endsWith('.yaml') || configFilename.endsWith('.yml')
      ? configFilename
      : `${configFilename}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportToTapis = async () => {
    if (!token || !username) {
      setExportError('You must be logged in to export directly to Tapis.');
      return;
    }

    setIsExporting(true);
    setExportError(null);
    setExportSuccessPath(null);

    try {
      const res = await exportConfigToTapis(token, username, configFilename, yamlContent);
      setExportSuccessPath(res.clusterPath);
      setShowExportModal(false);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed.');
    } finally {
      setIsExporting(false);
    }
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
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={handleDownload}
          >
            Download .yaml
          </button>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => setShowExportModal(true)}
            style={{
              background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.25) 0%, rgba(14, 165, 233, 0.35) 100%)',
              borderColor: 'var(--accent-cyan)',
              color: '#fafafa',
            }}
          >
            Export to Tapis ↗
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

      {/* Export notification badges */}
      {exportSuccessPath && (
        <div
          className="alert alert-success"
          style={{
            padding: '0.6rem 0.85rem',
            margin: '0.5rem 0',
            fontSize: '0.725rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.2rem',
          }}
        >
          <div style={{ fontWeight: 600 }}>✓ Exported to Tapis storage!</div>
          <div style={{ fontFamily: 'var(--font-mono)', wordBreak: 'break-all', opacity: 0.9 }}>
            {exportSuccessPath}
          </div>
          <div style={{ fontSize: '0.68rem', opacity: 0.8 }}>
            Available under <code>{TAPIS_CONFIGS_DIR}/</code> when launching jobs.
          </div>
        </div>
      )}

      {exportError && (
        <div
          className="alert alert-error"
          style={{ padding: '0.5rem 0.85rem', margin: '0.5rem 0', fontSize: '0.725rem' }}
        >
          {exportError}
        </div>
      )}

      {/* Modal Dialog for Export to Tapis */}
      {showExportModal && (
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
            padding: '1rem',
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '460px',
              width: '100%',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
              padding: '1.5rem',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
              Export YAML to Tapis Storage
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1.25rem', lineHeight: 1.45 }}>
              This will save your curriculum YAML directly to your personal Tapis workspace directory under:
              <br />
              <code style={{ color: 'var(--accent-cyan)' }}>~/smart_curriculum_designer_configs/</code>
            </p>

            <div className="form-group">
              <label className="form-label">Configuration Filename</label>
              <input
                type="text"
                value={configFilename}
                onChange={(e) => setConfigFilename(e.target.value)}
                placeholder="my_curriculum.yaml"
                autoFocus
              />
              <div className="form-helper">
                Will be saved as <code>{configFilename.endsWith('.yaml') ? configFilename : `${configFilename}.yaml`}</code>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowExportModal(false)}
                disabled={isExporting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleExportToTapis}
                disabled={isExporting || !configFilename.trim()}
              >
                {isExporting ? 'Exporting...' : 'Save to Tapis'}
              </button>
            </div>
          </div>
        </div>
      )}

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
