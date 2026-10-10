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
} from '../services/tapis';
import { LogsModal } from '../components/LogsModal';
import {
  JobSelectionToolbar,
  JobTelemetryHeader,
  PipelineProgressCard,
  StageDiagnosticsCard,
  JobArtifactsCard,
} from '../components/monitor';

const DEFAULT_STAGES: PipelineStage[] = [
  { id: 'dataset_ingestion', name: 'Dataset Ingestion', phase: 'Phase 1', status: 'READY', details: 'Scanning directory and resolving canonical classes' },
  { id: 'classification', name: 'Classification', phase: 'Phase 1', status: 'READY', details: 'DINOv2 backbone evaluation' },
  { id: 'segmentation', name: 'Segmentation', phase: 'Phase 1', status: 'READY', details: 'SAM mask extraction' },
  { id: 'curriculum_synthesis', name: 'Curriculum Synthesis', phase: 'Phase 2', status: 'READY', details: 'Multi-week syllabus & JSON generation' },
  { id: 'exercise_generation', name: 'Exercise Scaffolding & Validation', phase: 'Phase 2', status: 'READY', details: 'Generating starter code, solutions, and running unit test sandboxes' },
  { id: 'packaging', name: 'Artifact Packaging', phase: 'Phase 2', status: 'READY', details: 'Final report and requirements.txt' },
];

interface MonitorPageProps {
  initialJobId?: string;
}

export const MonitorPage: React.FC<MonitorPageProps> = ({ initialJobId }) => {
  const token = getStoredToken();

  // Jobs state
  const [jobs, setJobs] = useState<TapisJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>(initialJobId || '');
  const [activeJobDetails, setActiveJobDetails] = useState<TapisJob | null>(null);

  useEffect(() => {
    if (initialJobId) {
      setSelectedJobId(initialJobId);
    }
  }, [initialJobId]);

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
      <JobSelectionToolbar
        jobs={jobs}
        selectedJobId={selectedJobId}
        isLoadingJobs={isLoadingJobs}
        onSelectJob={(id) => setSelectedJobId(id)}
        onTrackCustomJob={(id) => setSelectedJobId(id)}
        errorMsg={errorMsg}
      />

      {/* Macro Telemetry & System Specs */}
      <JobTelemetryHeader
        macroStatus={macroStatus}
        selectedJobId={selectedJobId}
        activeJobDetails={activeJobDetails}
        progressPercent={progressPercent}
        elapsedTime={calculateElapsedTime()}
        lastHeartbeat={progressData?.updated_at}
      />

      {/* Granular Pipeline Stepper Card */}
      <PipelineProgressCard
        displayedStages={displayedStages}
        currentStageId={progressData?.current_stage}
        selectedStageId={selectedStage?.id}
        onSelectStage={(stg) => setSelectedStage(stg)}
        onViewLogs={handleOpenLogs}
        progressPercent={progressPercent}
        statusDescription={statusDescription}
        macroStatus={macroStatus}
      />

      {/* Selected Stage Diagnostic Details */}
      <StageDiagnosticsCard selectedStage={selectedStage} />

      {/* Download & Output Artifacts Card */}
      <JobArtifactsCard
        macroStatus={macroStatus}
        job={activeJobDetails}
        token={token}
        onDownloadArtifact={handleDownloadArtifact}
      />

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
