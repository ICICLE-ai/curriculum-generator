// Parity check for buildJobPayload: node --experimental-strip-types src/utils/jobPayload.check.ts
import assert from 'node:assert/strict';
import { buildJobPayload, DEFAULT_JOB_FIELDS, type JobFields } from './jobPayload.ts';
import { sanitizeTapisName } from './format.ts';

const ARCHIVES_DIR = 'smart_curriculum_designer_archives';

// Verbatim copy of SubmitJobPage's old generatePayload body, state inlined as params
function legacyPayload(f: JobFields, resolvedToken: string) {
  const {
    jobName, appId, appVersion, jobDescription, configFilePath, execSystemId, runMode, logicalQueue,
    resourceAllocation, gpuCount, nodeCount, coresPerNode, memoryMB, maxMinutes, bindGpu, bindExpanse,
    execDir, inputDir, outputDir, scratchCacheDir, selectedArchivePath, cleanUsername,
  } = f;
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

  const envVariables = [{ key: 'TAPIS_REFRESH_TOKEN', value: resolvedToken }];

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

const base: JobFields = { ...DEFAULT_JOB_FIELDS, jobName: 'my run', configFilePath: 'configs/a.yaml', selectedArchivePath: '', cleanUsername: 'jdoe' };
const cpu: JobFields = {
  ...base, runMode: 'cpu_phase2', logicalQueue: 'tapisShared', gpuCount: 0, maxMinutes: 800, bindGpu: '',
  selectedArchivePath: '/expanse/users/jdoe/' + ARCHIVES_DIR + '/run1/',
};
const sets: JobFields[] = [
  base,
  cpu,
  { ...base, jobName: '  ', cleanUsername: 'Authorized User', scratchCacheDir: '', bindExpanse: '', resourceAllocation: '', configFilePath: '' },
];
for (const f of sets) {
  const want = legacyPayload(f, 'tok');
  const got = buildJobPayload(f, 'tok');
  if (!f.jobName.trim()) assert.match(got.name, /^curriculum-run-\d{4}$/); // random fallback name: compare the rest
  assert.deepEqual(f.jobName.trim() ? got : { ...got, name: want.name }, want);
}

const full = buildJobPayload(base, 'tok');
assert.equal(full.archiveMode, 'SKIP_ON_FAIL');
assert.equal(full.archiveSystemDir, `/users/jdoe/${ARCHIVES_DIR}/my_run`);
const env = Object.fromEntries((full.parameterSet.envVariables ?? []).map((e) => [e.key, e.value]));
assert.equal(env.TAPIS_REFRESH_TOKEN, 'tok');
assert.equal(env.HF_HOME, '/expanse/lustre/scratch/harvest/temp_project/.cache/huggingface');
assert.equal(env.CONTENT_BANK_DIR, undefined);
assert.equal(full.notes, undefined);
assert.equal(full.execSystemLogicalQueue, 'tapisGPUshared');

const p2 = buildJobPayload(cpu, 'tok');
assert.equal(p2.archiveMode, undefined);
assert.equal(p2.parameterSet.envVariables?.find((e) => e.key === 'CONTENT_BANK_DIR')?.value, cpu.selectedArchivePath);
assert.deepEqual(p2.notes, { content_bank_archive: 'run1', content_bank_path: cpu.selectedArchivePath, queue: 'cpu' });
console.log('jobPayload.check OK');
