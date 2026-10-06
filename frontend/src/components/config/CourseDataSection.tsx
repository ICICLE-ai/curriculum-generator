import React from 'react';
import type { TapisDatasetItem } from '../../utils/tapisJobs';
import { PRESET_OPTIONS } from '../../presets';

interface CourseDataSectionProps {
  selectedPreset: string;
  onSelectPreset: (presetKey: string) => void;
  domain: string;
  onChangeDomain: (value: string) => void;
  contextStatement: string;
  onChangeContextStatement: (value: string) => void;
  datasetPath: string;
  onChangeDatasetPath: (value: string) => void;
  outputPath: string;
  onChangeOutputPath: (value: string) => void;
  availableDatasets: TapisDatasetItem[];
  systemRootDir: string;
  isLoadingDatasets: boolean;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
}

export const CourseDataSection: React.FC<CourseDataSectionProps> = ({
  selectedPreset,
  onSelectPreset,
  domain,
  onChangeDomain,
  contextStatement,
  onChangeContextStatement,
  datasetPath,
  onChangeDatasetPath,
  outputPath,
  onChangeOutputPath,
  availableDatasets,
  systemRootDir,
  isLoadingDatasets,
  renderHelpBtn,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Elevated Preset Picker Banner */}
      <div
        style={{
          background: 'var(--bg-card-subtle)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.15rem 1.25rem',
          marginBottom: '1.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
          <label className="form-label" style={{ marginBottom: 0, fontWeight: 600 }}>
            Load Sample Domain Preset
          </label>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={() => onSelectPreset('custom')}
            title="Wipe all inputs to blank state"
          >
            Wipe / Clear Inputs
          </button>
        </div>
        <select
          value={selectedPreset}
          onChange={(e) => onSelectPreset(e.target.value)}
        >
          {PRESET_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="form-helper">
          Select a predefined template to populate verified dataset paths and module syllabi, or choose Custom to start from scratch.
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          <span>Subject Area / Field of Study</span>
          {renderHelpBtn('project.domain')}
        </label>
        <input
          type="text"
          value={domain}
          onChange={(e) => onChangeDomain(e.target.value)}
          placeholder="e.g. Precision Agriculture, Clinical Oncology, Plant Pathology"
        />
      </div>

      <div className="form-group">
        <label className="form-label">
          <span>Context / Goal Statement</span>
          {renderHelpBtn('project.context_statement')}
        </label>
        <textarea
          rows={3}
          value={contextStatement}
          onChange={(e) => onChangeContextStatement(e.target.value)}
          placeholder="e.g. identifying crop foliar diseases and leaf infections from UAV aerial imagery"
        />
      </div>

      {/* Dataset Filepath & Interactive Cluster Discovery */}
      <div
        style={{
          background: 'var(--bg-card-subtle)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          marginBottom: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
          <label className="form-label" style={{ marginBottom: 0, fontWeight: 600 }}>
            <span>Dataset Filepath (dataset.root_path)</span>
            {renderHelpBtn('project.dataset_path')}
          </label>
          {datasetPath && (
            <button
              type="button"
              onClick={() => onChangeDatasetPath('')}
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

        <input
          type="text"
          value={datasetPath}
          onChange={(e) => onChangeDatasetPath(e.target.value)}
          placeholder={systemRootDir ? `${systemRootDir}shared/smart_curriculum_designer_datasets/skin_cancer_dataset` : '/cluster/shared/smart_curriculum_designer_datasets/skin_cancer_dataset'}
          style={{ fontFamily: 'var(--font-mono)', fontSize: '0.825rem', marginBottom: '0.75rem' }}
        />

        {/* System Mapping Helper Box */}
        <div
          style={{
            padding: '0.65rem 0.85rem',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.725rem',
            color: 'var(--text-secondary)',
            marginBottom: '0.85rem',
            lineHeight: '1.45',
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span>📁</span> Tapis Storage Mapping
          </div>
          <div>
            Shared datasets in <code>expanse-tapis-static/shared/smart_curriculum_designer_datasets/</code> resolve on Expanse at:
          </div>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              color: 'var(--accent-cyan)',
              marginTop: '0.25rem',
              wordBreak: 'break-all',
            }}
          >
            {systemRootDir || '/<cluster_root>/'}shared/smart_curriculum_designer_datasets/&lt;dataset_folder&gt;
          </div>
        </div>

        {/* Quick Autofill Scanned Datasets */}
        <div>
          <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Autofill Scanned Dataset {availableDatasets.length > 0 ? `(${availableDatasets.length} discovered)` : ''}
          </div>
          {isLoadingDatasets ? (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Scanning expanse-tapis-static for available datasets...
            </div>
          ) : availableDatasets.length === 0 ? (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              No dataset directories found in shared or personal cluster storage. Type your custom dataset path above.
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {availableDatasets.map((item) => {
                const isSelected = datasetPath === item.clusterPath || (item.name && datasetPath.endsWith(item.name));
                const getIcon = (name: string) => {
                  if (name.includes('skin') || name.includes('cancer')) return '🩺';
                  if (name.includes('plant') || name.includes('crop')) return '🌾';
                  if (name.includes('food') || name.includes('dish')) return '🍲';
                  return '📁';
                };
                return (
                  <button
                    key={item.name}
                    type="button"
                    onClick={() => onChangeDatasetPath(item.clusterPath)}
                    style={{
                      background: isSelected ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                      border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                      color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      fontSize: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      padding: '0.4rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                    }}
                  >
                    <span>{getIcon(item.name)}</span>
                    <span style={{ fontWeight: isSelected ? 600 : 400 }}>{item.name}</span>
                    <span
                      style={{
                        fontSize: '0.625rem',
                        padding: '0.1rem 0.35rem',
                        borderRadius: '3px',
                        background: item.source === 'user' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(255, 255, 255, 0.08)',
                        color: item.source === 'user' ? 'var(--accent-emerald)' : 'var(--text-muted)',
                      }}
                    >
                      {item.source === 'user' ? 'Personal' : 'Shared'}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Output Directory */}
      <div className="form-group">
        <label className="form-label">
          <span>Output Directory</span>
          {renderHelpBtn('project.output_path')}
        </label>
        <input
          type="text"
          value={outputPath}
          onChange={(e) => onChangeOutputPath(e.target.value)}
          placeholder="outputs/my_curriculum"
        />
        <div className="form-helper">Destination for synthesized labs & slides</div>
      </div>
    </div>
  );
};
