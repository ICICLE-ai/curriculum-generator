// Self-check for validateDatasetPlan (no test runner in this app): node --experimental-strip-types src/utils/assistant/datasetPlan.check.ts
import assert from 'node:assert/strict';
import { describePlan, validateDatasetPlan } from './datasetPlan.ts';
import type { DatasetPlan, HfDatasetInfo } from './types.ts';

const info: HfDatasetInfo = {
  id: 'o/leaves',
  revision: 'abc',
  gated: false,
  downloads: 1,
  layout: 'parquet',
  config: 'default',
  configs: ['default'],
  dataFiles: { train: ['data/train-*'] },
  splits: ['train'],
  imageColumns: ['image'],
  labelColumns: { label: ['Downey mildew', 'Downy mildew', 'Fresh leaf', 'Odd'] },
  classCounts: { label: { 'Downey mildew': 100, 'Downy mildew': 50, 'Fresh leaf': 900, Odd: 5 } },
  samples: [],
};
const good: DatasetPlan = {
  repo: 'o/leaves',
  revision: 'abc',
  layout: 'parquet',
  config: 'default',
  data_files: ['data/train-*'],
  splits: ['train'],
  image_column: 'image',
  label_column: 'label',
  class_map: { 'Downey mildew': 'downy_mildew', 'Downy mildew': 'downy_mildew', 'Fresh leaf': 'healthy', Odd: null },
  max_per_class: 500,
  name: 'leaves',
};
const bad = (patch: Record<string, unknown>) => validateDatasetPlan({ ...good, ...patch }, info);

assert.deepEqual(validateDatasetPlan(good, info).plan, good);
assert.ok(validateDatasetPlan({ ...good, extra: 1 }, info).ok);
assert.equal('extra' in (validateDatasetPlan({ ...good, extra: 1 }, info).plan ?? {}), false);
assert.equal(validateDatasetPlan('x', info).ok, false);
assert.equal(bad({ repo: 'other/x' }).ok, false);
assert.equal(bad({ revision: 'main' }).ok, false);
assert.equal(bad({ layout: 'imagefolder' }).ok, false);
assert.equal(bad({ splits: ['test'] }).ok, false);
assert.equal(bad({ splits: [] }).ok, false);
assert.equal(bad({ config: 'raw' }).ok, false);
assert.equal(bad({ data_files: ['other/*'] }).ok, false);
assert.equal(bad({ data_files: ['data/train-*', '../x'] }).ok, false);
assert.equal(bad({ data_files: [] }).ok, false);
assert.equal(bad({ image_column: 'img' }).ok, false);
assert.equal(bad({ label_column: 'plant_type' }).ok, false);
assert.equal(bad({ class_map: { ...good.class_map, Extra: 'x' } }).ok, false); // unknown label
assert.equal(bad({ class_map: { 'Downey mildew': 'a', 'Fresh leaf': 'b', Odd: null } }).ok, false); // missing label
assert.equal(bad({ class_map: { ...good.class_map, 'Fresh leaf': '../evil' } }).ok, false);
assert.equal(bad({ class_map: { ...good.class_map, 'Fresh leaf': 'Healthy' } }).ok, false);
assert.equal(bad({ class_map: { ...good.class_map, 'Fresh leaf': 'downy_mildew' } }).ok, false); // only 1 folder left
assert.equal(bad({ name: 'Has Space' }).ok, false);
assert.equal(bad({ name: 'a'.repeat(61) }).ok, false);
assert.equal(bad({ max_per_class: 19 }).ok, false);
assert.equal(bad({ max_per_class: 5001 }).ok, false);
assert.equal(bad({ max_per_class: 100.5 }).ok, false);
assert.equal(validateDatasetPlan(good, { ...info, layout: 'unsupported' }).ok, false);

// imagefolder: label column and image column are ""
const folder: HfDatasetInfo = { ...info, layout: 'imagefolder', labelColumns: { '': ['a', 'b'] }, classCounts: undefined };
const fp: DatasetPlan = { ...good, layout: 'imagefolder', image_column: '', label_column: '', class_map: { a: 'a', b: 'b' } };
assert.ok(validateDatasetPlan(fp, folder).ok);
assert.equal(validateDatasetPlan({ ...fp, image_column: 'image' }, folder).ok, false);

const lines = describePlan(good, info);
assert.equal(lines[0], '4 labels become 2 folders.');
assert.ok(lines.some((l) => l.includes('Downey mildew and Downy mildew are merged into downy_mildew')));
assert.ok(lines.some((l) => l.includes('Odd is dropped')));
assert.ok(lines.some((l) => l.includes('150 images in downy_mildew') && l.includes('500 images in healthy')));
console.log('datasetPlan.check.ts: ok');
