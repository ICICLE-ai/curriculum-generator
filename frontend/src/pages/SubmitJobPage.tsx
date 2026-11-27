import React, { useState, useEffect } from 'react';
import { Loader2, ArrowRight } from 'lucide-react';
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
  const cleanUsername = username.includes('@') ? username.split('@')[0] : username;

  const [userConfigFiles, setUserConfigFiles] = useState<TapisFileItem[]>([]);
  const [systemRootDir, setSystemRootDir] = useState<string>('');
  const [isLoadingConfigs, setIsLoadingConfigs] = useState<boolean>(false);

  const [jobName, setJobName] = useState<string>(`curriculum-run-${Date.now().toString().slice(-4)}`);
  const [appId, setAppId] = useState<string>('smart-curriculum-designer');
  const [appVersion, setAppVersion] = useState<string>('1.0.0');
  const [jobDescription, setJobDescription] = useState<string>('Run the AI pipeline using a provided YAML configuration.');

  const [configFilePath, setConfigFilePath] = useState<string>('');

  const [execSystemId, setExecSystemId] = useState<string>('expanse-tapis-static');
  const [logicalQueue, setLogicalQueue] = useState<string>('tapisGPUshared');
  const [resourceAllocation, setResourceAllocation] = useState<string>('-A uot260');
  const [gpuCount, setGpuCount] = useState<number>(1);

  const [nodeCount, setNodeCount] = useState<number>(1);
  const [coresPerNode, setCoresPerNode] = useState<number>(12);
  const [memoryMB, setMemoryMB] = useState<number>(64000);
  const [maxMinutes, setMaxMinutes] = useState<number>(480);

  const [bindGpu, setBindGpu] = useState<string>('--nv');
  const [bindExpanse, setBindExpanse] = useState<string>('--bind /expanse:/expanse');

  const [execDir, setExecDir] = useState<string>('/jobs/${JobUUID}');
  const [inputDir, setInputDir] = useState<string>('/jobs/${JobUUID}');
  const [outputDir, setOutputDir] = useState<string>('/jobs/${JobUUID}');

  const [scratchCacheDir, setScratchCacheDir] = useState<string>(
    '/expanse/lustre/scratch/harvest/temp_project/.cache'
  );

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionResult, setSubmissionResult] = useState<TapisJobSubmitResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

    const cleanCache = scratchCacheDir.trim().replace(/\/+$/, '');
    if (cleanCache) {
      schedulerOptions.push({
        name: 'singularity-cache-export',
        arg: `--export=ALL,SINGULARITY_CACHEDIR=${cleanCache}/singularity/cache,APPTAINER_CACHEDIR=${cleanCache}/singularity/cache`,
      });
    }

    const containerArgs = [];
    if (bindGpu.trim()) {
      containerArgs.push({ name: 'bind-gpu', arg: bindGpu.trim() });
    }
    if (bindExpanse.trim()) {
      containerArgs.push({ name: 'bind-expanse', arg: bindExpanse.trim() });
    }

    const envVariables = [{ key: 'TAPIS_REFRESH_TOKEN', value: resolvedToken }];

    if (cleanCache) {
      envVariables.push(
        { key: 'TRITON_CACHE_DIR', value: `${cleanCache}/triton` },
        { key: 'TORCH_EXTENSIONS_DIR', value: `${cleanCache}/torch_extensions` },
        { key: 'HF_HOME', value: `${cleanCache}/huggingface` },
        { key: 'XDG_CACHE_HOME', value: cleanCache },
        { key: 'MPLCONFIGDIR', value: `${cleanCache}/matplotlib` },
        { key: 'WANDB_DIR', value: `${cleanCache}/wandb` },
        { key: 'WANDB_CACHE_DIR', value: `${cleanCache}/wandb` }
      );
    }

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
              execSystemId={execSystemId}
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
