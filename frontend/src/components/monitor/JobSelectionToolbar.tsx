import React, { useState } from 'react';
import type { TapisJob } from '../../services/tapis';

interface JobSelectionToolbarProps {
  jobs: TapisJob[];
  selectedJobId: string;
  isLoadingJobs: boolean;
  onSelectJob: (jobId: string) => void;
  onTrackCustomJob: (customJobId: string) => void;
  errorMsg: string | null;
}

export const JobSelectionToolbar: React.FC<JobSelectionToolbarProps> = ({
  jobs,
  selectedJobId,
  isLoadingJobs,
  onSelectJob,
  onTrackCustomJob,
  errorMsg,
}) => {
  const [customJobInput, setCustomJobInput] = useState<string>('');

  const handleTrackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customJobInput.trim()) return;
    onTrackCustomJob(customJobInput.trim());
    setCustomJobInput('');
  };

  return (
    <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        {/* Job Dropdown */}
        <div style={{ flex: '1 1 320px' }}>
          <label
            htmlFor="job-select"
            style={{
              display: 'block',
              fontSize: '0.78rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: '0.35rem',
            }}
          >
            Select Tapis Job
          </label>
          <select
            id="job-select"
            className="text-input"
            style={{ width: '100%', fontSize: '0.85rem' }}
            value={selectedJobId}
            onChange={(e) => onSelectJob(e.target.value)}
            disabled={isLoadingJobs}
          >
            {jobs.map((j) => (
              <option key={j.uuid} value={j.uuid}>
                [{j.status}] {j.name || j.appId} - {j.uuid.substring(0, 8)}... (
                {j.created ? new Date(j.created).toLocaleDateString() : 'Recent'})
              </option>
            ))}
            {jobs.length === 0 && <option value="">No recent curriculum jobs found</option>}
          </select>
        </div>

        {/* Custom Job Search */}
        <form
          onSubmit={handleTrackSubmit}
          style={{ flex: '1 1 280px', display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}
        >
          <div style={{ flex: 1 }}>
            <label
              htmlFor="custom-job-input"
              style={{
                display: 'block',
                fontSize: '0.78rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.35rem',
              }}
            >
              Track Specific UUID
            </label>
            <input
              id="custom-job-input"
              type="text"
              className="text-input"
              style={{ width: '100%', fontSize: '0.85rem' }}
              placeholder="e.g. 5d7e8b91-4c12..."
              value={customJobInput}
              onChange={(e) => setCustomJobInput(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '0.55rem 0.85rem' }}
          >
            Track
          </button>
        </form>
      </div>

      {errorMsg && (
        <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--accent-rose)' }}>
          {errorMsg}
        </div>
      )}
    </div>
  );
};
