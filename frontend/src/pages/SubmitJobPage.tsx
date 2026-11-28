import React, { useState, useEffect } from 'react';
import { Loader2, ArrowRight } from 'lucide-react';
import { getStoredToken } from '../utils/storage';
import { parseJwt } from '../utils/jwt';
import { cleanTapisUsername } from '../utils/format';
import { buildJobPayload, DEFAULT_JOB_FIELDS } from '../utils/jobPayload';
import {
  submitTapisJob,
  ensureRefreshToken,
  fetchUserConfigFiles,
  fetchUserPhase1Archives,
  fetchSystemRootDir,
  TAPIS_ARCHIVES_DIR,
  type TapisFileItem,
  type TapisJobSubmitPayload,
  type TapisJobSubmitResponse,
} from '../services/tapis';
import { PageHeader } from '../components/ui';
import {
  JobIdentitySection,
  JobClusterConfigSection,
  JobResourcesSection,
  JobPayloadPreview,
} from '../components/submit';

interface SubmitJobPageProps {
  onJobSubmitted?: (jobUuid: string) => void;
}

export const SubmitJobPage: React.FC<SubmitJobPageProps> = ({ onJobSubmitted }) => {
  const token = getStoredToken();
  const decoded = token ? parseJwt(token) : null;
  const username = decoded?.payload['tapis/username'] || (decoded?.payload.sub as string) || 'Authorized User';
  const cleanUsername = cleanTapisUsername(username);

  const [userConfigFiles, setUserConfigFiles] = useState<TapisFileItem[]>([]);
  const [userArchives, setUserArchives] = useState<TapisFileItem[]>([]);
  const [systemRootDir, setSystemRootDir] = useState<string>('');
  const [isLoadingConfigs, setIsLoadingConfigs] = useState<boolean>(false);
  const [isLoadingArchives, setIsLoadingArchives] = useState<boolean>(false);
  const [selectedArchivePath, setSelectedArchivePath] = useState<string>('');

  const [jobName, setJobName] = useState<string>(`curriculum-run-${Date.now().toString().slice(-4)}`);
  const [appId, setAppId] = useState<string>(DEFAULT_JOB_FIELDS.appId);
  const [appVersion, setAppVersion] = useState<string>(DEFAULT_JOB_FIELDS.appVersion);
  const [jobDescription, setJobDescription] = useState<string>(DEFAULT_JOB_FIELDS.jobDescription);

  const [configFilePath, setConfigFilePath] = useState<string>('');

  const [execSystemId, setExecSystemId] = useState<string>(DEFAULT_JOB_FIELDS.execSystemId);
  const [runMode, setRunMode] = useState<'full' | 'cpu_phase2'>(DEFAULT_JOB_FIELDS.runMode);
  const [logicalQueue, setLogicalQueue] = useState<string>(DEFAULT_JOB_FIELDS.logicalQueue);
  const [resourceAllocation, setResourceAllocation] = useState<string>(DEFAULT_JOB_FIELDS.resourceAllocation);
  const [gpuCount, setGpuCount] = useState<number>(DEFAULT_JOB_FIELDS.gpuCount);

  const [nodeCount, setNodeCount] = useState<number>(DEFAULT_JOB_FIELDS.nodeCount);
  const [coresPerNode, setCoresPerNode] = useState<number>(DEFAULT_JOB_FIELDS.coresPerNode);
  const [memoryMB, setMemoryMB] = useState<number>(DEFAULT_JOB_FIELDS.memoryMB);
  const [maxMinutes, setMaxMinutes] = useState<number>(DEFAULT_JOB_FIELDS.maxMinutes);

  const [bindGpu, setBindGpu] = useState<string>(DEFAULT_JOB_FIELDS.bindGpu);
  const [bindExpanse, setBindExpanse] = useState<string>(DEFAULT_JOB_FIELDS.bindExpanse);

  const [execDir, setExecDir] = useState<string>(DEFAULT_JOB_FIELDS.execDir);
  const [inputDir, setInputDir] = useState<string>(DEFAULT_JOB_FIELDS.inputDir);
  const [outputDir, setOutputDir] = useState<string>(DEFAULT_JOB_FIELDS.outputDir);

  const [scratchCacheDir, setScratchCacheDir] = useState<string>(DEFAULT_JOB_FIELDS.scratchCacheDir);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionResult, setSubmissionResult] = useState<TapisJobSubmitResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (token && cleanUsername && cleanUsername !== 'Authorized User') {
      setIsLoadingConfigs(true);
      setIsLoadingArchives(true);
      fetchSystemRootDir(token, execSystemId)
        .then((root) => {
          if (active) setSystemRootDir(root);
        })
        .catch(() => {});

      fetchUserConfigFiles(token, cleanUsername, execSystemId)
        .then((files) => {
          if (active) {
            setUserConfigFiles(files);
          }
        })
        .catch(() => {})
        .finally(() => {
          if (active) setIsLoadingConfigs(false);
        });

      fetchUserPhase1Archives(token, cleanUsername, execSystemId)
        .then((archives) => {
          if (active) {
            setUserArchives(archives);
          }
        })
        .catch(() => {})
        .finally(() => {
          if (active) setIsLoadingArchives(false);
        });
    }
    return () => {
      active = false;
    };
  }, [token, cleanUsername, execSystemId]);

  const handleAppIdChange = (newAppId: string) => {
    setAppId(newAppId);
    if (newAppId === 'digital-age-edu-test') {
      setAppVersion('1.0.0-dev');
    } else if (newAppId === 'smart-curriculum-designer') {
      setAppVersion('1.0.0');
    } else if (newAppId === 'digital-age-edu') {
      setAppVersion('1.0.20');
    }
  };

  const handleRunModeChange = (mode: 'full' | 'cpu_phase2') => {
    setRunMode(mode);
    if (mode === 'full') {
      setLogicalQueue('tapisGPUshared');
      setGpuCount(1);
      setMaxMinutes(480);
      setBindGpu('--nv');
    } else {
      setLogicalQueue('tapisShared');
      setGpuCount(0);
      setMaxMinutes(800);
      setBindGpu('');
    }
  };

  const generatePayload = (resolvedToken = 'AUTOMATED_REFRESH_TOKEN'): TapisJobSubmitPayload =>
    buildJobPayload(
      {
        jobName, appId, appVersion, jobDescription, configFilePath, execSystemId, runMode, logicalQueue,
        resourceAllocation, gpuCount, nodeCount, coresPerNode, memoryMB, maxMinutes, bindGpu, bindExpanse,
        execDir, inputDir, outputDir, scratchCacheDir, selectedArchivePath, cleanUsername,
      },
      resolvedToken
    );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErrorMessage('You must be logged in to submit an HPC job.');
      return;
    }
    if (runMode === 'cpu_phase2' && !selectedArchivePath.trim()) {
      setErrorMessage('Please select a Phase 1 archive to run Phase 2 on.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setSubmissionResult(null);

    try {
      const refreshToken = await ensureRefreshToken(token);
      const finalPayload = generatePayload(refreshToken);
      const result = await submitTapisJob(token, finalPayload);
      setSubmissionResult(result);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Job submission failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Submit HPC Run"
        description="Launch your curriculum pipeline on SDSC Expanse via Tapis."
      />

      <div className="submit-shell">
        <div className="card">
          <form onSubmit={handleSubmit} className="stack-lg">
            <JobClusterConfigSection
              configFilePath={configFilePath}
              onChangeConfigFilePath={setConfigFilePath}
              systemRootDir={systemRootDir}
              cleanUsername={cleanUsername}
              userConfigFiles={userConfigFiles}
              isLoadingConfigs={isLoadingConfigs}
            />

            <div className="divider-top">
              <JobIdentitySection
                jobName={jobName}
                onChangeJobName={setJobName}
                appId={appId}
                onChangeAppId={handleAppIdChange}
                appVersion={appVersion}
                jobDescription={jobDescription}
                onChangeJobDescription={setJobDescription}
              />
            </div>

            <div className="divider-top">
              <div className="form-group" style={{ marginBottom: 'var(--space-4)' }}>
                <span className="form-label">Run Mode</span>
                <div className="row">
                  <button
                    type="button"
                    onClick={() => handleRunModeChange('full')}
                    className={`pill ${runMode === 'full' ? 'is-selected' : ''}`}
                  >
                    Full Run (Phase 1 GPU → Auto Phase 2 CPU)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRunModeChange('cpu_phase2')}
                    className={`pill ${runMode === 'cpu_phase2' ? 'is-selected' : ''}`}
                  >
                    Phase 2 from Archive (CPU)
                  </button>
                </div>
                <div className="form-helper">
                  {runMode === 'full'
                    ? `Runs Phase 1 on GPU, auto-submits a Phase 2 CPU job, and archives Phase 1 to users/${cleanUsername}/${TAPIS_ARCHIVES_DIR}/.`
                    : 'Runs on the CPU queue (tapisShared, up to 800 min, no GPU billed) using an archived Phase 1 content bank.'}
                </div>
              </div>

              {runMode === 'cpu_phase2' && (
                <div className="inset-panel stack" style={{ marginBottom: 'var(--space-4)' }}>
                  <div className="row-between">
                    <label htmlFor="archive-select" className="form-label mb-0">
                      Archived Phase 1 Content Bank
                    </label>
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost"
                      disabled={isLoadingArchives || !token || !cleanUsername || cleanUsername === 'Authorized User'}
                      onClick={() => {
                        if (!token || !cleanUsername || cleanUsername === 'Authorized User') return;
                        setIsLoadingArchives(true);
                        fetchUserPhase1Archives(token, cleanUsername, execSystemId)
                          .then((archives) => setUserArchives(archives))
                          .catch(() => {})
                          .finally(() => setIsLoadingArchives(false));
                      }}
                    >
                      {isLoadingArchives ? 'Refreshing...' : 'Refresh'}
                    </button>
                  </div>
                  <select
                    id="archive-select"
                    value={userArchives.some((a) => a.clusterPath === selectedArchivePath) ? selectedArchivePath : ''}
                    onChange={(e) => setSelectedArchivePath(e.target.value)}
                  >
                    <option value="">
                      {isLoadingArchives
                        ? 'Loading archives...'
                        : userArchives.length > 0
                        ? 'Select an archived Phase 1 run...'
                        : 'No Phase 1 archives found yet'}
                    </option>
                    {userArchives.map((arch) => (
                      <option key={arch.path} value={arch.clusterPath || arch.path}>
                        {arch.name}
                        {arch.lastModified ? ` (${new Date(arch.lastModified).toLocaleDateString()})` : ''}
                      </option>
                    ))}
                  </select>
                  <input
                    id="archive-path-input"
                    type="text"
                    className="mono"
                    value={selectedArchivePath}
                    onChange={(e) => setSelectedArchivePath(e.target.value)}
                    placeholder={`${systemRootDir || '/expanse/lustre/scratch/.../'}users/${cleanUsername}/${TAPIS_ARCHIVES_DIR}/<job-name>`}
                  />
                  <div className="form-helper">
                    Archived automatically from completed Full Runs under <code>users/{cleanUsername}/{TAPIS_ARCHIVES_DIR}/</code>.
                  </div>
                </div>
              )}

              <JobResourcesSection
                gpuCount={gpuCount}
                onChangeGpuCount={setGpuCount}
                nodeCount={nodeCount}
                onChangeNodeCount={setNodeCount}
                coresPerNode={coresPerNode}
                onChangeCoresPerNode={setCoresPerNode}
                memoryMB={memoryMB}
                onChangeMemoryMB={setMemoryMB}
                maxMinutes={maxMinutes}
                onChangeMaxMinutes={setMaxMinutes}
                resourceAllocation={resourceAllocation}
                onChangeResourceAllocation={setResourceAllocation}
                execSystemId={execSystemId}
                onChangeExecSystemId={setExecSystemId}
                logicalQueue={logicalQueue}
                onChangeLogicalQueue={setLogicalQueue}
                bindGpu={bindGpu}
                onChangeBindGpu={setBindGpu}
                bindExpanse={bindExpanse}
                onChangeBindExpanse={setBindExpanse}
                scratchCacheDir={scratchCacheDir}
                onChangeScratchCacheDir={setScratchCacheDir}
                execDir={execDir}
                onChangeExecDir={setExecDir}
                inputDir={inputDir}
                onChangeInputDir={setInputDir}
                outputDir={outputDir}
                onChangeOutputDir={setOutputDir}
              />
            </div>

            {errorMessage && (
              <div role="alert" className="alert alert-error">
                {errorMessage}
              </div>
            )}

            {submissionResult && (
              <div className="alert alert-success alert-col">
                <div className="row-between">
                  <strong>Run submitted</strong>
                  <span className="badge badge-success">{submissionResult.status}</span>
                </div>
                <span className="mono">UUID: {submissionResult.uuid}</span>
                {onJobSubmitted && (
                  <div>
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => onJobSubmitted(submissionResult.uuid)}
                    >
                      <span>Track in Live Monitor</span>
                      <ArrowRight size={14} aria-hidden="true" />
                    </button>
                  </div>
                )}
              </div>
            )}

            <div className="row">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting && <Loader2 size={16} className="spin" aria-hidden="true" />}
                <span>{isSubmitting ? 'Submitting Run...' : 'Submit Run'}</span>
              </button>
            </div>
          </form>
        </div>

        <JobPayloadPreview payload={generatePayload()} />
      </div>
    </div>
  );
};
