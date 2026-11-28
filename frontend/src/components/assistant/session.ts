import { useEffect, useState } from 'react';
import { getStoredToken } from '../../utils/storage';
import { parseJwt } from '../../utils/jwt';
import { cleanTapisUsername } from '../../utils/format';
import { fetchJobDetails, fetchJobProgress, fetchJobStatus, type PipelineProgressData, type TapisJob } from '../../services/tapis';

export const TERMINAL = ['FINISHED', 'FAILED', 'CANCELLED'];

export function useSession() {
  const token = getStoredToken();
  const payload = token ? parseJwt(token)?.payload : null;
  const username = cleanTapisUsername((payload?.['tapis/username'] as string) || (payload?.sub as string) || '');
  return { token, username };
}

/** Loads a job once, then every `everyMs` while it is not finished (0 = load once). */
export function useJob(jobUuid: string, everyMs = 0, initialStatus = 'UNKNOWN') {
  const { token } = useSession();
  const [job, setJob] = useState<TapisJob | null>(null);
  const [status, setStatus] = useState(initialStatus);
  const [progress, setProgress] = useState<PipelineProgressData | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    let timer: number | undefined;
    const tick = async () => {
      let next = 'UNKNOWN';
      try {
        next = (await fetchJobStatus(token, jobUuid)).status || 'UNKNOWN';
        const details = await fetchJobDetails(token, jobUuid);
        const prog = await fetchJobProgress(token, jobUuid, details);
        if (cancelled) return;
        setStatus(next);
        setJob(details);
        setProgress(prog);
      } catch (err) {
        console.warn('Assistant job poll failed:', err);
      }
      if (!cancelled && everyMs && !TERMINAL.includes(next)) timer = window.setTimeout(tick, everyMs);
    };
    tick();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [token, jobUuid, everyMs]);

  return { token, job, status, progress };
}
