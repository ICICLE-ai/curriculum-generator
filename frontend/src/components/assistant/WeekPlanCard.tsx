import React, { useState } from 'react';
import { WeeklyModulesSection } from '../config';
import { getStoredToken } from '../../utils/storage';
import type { CurriculumAgent, CurriculumModule } from '../../utils/assistant/types';

// The Config page's weekly modules editor (week tabs, outcomes, objective ideas), wired to the assistant's draft
export const WeekPlanCard: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const { draft } = agent.state; // live, not a snapshot
  const [newObjectiveInputs, setNewObjectiveInputs] = useState<Record<number, string>>({});
  const [sent, setSent] = useState(false);
  const setModule = (i: number, fn: (m: CurriculumModule) => CurriculumModule) =>
    agent.editDraft((d) => ({ ...d, modules: d.modules.map((m, j) => (j === i ? fn(m) : m)) }));

  return (
    <div className="stack-sm">
      <WeeklyModulesSection
        modules={draft.modules}
        onAddModule={(week) =>
          agent.editDraft((d) => ({
            ...d,
            modules: [...d.modules, { id: `week_${week}_module`, title: '', week, context: '', difficulty: 'Beginner', learning_outcomes: [] }],
          }))
        }
        onRemoveModule={(i) => agent.editDraft((d) => ({ ...d, modules: d.modules.filter((_, j) => j !== i) }))}
        onUpdateModule={(i, field, value) =>
          setModule(i, (m) => {
            const next = { ...m, [field]: value };
            // Same id rule as ConfigPage: the module id follows its title
            const id = field === 'title' ? String(value).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') : '';
            return id ? { ...next, id } : next;
          })
        }
        onAddLearningOutcome={(i, text) => text.trim() && setModule(i, (m) => ({ ...m, learning_outcomes: [...m.learning_outcomes, text.trim()] }))}
        onRemoveLearningOutcome={(i, k) => setModule(i, (m) => ({ ...m, learning_outcomes: m.learning_outcomes.filter((_, n) => n !== k) }))}
        newObjectiveInputs={newObjectiveInputs}
        setNewObjectiveInputs={setNewObjectiveInputs}
        renderHelpBtn={() => null}
        domain={draft.domain}
        contextStatement={draft.contextStatement}
        subject={draft.subject}
        targetLevel={draft.targetLevel}
        token={getStoredToken()}
      />
      <div className="col-end">
        <button
          type="button"
          className="btn btn-primary"
          disabled={sent}
          onClick={() => {
            setSent(true);
            agent.editDraft((d) => d, 'I finished editing the week plan.');
          }}
        >
          {sent ? 'Sent to the assistant' : 'Done editing'}
        </button>
      </div>
    </div>
  );
};
