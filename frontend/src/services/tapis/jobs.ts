import { getTapisApiUrl, getTapisHeaders } from './client';
import { parseJwt } from '../../utils/jwt';
import { getStoredRefreshToken, setStoredRefreshToken } from '../../utils/storage';
import type {
  TapisJob,
  PipelineProgressData,
  TapisJobSubmitPayload,
  TapisJobSubmitResponse,
  TapisFileItem,
} from './types';

/**
 * Fetch recent jobs submitted by the user.
 * Tries filtering for digital-age-edu / digitalagedu or returns all recent jobs.
 */
export async function fetchUserJobs(token: string, limit = 50): Promise<TapisJob[]> {
  try {
    const url = getTapisApiUrl(`/v3/jobs/list?limit=${limit}&orderBy=created(desc)`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });

    if (!resp.ok) {
      throw new Error(`Tapis API Error (${resp.status}): ${await resp.text()}`);
    }

    const data = await resp.json();
    const allJobs: TapisJob[] = data.result || [];

    // Filter to Smart Curriculum Designer app jobs
    const eduJobs = allJobs.filter(
      (j) =>
        j.appId?.toLowerCase().includes('smart-curriculum') ||
        j.appId?.toLowerCase().includes('curriculum-designer') ||
        j.appId?.toLowerCase().includes('curriculum') ||
        j.appId?.toLowerCase().includes('digital-age-edu') ||
        j.appId?.toLowerCase().includes('digital-age') ||
        j.appId?.toLowerCase().includes('digitalage') ||
        j.name?.toLowerCase().includes('smart-curriculum') ||
        j.name?.toLowerCase().includes('curriculum') ||
        j.name?.toLowerCase().includes('digital-age') ||
        j.name?.toLowerCase().includes('digitalage')
    );

    return eduJobs.length > 0 ? eduJobs : allJobs;
  } catch (err) {
    console.error('Failed to fetch user jobs:', err);
    throw err;
  }
}

/**
 * Get the macro status for a specific job.
 */
export async function fetchJobStatus(
  token: string,
  jobUuid: string
): Promise<{ status: string; condition?: string; lastMessage?: string }> {
  try {
    const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/status`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });

    if (!resp.ok) {
      throw new Error(`Failed to fetch status (${resp.status})`);
    }

    const data = await resp.json();
    return data.result || { status: 'UNKNOWN' };
  } catch (err) {
    console.error(`Failed to fetch status for job ${jobUuid}:`, err);
    throw err;
  }
}

/**
 * Fetch full details of a specific job.
 */
export async function fetchJobDetails(token: string, jobUuid: string): Promise<TapisJob> {
  const url = getTapisApiUrl(`/v3/jobs/${jobUuid}`);
  const resp = await fetch(url, {
    method: 'GET',
    headers: getTapisHeaders(token),
  });

  if (!resp.ok) {
    throw new Error(`Failed to fetch job details (${resp.status})`);
  }

  const data = await resp.json();
  return data.result;
}

/**
 * Dynamically list all output files for a job using the Tapis Files API.
 * Uses execSystemId and execSystemOutputDir from the job metadata.
 */
export async function listJobOutputFiles(
  token: string,
  jobDetails?: TapisJob | null
): Promise<{ systemId: string; filePaths: string[] } | null> {
  if (!jobDetails?.execSystemId || !jobDetails?.execSystemOutputDir) {
    return null;
  }

  const systemId = jobDetails.execSystemId;
  const outputDir = jobDetails.execSystemOutputDir.replace(/^\/+/, '');

  try {
    const url = getTapisApiUrl(`/v3/files/ops/${systemId}/${outputDir}?recurse=true`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: { 'X-Tapis-Token': token.trim() },
    });

    if (!resp.ok) return null;
    const data = await resp.json();
    const items = data.result || [];
    const filePaths: string[] = items.map((item: any) => item.path || item.name || '').filter(Boolean);
    return { systemId, filePaths };
  } catch (err) {
    console.warn('Could not list output files via Files API:', err);
    return null;
  }
}

/**
 * Fetch granular progress.json directly from the running or completed job.
 * Dynamically discovers the path on the execution system via Files API.
 */
export async function fetchJobProgress(
  token: string,
  jobUuid: string,
  jobDetails?: TapisJob | null
): Promise<PipelineProgressData | null> {
  // 1. Try dynamic file discovery on the execution system
  if (jobDetails) {
    const listing = await listJobOutputFiles(token, jobDetails);
    if (listing && listing.filePaths.length > 0) {
      const matchPath = listing.filePaths.find(
        (p) => p.endsWith('/progress.json') || p === 'progress.json'
      );
      if (matchPath) {
        try {
          const contentUrl = getTapisApiUrl(`/v3/files/content/${listing.systemId}/${matchPath.replace(/^\/+/, '')}`);
          const resp = await fetch(contentUrl, {
            method: 'GET',
            headers: { 'X-Tapis-Token': token.trim() },
          });
          if (resp.ok) {
            const data = await resp.json();
            if (data && (data.stages || data.status || data.progress_percent !== undefined)) {
              return data as PipelineProgressData;
            }
          }
        } catch {
          // Fall through to standard endpoint
        }
      }
    }
  }

  // 2. Fallback to Jobs API output download endpoint
  try {
    const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/progress.json`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: { 'X-Tapis-Token': token.trim() },
    });

    if (resp.ok) {
      const data = await resp.json();
      return data as PipelineProgressData;
    }
  } catch {
    // Return null if not ready
  }

  return null;
}

