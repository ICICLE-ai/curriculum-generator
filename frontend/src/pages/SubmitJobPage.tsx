import React, { useState, useEffect } from 'react';
import { getStoredToken } from '../utils/storage';
import { parseJwt } from '../utils/jwt';
import {
  submitTapisJob,
  ensureRefreshToken,
  fetchUserConfigFiles,
  fetchSystemRootDir,
  type TapisFileItem,
  type TapisJobSubmitPayload,
  type TapisJobSubmitResponse,
} from '../services/tapis';
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
  const cleanUsername = username.includes('@') ? username.split('@')[0] : username;

  // Discovered config files in Tapis Files storage
  const [userConfigFiles, setUserConfigFiles] = useState<TapisFileItem[]>([]);
  const [systemRootDir, setSystemRootDir] = useState<string>('');
  const [isLoadingConfigs, setIsLoadingConfigs] = useState<boolean>(false);

  // Job Identification & Defaults
  const [jobName, setJobName] = useState<string>(`curriculum-run-${Date.now().toString().slice(-4)}`);
  const [appId, setAppId] = useState<string>('smart-curriculum-designer');
  const [appVersion, setAppVersion] = useState<string>('1.0.0');
  const [jobDescription, setJobDescription] = useState<string>('Run the AI pipeline using a provided YAML configuration.');

  // Config file path
  const [configFilePath, setConfigFilePath] = useState<string>('');

  // Slurm Scheduler & System Defaults from app.json
  const [execSystemId, setExecSystemId] = useState<string>('expanse-tapis-static');
  const [logicalQueue, setLogicalQueue] = useState<string>('tapisGPUshared');
  const [resourceAllocation, setResourceAllocation] = useState<string>('-A uot260');
  const [gpuCount, setGpuCount] = useState<number>(1);

  // Compute Hardware Specs
  const [nodeCount, setNodeCount] = useState<number>(1);
  const [coresPerNode, setCoresPerNode] = useState<number>(12);
  const [memoryMB, setMemoryMB] = useState<number>(64000);
  const [maxMinutes, setMaxMinutes] = useState<number>(300);

  // Container Bind Options
  const [bindGpu, setBindGpu] = useState<string>('--nv');
  const [bindExpanse, setBindExpanse] = useState<string>('--bind /expanse:/expanse');

  // Directory Specs
  const [execDir, setExecDir] = useState<string>('/jobs/${JobUUID}');
  const [inputDir, setInputDir] = useState<string>('/jobs/${JobUUID}');
  const [outputDir, setOutputDir] = useState<string>('/jobs/${JobUUID}/outputs');

  // UI States
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionResult, setSubmissionResult] = useState<TapisJobSubmitResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Dynamically query system root directory & auto-fetch user's YAML config files
  useEffect(() => {
    let active = true;
    if (token && cleanUsername && cleanUsername !== 'Authorized User') {
      setIsLoadingConfigs(true);
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
    }
    return () => {
      active = false;
    };
  }, [token, cleanUsername, execSystemId]);

  // Auto-sync version with App ID selection
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

  // Generate payload for submission and live preview
  const generatePayload = (resolvedToken = 'AUTOMATED_REFRESH_TOKEN'): TapisJobSubmitPayload => {
    const appArgs = [];
    if (configFilePath.trim()) {
      appArgs.push({ name: 'config_file', arg: configFilePath.trim() });
    }

    const schedulerOptions = [];
    if (resourceAllocation.trim()) {
      schedulerOptions.push({ name: 'resource-allocation', arg: resourceAllocation.trim() });
    }
    if (gpuCount > 0) {
      schedulerOptions.push({ name: 'gpu-request', arg: `--gpus=${gpuCount}` });
    }

    const containerArgs = [];
    if (bindGpu.trim()) {
      containerArgs.push({ name: 'bind-gpu', arg: bindGpu.trim() });
    }
    if (bindExpanse.trim()) {
      containerArgs.push({ name: 'bind-expanse', arg: bindExpanse.trim() });
    }

    const envVariables = [
      { key: 'TAPIS_REFRESH_TOKEN', value: resolvedToken },
    ];

    return {
      name: jobName.trim() || `curriculum-run-${Date.now().toString().slice(-4)}`,
      appId: appId.trim(),
      appVersion: appVersion.trim(),
      description: jobDescription.trim(),
      execSystemId: execSystemId.trim(),
      execSystemLogicalQueue: logicalQueue.trim(),
      nodeCount,
      coresPerNode,
      memoryMB,
      maxMinutes,
      execSystemExecDir: execDir.trim(),
      execSystemInputDir: inputDir.trim(),
      execSystemOutputDir: outputDir.trim(),
      parameterSet: {
        appArgs,
        schedulerOptions,
        containerArgs,
        envVariables,
      },
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErrorMessage('You must be logged in to submit an HPC job.');
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
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Submit HPC Cluster Job</h1>
        <p className="page-description">
          Launch automated model training and curriculum synthesis on the cluster via the Tapis v3 Jobs API.
        </p>
      </div>

      <div className="builder-grid-layout">
        {/* Left Column: Job Submission Form */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <form onSubmit={handleSubmit}>
            {/* Automated Security & Token Shield */}
            
             
              

            {/* Section 1: Job Identity & Target App */}
            <JobIdentitySection
              jobName={jobName}
              onChangeJobName={setJobName}
              appId={appId}
              onChangeAppId={handleAppIdChange}
              appVersion={appVersion}
              jobDescription={jobDescription}
              onChangeJobDescription={setJobDescription}
            />

            {/* Section 2: Configuration File Path */}
            <JobClusterConfigSection
              configFilePath={configFilePath}
              onChangeConfigFilePath={setConfigFilePath}
              systemRootDir={systemRootDir}
              cleanUsername={cleanUsername}
              execSystemId={execSystemId}
              userConfigFiles={userConfigFiles}
              isLoadingConfigs={isLoadingConfigs}
            />

            {/* Section 3: Compute Resources & Advanced Settings */}
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
              execDir={execDir}
              onChangeExecDir={setExecDir}
              inputDir={inputDir}
              onChangeInputDir={setInputDir}
              outputDir={outputDir}
              onChangeOutputDir={setOutputDir}
            />

            {/* Error Banner */}
            {errorMessage && (
              <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <div style={{ flex: 1 }}>{errorMessage}</div>
              </div>
            )}

            {/* Success Banner */}
            {submissionResult && (
              <div className="alert alert-success" style={{ marginBottom: '1.25rem', flexDirection: 'column', alignItems: 'stretch' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.45rem' }}>
                  <div style={{ fontWeight: 600 }}>Job Submitted Successfully!</div>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      padding: '0.15rem 0.45rem',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(52, 211, 153, 0.2)',
                    }}
                  >
                    Status: {submissionResult.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', wordBreak: 'break-all', marginBottom: '0.75rem' }}>
                  UUID: {submissionResult.uuid}
                </div>
                {onJobSubmitted && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => onJobSubmitted(submissionResult.uuid)}
                    style={{ alignSelf: 'flex-start', padding: '0.45rem 0.95rem', fontSize: '0.8rem' }}
                  >
                    Track in Live Monitor →
                  </button>
                )}
              </div>
            )}

            {/* Action Bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
                style={{ padding: '0.75rem 1.75rem', fontSize: '0.9rem' }}
              >
                {isSubmitting ? (
                  <>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      style={{ animation: 'spin 1s linear infinite' }}
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    Submitting Job...
                  </>
                ) : (
                  'Submit Batch Job 🚀'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Live Tapis JSON Preview */}
        <JobPayloadPreview payload={generatePayload()} />
      </div>
    </div>
  );
};
