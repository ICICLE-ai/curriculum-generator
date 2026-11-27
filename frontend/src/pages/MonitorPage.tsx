import React, { useState, useEffect, useRef, useCallback } from 'react';
import { RefreshCw, Terminal } from 'lucide-react';
import { getStoredToken } from '../utils/storage';
import {
  fetchUserJobs,
  fetchJobStatus,
  fetchJobDetails,
  fetchJobProgress,
  fetchJobLogs,
  downloadJobArtifact,
  parseJobJson,
  type TapisJob,
  type PipelineProgressData,
  type PipelineStage,
} from '../services/tapis';
import { LogsModal } from '../components/LogsModal';
import { PageHeader } from '../components/ui';
import { deriveStages, stagePercent } from '../utils/stages';
import {
  JobSelectionToolbar,
  JobTelemetryHeader,
  PipelineProgressCard,
  StageDiagnosticsCard,
  JobArtifactsCard,
  RerunPhase2Dialog,
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

  const [isRerunOpen, setIsRerunOpen] = useState<boolean>(false);
  useEffect(() => setSelectedStage(null), [selectedJobId]);
  const rerunOf = parseJobJson(activeJobDetails?.notes);

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

  const isActive = !['FINISHED', 'FAILED', 'CANCELLED'].includes(macroStatus);
  const displayedStages: PipelineStage[] = deriveStages(progressData?.stages, DEFAULT_STAGES, macroStatus);
  const progressPercent = stagePercent(displayedStages);

  const statusDescription =
    macroStatus === 'FINISHED'
      ? 'All stages finished.'
      : macroStatus === 'FAILED'
      ? `Failed${displayedStages.find((s) => s.status === 'FAILED') ? ` during ${displayedStages.find((s) => s.status === 'FAILED')!.name}` : ''}. The log has the details.`
      : macroStatus === 'CANCELLED'
      ? 'Cancelled.'
      : macroStatus === 'QUEUED'
      ? 'Waiting in the Slurm queue for a node.'
      : progressData?.current_message || 'Waiting for the first stage update.';

  const canRerun = !!activeJobDetails && !isActive;

  return (
    <div className="page-container">
      <PageHeader
        title="Runs"
        description="Status, outputs and logs for your pipeline runs."
        actions={
          <>
            <button type="button" className="btn btn-secondary" onClick={pollActiveJob} disabled={isRefreshing || !selectedJobId}>
              <RefreshCw size={14} className={isRefreshing ? 'spin' : undefined} aria-hidden="true" />
              <span>Refresh</span>
            </button>
            <button type="button" className="btn btn-secondary" onClick={handleOpenLogs} disabled={!selectedJobId}>
              <Terminal size={14} aria-hidden="true" />
              <span>Log</span>
            </button>
            {/* The page's primary action only when a run failed; otherwise it stays secondary */}
            <button
              type="button"
              className={`btn ${macroStatus === 'FAILED' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setIsRerunOpen(true)}
              disabled={!canRerun}
              title={canRerun ? "Run Phase 2 again on this run's Phase 1 outputs" : 'Available once the run has ended'}
            >
              Run Phase 2 again
            </button>
          </>
        }
      >
        {rerunOf.parent_job && (
          <p className="muted" style={{ marginTop: 'var(--space-2)' }}>
            Phase 2 rerun ({rerunOf.weeks === 'all' ? 'all weeks' : 'failed weeks'}, {(rerunOf.queue || 'cpu').toUpperCase()}) of{' '}
            <button
              type="button"
              onClick={() => setSelectedJobId(rerunOf.parent_job)}
              style={{ border: 'none', padding: 0, color: 'var(--text)', textDecoration: 'underline', cursor: 'pointer', font: 'inherit', background: 'none' }}
            >
              {rerunOf.parent_name || rerunOf.parent_job}
            </button>
          </p>
        )}
      </PageHeader>

      {/* Job Selection Toolbar */}
      <JobSelectionToolbar
        jobs={jobs}
        selectedJobId={selectedJobId}
        isLoadingJobs={isLoadingJobs}
        onSelectJob={(id) => setSelectedJobId(id)}
        onTrackCustomJob={(id) => setSelectedJobId(id)}
        errorMsg={errorMsg}
      />

      <JobTelemetryHeader
        macroStatus={macroStatus}
        selectedJobId={selectedJobId}
        activeJobDetails={activeJobDetails}
        progressPercent={progressPercent}
        elapsedTime={calculateElapsedTime()}
        lastHeartbeat={progressData?.updated_at}
        isActive={isActive}
      />

      <PipelineProgressCard
        displayedStages={displayedStages}
        selectedStageId={selectedStage?.id}
        onSelectStage={(stg) => setSelectedStage(stg)}
        progressPercent={progressPercent}
        statusDescription={statusDescription}
        isActive={isActive}
      />

      <StageDiagnosticsCard selectedStage={selectedStage} />

      <JobArtifactsCard
        macroStatus={macroStatus}
        job={activeJobDetails}
        token={token}
        onDownloadArtifact={handleDownloadArtifact}
      />

      {isRerunOpen && activeJobDetails && token && (
        <RerunPhase2Dialog
          job={activeJobDetails}
          status={macroStatus}
          token={token}
          onClose={() => setIsRerunOpen(false)}
          onSubmitted={(uuid) => {
            setIsRerunOpen(false);
            setSelectedJobId(uuid);
            loadUserJobs();
          }}
        />
      )}

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