/**
 * Fetch raw stdout logs (tapisjob.out) for the job dynamically from execution system or Jobs API.
 */
export async function fetchJobLogs(
  token: string,
  jobUuid: string,
  jobDetails?: TapisJob | null
): Promise<string> {
  // 1. Try dynamic file discovery on the execution system
  if (jobDetails) {
    const listing = await listJobOutputFiles(token, jobDetails);
    if (listing && listing.filePaths.length > 0) {
      const matchPath = listing.filePaths.find(
        (p) => p.endsWith('/tapisjob.out') || p === 'tapisjob.out'
      );
      if (matchPath) {
        try {
          const contentUrl = getTapisApiUrl(`/v3/files/content/${listing.systemId}/${matchPath.replace(/^\/+/, '')}`);
          const resp = await fetch(contentUrl, {
            method: 'GET',
            headers: { 'X-Tapis-Token': token.trim() },
          });
          if (resp.ok) {
            const text = await resp.text();
            if (text && text.trim().length > 0) {
              return text;
            }
          }
        } catch {
          // Fall through to standard endpoint
        }
      }
    }
  }

  // 2. Fallback to Jobs API output download
  try {
    const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/tapisjob.out`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: { 'X-Tapis-Token': token.trim() },
    });

    if (resp.ok) {
      return await resp.text();
    }
  } catch {
    // Ignore
  }

  return 'No output logs available yet. The job is queued or staging on the compute node.';
}

/**
 * Saves a fetched file to the user's computer. The object URL stays alive for a minute: revoking it right after
 * click() can cut off a download the browser is still writing (a truncated .pptx PowerPoint "can't read").
 */
async function saveResponseAsFile(resp: Response, filename: string): Promise<void> {
  const blob = await resp.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => window.URL.revokeObjectURL(downloadUrl), 60_000);
}

/**
 * Trigger download of an output artifact from the job directory dynamically.
 */
export async function downloadJobArtifact(
  token: string,
  jobUuid: string,
  filename: string,
  jobDetails?: TapisJob | null
): Promise<void> {
  // 1. Try dynamic file discovery on the execution system
  if (jobDetails) {
    const listing = await listJobOutputFiles(token, jobDetails);
    if (listing && listing.filePaths.length > 0) {
      const matchPath = listing.filePaths.find(
        (p) => p.endsWith(`/${filename}`) || p === filename
      );
      if (matchPath) {
        try {
          const contentUrl = getTapisApiUrl(`/v3/files/content/${listing.systemId}/${matchPath.replace(/^\/+/, '')}`);
          const resp = await fetch(contentUrl, {
            method: 'GET',
            headers: { 'X-Tapis-Token': token.trim() },
          });
          if (resp.ok) {
            await saveResponseAsFile(resp, filename.split('/').pop() || filename);
            return;
          }
        } catch {
          // Fall through to the Jobs API
        }
      }
    }
  }

  // 2. Fallback to standard Jobs API download
  const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/${filename}`);
  const resp = await fetch(url, {
    method: 'GET',
    headers: { 'X-Tapis-Token': token.trim() },
  });

  if (!resp.ok) {
    throw new Error(`Artifact ${filename} not found in job output directory.`);
  }

  await saveResponseAsFile(resp, filename.split('/').pop() || filename);
}

