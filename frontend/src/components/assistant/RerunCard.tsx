import React, { useEffect, useState } from 'react';
import { fetchPhase2RerunStatus, type Phase2RerunStatus } from '../../services/tapis';
import type { CurriculumAgent } from '../../utils/assistant/types';
import { useJob } from './session';

export const RerunCard: React.FC<{ agent: CurriculumAgent; jobUuid: string; weeks: 'failed' | 'all' }> = ({ agent, jobUuid, weeks }) => {
  const { token, job, status } = useJob(jobUuid);
  const [check, setCheck] = useState<Phase2RerunStatus | null>(null);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !job) return;
    fetchPhase2RerunStatus(token, job, status).then(setCheck, (e) => setCheck({ eligible: false, reason: String(e?.message || e), finishedWeeks: [] }));
  }, [token, job, status]);

  const go = async () => {
    setSent(true);
    setError(null);
    try {
      await agent.rerun(jobUuid, weeks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rerun failed.');
      setSent(false);
    }
  };

  return (
    <div className="stack-sm">
      <strong>{weeks === 'failed' ? 'Rerun the weeks that did not finish?' : 'Regenerate every week?'}</strong>
      {!check && <p className="muted mb-0">Checking which weeks finished...</p>}
      {check && !check.eligible && <p role="alert" className="text-danger mb-0">{check.reason}</p>}
      {check?.eligible && (
        <p className="muted mb-0">
          {weeks === 'failed' && check.finishedWeeks.length
            ? `Keeps ${check.finishedWeeks.map((w) => w.split('/')[0].replace('_', ' ')).join(', ')} as they are.`
            : 'Every week will be generated again.'}{' '}
          This uses the same settings as the original run.
        </p>
      )}
      <div className="col-end">
        <button type="button" className="btn btn-primary" onClick={go} disabled={!check?.eligible || sent}>
          {sent ? 'Rerun requested' : 'Start rerun'}
        </button>
      </div>
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  );
};
