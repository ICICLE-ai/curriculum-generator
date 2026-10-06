import React from 'react';
import type { CurriculumModule } from '../../presets';

interface WeeklyModulesSectionProps {
  modules: CurriculumModule[];
  onAddModule: () => void;
  onRemoveModule: (index: number) => void;
  onUpdateModule: (index: number, field: keyof CurriculumModule, value: string | number) => void;
  onAddLearningOutcome: (moduleIndex: number, outcomeText: string) => void;
  onRemoveLearningOutcome: (moduleIndex: number, outcomeIndex: number) => void;
  newObjectiveInputs: Record<number, string>;
  setNewObjectiveInputs: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
}

export const WeeklyModulesSection: React.FC<WeeklyModulesSectionProps> = ({
  modules,
  onAddModule,
  onRemoveModule,
  onUpdateModule,
  onAddLearningOutcome,
  onRemoveLearningOutcome,
  newObjectiveInputs,
  setNewObjectiveInputs,
  renderHelpBtn,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>Curriculum Modules & Weekly Labs ({modules.length})</span>
            {renderHelpBtn('curriculum.modules')}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Scaffolded weekly milestone labs with interactive learning objective blocks.
          </div>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onAddModule}
        >
          + Add Module
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {modules.map((m, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem',
              padding: '1.25rem 1.4rem',
              background: 'var(--bg-card-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            {/* Module Meta Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.35rem 0.65rem',
                  borderRadius: 'var(--radius-sm)',
                  background: '#27272a',
                  color: '#fafafa',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                Week {m.week}
              </span>
              <input
                type="text"
                value={m.title}
                onChange={(e) => onUpdateModule(idx, 'title', e.target.value)}
                placeholder="Module Title (e.g. NumPy Basics & Image Arrays)..."
                style={{ flex: '1 1 200px', fontWeight: 600 }}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Wk</span>
                <input
                  type="number"
                  min="1"
                  max="52"
                  value={m.week}
                  onChange={(e) => onUpdateModule(idx, 'week', Number(e.target.value))}
                  style={{ width: '48px', textAlign: 'center' }}
                />
              </div>
              <select
                value={m.difficulty}
                onChange={(e) => onUpdateModule(idx, 'difficulty', e.target.value as 'Beginner' | 'Intermediate' | 'Advanced')}
                style={{ width: '120px' }}
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => onRemoveModule(idx)}
                style={{ color: 'var(--accent-rose)' }}
                title="Remove lesson module"
              >
                Remove
              </button>
            </div>

            {/* Context / Problem Description */}
            <div>
              <input
                type="text"
                value={m.context}
                onChange={(e) => onUpdateModule(idx, 'context', e.target.value)}
                placeholder="Lab Context: What do students implement? (e.g. Inspect lesion patterns, extract features)..."
              />
            </div>

            {/* Learning Outcomes as Interactive Blocks */}
            <div style={{ marginTop: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Learning Objectives ({m.learning_outcomes?.length || 0})
                </span>
                <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                  Saved to <code>learning_outcomes</code> in YAML
                </span>
              </div>

              {/* Blocks / Pills List */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem', marginBottom: '0.65rem' }}>
                {(m.learning_outcomes || []).map((outcome, oIdx) => (
                  <div
                    key={oIdx}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.35rem 0.7rem',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.8rem',
                      color: 'var(--text-primary)',
                      lineHeight: 1.35,
                      maxWidth: '100%',
                    }}
                  >
                    <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>•</span>
                    <span style={{ wordBreak: 'break-word' }}>{outcome}</span>
                    <button
                      type="button"
                      onClick={() => onRemoveLearningOutcome(idx, oIdx)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '0 0.15rem',
                        fontSize: '0.9rem',
                        lineHeight: 1,
                        display: 'inline-flex',
                        alignItems: 'center',
                        transition: 'color 0.15s ease',
                      }}
                      title="Remove learning objective"
                      onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--accent-rose)')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                    >
                      ×
                    </button>
                  </div>
                ))}
                {(!m.learning_outcomes || m.learning_outcomes.length === 0) && (
                  <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '0.35rem 0' }}>
                    No learning objectives added. Type below and press Enter to add one.
                  </span>
                )}
              </div>

              {/* Add Objective Input */}
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  value={newObjectiveInputs[idx] || ''}
                  onChange={(e) => setNewObjectiveInputs({ ...newObjectiveInputs, [idx]: e.target.value })}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const text = (newObjectiveInputs[idx] || '').trim();
                      if (text) {
                        onAddLearningOutcome(idx, text);
                        setNewObjectiveInputs({ ...newObjectiveInputs, [idx]: '' });
                      }
                    }
                  }}
                  placeholder="Type learning objective (e.g. Extract GLCM texture features) and press Enter..."
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    const text = (newObjectiveInputs[idx] || '').trim();
                    if (text) {
                      onAddLearningOutcome(idx, text);
                      setNewObjectiveInputs({ ...newObjectiveInputs, [idx]: '' });
                    }
                  }}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  + Add Objective
                </button>
              </div>
            </div>
          </div>
        ))}
        {modules.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No modules added yet. Click "+ Add Module" to build your custom weekly syllabus.
          </div>
        )}
      </div>
    </div>
  );
};
