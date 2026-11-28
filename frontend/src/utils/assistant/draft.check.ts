// Self-check for the assistant draft helpers: node --experimental-strip-types src/utils/assistant/draft.check.ts
import assert from 'node:assert/strict';
import { DEFAULT_DRAFT, WEEKS_MAX, WEEKS_MIN, applyPatch, editWeek, missingFields, setDataset, setWeekPlan, validateDraft } from './draft.ts';

const fields = (d: Parameters<typeof missingFields>[0]) => missingFields(d).map((m) => m.field);

// untrusted input is rejected and the draft is returned unchanged
let r = applyPatch(DEFAULT_DRAFT, { datasetPath: '/data/x' });
assert.ok(!r.ok && r.draft === DEFAULT_DRAFT && r.errors[0].includes('datasetPath can only be set'));
r = applyPatch(DEFAULT_DRAFT, { domain: 'Biology', bogus: 1 });
assert.ok(!r.ok && r.errors.some((e) => e.includes('bogus')));
assert.ok(!applyPatch(DEFAULT_DRAFT, { weeks: WEEKS_MAX + 1 }).ok);
assert.ok(!applyPatch(DEFAULT_DRAFT, { weeks: WEEKS_MIN - 1 }).ok);
assert.ok(!applyPatch(DEFAULT_DRAFT, { weeks: 6.5 }).ok);
assert.ok(!applyPatch(DEFAULT_DRAFT, { outputPath: '../out' }).ok);
assert.ok(!applyPatch(DEFAULT_DRAFT, { domain: '   ' }).ok);
assert.ok(!applyPatch(DEFAULT_DRAFT, 'domain').ok);

// weeks resizes modules; changes list only what changed
r = applyPatch(DEFAULT_DRAFT, { weeks: 6, domain: '  Biology ' });
assert.ok(r.ok && r.draft.modules.length === 6 && r.draft.modules[5].week === 6 && r.draft.domain === 'Biology');
assert.deepEqual(r.changes.map((c) => c.field), ['weeks', 'domain']);
assert.equal(applyPatch(r.draft, { weeks: 4 }).draft.modules.length, 4);
assert.deepEqual(applyPatch(r.draft, { domain: 'Biology' }).changes, []);

// missingFields order
assert.deepEqual(fields(DEFAULT_DRAFT), ['domain', 'contextStatement', 'targetLevel', 'weeks', 'datasetPath', 'subject', 'classificationTask', 'segmentationPrompt', 'outputPath']);

// weeks set but plan unwritten: one 'modules' item, right after weeks and before the dataset
const sized = applyPatch(DEFAULT_DRAFT, { weeks: 6 }).draft;
assert.deepEqual(fields(sized), ['domain', 'contextStatement', 'targetLevel', 'modules', 'datasetPath', 'subject', 'classificationTask', 'segmentationPrompt', 'outputPath']);
// a partly written plan reports the blank weeks individually
const partial = editWeek(sized, 1, { title: 'Intro', context: 'c', learning_outcomes: ['o'] }).draft;
assert.deepEqual(fields(partial).slice(3, 6), ['week 2.title', 'week 2.context', 'week 2.learning_outcomes']);

// a week plan: unique ids, week numbers from index
const mod = (title: string) => ({ title, context: 'c', difficulty: 'Beginner', learning_outcomes: ['o'] });
const plan = setWeekPlan(DEFAULT_DRAFT, [mod('Intro'), mod('Intro'), mod('Data & Models'), mod('Intro')]);
assert.ok(plan.ok);
assert.deepEqual(plan.draft.modules.map((m) => m.id), ['intro', 'intro_2', 'data_models', 'intro_3']);
assert.deepEqual(plan.draft.modules.map((m) => m.week), [1, 2, 3, 4]);
assert.ok(!setWeekPlan(DEFAULT_DRAFT, [mod('a')]).ok);
assert.ok(!setWeekPlan(DEFAULT_DRAFT, plan.draft.modules.map(() => ({ ...mod('x'), difficulty: 'Hard' }))).ok);

// a fully filled draft has nothing missing and validates
let d = applyPatch(plan.draft, {
  domain: 'Biology', contextStatement: 'Leaf disease', targetLevel: 'Grade 9', subject: 'Plant health',
  classificationTask: 'healthy vs diseased', segmentationPrompt: 'leaf', outputPath: 'output/run1',
}).draft;
assert.deepEqual(fields(d), ['datasetPath']);
d = setDataset(d, '/data/leaves');
assert.deepEqual(missingFields(d), []);
assert.deepEqual(validateDraft(d), []);

// editWeek validates, changes only the given fields, and keeps the id
assert.ok(!editWeek(d, 2, { title: 'Models', learning_outcomes: [] }).ok);
const e = editWeek(d, 2, { title: 'Models' });
assert.ok(e.ok && e.draft.modules[1].title === 'Models' && e.draft.modules[1].id === 'intro_2' && e.changes.length === 1);
assert.ok(!editWeek(d, 9, { title: 'x' }).ok);
assert.deepEqual(fields({ ...d, modules: [...d.modules.slice(0, 3), { ...d.modules[3], week: 3 }] }), ['modules']);
console.log('draft.check ok');