/**
 * Check if the user already has a valid refresh token.
 */
export async function ensureRefreshToken(token: string): Promise<string> {
  const existing = getStoredRefreshToken();
  if (existing) {
    const parsed = parseJwt(existing);
    // The job reads this token only after queueing (hours on Expanse) and Phase 1, so "not expired now" is not
    // enough: run 2762 got a token with 1h40m left, queued 3.4h, and Phase 2 failed every week on HTTP 400
    if (parsed && parsed.expiresInSeconds > 2 * 86400) {
      return existing;
    }
  }

  // Generate 30-day refresh token via Tapis Tokens API in the background
  try {
    const decoded = parseJwt(token);
    const username = decoded?.payload['tapis/username'] || decoded?.payload.sub;
    const tenantId = (decoded?.payload['tapis/tenant_id'] as string) || 'icicleai';

    const requestUrl = getTapisApiUrl('/v3/tokens');
    const payload = {
      token_tenant_id: tenantId,
      token_username: username,
      account_type: 'user',
      access_token_ttl: 14400,
      refresh_token_ttl: 2592000,
      generate_refresh_token: true,
    };

    const resp = await fetch(requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tapis-Token': token.trim(),
      },
      body: JSON.stringify(payload),
    });

    if (resp.ok) {
      const resJson = await resp.json();
      const result = resJson?.result;
      const newRefresh = result?.refresh_token?.refresh_token || result?.refresh_token;
      if (newRefresh) {
        setStoredRefreshToken(newRefresh);
        return newRefresh;
      }
    }
  } catch (err) {
    console.warn('[Tapis] Auto-refresh token generation skipped:', err);
  }

  // Fallback to active access token
  return token.trim();
}

/**
 * Submit a batch HPC job to Tapis
 */
export async function submitTapisJob(
  token: string,
  payload: TapisJobSubmitPayload
): Promise<TapisJobSubmitResponse> {
  const url = getTapisApiUrl('/v3/jobs/submit');
  const resp = await fetch(url, {
    method: 'POST',
    headers: getTapisHeaders(token),
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    let message = `Job submission failed (${resp.status}): ${errorText}`;
    try {
      const errJson = JSON.parse(errorText);
      if (errJson.message) {
        message = Array.isArray(errJson.message) ? errJson.message.join(', ') : errJson.message;
      }
    } catch {
      // Use raw text
    }
    throw new Error(message);
  }

  const json = await resp.json();
  const result = json.result || json;
  return {
    uuid: result.uuid,
    name: result.name || payload.name,
    status: result.status || 'ACCEPTED',
    appId: result.appId || payload.appId,
    created: result.created,
  };
}

/**
 * List files and directories within a job's output folder (supports subfolder navigation).
 * Tries the Tapis Jobs output list endpoint first, with fallback to Files ops API.
 */
export async function listJobDirectoryContents(
  token: string,
  job: TapisJob,
  subpath = ''
): Promise<TapisFileItem[]> {
  const cleanSub = subpath.replace(/^\/+/, '').replace(/\/+$/, '');

  // 1. Try Tapis Jobs output list endpoint
  try {
    const query = cleanSub ? `?path=${encodeURIComponent(cleanSub)}` : '';
    const url = getTapisApiUrl(`/v3/jobs/${job.uuid}/output/list${query}`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });
    if (resp.ok) {
      const data = await resp.json();
      const items: any[] = data.result || [];
      if (items.length > 0) {
        return items.map((it) => {
          const isDir =
            it.type === 'dir' ||
            it.type === 'folder' ||
            it.format === 'folder' ||
            (!it.name?.includes('.') && (it.size === 4096 || it.size === 0));
          return {
            name: it.name || it.path?.split('/').pop() || 'unknown',
            path: cleanSub ? `${cleanSub}/${it.name}` : it.name,
            size: it.size,
            lastModified: it.lastModified,
            type: isDir ? 'dir' : 'file',
          };
        });
      }
    }
  } catch (err) {
    console.warn('[Tapis] Jobs output/list failed, attempting Files ops API:', err);
  }

  // 2. Fallback to Tapis Files ops API on exec/archive system
  try {
    const systemId = job.archiveSystemId || job.execSystemId || 'expanse-tapis-static';
    const baseDir = (job.archiveSystemDir || job.execSystemOutputDir || `jobs/${job.uuid}/outputs`).replace(/^\/+/, '');
    const targetDir = cleanSub ? `${baseDir}/${cleanSub}` : baseDir;
    const filesUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/${targetDir}`);
    const resp = await fetch(filesUrl, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });
    if (resp.ok) {
      const data = await resp.json();
      const items: any[] = data.result || [];
      return items.map((it) => ({
        name: it.name,
        path: cleanSub ? `${cleanSub}/${it.name}` : it.name,
        size: it.size,
        lastModified: it.lastModified,
        type: it.type === 'dir' ? 'dir' : 'file',
      }));
    }
  } catch (err) {
    console.warn('[Tapis] Files ops API failed for output directory:', err);
  }

  return [];
}

/**
 * Fetch the raw text content of an output file for inline previewing.
 */
export async function fetchJobOutputFileText(
  token: string,
  jobUuid: string,
  relativePath: string
): Promise<string> {
  const cleanPath = relativePath.replace(/^\/+/, '');
  const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/${cleanPath}`);
  const resp = await fetch(url, {
    method: 'GET',
    headers: { 'X-Tapis-Token': token.trim() },
  });

  if (!resp.ok) {
    throw new Error(`Failed to load file preview (${resp.status})`);
  }

  return await resp.text();
}


