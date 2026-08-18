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
  return cleanPath;
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
 * Fetch granular progress.json directly from the running or completed job.
 * Returns null if progress.json is not yet created on the cluster.
 */
export async function fetchJobProgress(
  token: string,
  jobUuid: string
): Promise<PipelineProgressData | null> {
  try {
    const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/progress.json`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: {
        'X-Tapis-Token': token.trim(),
      },
    });

    if (!resp.ok) {
      return null;
    }

    const data = await resp.json();
    return data as PipelineProgressData;
  } catch {
    return null;
  }
}

/**
 * Fetch raw stdout logs (tapisjob.out) for the job.
 */
export async function fetchJobLogs(token: string, jobUuid: string): Promise<string> {
  try {
    const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/tapisjob.out`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: {
        'X-Tapis-Token': token.trim(),
      },
    });

    if (!resp.ok) {
      return 'No output logs available yet. The job is queued or staging on the compute node.';
    }

    return await resp.text();
  } catch (err) {
    console.error(`Failed to fetch logs for job ${jobUuid}:`, err);
    return 'Failed to retrieve logs from compute node.';
  }
}

/**
 * Trigger download of an output artifact from the job directory.
 */
export async function downloadJobArtifact(token: string, jobUuid: string, filename: string): Promise<void> {
  const url = getTapisApiUrl(`/v3/jobs/${jobUuid}/output/download/${filename}`);
  const resp = await fetch(url, {
    method: 'GET',
    headers: {
      'X-Tapis-Token': token.trim(),
    },
  });

  if (!resp.ok) {
    throw new Error(`Artifact ${filename} not found (${resp.status})`);
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
