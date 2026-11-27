import React, { useEffect, useState } from 'react';
import { SlidersHorizontal, Server, Activity, ArrowRight } from 'lucide-react';
import { PageHeader, StatusBadge } from '../components/ui';
import { fetchUserJobs, type TapisJob } from '../services/tapis';
import { getStoredToken } from '../utils/storage';

interface WelcomePageProps {
  onNavigate: (tab: 'config' | 'submit' | 'monitor', presetKey?: string) => void;
  onOpenJob?: (jobUuid: string) => void;
}

export const WelcomePage: React.FC<WelcomePageProps> = ({ onNavigate, onOpenJob }) => {
  const token = getStoredToken();
  const [recentJobs, setRecentJobs] = useState<TapisJob[]>([]);
  const [loadingJobs, setLoadingJobs] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    if (!token) return;
    setLoadingJobs(true);
    fetchUserJobs(token, 5)
      .then((jobs) => {
        if (active) setRecentJobs(jobs.slice(0, 5));
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoadingJobs(false);
      });
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <div className="page-container">
      <PageHeader
        title="Overview"
        description="Turn a labeled image dataset into a multi-week AI course: slides, exercises, and unit tests."
        actions={
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onNavigate('config')}
          >
            <SlidersHorizontal size={16} aria-hidden="true" />
            <span>Design Curriculum</span>
          </button>
        }
      />

      <section className="grid-3">
        <div className="card workflow-card">
          <div className="stack-sm">
            <div className="row-between">
              <span className="step-eyebrow">Step 01</span>
              <SlidersHorizontal size={16} className="muted" aria-hidden="true" />
            </div>
            <h2 className="card-title">Configure Course</h2>
            <p className="muted">
              Select a dataset, choose computer vision tools for artifact generation, and organize weekly modules and learning objectives.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-full"
            onClick={() => onNavigate('config')}
          >
            <span>Open Config Studio</span>
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        </div>

        <div className="card workflow-card">
          <div className="stack-sm">
            <div className="row-between">
              <span className="step-eyebrow">Step 02</span>
              <Server size={16} className="muted" aria-hidden="true" />
            </div>
            <h2 className="card-title">Submit HPC Run</h2>
            <p className="muted">
              Dispatch your curriculum configuration to SDSC Expanse via Tapis with GPU allocation and automated container setup.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-full"
            onClick={() => onNavigate('submit')}
          >
            <span>Submit Job</span>
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        </div>

        <div className="card workflow-card">
          <div className="stack-sm">
            <div className="row-between">
              <span className="step-eyebrow">Step 03</span>
              <Activity size={16} className="muted" aria-hidden="true" />
            </div>
            <h2 className="card-title">Track &amp; Download</h2>
            <p className="muted">
              Monitor stage progress and logs in real time, then download generated syllabi, slides (.pptx), and Python labs.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-full"
            onClick={() => onNavigate('monitor')}
          >
            <span>Open Live Monitor</span>
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Recent Runs</h2>
            <p className="card-subtitle">Your 5 most recent curriculum pipeline runs on Tapis.</p>
          </div>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={() => onNavigate('monitor')}
          >
            View All Runs
          </button>
        </div>

        {loadingJobs ? (
          <p className="muted">Loading recent runs...</p>
        ) : recentJobs.length === 0 ? (
          <div className="empty-state">
            No runs found yet. Configure a curriculum and submit your first HPC run.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run Name</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th className="col-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {recentJobs.map((job) => (
                  <tr key={job.uuid}>
                    <td className="mono">{job.name || job.appId}</td>
                    <td>
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="muted">
                      {job.created ? new Date(job.created).toLocaleString() : '—'}
                    </td>
                    <td className="col-right">
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => (onOpenJob ? onOpenJob(job.uuid) : onNavigate('monitor'))}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};
