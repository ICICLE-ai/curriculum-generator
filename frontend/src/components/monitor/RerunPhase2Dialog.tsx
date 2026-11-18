import React, { useEffect, useState } from 'react';
import { fetchPhase2RerunStatus, parseJobJson, submitPhase2Rerun, type Phase2RerunStatus, type TapisJob } from '../../services/tapis';
import { Dialog } from '../ui';

interface RerunPhase2DialogProps {
  job: TapisJob;
  status: string;
  token: string;
  onClose: () => void;
  onSubmitted: (uuid: string) => void;
}

const Choice: React.FC<{ checked: boolean; onChange: () => void; label: string; hint: string; disabled?: boolean; name: string }> = ({
  checked,
  onChange,
  label,
  hint,
  disabled = false,
  name,
}) => (
  <label className="choice" aria-disabled={disabled}>
    <input type="radio" name={name} checked={checked} onChange={onChange} disabled={disabled} style={{ marginTop: 4 }} />
    <span>
      <span className="choice-label">{label}</span>
      <span className="choice-hint">{hint}</span>
    </span>
  </label>
);

/** Runs Phase 2 again on the selected job's Phase 1 outputs: failed weeks only (default) or all, CPU queue (default). */
export const RerunPhase2Dialog: React.FC<RerunPhase2DialogProps> = ({ job, status, token, onClose, onSubmitted }) => {
  const [check, setCheck] = useState<Phase2RerunStatus | null>(null);
  const [weeks, setWeeks] = useState<'failed' | 'all'>('failed');
  const [queue, setQueue] = useState<'cpu' | 'gpu'>('cpu');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchPhase2RerunStatus(token, job, status)
      .then((result) => {
        if (cancelled) return;
        setCheck(result);
        if (!result.finishedWeeks.length) setWeeks('all');
      })
      .catch((err) => !cancelled && setCheck({ eligible: false, reason: String(err?.message || err), finishedWeeks: [] }));
    return () => {
      cancelled = true;
    };
  }, [token, job, status]);

  const configFile = parseJobJson(job.parameterSet).appArgs?.find((a: any) => a.name === 'config_file')?.arg || 'unknown';

  const start = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const submitted = await submitPhase2Rerun(token, job, weeks, queue);
      onSubmitted(submitted.uuid);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed.');
      setSubmitting(false);
    }
  };

  return (
    <Dialog
      title={`Run Phase 2 again on ${job.name}`}
      onClose={onClose}
      busy={submitting}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>Cancel</button>
          <button type="button" className="btn btn-primary" onClick={start} disabled={!check?.eligible || submitting}>
            {submitting ? 'Submitting…' : 'Start rerun'}
          </button>
        </>
      }
    >
      {!check && <p className="muted">Checking this job's Phase 1 outputs and weeks…</p>}
      {check && !check.eligible && <p role="alert" style={{ color: 'var(--danger)' }}>{check.reason}</p>}

      {check?.eligible && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          <fieldset style={{ border: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <legend className="form-label">Weeks</legend>
            <Choice
              name="weeks"
              checked={weeks === 'failed'}
              onChange={() => setWeeks('failed')}
              label="Only failed or unfinished weeks"
              hint={
                check.finishedWeeks.length
                  ? `Keeps ${check.finishedWeeks.map((w) => w.split('/')[0].replace('_', ' ')).join(', ')}`
                  : 'No week finished in this job'
              }
              disabled={!check.finishedWeeks.length}
            />
            <Choice name="weeks" checked={weeks === 'all'} onChange={() => setWeeks('all')} label="All weeks" hint="Regenerates every week from the same Phase 1 outputs" />
          </fieldset>

          <fieldset style={{ border: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <legend className="form-label">Queue</legend>
            <Choice name="queue" checked={queue === 'cpu'} onChange={() => setQueue('cpu')} label="CPU (recommended)" hint="Phase 2 needs no GPU. No GPU hours, up to 13 h" />
            <Choice name="queue" checked={queue === 'gpu'} onChange={() => setQueue('gpu')} label="GPU" hint="Use if exercise tests time out on CPU" />
          </fieldset>

          <div>
            <div className="form-label">Config</div>
            <code className="muted" style={{ wordBreak: 'break-all' }}>{configFile}</code>
            <p className="form-helper">Locked to the original run. If the file has changed since, the rerun stops within seconds.</p>
          </div>
        </div>
      )}

      {error && <p role="alert" style={{ color: 'var(--danger)', marginTop: 'var(--space-4)' }}>{error}</p>}
    </Dialog>
  );
};
