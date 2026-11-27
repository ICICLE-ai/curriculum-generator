import React, { useState } from 'react';
import { Plus, Sparkles, Trash2, X } from 'lucide-react';
import type { CurriculumModule } from '../../presets';
import { generateLearningObjectiveIdeas, type LearningObjectiveIdea } from '../../services/llm';

interface WeeklyModulesSectionProps {
  modules: CurriculumModule[];
  onAddModule: (weekNumber: number) => void;
  onRemoveModule: (index: number) => void;
  onUpdateModule: (index: number, field: keyof CurriculumModule, value: string | number | undefined) => void;
  onAddLearningOutcome: (moduleIndex: number, outcomeText: string) => void;
  onRemoveLearningOutcome: (moduleIndex: number, outcomeIndex: number) => void;
  newObjectiveInputs: Record<number, string>;
  setNewObjectiveInputs: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
  domain: string;
  contextStatement: string;
  subject: string;
  targetLevel: string;
  token: string | null;
}

interface ModuleIdeasState {
  loading: boolean;
  error: string | null;
  ideas: LearningObjectiveIdea[];
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
  domain,
  contextStatement,
  subject,
  targetLevel,
  token,
}) => {
  const [emptyWeeks, setEmptyWeeks] = useState<number[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [ideasByModule, setIdeasByModule] = useState<Record<number, ModuleIdeasState>>({});

  const populatedWeeks = new Set(modules.map((m) => m.week));
  const weekNumbers = Array.from(new Set([...populatedWeeks, ...emptyWeeks])).sort((a, b) => a - b);

  const activeWeek =
    selectedWeek !== null && weekNumbers.includes(selectedWeek)
      ? selectedWeek
      : weekNumbers[0] ?? null;

  const handleAddWeek = () => {
    const nextWeek = weekNumbers.length > 0 ? Math.max(...weekNumbers) + 1 : 1;
    setEmptyWeeks((prev) => (prev.includes(nextWeek) ? prev : [...prev, nextWeek]));
    setSelectedWeek(nextWeek);
  };

  const handleRemoveEmptyWeek = (weekNum: number) => {
    setEmptyWeeks((prev) => prev.filter((w) => w !== weekNum));
    if (selectedWeek === weekNum) {
      const remaining = weekNumbers.filter((w) => w !== weekNum);
      setSelectedWeek(remaining[0] ?? null);
    }
  };

  const handleAddModuleToWeek = (weekNum: number) => {
    setEmptyWeeks((prev) => prev.filter((w) => w !== weekNum));
    onAddModule(weekNum);
  };

  const handleRemoveModuleWithCleanup = (moduleIdx: number) => {
    setIdeasByModule((prev) => {
      const next: Record<number, ModuleIdeasState> = {};
      Object.entries(prev).forEach(([k, val]) => {
        const keyNum = Number(k);
        if (keyNum < moduleIdx) next[keyNum] = val;
        else if (keyNum > moduleIdx) next[keyNum - 1] = val;
      });
      return next;
    });
    onRemoveModule(moduleIdx);
  };

  const handleGenerateIdeas = async (moduleIdx: number, mod: CurriculumModule) => {
    setIdeasByModule((prev) => ({
      ...prev,
      [moduleIdx]: { loading: true, error: null, ideas: prev[moduleIdx]?.ideas || [] },
    }));

    try {
      const ideas = await generateLearningObjectiveIdeas(token || '', {
        domain,
        contextStatement,
        subject,
        targetLevel,
        moduleTitle: mod.title,
        moduleContext: mod.context,
        difficulty: mod.difficulty,
        week: mod.week,
        estimatedDays: mod.estimated_days,
        existingObjectives: mod.learning_outcomes || [],
      });
      setIdeasByModule((prev) => ({
        ...prev,
        [moduleIdx]: { loading: false, error: null, ideas },
      }));
    } catch (err) {
      setIdeasByModule((prev) => ({
        ...prev,
        [moduleIdx]: {
          loading: false,
          error: err instanceof Error ? err.message : 'Failed to generate learning objective ideas.',
          ideas: [],
        },
      }));
    }
  };

  const handleDismissIdeas = (moduleIdx: number) => {
    setIdeasByModule((prev) => {
      const next = { ...prev };
      delete next[moduleIdx];
      return next;
    });
  };

  return (
    <div className="stack">
      <div className="row-between" style={{ flexWrap: 'wrap' }}>
        <div>
          <div className="inline-label-pair">
            <h2 className="card-title">Weekly Labs &amp; Modules ({modules.length})</h2>
            {renderHelpBtn('curriculum.modules')}
          </div>
          <p className="card-subtitle">
            Organize modules into weeks, estimate days spent, and generate learning objective ideas. Leave empty to let the AI plan the syllabus.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={handleAddWeek}>
          <Plus size={16} aria-hidden="true" />
          <span>Add Week</span>
        </button>
      </div>

      {weekNumbers.length > 0 && (
        <div className="tab-strip" role="tablist" aria-label="Course Weeks">
          {weekNumbers.map((weekNum) => {
            const count = modules.filter((m) => m.week === weekNum).length;
            const isActive = activeWeek === weekNum;
            return (
              <button
                key={weekNum}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setSelectedWeek(weekNum)}
                className={`btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}
              >
                <span>Week {weekNum}</span>
                <span className="tab-count">{count}</span>
              </button>
            );
          })}
        </div>
      )}

      {activeWeek !== null ? (
        (() => {
          const weekNum = activeWeek;
          const weekModules = modules
            .map((m, idx) => ({ m, idx }))
            .filter(({ m }) => m.week === weekNum);
          const totalWeekDays = weekModules.reduce(
            (sum, { m }) => sum + (m.estimated_days && m.estimated_days > 0 ? m.estimated_days : 0),
            0
          );

          return (
            <div key={weekNum} role="tabpanel" className="week-card">
              <div className="week-card-header">
                <div className="row-wrap">
                  <span className="week-pill">Week {weekNum}</span>
                  <span className="muted">
                    {weekModules.length} {weekModules.length === 1 ? 'module' : 'modules'}
                  </span>
                  {totalWeekDays > 0 && (
                    <span className="pill-tag">
                      {totalWeekDays} {totalWeekDays === 1 ? 'day' : 'days'} est.
                    </span>
                  )}
                </div>

                <div className="row">
                  {weekModules.length === 0 && (
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost"
                      onClick={() => handleRemoveEmptyWeek(weekNum)}
                    >
                      Remove Week
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleAddModuleToWeek(weekNum)}
                  >
                    <Plus size={14} aria-hidden="true" />
                    <span>Add Module</span>
                  </button>
                </div>
              </div>

              {weekModules.length === 0 ? (
                <div className="empty-state">
                  No modules in Week {weekNum} yet. Click <strong>Add Module</strong> above to add a lesson.
                </div>
              ) : (
                <div className="stack">
                  {weekModules.map(({ m, idx }) => {
                    const ideaState = ideasByModule[idx];
                    const existingSet = new Set(
                      (m.learning_outcomes || []).map((o) => o.trim().toLowerCase())
                    );

                    return (
                      <div key={idx} className="module-card">
                        <div className="row-wrap">
                          <input
                            type="text"
                            aria-label="Module title"
                            value={m.title}
                            onChange={(e) => onUpdateModule(idx, 'title', e.target.value)}
                            placeholder="Module Title (e.g. Python Basics: Variables, Lists & Loops)"
                            style={{ flex: '1 1 220px', fontWeight: 600 }}
                          />

                          <div className="row" title="Estimated days spent on this module">
                            <label htmlFor={`module-days-${idx}`} className="muted">
                              ETA (Days)
                            </label>
                            <input
                              id={`module-days-${idx}`}
                              type="number"
                              min="0.5"
                              step="0.5"
                              placeholder="2"
                              className="input-compact"
                              value={m.estimated_days ?? ''}
                              onChange={(e) => {
                                const raw = e.target.value.trim();
                                if (raw === '') {
                                  onUpdateModule(idx, 'estimated_days', undefined);
                                } else {
                                  const parsed = parseFloat(raw);
                                  onUpdateModule(idx, 'estimated_days', !isNaN(parsed) && parsed > 0 ? parsed : undefined);
                                }
                              }}
                            />
                          </div>

                          <select
                            aria-label="Module difficulty"
                            className="input-compact-wide"
                            value={m.difficulty}
                            onChange={(e) =>
                              onUpdateModule(idx, 'difficulty', e.target.value as 'Beginner' | 'Intermediate' | 'Advanced')
                            }
                          >
                            <option value="Beginner">Beginner</option>
                            <option value="Intermediate">Intermediate</option>
                            <option value="Advanced">Advanced</option>
                          </select>

                          <button
                            type="button"
                            className="btn btn-sm btn-danger"
                            onClick={() => handleRemoveModuleWithCleanup(idx)}
                            title="Remove lesson module"
                          >
                            <Trash2 size={14} aria-hidden="true" />
                            <span>Remove</span>
                          </button>
                        </div>

                        <input
                          type="text"
                          aria-label="Module lab context"
                          value={m.context}
                          onChange={(e) => onUpdateModule(idx, 'context', e.target.value)}
                          placeholder="Lab Context: What do students implement?"
                        />

                        <div className="stack-sm">
                          <div className="row-between">
                            <span className="form-label mb-0">
                              Learning Objectives ({m.learning_outcomes?.length || 0})
                            </span>

                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              disabled={ideaState?.loading || !token}
                              onClick={() => handleGenerateIdeas(idx, m)}
                              title={
                                token
                                  ? 'Suggest learning objectives with plain-English explanations'
                                  : 'Sign in to generate AI learning objective ideas'
                              }
                            >
                              <Sparkles size={14} aria-hidden="true" />
                              <span>{ideaState?.loading ? 'Generating Ideas...' : 'Generate Ideas'}</span>
                            </button>
                          </div>

                          <div className="pill-list">
                            {(m.learning_outcomes || []).map((outcome, oIdx) => (
                              <div key={oIdx} className="objective-chip">
                                <span>{outcome}</span>
                                <button
                                  type="button"
                                  className="icon-remove-btn"
                                  onClick={() => onRemoveLearningOutcome(idx, oIdx)}
                                  aria-label={`Remove objective: ${outcome}`}
                                  title="Remove learning objective"
                                >
                                  <X size={14} aria-hidden="true" />
                                </button>
                              </div>
                            ))}
                            {(!m.learning_outcomes || m.learning_outcomes.length === 0) && (
                              <span className="muted">
                                No learning objectives added yet. Type below or click <strong>Generate Ideas</strong>.
                              </span>
                            )}
                          </div>

                          {ideaState && (ideaState.loading || ideaState.error || ideaState.ideas.length > 0) && (
                            <div className="suggestion-panel">
                              <div className="row-between">
                                <strong className="text-info">
                                  Suggested Learning Objectives
                                </strong>
                                <div className="row">
                                  {!ideaState.loading && (
                                    <button
                                      type="button"
                                      className="btn btn-sm btn-ghost"
                                      onClick={() => handleGenerateIdeas(idx, m)}
                                    >
                                      Regenerate
                                    </button>
                                  )}
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-ghost"
                                    onClick={() => handleDismissIdeas(idx)}
                                  >
                                    Dismiss
                                  </button>
                                </div>
                              </div>

                              {ideaState.loading && (
                                <p className="muted">Generating learning objective ideas and plain-English overviews...</p>
                              )}

                              {ideaState.error && (
                                <p role="alert" className="text-danger">
                                  {ideaState.error}
                                </p>
                              )}

                              {!ideaState.loading && !ideaState.error && ideaState.ideas.length > 0 && (
                                <div className="stack-sm">
                                  {ideaState.ideas.map((idea, iIdx) => {
                                    const alreadyAdded = existingSet.has(idea.objective.trim().toLowerCase());
                                    return (
                                      <div key={iIdx} className="suggestion-item">
                                        <div className="flex-1 stack-sm">
                                          <strong>{idea.objective}</strong>
                                          <span className="muted">
                                            <strong>In plain English:</strong> {idea.plainEnglishOverview}
                                          </span>
                                        </div>
                                        <button
                                          type="button"
                                          className="btn btn-sm btn-secondary"
                                          disabled={alreadyAdded}
                                          onClick={() => onAddLearningOutcome(idx, idea.objective)}
                                        >
                                          {alreadyAdded ? 'Added' : 'Add'}
                                        </button>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          )}

                          <div className="row">
                            <input
                              type="text"
                              aria-label="New learning objective"
                              className="flex-1"
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
                              placeholder="Type a learning objective and press Enter..."
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
                            >
                              <Plus size={14} aria-hidden="true" />
                              <span>Add Objective</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })()
      ) : (
        <div className="empty-state">
          No weeks added yet. Click <strong>Add Week</strong> to start organizing your weekly syllabus, or leave empty to let the AI plan it.
        </div>
      )}
    </div>
  );
};
