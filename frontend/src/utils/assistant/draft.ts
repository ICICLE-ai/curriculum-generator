// Draft state helpers for the Curriculum Assistant. Everything the LLM sends goes through applyPatch/setWeekPlan/editWeek.
import { DEFAULT_LLM_MODELS, generateCurriculumYaml } from '../yamlGenerator.ts';
import schema from '../../data/rootConfigSchema.json' with { type: 'json' };
import type { CurriculumModule, Draft, FieldChange, MissingField, PatchResult } from './types.ts';

// Pydantic only emits min/max when declared on the Field; config.py enforces 4..24 in a validator, hence the fallbacks
const weeksSchema = schema.$defs.CurriculumConfig.properties.weeks.anyOf[0] as { minimum?: number; maximum?: number };
export const WEEKS_MIN = weeksSchema.minimum ?? 4;
export const WEEKS_MAX = weeksSchema.maximum ?? 24;

export const DEFAULT_DRAFT: Draft = {
  domain: '',
  contextStatement: '',
  useCase: 'educational_curriculum',
  datasetPath: '',
  outputPath: '',
  classificationActive: true,
  classificationTask: '',
  segmentationActive: true,
  segmentationPrompt: '',
  xaiActive: true,
  device: 'cuda',
  batchSize: 16,
  imageSize: 518,
  maxSamples: null,
  seed: 42,
  llmModels: DEFAULT_LLM_MODELS,
  subject: '',
  targetLevel: '',
  modules: [],
  resources: [],
  jobName: `curriculum-run-${Date.now().toString().slice(-4)}`,
  codingExperience: '',
};

const DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced'];
const TEXT_MAX = { domain: 200, contextStatement: 2000, subject: 200, targetLevel: 100, classificationTask: 500, segmentationPrompt: 500, outputPath: 300, topicName: 200, topicDescription: 1000, jobName: 100 } as const;
const BOOLS = ['classificationActive', 'segmentationActive', 'xaiActive'] as const;
const PATCH_KEYS = new Set<string>([...Object.keys(TEXT_MAX), ...BOOLS, 'weeks', 'codingExperience']);
const CODING = ['none', 'some', 'comfortable'] as const;

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const rec = (v: object) => v as Record<string, unknown>;
const placeholder = (week: number): CurriculumModule => ({ id: `week_${week}`, title: '', week, context: '', difficulty: 'Beginner', learning_outcomes: [] });
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'module';

function text(v: unknown, label: string, max: number, errs: string[]): string | undefined {
  if (typeof v !== 'string') return void errs.push(`${label} must be a string`);
  const t = v.trim();
  if (!t) return void errs.push(`${label} must not be empty`);
  if (t.length > max) return void errs.push(`${label} must be at most ${max} characters`);
  return t;
}

function relativePath(v: unknown, errs: string[]): string | undefined {
  const p = text(v, 'outputPath', TEXT_MAX.outputPath, errs);
  if (p !== undefined && (/^([a-zA-Z]:|[\\/])/.test(p) || p.split(/[\\/]/).includes('..'))) return void errs.push('outputPath must be a relative path without ..');
  return p;
}

// Validates the module fields present in `raw` (all required unless `partial`); returns the cleaned fields
function moduleFields(raw: Record<string, unknown>, label: string, partial: boolean, errs: string[]) {
  const allowed = ['title', 'context', 'difficulty', 'learning_outcomes', 'estimated_days'];
  for (const k of Object.keys(raw)) if (!allowed.includes(k)) errs.push(`${label}: unknown field "${k}"`);
  const out: Partial<CurriculumModule> = {};
  for (const k of ['title', 'context'] as const) {
    if (k in raw) out[k] = text(raw[k], `${label}.${k}`, k === 'title' ? 150 : 1500, errs);
    else if (!partial) errs.push(`${label}.${k} is required`);
  }
  if ('difficulty' in raw) {
    if (DIFFICULTIES.includes(raw.difficulty as string)) out.difficulty = raw.difficulty as CurriculumModule['difficulty'];
    else errs.push(`${label}.difficulty must be one of ${DIFFICULTIES.join(', ')}`);
  } else if (!partial) errs.push(`${label}.difficulty is required`);
  if ('learning_outcomes' in raw) {
    const lo = raw.learning_outcomes;
    if (!Array.isArray(lo) || lo.length < 1 || lo.length > 10) errs.push(`${label}.learning_outcomes must be an array of 1-10 strings`);
    else {
      const items = lo.map((o, i) => text(o, `${label}.learning_outcomes[${i}]`, 300, errs));
      if (!items.includes(undefined)) out.learning_outcomes = items as string[];
    }
  } else if (!partial) errs.push(`${label}.learning_outcomes is required`);
  if ('estimated_days' in raw) {
    const n = raw.estimated_days;
    if (Number.isInteger(n) && (n as number) >= 1 && (n as number) <= 14) out.estimated_days = n as number;
    else errs.push(`${label}.estimated_days must be an integer 1-14`);
  }
  return out;
}

