const BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB'] as const;

/** Format a byte count into a human-readable string (e.g. "12.4 MB"). */
export function formatBytes(bytes?: number): string {
  if (bytes === undefined || bytes === null || Number.isNaN(bytes) || bytes < 0) return '—';
  if (bytes === 0) return '0 B';
  const i = Math.max(0, Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), BYTE_UNITS.length - 1));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${BYTE_UNITS[i]}`;
}

/** Strip an institutional domain suffix (e.g. "@osu.edu") from a Tapis username. */
export function cleanTapisUsername(username: string): string {
  return username.includes('@') ? username.split('@')[0] : username;
}

/** Sanitize a file or folder name for Tapis storage paths. */
export function sanitizeTapisName(name: string, options?: { allowDots?: boolean }): string {
  const pattern = options?.allowDots === false ? /[^a-zA-Z0-9_-]/g : /[^a-zA-Z0-9_\-.]/g;
  return name.trim().replace(pattern, '_');
}
