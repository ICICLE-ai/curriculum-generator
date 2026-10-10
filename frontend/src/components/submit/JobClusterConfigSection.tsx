import React from 'react';
import type { TapisFileItem } from '../../services/tapis';

interface JobClusterConfigSectionProps {
  configFilePath: string;
  onChangeConfigFilePath: (val: string) => void;
  systemRootDir: string;
  cleanUsername: string;
  execSystemId: string;
  userConfigFiles: TapisFileItem[];
  isLoadingConfigs: boolean;
}

export const JobClusterConfigSection: React.FC<JobClusterConfigSectionProps> = ({
  configFilePath,
  onChangeConfigFilePath,
  systemRootDir,
  cleanUsername,
  execSystemId: _execSystemId,
  userConfigFiles,
  isLoadingConfigs,
}) => {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          2. Cluster YAML Configuration File
        </div>
        {configFilePath && (
          <button
            type="button"
            onClick={() => onChangeConfigFilePath('')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            Clear Path
          </button>
        )}
      </div>

      <div className="form-group" style={{ marginBottom: '0.75rem' }}>
        <label className="form-label">
          <span>Absolute Path on Cluster (config_file)</span>
        </label>
        <input
          type="text"
          value={configFilePath}
          onChange={(e) => onChangeConfigFilePath(e.target.value)}
          placeholder={systemRootDir ? `${systemRootDir}users/${cleanUsername}/config.yaml` : `/cluster/path/users/${cleanUsername}/config.yaml`}
          style={{ fontFamily: 'var(--font-mono)', fontSize: '0.825rem' }}
        />
      </div>

      {/* Tapis Files Path Mapping Box */}
      <div
        style={{
          padding: '0.75rem 0.95rem',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.75rem',
          lineHeight: '1.5',
          color: 'var(--text-secondary)',
          marginBottom: '0.85rem',
        }}
      >
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span>📁</span> Tapis Storage Mapping
        </div>
        <div>
          Configurations saved under <code>users/{cleanUsername}/smart_curriculum_designer_configs/</code> resolve on the cluster at:
        </div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--accent-cyan)',
            background: 'rgba(6, 182, 212, 0.08)',
            padding: '0.35rem 0.6rem',
            borderRadius: '4px',
            marginTop: '0.35rem',
            wordBreak: 'break-all',
            userSelect: 'all',
          }}
        >
          {systemRootDir || '/<cluster_root>/'}users/{cleanUsername}/smart_curriculum_designer_configs/&lt;filename&gt;.yaml
        </div>
      </div>

      {/* Quick Config Selector Pills */}
      <div>
        <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.45rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Autofill Config Path {userConfigFiles.length > 0 ? `(${userConfigFiles.length} found in Tapis storage)` : ''}
        </div>
        {isLoadingConfigs ? (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Scanning Tapis storage for configuration files...
          </div>
        ) : userConfigFiles.length === 0 ? (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            No YAML files found in <code>users/{cleanUsername}/smart_curriculum_designer_configs</code>. Export a config from the Curriculum Config studio or type the cluster path above.
          </div>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
            {userConfigFiles.map((file) => {
              const fullClusterPath = file.clusterPath || `${systemRootDir}users/${cleanUsername}/${file.name}`;
              const isSelected = configFilePath === fullClusterPath;
              return (
                <button
                  key={file.name}
                  type="button"
                  onClick={() => onChangeConfigFilePath(fullClusterPath)}
                  style={{
                    background: isSelected ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    fontSize: '0.72rem',
                    fontFamily: 'var(--font-mono)',
                    padding: '0.3rem 0.65rem',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <span>📄</span>
                  {file.name}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
