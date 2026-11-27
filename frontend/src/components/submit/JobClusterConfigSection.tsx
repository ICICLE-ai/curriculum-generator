import React from 'react';
import { Folder, FileCode } from 'lucide-react';
import type { TapisFileItem } from '../../services/tapis';

interface JobClusterConfigSectionProps {
  configFilePath: string;
  onChangeConfigFilePath: (val: string) => void;
  systemRootDir: string;
  cleanUsername: string;
  userConfigFiles: TapisFileItem[];
  isLoadingConfigs: boolean;
}

export const JobClusterConfigSection: React.FC<JobClusterConfigSectionProps> = ({
  configFilePath,
  onChangeConfigFilePath,
  systemRootDir,
  cleanUsername,
  userConfigFiles,
  isLoadingConfigs,
}) => {
  return (
    <div className="stack">
      <div className="row-between">
        <div className="section-title">Config File</div>
        {configFilePath && (
          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={() => onChangeConfigFilePath('')}
          >
            Clear Path
          </button>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="submit-config-path" className="form-label">
          Config File Path on Cluster
        </label>
        <input
          id="submit-config-path"
          type="text"
          className="mono"
          value={configFilePath}
          onChange={(e) => onChangeConfigFilePath(e.target.value)}
          placeholder={systemRootDir ? `${systemRootDir}users/${cleanUsername}/config.yaml` : `/cluster/path/users/${cleanUsername}/config.yaml`}
        />
        <div className="form-helper">
          Passed as the <code>config_file</code> argument when the job starts.
        </div>
      </div>

      <div className="inset-panel stack-sm">
        <div className="row">
          <Folder size={15} className="muted" aria-hidden="true" />
          <strong>Tapis Storage Mapping</strong>
        </div>
        <p className="muted">
          Configs exported to <code>users/{cleanUsername}/smart_curriculum_designer_configs/</code> live on the cluster at:
        </p>
        <div className="path-chip">
          {systemRootDir || '/<cluster_root>/'}users/{cleanUsername}/smart_curriculum_designer_configs/&lt;filename&gt;.yaml
        </div>
      </div>

      <div className="stack-sm">
        <div className="section-heading-xs" style={{ marginBottom: 0 }}>
          Saved Configurations {userConfigFiles.length > 0 ? `(${userConfigFiles.length})` : ''}
        </div>
        {isLoadingConfigs ? (
          <p className="muted">Scanning Tapis storage for saved YAML files...</p>
        ) : userConfigFiles.length === 0 ? (
          <p className="muted">
            No YAML files found in <code>users/{cleanUsername}/smart_curriculum_designer_configs</code>. Export one from Curriculum Config or paste a cluster path above.
          </p>
        ) : (
          <div className="pill-list">
            {userConfigFiles.map((file) => {
              const fullClusterPath = file.clusterPath || `${systemRootDir}users/${cleanUsername}/${file.name}`;
              const isSelected = configFilePath === fullClusterPath;
              return (
                <button
                  key={file.name}
                  type="button"
                  onClick={() => onChangeConfigFilePath(fullClusterPath)}
                  className={`pill ${isSelected ? 'is-selected' : ''}`}
                >
                  <FileCode size={14} aria-hidden="true" />
                  <span>{file.name}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
