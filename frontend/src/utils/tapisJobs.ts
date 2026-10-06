import { parseJwt } from './jwt';
import { getStoredRefreshToken, setStoredRefreshToken } from './storage';

export interface TapisJob {
  uuid: string;
  name: string;
  appId: string;
  appVersion?: string;
  status: string;
  created?: string;
  ended?: string;
  lastMessage?: string;
  execSystemId?: string;
  execSystemExecDir?: string;
  execSystemOutputDir?: string;
  archiveSystemId?: string;
  archiveSystemDir?: string;
  parameterSet?: any;
  nodeCount?: number;
  coresPerNode?: number;
  memoryMB?: number;
  maxMinutes?: number;
}

export interface PipelineStage {
  id: string;
  name: string;
  phase?: string;
  status: 'READY' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  details?: string;
  progress?: string;
  start_time?: number;
  end_time?: number;
  duration_sec?: number;
  metrics?: Record<string, unknown>;
  error?: string;
}

export interface PipelineProgressData {
  status: string;
  current_stage?: string;
  current_message?: string;
  progress_percent: number;
  elapsed_seconds?: number;
  updated_at?: string;
  stages: PipelineStage[];
  final_metrics?: Record<string, unknown>;
}

export function getTapisApiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // In local development, use the Vite dev proxy
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return cleanPath;
    }
  }
  // When deployed on Tapis Pods or any remote host, target Tapis API directly
  return `https://icicleai.tapis.io${cleanPath}`;
}

function getHeaders(token: string) {
  return {
    'X-Tapis-Token': token.trim(),
    'Content-Type': 'application/json',
  };
}

/**
 * Fetch recent jobs submitted by the user.
 * Tries filtering for digital-age-edu / digitalagedu or returns all recent jobs.
 */
export async function fetchUserJobs(token: string, limit = 50): Promise<TapisJob[]> {
  try {
    const url = getTapisApiUrl(`/v3/jobs/list?limit=${limit}&orderBy=created(desc)`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getHeaders(token),
    });

    if (!resp.ok) {
      throw new Error(`Tapis API Error (${resp.status}): ${await resp.text()}`);
    }

    const data = await resp.json();
    const allJobs: TapisJob[] = data.result || [];

    // Filter to Smart Curriculum Designer app jobs (supporting smart-curriculum-designer, digital-age-edu, etc.)
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
      headers: getHeaders(token),
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
    headers: getHeaders(token),
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
            const blob = await resp.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            return;
          }
        } catch {
          // Fall through
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

  const blob = await resp.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(downloadUrl);
  document.body.removeChild(a);
}

export interface TapisJobSubmitPayload {
  name: string;
  appId: string;
  appVersion: string;
  description?: string;
  execSystemId?: string;
  execSystemLogicalQueue?: string;
  execSystemExecDir?: string;
  execSystemInputDir?: string;
  execSystemOutputDir?: string;
  nodeCount?: number;
  coresPerNode?: number;
  memoryMB?: number;
  maxMinutes?: number;
  parameterSet?: {
    appArgs?: Array<{ name?: string; arg: string }>;
    schedulerOptions?: Array<{ name?: string; arg: string }>;
    containerArgs?: Array<{ name?: string; arg: string }>;
    envVariables?: Array<{ key: string; value: string }>;
  };
}

export interface TapisJobSubmitResponse {
  uuid: string;
  name: string;
  status: string;
  appId: string;
  created?: string;
}

/**
 * Automatically ensures a valid Tapis Refresh Token is available.
 * 1. Checks localStorage for existing refresh token.
 * 2. If missing, calls /v3/tokens using the active access token in the background,
 *    caches the new 30-day refresh token, and returns it.
 * 3. Falls back to returning the access token if generation is unavailable.
 */