const diff = (field: string, from: unknown, to: unknown): FieldChange[] => (JSON.stringify(from) === JSON.stringify(to) ? [] : [{ field, from, to }]);
const fail = (d: Draft, errors: string[]): PatchResult => ({ ok: false, draft: d, errors, changes: [] });

export function applyPatch(d: Draft, patch: unknown): PatchResult {
  if (!isObj(patch)) return fail(d, ['patch must be an object']);
  const errs: string[] = [];
  const next: Draft = { ...d };
  for (const [k, v] of Object.entries(patch)) {
    if (k === 'datasetPath') errs.push("datasetPath can only be set by the educator's upload or picker");
    else if (!PATCH_KEYS.has(k)) errs.push(`unknown field "${k}"`);
    else if (k === 'weeks') {
      if (!Number.isInteger(v) || (v as number) < WEEKS_MIN || (v as number) > WEEKS_MAX) errs.push(`weeks must be an integer between ${WEEKS_MIN} and ${WEEKS_MAX}`);
      else next.modules = Array.from({ length: v as number }, (_, i) => d.modules[i] ?? placeholder(i + 1));
    } else if (k === 'codingExperience') {
      if ((CODING as readonly unknown[]).includes(v)) next.codingExperience = v as Draft['codingExperience'];
      else errs.push(`codingExperience must be one of ${CODING.join(', ')}`);
    } else if ((BOOLS as readonly string[]).includes(k)) {
      if (typeof v === 'boolean') rec(next)[k] = v;
      else errs.push(`${k} must be a boolean`);
    } else {
      const t = k === 'outputPath' ? relativePath(v, errs) : text(v, k, TEXT_MAX[k as keyof typeof TEXT_MAX], errs);
      if (t !== undefined) rec(next)[k] = t;
    }
  }
  if (errs.length) return fail(d, errs);
  const changes = Object.keys(patch).flatMap((k) => (k === 'weeks' ? diff('weeks', d.modules.length, next.modules.length) : diff(k, rec(d)[k], rec(next)[k])));
  return { ok: true, draft: next, errors: [], changes };
}

export function setWeekPlan(d: Draft, modules: unknown): PatchResult {
  if (!Array.isArray(modules)) return fail(d, ['modules must be an array']);
  if (modules.length < WEEKS_MIN || modules.length > WEEKS_MAX) return fail(d, [`the plan needs ${WEEKS_MIN} to ${WEEKS_MAX} weeks, got ${modules.length}`]);
  const errs: string[] = [];
  const used = new Set<string>();
  const next = modules.map((m, i): CurriculumModule => {
    if (!isObj(m)) {
      errs.push(`week ${i + 1} must be an object`);
      return placeholder(i + 1);
    }
    const f = moduleFields(m, `week ${i + 1}`, false, errs);
    const base = slug(f.title ?? '');
    let id = base;
    for (let n = 2; used.has(id); n++) id = `${base}_${n}`;
    used.add(id);
    return { ...placeholder(i + 1), ...f, id, week: i + 1 };
  });
  if (errs.length) return fail(d, errs);
  return { ok: true, draft: { ...d, modules: next }, errors: [], changes: diff('modules', d.modules, next) };
}

export function editWeek(d: Draft, week: number, patch: unknown): PatchResult {
  const idx = d.modules.findIndex((m) => m.week === week);
  if (idx < 0) return fail(d, [`there is no week ${week} in the plan`]);
  if (!isObj(patch)) return fail(d, ['patch must be an object']);
  const errs: string[] = [];
  const f = moduleFields(patch, `week ${week}`, true, errs);
  if (errs.length) return fail(d, errs);
  const next = { ...d.modules[idx], ...f };
  const modules = d.modules.map((m, i) => (i === idx ? next : m));
  const changes = Object.keys(f).flatMap((k) => diff(`week ${week}.${k}`, rec(d.modules[idx])[k], rec(next)[k]));
  return { ok: true, draft: { ...d, modules }, errors: [], changes };
}

