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

/**
 * Check if the user already has a valid refresh token.
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