export async function ensureRefreshToken(token: string): Promise<string> {
  const existing = getStoredRefreshToken();
  if (existing) {
    const parsed = parseJwt(existing);
    if (parsed && !parsed.isExpired) {
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
    headers: getHeaders(token),
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

export interface TapisFileItem {
  name: string;
  path: string;
  clusterPath?: string;
  size?: number;
  lastModified?: string;
  type?: string;
}

const cachedSystemRootDir: Record<string, string> = {};

/**
 * Dynamically fetch the system's root directory directly from Tapis Systems API
 * (e.g. GET /v3/systems/{systemId})
 */
export async function fetchSystemRootDir(token: string, systemId = 'expanse-tapis-static'): Promise<string> {
  if (cachedSystemRootDir[systemId]) {
    return cachedSystemRootDir[systemId];
  }
  try {
    const url = getTapisApiUrl(`/v3/systems/${systemId}`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getHeaders(token),
    });
    if (resp.ok) {
      const data = await resp.json();
      let rootDir: string = data.result?.rootDir || '';
      if (rootDir && !rootDir.endsWith('/')) {
        rootDir += '/';
      }
      if (rootDir) {
        cachedSystemRootDir[systemId] = rootDir;
        return rootDir;
      }
    }
  } catch (err) {
    console.warn(`[Tapis] Failed to query system info for ${systemId}:`, err);
  }
  return '';
}

/**
 * Fetch list of files in the user's expanse-tapis-static directory
 */
export async function fetchUserConfigFiles(
  token: string,
  username: string,
  systemId = 'expanse-tapis-static'
): Promise<TapisFileItem[]> {
  try {
    const rootDir = await fetchSystemRootDir(token, systemId);
    const cleanUser = username.includes('@') ? username.split('@')[0] : username;
    const url = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getHeaders(token),
    });
    if (!resp.ok) {
      return [];
    }
    const data = await resp.json();
    const files: any[] = data.result || [];
    return files
      .filter((f) => f.name.endsWith('.yaml') || f.name.endsWith('.yml'))
      .map((f) => {
        const cleanPath = (f.path || '').replace(/^\/+/, '');
        return {
          name: f.name,
          path: f.path,
          clusterPath: rootDir ? `${rootDir}${cleanPath}` : `/${cleanPath}`,
          size: f.size,
          lastModified: f.lastModified,
          type: f.type,
        };
      });
  } catch (err) {
    console.warn('[Tapis] Could not fetch user config files:', err);
    return [];
  }
}

export const EXPANSE_SHARED_DATASETS_DIR = 'shared/smart_curriculum_designer_datasets';

export interface TapisDatasetItem {
  name: string;
  path: string;
  clusterPath: string;
  type?: string;
  source: 'shared' | 'user';
}

/**
 * Fetch available datasets by dynamically querying the shared smart curriculum designer datasets
 * folder and the user's directory on expanse-tapis-static.
 */
export async function fetchAvailableDatasets(
  token: string,
  username?: string,
  systemId = 'expanse-tapis-static'
): Promise<TapisDatasetItem[]> {
  const rootDir = await fetchSystemRootDir(token, systemId);
  const datasets: TapisDatasetItem[] = [];

  // 1. Scan shared smart curriculum designer datasets folder
  try {
    const url = getTapisApiUrl(`/v3/files/ops/${systemId}/${EXPANSE_SHARED_DATASETS_DIR}`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getHeaders(token),
    });
    if (resp.ok) {
      const data = await resp.json();
      const items: any[] = data.result || [];
      for (const item of items) {
        if (item.type === 'dir' || !item.name.includes('.')) {
          const cleanItemPath = (item.path || '').replace(/^\/+/, '');
          const fullClusterPath = rootDir ? `${rootDir}${cleanItemPath}` : `/${cleanItemPath}`;
          datasets.push({
            name: item.name,
            path: item.path,
            clusterPath: fullClusterPath,
            type: item.type,
            source: 'shared',
          });
        }
      }
    }
  } catch (err) {
    console.warn('[Tapis] Could not scan shared datasets folder:', err);
  }

  // 2. Scan user's personal storage folder for any dataset directories
  if (username && username !== 'Authorized User') {
    try {
      const cleanUser = username.includes('@') ? username.split('@')[0] : username;
      const url = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}`);
      const resp = await fetch(url, {
        method: 'GET',
        headers: getHeaders(token),
      });
      if (resp.ok) {
        const data = await resp.json();
        const items: any[] = data.result || [];
        for (const item of items) {
          if (
            item.type === 'dir' &&
            (item.name.toLowerCase().includes('data') || item.name.toLowerCase().includes('dataset'))
          ) {
            const cleanItemPath = (item.path || '').replace(/^\/+/, '');
            const fullClusterPath = rootDir ? `${rootDir}${cleanItemPath}` : `/${cleanItemPath}`;
            datasets.push({
              name: item.name,
              path: item.path,
              clusterPath: fullClusterPath,
              type: item.type,
              source: 'user',
            });
          }
        }
      }
    } catch (err) {
      console.warn('[Tapis] Could not scan user datasets folder:', err);
    }
  }

  return datasets;
}
