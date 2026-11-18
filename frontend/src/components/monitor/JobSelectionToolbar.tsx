import React, { useState } from 'react';
import type { TapisJob } from '../../services/tapis';
import { statusLabel } from '../../utils/status';

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
    <section className="card" style={{ marginBottom: 'var(--space-6)', padding: 'var(--space-4)' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div style={{ flex: '2 1 320px' }}>
          <label htmlFor="job-select" className="form-label">Run</label>
          <select id="job-select" value={selectedJobId} onChange={(e) => onSelectJob(e.target.value)} disabled={isLoadingJobs}>
            {jobs.map((j) => (
              <option key={j.uuid} value={j.uuid}>
                {j.name || j.appId} · {statusLabel(j.status)} · {j.created ? new Date(j.created).toLocaleDateString() : 'recent'}
              </option>
            ))}
            {jobs.length === 0 && <option value="">{isLoadingJobs ? 'Loading runs…' : 'No runs yet'}</option>}
          </select>
        </div>

        <form onSubmit={handleTrackSubmit} style={{ flex: '1 1 280px', display: 'flex', alignItems: 'flex-end', gap: 'var(--space-2)' }}>
          <div style={{ flex: 1 }}>
            <label htmlFor="custom-job-input" className="form-label">Open by job ID</label>
            <input
              id="custom-job-input"
              type="text"
              className="mono"
              placeholder="5d7e8b91-4c12-…"
              value={customJobInput}
              onChange={(e) => setCustomJobInput(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-secondary">Open</button>
        </form>
      </div>

      {errorMsg && (
        <p role="alert" style={{ marginTop: 'var(--space-3)', color: 'var(--danger)', fontSize: 'var(--text-sm)' }}>
          {errorMsg}
        </p>
      )}
    </section>
  );
};
