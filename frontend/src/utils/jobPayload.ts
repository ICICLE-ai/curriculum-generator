import { sanitizeTapisName } from './format.ts';
import type { TapisJobSubmitPayload } from '../services/tapis/types';

// Same value as TAPIS_ARCHIVES_DIR in services/tapis/files.ts (importing it would pull the whole service layer into the node check)
const ARCHIVES_DIR = 'smart_curriculum_designer_archives';

export interface JobFields {
  jobName: string;
  appId: string;
  appVersion: string;
  jobDescription: string;
  configFilePath: string;
  execSystemId: string;
  runMode: 'full' | 'cpu_phase2';
  logicalQueue: string;
  resourceAllocation: string;
  gpuCount: number;
  nodeCount: number;
  coresPerNode: number;
  memoryMB: number;
  maxMinutes: number;
  bindGpu: string;
  bindExpanse: string;
  execDir: string;
  inputDir: string;
  outputDir: string;
  scratchCacheDir: string;
  selectedArchivePath: string;
  cleanUsername: string;
}

/** Initial values for the cluster settings; callers supply the per-user fields. */
export const DEFAULT_JOB_FIELDS: Omit<JobFields, 'jobName' | 'configFilePath' | 'selectedArchivePath' | 'cleanUsername'> = {
  appId: 'smart-curriculum-designer',
  appVersion: '1.0.0',
  jobDescription: 'Run the AI pipeline using a provided YAML configuration.',
  execSystemId: 'expanse-tapis-static',
  runMode: 'full',
  logicalQueue: 'tapisGPUshared',
  resourceAllocation: '-A uot260',
  gpuCount: 1,
  nodeCount: 1,
  coresPerNode: 12,
  memoryMB: 64000,
  maxMinutes: 480,
  bindGpu: '--nv',
  bindExpanse: '--bind /expanse:/expanse',
  execDir: '/jobs/${JobUUID}',
  inputDir: '/jobs/${JobUUID}',
  outputDir: '/jobs/${JobUUID}',
  scratchCacheDir: '/expanse/lustre/scratch/harvest/temp_project/.cache',
};

export function buildJobPayload(fields: JobFields, refreshToken: string): TapisJobSubmitPayload {
  const {
    jobName, appId, appVersion, jobDescription, configFilePath, execSystemId, runMode, logicalQueue,
    resourceAllocation, gpuCount, nodeCount, coresPerNode, memoryMB, maxMinutes, bindGpu, bindExpanse,
    execDir, inputDir, outputDir, scratchCacheDir, selectedArchivePath, cleanUsername,
  } = fields;
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
  } else {
    schedulerOptions.push({ name: 'gpu-request', arg: '--gpus=1', include: false });
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
  } else {
    containerArgs.push({ name: 'bind-gpu', arg: '--nv', include: false });
  }
  if (bindExpanse.trim()) {
    containerArgs.push({ name: 'bind-expanse', arg: bindExpanse.trim() });
  }

  const envVariables = [{ key: 'TAPIS_REFRESH_TOKEN', value: refreshToken }];

  if (runMode === 'cpu_phase2' && selectedArchivePath.trim()) {
    envVariables.push({ key: 'CONTENT_BANK_DIR', value: selectedArchivePath.trim() });
  }

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

  const resolvedJobName = jobName.trim() || `curriculum-run-${Date.now().toString().slice(-4)}`;
  const safeArchiveName = sanitizeTapisName(resolvedJobName);
  const hasValidUser = Boolean(cleanUsername && cleanUsername !== 'Authorized User');
  const selectedArchiveName =
    selectedArchivePath.trim().replace(/\/+$/, '').split('/').pop() || selectedArchivePath.trim();

  return {
    name: resolvedJobName,
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
    ...(runMode === 'full' && hasValidUser
      ? {
          archiveMode: 'SKIP_ON_FAIL' as const,
          archiveSystemId: execSystemId.trim(),
          archiveSystemDir: `/users/${cleanUsername}/${ARCHIVES_DIR}/${safeArchiveName}`,
        }
      : {}),
    parameterSet: {
      appArgs,
      schedulerOptions,
      containerArgs,
      envVariables,
    },
    ...(runMode === 'cpu_phase2' && selectedArchivePath.trim()
      ? {
          notes: {
            content_bank_archive: selectedArchiveName,
            content_bank_path: selectedArchivePath.trim(),
            queue: 'cpu',
          },
        }
      : {}),
  };
}
