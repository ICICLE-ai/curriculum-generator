import React, { useState } from 'react';
import { explainFailure } from '../../utils/assistant/failures';
import type { CurriculumAgent, ModuleFailure } from '../../utils/assistant/types';

export const FailureCard: React.FC<{ agent: CurriculumAgent; jobUuid: string; failures: ModuleFailure[] }> = ({ agent, jobUuid, failures }) => {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const go = async () => {
    setSent(true);
    setError(null);
    try {
      await agent.rerun(jobUuid, 'failed');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rerun failed.');
      setSent(false);
    }
  };
  return (
    <div className="stack-sm">
      <strong>{failures.length} {failures.length === 1 ? 'week' : 'weeks'} did not finish</strong>
      <ul className="assistant-list">
        {failures.map((f) => {
          const { reason, advice } = explainFailure(f);
          return (
            <li key={`${f.week}-${f.module}`}>
              <strong>Week {f.week}{f.module ? ` (${f.module})` : ''}:</strong> {reason} <span className="muted">{advice}</span>
            </li>
          );
        })}
      </ul>
      <div className="col-end">
        <button type="button" className="btn btn-primary" onClick={go} disabled={sent}>
          {sent ? 'Rerun requested' : 'Rerun failed weeks'}
        </button>
      </div>
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  );
};
