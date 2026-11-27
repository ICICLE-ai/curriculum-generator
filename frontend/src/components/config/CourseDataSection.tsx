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
  availableDatasets,
  systemRootDir,
  isLoadingDatasets,
  onOpenUrlTransferModal,
  renderHelpBtn,
}) => {
  return (
    <div className="stack">
      <div className="row-between">
        <div>
          <h2 className="card-title">Course &amp; Dataset</h2>
          <p className="card-subtitle">Start from a K-12 template or enter your own subject and image dataset.</p>
        </div>
      </div>

      <div className="inset-panel">
        <div className="row-between mb-0">
          <label htmlFor="preset-select" className="form-label mb-0">
            Course Preset
          </label>
          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={() => onSelectPreset('custom')}
            title="Clear all fields to start from scratch"
          >
            Clear Inputs
          </button>
        </div>
        <select
          id="preset-select"
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
          Populates verified dataset paths and a 3-week K-12 syllabus, or choose Custom to start blank.
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="domain-input" className="form-label">
          <span>Subject Area / Field of Study</span>
          {renderHelpBtn('project.domain')}
        </label>
        <input
          id="domain-input"
          type="text"
          value={domain}
          onChange={(e) => onChangeDomain(e.target.value)}
          placeholder="e.g. Agricultural Science, Medical Imaging, Environmental STEM"
        />
      </div>

      <div className="form-group">
        <label htmlFor="context-input" className="form-label">
          <span>Context / Goal Statement</span>
          {renderHelpBtn('project.context_statement')}
        </label>
        <textarea
          id="context-input"
          rows={3}
          value={contextStatement}
          onChange={(e) => onChangeContextStatement(e.target.value)}
          placeholder="e.g. spotting healthy vs. diseased crop leaves from farm photos"
        />
      </div>

      <DatasetUploader
        datasetPath={datasetPath}
        onChangeDatasetPath={onChangeDatasetPath}
        availableDatasets={availableDatasets}
        systemRootDir={systemRootDir}
        isLoadingDatasets={isLoadingDatasets}
        onRefreshDatasets={() => {
          if (onOpenUrlTransferModal) {
            onOpenUrlTransferModal();
          }
        }}
        renderHelpBtn={renderHelpBtn}
      />
    </div>
  );
};
