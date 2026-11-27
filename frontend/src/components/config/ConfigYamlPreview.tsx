import React, { useState } from 'react';
import { Download, CloudUpload, ArrowRight } from 'lucide-react';
import { exportConfigToTapis, TAPIS_CONFIGS_DIR } from '../../services/tapis';
import { getStoredToken } from '../../utils/storage';
import { parseJwt } from '../../utils/jwt';
import { Dialog } from '../ui';

interface ConfigYamlPreviewProps {
  yamlContent: string;
  defaultConfigName?: string;
  onNavigateToSubmit?: () => void;
}

/** Config export & submit actions (Download .yaml, Export to Tapis, Submit Job). */
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
    <>
      <div className="row-wrap">
        <button type="button" className="btn btn-secondary" onClick={handleDownload}>
          <Download size={15} aria-hidden="true" />
          <span>Download .yaml</span>
        </button>
        <button type="button" className="btn btn-primary" onClick={() => setShowExportModal(true)}>
          <CloudUpload size={15} aria-hidden="true" />
          <span>Export to Tapis</span>
        </button>
        {onNavigateToSubmit && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onNavigateToSubmit}
            title="Proceed to Job Launch tab"
          >
            <span>Submit Job</span>
            <ArrowRight size={15} aria-hidden="true" />
          </button>
        )}
      </div>

      {exportSuccessPath && (
        <div className="alert alert-success alert-col btn-full">
          <strong>Saved to Tapis storage</strong>
          <span className="mono">{exportSuccessPath}</span>
          <span className="muted">
            Available under <code>{TAPIS_CONFIGS_DIR}/</code> when launching jobs.
          </span>
        </div>
      )}

      {exportError && (
        <div role="alert" className="alert alert-error btn-full">
          {exportError}
        </div>
      )}

      {showExportModal && (
        <Dialog
          title="Export Configuration to Tapis Storage"
          onClose={() => setShowExportModal(false)}
          width={480}
          busy={isExporting}
          footer={
            <>
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
            </>
          }
        >
          <p className="muted mb-0">
            Saves your curriculum configuration to your Tapis workspace under{' '}
            <code>~/smart_curriculum_designer_configs/</code>.
          </p>

          <div className="form-group mt-4">
            <label htmlFor="export-config-filename" className="form-label">
              Configuration Filename
            </label>
            <input
              id="export-config-filename"
              type="text"
              value={configFilename}
              onChange={(e) => setConfigFilename(e.target.value)}
              placeholder="my_curriculum.yaml"
            />
            <div className="form-helper">
              Will be saved as{' '}
              <code>{configFilename.endsWith('.yaml') || configFilename.endsWith('.yml') ? configFilename : `${configFilename}.yaml`}</code>
            </div>
          </div>
        </Dialog>
      )}
    </>
  );
};
