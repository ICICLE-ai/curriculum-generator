import React, { useEffect, useState } from 'react';
import { StatusBadge } from '../ui';
import { TERMINAL } from './session';
import type { CurriculumAgent, TrackedRun } from '../../utils/assistant/types';

const KIND_LABEL: Record<TrackedRun['kind'], string> = {
  dataset: 'Preparing images',
  phase1: 'Analysing images (Phase 1)',
  phase2: 'Writing lessons (Phase 2)',
  rerun: 'Rerunning weeks',
};

const elapsed = (ms: number) => {
  const m = Math.floor(ms / 60000);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${m % 60} min`;
};

// What is happening in the background, so the educator can keep chatting while jobs run
export const BackgroundTasksPanel: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(id);
  }, []);

  const runs = [...agent.state.runs].reverse(); // newest first
  const active = runs.filter((r) => !TERMINAL.includes(r.lastStatus ?? ''));
  const done = runs.filter((r) => TERMINAL.includes(r.lastStatus ?? '')).slice(0, 5);
  // Only while a job runs: showing it for model turns too would make the chat jump sideways on every message
  if (!active.length) return null;
  const row = (r: TrackedRun) => (
    <li key={r.jobUuid} className="assistant-task">
      <div className="row-between">
        <strong>{KIND_LABEL[r.kind]}</strong>
        <StatusBadge status={r.lastStatus ?? 'PENDING'} />
      </div>
      <span className="muted">
        {r.name}
        {r.startedAt && !TERMINAL.includes(r.lastStatus ?? '') ? ` · ${elapsed(now - r.startedAt)}` : ''}
      </span>
    </li>
  );

  return (
    <aside className="assistant-tasks" aria-label="Background tasks">
      <h2 className="assistant-tasks-title">Background tasks</h2>
      {agent.busy && <p className="assistant-task-now" role="status">{agent.status ?? 'Thinking...'}</p>}
      <ul className="assistant-task-list">{active.map(row)}</ul>
      {done.length > 0 && (
        <>
          <h3 className="assistant-tasks-subtitle">Recently finished</h3>
          <ul className="assistant-task-list">{done.map(row)}</ul>
        </>
      )}
    </aside>
  );
};
