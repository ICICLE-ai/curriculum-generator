import React, { useState } from 'react';
import { ConfigYamlPreview } from '../config/ConfigYamlPreview';
import { generateCurriculumYaml } from '../../utils/yamlGenerator';
import { missingFields, validateDraft } from '../../utils/assistant/draft';
import type { CurriculumAgent } from '../../utils/assistant/types';

export const ReviewCard: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const d = agent.state.draft;
  const missing = missingFields(d);
  const problems = validateDraft(d);
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [uuid, setUuid] = useState('');

  const submit = async () => {
    setState('sending');
    setError(null);
    try {
      setUuid((await agent.submit()).uuid);
      setState('sent');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submitting failed.');
      setState('idle');
    }
  };

  const yaml = generateCurriculumYaml(d);
  return (
    <div className="stack-sm">
      <strong>Ready to review</strong>
      <ul className="assistant-list">
        <li><strong>Course:</strong> {d.subject || d.domain || '(not set)'} for {d.targetLevel || '(level not set)'}</li>
        <li><strong>Length:</strong> {d.modules.length} weeks</li>
        <li><strong>Photos:</strong> {d.datasetPath || '(none yet)'}</li>
        <li><strong>Run name:</strong> {d.jobName || '(not set)'}</li>
      </ul>
      {missing.length > 0 && (
        <div className="alert alert-warning alert-col">
          <strong>Still needed</strong>
          <ul className="assistant-list">{missing.map((m) => <li key={m.field}>{m.question}</li>)}</ul>
        </div>
      )}
      {missing.length === 0 && problems.length > 0 && (
        <div role="alert" className="alert alert-error alert-col">
          <strong>Please fix</strong>
          <ul className="assistant-list">{problems.map((p) => <li key={p}>{p}</li>)}</ul>
        </div>
      )}
      <details>
        <summary>Show the technical settings</summary>
        <pre className="assistant-yaml">{yaml}</pre>
        <ConfigYamlPreview yamlContent={yaml} defaultConfigName={d.jobName || 'curriculum_config'} />
      </details>
      <div className="col-end">
        <button type="button" className="btn btn-primary" onClick={submit} disabled={problems.length > 0 || state !== 'idle'}>
          {state === 'sending' ? 'Submitting...' : state === 'sent' ? 'Submitted' : 'Submit run'}
        </button>
      </div>
      {state === 'sent' && <div className="alert alert-success">Run submitted ({uuid.slice(0, 8)}).</div>}
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  );
};
