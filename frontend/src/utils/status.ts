export type Tone = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

// Tapis job statuses and pipeline stage statuses, as a tone and a plain label
export const STATUS: Record<string, [Tone, string]> = {
  FINISHED: ['success', 'Finished'],
  COMPLETED: ['success', 'Done'],
  RUNNING: ['info', 'Running'],
  IN_PROGRESS: ['info', 'Running'],
  ARCHIVING: ['info', 'Archiving'],
  QUEUED: ['warning', 'Queued'],
  PENDING: ['warning', 'Pending'],
  PROCESSING_INPUTS: ['warning', 'Preparing'],
  STAGING_INPUTS: ['warning', 'Preparing'],
  STAGING_JOB: ['warning', 'Preparing'],
  SUBMITTING_JOB: ['warning', 'Submitting'],
  BLOCKED: ['warning', 'Blocked'],
  PAUSED: ['warning', 'Paused'],
  FAILED: ['danger', 'Failed'],
  CANCELLED: ['neutral', 'Cancelled'],
  READY: ['neutral', 'Not started'],
  SKIPPED: ['neutral', 'Skipped'],
};

export const statusLabel = (status: string): string =>
  STATUS[status]?.[1] ?? (status ? status.charAt(0) + status.slice(1).toLowerCase().replace(/_/g, ' ') : 'Unknown');
