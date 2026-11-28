import React, { useState } from 'react';
import { describePlan, validateDatasetPlan } from '../../utils/assistant/datasetPlan';
import type { CurriculumAgent, DatasetPlan } from '../../utils/assistant/types';

const SAFE = /^[a-z0-9_]+$/;
const snake = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');

export const DatasetPlanCard: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const live = agent.state.datasetPlan;
  // In-progress text that isn't valid yet, so typing isn't blocked; cleared once the value is accepted
  const [typed, setTyped] = useState<Record<string, string>>({});
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');
  const [error, setError] = useState<string | null>(null);

  if (!live) return <p className="assistant-note muted">No dataset plan right now.</p>;
  const { info, plan } = live;
  const edit = (fn: (p: DatasetPlan) => DatasetPlan) => agent.editDatasetPlan(fn);
  const problems = validateDatasetPlan(plan, info);
  const counts = info.classCounts?.[plan.label_column];
  const columns = Object.keys(info.labelColumns);
  const locked = state !== 'idle';

  // Text field: keep what was typed locally; commit to the plan only when valid
  const setText = (key: string, value: string, valid: boolean, commit: () => void) => {
    setTyped((t) => {
      const next = { ...t };
      if (valid) delete next[key];
      else next[key] = value;
      return next;
    });
    if (valid) commit();
  };
  const invalid = (key: string) => key in typed;

  const prepare = async () => {
    setState('sending');
    setError(null);
    try {
      await agent.prepareDataset();
      setState('sent');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start preparing the dataset.');
      setState('idle');
    }
  };

  return (
    <div className="stack-sm">
      <strong>Dataset plan: {info.id} <span className="muted">(version {plan.revision.slice(0, 7)})</span></strong>
      <ul className="assistant-list">{describePlan(plan, info).map((l) => <li key={l}>{l}</li>)}</ul>

      {columns.length > 1 && (
        <div className="form-group">
          <label htmlFor="plan-label-col" className="form-label">Which labels to use</label>
          <select
            id="plan-label-col"
            value={plan.label_column}
            disabled={locked}
            onChange={(e) => {
              const col = e.target.value;
              setTyped({});
              edit((p) => ({ ...p, label_column: col, class_map: Object.fromEntries(info.labelColumns[col].map((n) => [n, snake(n) || null])) }));
            }}
          >
            {columns.map((c) => <option key={c} value={c}>{c || '(folder names)'}</option>)}
          </select>
        </div>
      )}

      <div className="table-scroll">
        <table className="plan-table">
          <thead>
            <tr><th scope="col">Original label</th><th scope="col">Folder name</th><th scope="col">Keep</th><th scope="col">Images</th></tr>
          </thead>
          <tbody>
            {Object.entries(plan.class_map).map(([label, target]) => {
              const key = `c:${label}`;
              return (
                <tr key={label} className={target === null ? 'plan-dropped' : undefined}>
                  <th scope="row">{label}</th>
                  <td>
                    <input
                      type="text"
                      aria-label={`Folder name for ${label}`}
                      aria-invalid={invalid(key)}
                      value={typed[key] ?? target ?? ''}
                      disabled={locked || target === null}
                      onChange={(e) => {
                        const v = e.target.value;
                        setText(key, v, SAFE.test(v), () => edit((p) => ({ ...p, class_map: { ...p.class_map, [label]: v } })));
                      }}
                    />
                    {invalid(key) && <div className="form-helper plan-invalid">Use lowercase letters, numbers and _ only.</div>}
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      aria-label={`Keep ${label}`}
                      checked={target !== null}
                      disabled={locked}
                      onChange={(e) => {
                        setTyped((t) => { const n = { ...t }; delete n[key]; return n; });
                        edit((p) => ({ ...p, class_map: { ...p.class_map, [label]: e.target.checked ? snake(label) || 'class' : null } }));
                      }}
                    />
                  </td>
                  <td>{counts?.[label]?.toLocaleString() ?? ''}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="row-wrap">
        <div className="form-group">
          <label htmlFor="plan-max" className="form-label">Most images per folder</label>
          <input
            id="plan-max"
            type="number"
            min={1}
            aria-invalid={invalid('max')}
            value={typed.max ?? plan.max_per_class}
            disabled={locked}
            onChange={(e) => {
              const v = e.target.value;
              const n = Number(v);
              setText('max', v, v !== '' && Number.isInteger(n) && n >= 1, () => edit((p) => ({ ...p, max_per_class: n })));
            }}
          />
        </div>
        <div className="form-group">
          <label htmlFor="plan-name" className="form-label">Dataset folder name</label>
          <input
            id="plan-name"
            type="text"
            aria-invalid={invalid('name')}
            value={typed.name ?? plan.name}
            disabled={locked}
            onChange={(e) => {
              const v = e.target.value;
              setText('name', v, SAFE.test(v), () => edit((p) => ({ ...p, name: v })));
            }}
          />
          {invalid('name') && <div className="form-helper plan-invalid">Use lowercase letters, numbers and _ only.</div>}
        </div>
      </div>

      {!problems.ok && (
        <div role="alert" className="alert alert-warning alert-col">
          <strong>Please fix</strong>
          <ul className="assistant-list">{problems.errors.map((e) => <li key={e}>{e}</li>)}</ul>
        </div>
      )}
      <div className="col-end">
        <button type="button" className="btn btn-primary" onClick={prepare} disabled={locked || agent.busy || !problems.ok}>
          {state === 'sending' ? 'Starting...' : state === 'sent' ? 'Started' : 'Download and prepare'}
        </button>
      </div>
      {state === 'sent' && <div className="alert alert-success">Preparing on Expanse — this usually takes a few minutes.</div>}
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  );
};