export function setDataset(d: Draft, path: string): Draft {
  return { ...d, datasetPath: path };
}

export function missingFields(d: Draft): MissingField[] {
  const out: MissingField[] = [];
  const need = (ok: unknown, field: string, question: string) => {
    if (!ok) out.push({ field, question });
  };
  need(d.domain.trim(), 'domain', 'What field or domain is the course for (for example, plant biology)?');
  need(d.contextStatement.trim(), 'contextStatement', 'Briefly, what is the course about and what should students get out of it?');
  need(d.targetLevel.trim(), 'targetLevel', 'Which students is it for (grade or level)?');
  // `?? ''`: drafts saved before this field existed
  need(d.codingExperience ?? '', 'codingExperience', 'How much coding have the students done: none, some, or comfortable with Python? If the teacher is unsure, use none.');
  need(d.modules.length, 'weeks', `How many weeks should the course run (${WEEKS_MIN} to ${WEEKS_MAX})?`);
  // Before the dataset, so the model drafts the plan as soon as it knows topic, level and length.
  // An unwritten plan is one item, not 3 per week, so it doesn't drown the rest of the list.
  if (d.modules.length && d.modules.every((m) => !m.title.trim())) {
    out.push({ field: 'modules', question: 'Propose the whole weekly plan now with set_week_plan, then ask the educator to review it.' });
  } else {
    const weeks = d.modules.map((m) => m.week).sort((a, b) => a - b);
    if (weeks.some((w, i) => w !== i + 1)) out.push({ field: 'modules', question: `The weeks must be numbered 1 to ${weeks.length} with no gaps or repeats; fix the plan.` });
    for (const m of d.modules) {
      need(m.title.trim(), `week ${m.week}.title`, `Week ${m.week} needs a title.`);
      need(m.context.trim(), `week ${m.week}.context`, `Week ${m.week} needs a short description of what it covers.`);
      need(m.learning_outcomes.length, `week ${m.week}.learning_outcomes`, `Week ${m.week} needs at least one learning outcome.`);
    }
  }
  need(d.datasetPath.trim(), 'datasetPath', 'Which image dataset should the course use? Ask them to upload one or pick an existing one.');
  need(d.subject.trim(), 'subject', 'Propose a short subject name for the course and confirm it.');
  if (d.classificationActive) need(d.classificationTask.trim(), 'classificationTask', 'Propose what the image classification task should be and confirm it.');
  if (d.segmentationActive) need(d.segmentationPrompt.trim(), 'segmentationPrompt', 'Propose what the segmentation step should outline in the images and confirm it.');
  need(d.outputPath.trim(), 'outputPath', 'Propose an output folder for the results and confirm it.');
  return out;
}

export function validateDraft(d: Draft): string[] {
  const errs = missingFields(d).map((m) => `${m.field}: ${m.question}`);
  if (d.modules.length && (d.modules.length < WEEKS_MIN || d.modules.length > WEEKS_MAX)) errs.push(`weeks must be between ${WEEKS_MIN} and ${WEEKS_MAX}`);
  if (d.outputPath) relativePath(d.outputPath, errs);
  return errs;
}

/** The draft and what is missing, put into the system prompt every model call so the model never spends a call reading state. */
export function draftContext(d: Draft): string {
  const { llmModels: _m, device: _d, batchSize: _b, imageSize: _i, maxSamples: _s, seed: _e, resources: _r, ...shown } = d;
  return JSON.stringify({ draft: { ...shown, weeks: d.modules.length }, missing: missingFields(d) });
}

const CODING_PHRASE: Record<string, string> = {
  none: 'no prior coding experience',
  some: 'some coding experience',
  comfortable: 'comfortable with Python',
};

/** target_level as the pipeline sees it: every Phase 2 prompt reads it (CurriculumConfig.level), so the coding level goes in here. */
export const pipelineLevel = (d: Draft): string =>
  d.codingExperience ? `${d.targetLevel.trim()} (${CODING_PHRASE[d.codingExperience]})` : d.targetLevel.trim();

/** The YAML the run uses; the review card's preview and the submit both go through this. */
export const draftYaml = (d: Draft): string => generateCurriculumYaml({ ...d, targetLevel: pipelineLevel(d) });
