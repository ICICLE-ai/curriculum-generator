// Self-check for deriveStages (no test runner in this app): node --experimental-strip-types src/utils/stages.check.ts
import assert from 'node:assert/strict';
import { deriveStages, stagePercent } from './stages.ts';
import type { PipelineStage } from '../services/tapis/types';

const stage = (id: string, phase: string, status: PipelineStage['status']): PipelineStage => ({ id, name: id, phase, status });
const defaults = [stage('ingest', 'Phase 1', 'READY'), stage('cls', 'Phase 1', 'READY'), stage('synth', 'Phase 2', 'READY')];
const statuses = (s: PipelineStage[]) => s.map((x) => x.status);

// Run 2736: Phase 2 failed. The Phase 2 process reset Phase 1 to READY; Phase 1 must still show done
assert.deepEqual(
  statuses(deriveStages([stage('ingest', 'Phase 1', 'READY'), stage('cls', 'Phase 1', 'READY'), stage('synth', 'Phase 2', 'FAILED')], defaults, 'FAILED')),
  ['COMPLETED', 'COMPLETED', 'FAILED']
);
// Run 8432: timed out while Phase 2 was running
assert.deepEqual(
  statuses(deriveStages([stage('ingest', 'Phase 1', 'COMPLETED'), stage('cls', 'Phase 1', 'COMPLETED'), stage('synth', 'Phase 2', 'IN_PROGRESS')], defaults, 'FAILED')),
  ['COMPLETED', 'COMPLETED', 'FAILED']
);
// Run 2955: finished, but the Phase 2 tracker only ticked its own stage
const finished = deriveStages([stage('ingest', 'Phase 1', 'READY'), stage('cls', 'Phase 1', 'READY'), stage('synth', 'Phase 2', 'COMPLETED')], defaults, 'FINISHED');
assert.deepEqual(statuses(finished), ['COMPLETED', 'COMPLETED', 'COMPLETED']);
assert.equal(stagePercent(finished), 100);
// Phase 1 failed: Phase 2 never started, so nothing is inferred
assert.deepEqual(
  statuses(deriveStages([stage('ingest', 'Phase 1', 'COMPLETED'), stage('cls', 'Phase 1', 'FAILED'), stage('synth', 'Phase 2', 'READY')], defaults, 'FAILED')),
  ['COMPLETED', 'FAILED', 'READY']
);
// No progress.json on a failed job: unknown, so not started, never all failed
assert.deepEqual(statuses(deriveStages(undefined, defaults, 'FAILED')), ['READY', 'READY', 'READY']);
assert.deepEqual(statuses(deriveStages([], defaults, 'RUNNING')), ['IN_PROGRESS', 'READY', 'READY']);
console.log('stages.check: all passed');
