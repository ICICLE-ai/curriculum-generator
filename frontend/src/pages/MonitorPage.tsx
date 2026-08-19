import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getStoredToken } from '../utils/storage';
import {
  fetchUserJobs,
  fetchJobStatus,
  fetchJobDetails,
  fetchJobProgress,
  fetchJobLogs,
  downloadJobArtifact,
  type TapisJob,
  type PipelineProgressData,
  type PipelineStage,
} from '../utils/tapisJobs';
import { StepperStatusBar } from '../components/StepperStatusBar';
import { LogsModal } from '../components/LogsModal';

const DEFAULT_STAGES: PipelineStage[] = [
  { id: 'dataset_ingestion', name: 'Dataset Ingestion', phase: 'Phase 1', status: 'READY', details: 'Scanning directory and resolving canonical classes' },
  { id: 'classification', name: 'Classification', phase: 'Phase 1', status: 'READY', details: 'DINOv2 backbone evaluation' },
  { id: 'segmentation', name: 'Segmentation', phase: 'Phase 1', status: 'READY', details: 'SAM mask extraction' },
  { id: 'curriculum_synthesis', name: 'Curriculum Synthesis', phase: 'Phase 2', status: 'READY', details: 'Multi-week syllabus & JSON generation' },
  { id: 'exercise_generation', name: 'Exercise Scaffolding & Validation', phase: 'Phase 2', status: 'READY', details: 'Generating starter code, solutions, and running unit test sandboxes' },
  { id: 'packaging', name: 'Artifact Packaging', phase: 'Phase 2', status: 'READY', details: 'Final report and requirements.txt' },
];

