import React from 'react';
import type { TapisDatasetItem } from '../../services/tapis';
import { PRESET_OPTIONS } from '../../presets';
import { DatasetUploader } from './DatasetUploader';

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
  onOpenUrlTransferModal?: () => void;
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
  onOpenUrlTransferModal,
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

      {/* Dataset Selection, Upload & URL Transfer Uploader */}
      <DatasetUploader
        datasetPath={datasetPath}
        onChangeDatasetPath={onChangeDatasetPath}
        availableDatasets={availableDatasets}
        systemRootDir={systemRootDir}
        isLoadingDatasets={isLoadingDatasets}
        onRefreshDatasets={() => {
          if (onOpenUrlTransferModal) {
            // Re-trigger scanning
            onOpenUrlTransferModal();
          }
        }}
        renderHelpBtn={renderHelpBtn}
      />

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
