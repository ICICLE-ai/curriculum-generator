// Self-check for the failure parser: node --experimental-strip-types src/utils/assistant/failures.check.ts
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { explainFailure, parseFailures } from './failures.ts';

const log = readFileSync(new URL('./fixtures/phase2_9844da66.log', import.meta.url), 'utf8');
const f = parseFailures(log);
assert.equal(f.length, 2);
assert.deepEqual(f.map((x) => [x.week, x.module, x.kind]), [
  [1, 'python_variables_loops', 'planning'],
  [3, 'domain_food_classifier', 'connection'],
]);
assert.match(explainFailure(f[0]).advice, /reword/);
assert.match(explainFailure(f[1]).advice, /Rerunning/);

// No summary block: fall back to the per-week lines
const fb = parseFailures(
  "[Week 2] FAILED: Something odd happened (5 min) | log: ./outputs/exercises/Week_02/pandas_food_tables/pandas_food_tables_phase2.log\n[Week 2] finished (9 min)\n"
);
assert.deepEqual(fb, [{ week: 2, module: 'pandas_food_tables', kind: 'other', message: 'Something odd happened' }]);
assert.deepEqual(parseFailures('[Week 1] finished (3 min)'), []);
console.log('failures.check OK');