export const MonitorPage: React.FC = () => {
  const token = getStoredToken();

  // Jobs state
  const [jobs, setJobs] = useState<TapisJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [customJobInput, setCustomJobInput] = useState<string>('');
  const [activeJobDetails, setActiveJobDetails] = useState<TapisJob | null>(null);

  // Live telemetry state
  const [progressData, setProgressData] = useState<PipelineProgressData | null>(null);
  const [macroStatus, setMacroStatus] = useState<string>('UNKNOWN');
  const [selectedStage, setSelectedStage] = useState<PipelineStage | null>(null);

  // UI state
  const [isLoadingJobs, setIsLoadingJobs] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Logs modal state
  const [isLogsOpen, setIsLogsOpen] = useState<boolean>(false);
  const [logsContent, setLogsContent] = useState<string>('');
  const [isLoadingLogs, setIsLoadingLogs] = useState<boolean>(false);

  const intervalIdRef = useRef<number | null>(null);

  // Load jobs list
  const loadUserJobs = useCallback(async () => {
    if (!token) return;
    setIsLoadingJobs(true);
    setErrorMsg(null);
    try {
      const userJobs = await fetchUserJobs(token);
      setJobs(userJobs);
      if (userJobs.length > 0 && !selectedJobId) {
        setSelectedJobId(userJobs[0].uuid);
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to fetch jobs from Tapis.');
    } finally {
      setIsLoadingJobs(false);
    }
  }, [token, selectedJobId]);

  useEffect(() => {
    loadUserJobs();
  }, [loadUserJobs]);

  // Fetch telemetry for active job
  const pollActiveJob = useCallback(async () => {
    if (!token || !selectedJobId) return;

    try {
      setIsRefreshing(true);

      // 1. Fetch macro status
      const statusRes = await fetchJobStatus(token, selectedJobId);
      const currentMacro = statusRes.status || 'UNKNOWN';
      setMacroStatus(currentMacro);

      // 2. Fetch full job details if not yet loaded
      const details = await fetchJobDetails(token, selectedJobId);
      setActiveJobDetails(details);

      // 3. Fetch granular progress.json (resolves subpaths and Files API)
      const progress = await fetchJobProgress(token, selectedJobId, details);
      setProgressData(progress);

      // If job finished or failed, clear polling interval
      if (['FINISHED', 'FAILED', 'CANCELLED'].includes(currentMacro)) {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
        }
      }
    } catch (err) {
      console.warn('Error polling job state:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [token, selectedJobId]);

  // Setup / teardown polling timer
  useEffect(() => {
    if (!selectedJobId || !token) return;

    pollActiveJob();

    if (intervalIdRef.current) {
      clearInterval(intervalIdRef.current);
    }

    intervalIdRef.current = window.setInterval(pollActiveJob, 10000);

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [selectedJobId, token, pollActiveJob]);

  // Handle manual tracking
  const handleTrackCustomJob = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customJobInput.trim()) return;
    setSelectedJobId(customJobInput.trim());
    setCustomJobInput('');
  };

  // Open Logs Modal
  const handleOpenLogs = async () => {
    if (!token || !selectedJobId) return;
    setIsLogsOpen(true);
    setIsLoadingLogs(true);
    try {
      const logs = await fetchJobLogs(token, selectedJobId, activeJobDetails);
      setLogsContent(logs);
    } catch (err) {
      setLogsContent(`Failed to load logs: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const handleDownloadArtifact = async (filename: string) => {
    if (!token || !selectedJobId) return;
    try {
      await downloadJobArtifact(token, selectedJobId, filename, activeJobDetails);
    } catch (err) {
      alert(`Could not download ${filename}: ${err instanceof Error ? err.message : 'File not available'}`);
    }
  };

  // Live 1-second ticking clock for elapsed timer
  const [currentTimeMs, setCurrentTimeMs] = useState<number>(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setCurrentTimeMs(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Compute live elapsed time (from job created timestamp)
  const calculateElapsedTime = () => {
    if (activeJobDetails?.created) {
      const start = new Date(activeJobDetails.created).getTime();
      const end = activeJobDetails.ended ? new Date(activeJobDetails.ended).getTime() : currentTimeMs;
      const diffSec = Math.max(0, Math.floor((end - start) / 1000));
      const h = Math.floor(diffSec / 3600);
      const m = Math.floor((diffSec % 3600) / 60);
      const s = diffSec % 60;
      if (h > 0) return `${h}h ${m}m ${s}s`;
      return `${m}m ${s}s`;
    }
    if (progressData?.elapsed_seconds && progressData.elapsed_seconds > 1) {
      const sec = Math.round(progressData.elapsed_seconds);
      const h = Math.floor(sec / 3600);
      const m = Math.floor((sec % 3600) / 60);
      const s = sec % 60;
      if (h > 0) return `${h}h ${m}m ${s}s`;
      return `${m}m ${s}s`;
    }
    return 'Calculating...';
  };

  // Compute active stages
  const displayedStages: PipelineStage[] = progressData?.stages?.length
    ? progressData.stages
    : DEFAULT_STAGES.map((stg, idx) => {
        if (macroStatus === 'FINISHED') return { ...stg, status: 'COMPLETED' };
        if (macroStatus === 'FAILED') return { ...stg, status: 'FAILED' };
        if (macroStatus === 'RUNNING' && idx === 0) return { ...stg, status: 'IN_PROGRESS', details: 'Job executing on cluster node' };
        return stg;
      });

  const progressPercent = progressData?.progress_percent ?? (macroStatus === 'FINISHED' ? 100 : macroStatus === 'RUNNING' ? 25 : 0);

  const statusDescription =
    progressData?.current_message ||
    (macroStatus === 'RUNNING'
      ? 'Job is actively running on compute node... (Monitoring stdout logs)'
      : macroStatus === 'QUEUED'
      ? 'Waiting in Slurm queue for GPU node allocation...'
      : macroStatus === 'FINISHED'
      ? 'All pipeline stages completed successfully'
      : macroStatus === 'FAILED'
      ? 'Pipeline execution failed on cluster'
      : 'Awaiting cluster stage updates...');

  return (
    <div className="page-container">
      {/* Header & Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1 className="page-title">Live Pipeline & Job Monitor</h1>
          <p className="page-description" style={{ marginBottom: 0 }}>
            Granular stage telemetry, HPC cluster output tracking, and real-time execution logs.
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={pollActiveJob}
            disabled={isRefreshing || !selectedJobId}
            style={{ fontSize: '0.85rem' }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }}
            >
              <path d="M23 4v6h-6" />
              <path d="M1 20v-6h6" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            Refresh State
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleOpenLogs}
            disabled={!selectedJobId}
            style={{ fontSize: '0.85rem' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="4 17 10 11 4 5" />
              <line x1="12" y1="19" x2="20" y2="19" />
            </svg>
            View Raw Logs
          </button>
        </div>
      </div>

      {/* Job Selection Toolbar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          {/* Job Dropdown */}
          <div style={{ flex: '1 1 320px' }}>
            <label
              htmlFor="job-select"
              style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}
            >
              Select Tapis Job
            </label>
            <select
              id="job-select"
              className="text-input"
              style={{ width: '100%', fontSize: '0.85rem' }}
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              disabled={isLoadingJobs}
            >
              {jobs.map((j) => (
                <option key={j.uuid} value={j.uuid}>
                  [{j.status}] {j.name || j.appId} - {j.uuid.substring(0, 8)}... ({j.created ? new Date(j.created).toLocaleDateString() : 'Recent'})
                </option>
              ))}
              {jobs.length === 0 && <option value="">No recent DigitalAgEdu jobs found</option>}
            </select>
          </div>

          {/* Custom Job Search */}
          <form onSubmit={handleTrackCustomJob} style={{ flex: '1 1 280px', display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
            <div style={{ flex: 1 }}>
              <label
                htmlFor="custom-job-input"
                style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}
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
            <button type="submit" className="btn btn-secondary" style={{ fontSize: '0.85rem', padding: '0.55rem 0.85rem' }}>
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

      {/* Macro Telemetry & System Specs */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="meta-item">
            <span className="meta-key">Tapis Status</span>
            <span
              className="status-badge"
              style={{
                background:
                  macroStatus === 'FINISHED'
                    ? 'var(--accent-emerald-subtle)'
                    : macroStatus === 'RUNNING'
                    ? 'var(--accent-primary-subtle)'
                    : macroStatus === 'FAILED'
                    ? 'var(--accent-rose-subtle)'
                    : 'var(--bg-card-subtle)',
                color:
                  macroStatus === 'FINISHED'
                    ? 'var(--accent-emerald)'
                    : macroStatus === 'RUNNING'
                    ? 'var(--accent-primary)'
                    : macroStatus === 'FAILED'
                    ? 'var(--accent-rose)'
                    : 'var(--text-secondary)',
              }}
            >
              <span className="status-dot" />
              {macroStatus}
            </span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Job UUID</span>
            <span className="meta-val" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
              {selectedJobId || 'None'}
            </span>
          </div>
          <div className="meta-item">
            <span className="meta-key">App ID</span>
            <span className="meta-val">{activeJobDetails?.appId || 'digital-age-edu-test'}</span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="meta-item">
            <span className="meta-key">Execution System</span>
            <span className="meta-val">{activeJobDetails?.execSystemId || 'OSC / TACC Cluster'}</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Nodes / Cores</span>
            <span className="meta-val">
              {activeJobDetails?.nodeCount ?? 1} Node / {activeJobDetails?.coresPerNode ?? 12} Cores
            </span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Memory Allocated</span>
            <span className="meta-val">
              {activeJobDetails?.memoryMB ? `${Math.round(activeJobDetails.memoryMB / 1024)} GB` : '64 GB'}
            </span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="meta-item">
            <span className="meta-key">Overall Progress</span>
            <span className="meta-val" style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
              {progressPercent}%
            </span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Elapsed Time</span>
            <span className="meta-val">
              {calculateElapsedTime()}
            </span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Last Heartbeat</span>
            <span className="meta-val" style={{ fontSize: '0.78rem' }}>
              {progressData?.updated_at
                ? new Date(progressData.updated_at).toLocaleTimeString()
                : macroStatus === 'RUNNING'
                ? 'Active (Polling)'
                : 'Awaiting start'}
            </span>
          </div>
        </div>
      </div>

      {/* Granular Pipeline Stepper Card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h2 className="card-title" style={{ margin: 0 }}>Pipeline Stage Progression</h2>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Select any stage for diagnostic inspection
          </span>
        </div>

        <StepperStatusBar
          stages={displayedStages}
          currentStageId={progressData?.current_stage}
          selectedStageId={selectedStage?.id}
          onSelectStage={(stg) => setSelectedStage(stg)}
          onViewLogs={handleOpenLogs}
        />

        {/* Progress Bar */}
        <div style={{ marginTop: '1.25rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              marginBottom: '0.4rem',
            }}
          >
            <span>{statusDescription}</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{progressPercent}%</span>
          </div>
          <div
            style={{
              height: '8px',
              borderRadius: '999px',
              background: 'var(--bg-card-subtle)',
              border: '1px solid var(--border-subtle)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${progressPercent}%`,
                background:
                  macroStatus === 'FAILED'
                    ? 'var(--accent-rose)'
                    : 'linear-gradient(90deg, var(--accent-primary), var(--accent-emerald))',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
        </div>
      </div>

      {/* Selected Stage Diagnostic Details */}
      {selectedStage && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Stage Diagnostics: {selectedStage.name}
            </h3>
            <span
              className="status-badge"
              style={{
                background:
                  selectedStage.status === 'COMPLETED'
                    ? 'var(--accent-emerald-subtle)'
                    : selectedStage.status === 'IN_PROGRESS'
                    ? 'var(--accent-amber-subtle)'
                    : selectedStage.status === 'FAILED'
                    ? 'var(--accent-rose-subtle)'
                    : 'var(--bg-card)',
                color:
                  selectedStage.status === 'COMPLETED'
                    ? 'var(--accent-emerald)'
                    : selectedStage.status === 'IN_PROGRESS'
                    ? 'var(--accent-amber)'
                    : selectedStage.status === 'FAILED'
                    ? 'var(--accent-rose)'
                    : 'var(--text-secondary)',
              }}
            >
              <span className="status-dot" />
              {selectedStage.status}
            </span>
          </div>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            <p style={{ margin: '0 0 0.5rem 0' }}>{selectedStage.details}</p>
            {selectedStage.duration_sec && (
              <div>Execution duration: <strong>{selectedStage.duration_sec} seconds</strong></div>
            )}
            {selectedStage.error && (
              <div style={{ marginTop: '0.5rem', color: 'var(--accent-rose)' }}>
                Error details: {selectedStage.error}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Download & Output Artifacts Card */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: '0.5rem' }}>Curriculum Artifacts & Results</h2>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Download the synthesized syllabus, machine learning metrics report, student exercises, and dependency configurations.
        </p>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleDownloadArtifact('curriculum.json')}
            disabled={macroStatus !== 'FINISHED'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download curriculum.json
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleDownloadArtifact('curriculum_grade_10.md')}
            disabled={macroStatus !== 'FINISHED'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            Download Syllabus (Markdown)
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleDownloadArtifact('results.csv')}
            disabled={macroStatus !== 'FINISHED'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            Download results.csv
          </button>

            
        </div>
      </div>

      {/* Logs Modal */}
      <LogsModal
        isOpen={isLogsOpen}
        onClose={() => setIsLogsOpen(false)}
        logs={logsContent}
        jobUuid={selectedJobId}
        isLoading={isLoadingLogs}
        onRefresh={handleOpenLogs}
      />
    </div>
  );
};