// ---------------------------------------------------------------------------------------------------------------
// Phase 2 rerun: run Phase 2 again on a finished job's Phase 1 outputs (entrypoint.sh reads RERUN_FROM_DIR)
// ---------------------------------------------------------------------------------------------------------------

const PHASE1_MARKERS = ['results.csv', 'provenance.json', 'run_summary.json'];
const TERMINAL_STATUSES = ['FINISHED', 'FAILED', 'CANCELLED'];

export interface Phase2RerunStatus {
  eligible: boolean;
  reason?: string;
  runDir?: string; // outputs/<run name>, relative to the job's output dir
  finishedWeeks: string[]; // Week_XX/<module> folders that verified and have a deck
}

/** The jobs API returns parameterSet and notes as JSON strings; parsed here, {} if absent or unreadable. */
export function parseJobJson(value: unknown): Record<string, any> {
  if (!value) return {};
  if (typeof value === 'object') return value as Record<string, any>;
  try {
    return JSON.parse(String(value));
  } catch {
    return {};
  }
}

/** Whether a job can be rerun from its Phase 1 outputs, and which of its weeks a "failed weeks" rerun would keep. */
export async function fetchPhase2RerunStatus(token: string, job: TapisJob, status: string): Promise<Phase2RerunStatus> {
  if (!TERMINAL_STATUSES.includes(status)) {
    return { eligible: false, reason: 'The job is still running.', finishedWeeks: [] };
  }
  // Web app jobs write to /jobs/<uuid>, so outputs/ is a subfolder; app-default jobs write straight into .../outputs
  const outputsPrefix = (job.execSystemOutputDir || '').replace(/\/+$/, '').endsWith('/outputs') ? '' : 'outputs';
  const runDirs = (await listJobDirectoryContents(token, job, outputsPrefix)).filter((it) => it.type === 'dir');
  for (const dir of runDirs) {
    const names = new Set((await listJobDirectoryContents(token, job, dir.path)).map((it) => it.name));
    if (!PHASE1_MARKERS.every((m) => names.has(m))) continue;

    const finishedWeeks: string[] = [];
    if (names.has('exercises')) {
      const weeks = (await listJobDirectoryContents(token, job, `${dir.path}/exercises`)).filter(
        (it) => it.type === 'dir' && it.name.startsWith('Week_')
      );
      for (const week of weeks) {
        for (const mod of (await listJobDirectoryContents(token, job, week.path)).filter((it) => it.type === 'dir')) {
          const files = new Set((await listJobDirectoryContents(token, job, mod.path)).map((it) => it.name));
          if (!files.has(`${mod.name}_verification.json`) || !files.has(`${mod.name}_presentation.pptx`)) continue;
          try {
            const text = await fetchJobOutputFileText(token, job.uuid, `${mod.path}/${mod.name}_verification.json`);
            if (JSON.parse(text).verified) finishedWeeks.push(`${week.name}/${mod.name}`);
          } catch {
            // unreadable verification: treat the week as unfinished
          }
        }
      }
    }
    return { eligible: true, runDir: dir.path, finishedWeeks };
  }
  return {
    eligible: false,
    reason: "Phase 1 didn't finish in this job (no results.csv, provenance.json and run_summary.json), or its files were purged from scratch.",
    finishedWeeks: [],
  };
}

