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

    // Filter to DigitalAgEdu app jobs (supporting digital-age-edu-test and digital-age-edu)
    const eduJobs = allJobs.filter(
      (j) =>
        j.appId?.toLowerCase().includes('digital-age-edu-test') ||
        j.appId?.toLowerCase().includes('digital-age') ||
        j.appId?.toLowerCase().includes('digitalage') ||
        j.name?.toLowerCase().includes('digital-age') ||
        j.name?.toLowerCase().includes('digitalage') ||
        j.name?.toLowerCase().includes('curriculum')
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
