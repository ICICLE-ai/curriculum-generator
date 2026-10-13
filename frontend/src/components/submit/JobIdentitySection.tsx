import React from 'react';

interface JobIdentitySectionProps {
  jobName: string;
  onChangeJobName: (val: string) => void;
  appId: string;
  onChangeAppId: (val: string) => void;
  appVersion: string;
  jobDescription: string;
  onChangeJobDescription: (val: string) => void;
}

export const JobIdentitySection: React.FC<JobIdentitySectionProps> = ({
  jobName,
  onChangeJobName,
  appId,
  onChangeAppId,
  appVersion,
  jobDescription,
  onChangeJobDescription,
}) => {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
        1. Job Identity & Target Application
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">
            <span>Job Name</span>
          </label>
          <input
            type="text"
            value={jobName}
            onChange={(e) => onChangeJobName(e.target.value)}
            placeholder="e.g. skin-cancer-curriculum-run"
            required
          />
          <div className="form-helper">Identifier displayed in Tapis Jobs list</div>
        </div>

        <div className="form-group">
          <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Target Tapis App</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>v{appVersion}</span>
          </label>
          <select
            value={appId}
            onChange={(e) => onChangeAppId(e.target.value)}
          >
            <option value="smart-curriculum-designer">smart-curriculum-designer (v1.0.0 — Production)</option>
            <option value="digital-age-edu-test">digital-age-edu-test (v1.0.0-dev — Testing App)</option>
            <option value="digital-age-edu">digital-age-edu (v1.0.20 — Legacy)</option>
          </select>
          <div className="form-helper">Target: <code>{appId}</code> (v<code>{appVersion}</code>)</div>
        </div>
      </div>

      <div className="form-group" style={{ marginBottom: 0 }}>
        <label className="form-label">
          <span>Job Description</span>
        </label>
        <input
          type="text"
          value={jobDescription}
          onChange={(e) => onChangeJobDescription(e.target.value)}
          placeholder="Run the AI pipeline using a provided YAML configuration."
        />
      </div>
    </div>
  );
};