/**
 * Submit a Phase 2 rerun of `parent`: same app, config file and allocation, with the config locked to the original
 * (the pipeline checks its hash). On the CPU queue the GPU request and --nv are left out (needs gpu-request to be
 * INCLUDE_BY_DEFAULT in the app definition).
 */
export async function submitPhase2Rerun(
  token: string,
  parent: TapisJob,
  weeks: 'failed' | 'all',
  queue: 'cpu' | 'gpu'
): Promise<TapisJobSubmitResponse> {
  const systemId = parent.execSystemId || 'expanse-tapis-static';
  const sysResp = await fetch(getTapisApiUrl(`/v3/systems/${systemId}?select=rootDir`), { headers: getTapisHeaders(token) });
  if (!sysResp.ok) throw new Error(`Could not read ${systemId}'s root directory (${sysResp.status})`);
  const rootDir: string = (await sysResp.json()).result?.rootDir || '';
  const params = parseJobJson(parent.parameterSet);
  const pick = (list: any[] | undefined, names: string[]) =>
    (list || []).filter((o) => names.includes(o.name)).map((o) => ({ name: o.name, arg: o.arg }));
  const cpu = queue === 'cpu';

  return submitTapisJob(token, {
    name: `${parent.name}-p2`,
    appId: parent.appId,
    appVersion: parent.appVersion || '1.0.0',
    description: `Phase 2 rerun of ${parent.name} (${weeks} weeks)`,
    execSystemId: systemId,
    execSystemLogicalQueue: cpu ? 'tapisShared' : 'tapisGPUshared',
    nodeCount: parent.nodeCount || 1,
    coresPerNode: parent.coresPerNode || 12,
    memoryMB: parent.memoryMB || 64000,
    maxMinutes: cpu ? 800 : parent.maxMinutes || 480,
    // A new job directory: the parent's outputs are copied from RERUN_FROM_DIR, never written to
    execSystemExecDir: '/jobs/${JobUUID}',
    execSystemInputDir: '/jobs/${JobUUID}',
    execSystemOutputDir: '/jobs/${JobUUID}',
    parameterSet: {
      appArgs: pick(params.appArgs, ['config_file']).map((a) => ({ name: a.name, arg: String(a.arg) })),
      schedulerOptions: [
        ...pick(params.schedulerOptions, ['resource-allocation', 'singularity-cache-export']),
        // Tapis requires `arg` even on an excluded option
        ...(cpu ? [{ name: 'gpu-request', arg: '--gpus=1', include: false }] : pick(params.schedulerOptions, ['gpu-request'])),
      ],
      containerArgs: [
        ...pick(params.containerArgs, ['bind-expanse']),
        ...(cpu ? [{ name: 'bind-gpu', arg: '--nv', include: false }] : pick(params.containerArgs, ['bind-gpu'])),
      ],
      envVariables: [
        { key: 'RERUN_FROM_DIR', value: `${rootDir.replace(/\/+$/, '')}/${(parent.execSystemExecDir || '').replace(/^\/+/, '')}` },
        { key: 'RERUN_WEEKS', value: weeks },
        { key: 'TAPIS_REFRESH_TOKEN', value: await ensureRefreshToken(token) },
      ],
    },
    notes: { parent_job: parent.uuid, parent_name: parent.name, rerun: 'phase2', weeks, queue },
  });
}
