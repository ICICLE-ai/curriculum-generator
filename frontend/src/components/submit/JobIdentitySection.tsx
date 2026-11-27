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
    <div className="stack">
      <div className="section-title">Run Details</div>

      <div className="grid-2">
        <div className="form-group">
          <label htmlFor="submit-job-name" className="form-label">
            Run Name
          </label>
          <input
            id="submit-job-name"
            type="text"
            value={jobName}
            onChange={(e) => onChangeJobName(e.target.value)}
            placeholder="e.g. skin-cancer-curriculum-run"
            required
          />
          <div className="form-helper">Shown in Live Monitor and the Tapis jobs list.</div>
        </div>

        <div className="form-group">
          <label htmlFor="submit-app-id" className="form-label">
            <span>Pipeline App</span>
            <span className="muted mono">v{appVersion}</span>
          </label>
          <select
            id="submit-app-id"
            value={appId}
            onChange={(e) => onChangeAppId(e.target.value)}
          >
            <option value="smart-curriculum-designer">smart-curriculum-designer (1.0.0 — Production)</option>
            <option value="digital-age-edu-test">digital-age-edu-test (1.0.0-dev — Testing)</option>
            <option value="digital-age-edu">digital-age-edu (1.0.20 — Previous)</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="submit-job-desc" className="form-label">
          Description
        </label>
        <input
          id="submit-job-desc"
          type="text"
          value={jobDescription}
          onChange={(e) => onChangeJobDescription(e.target.value)}
          placeholder="Run the AI pipeline using a provided YAML configuration."
        />
      </div>
    </div>
  );
};
