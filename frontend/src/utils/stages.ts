import type { PipelineStage } from '../services/tapis/types';

const TERMINAL = ['FINISHED', 'FAILED', 'CANCELLED'];

/**
 * The stages to show for a job, made consistent with what actually happened:
 * - Phase 2 runs as its own process with a fresh progress tracker, which resets the Phase 1 stages to READY;
 *   Phase 2 only starts after Phase 1 succeeded, so once any Phase 2 stage has started, Phase 1 is done.
 * - In a finished job every stage ran; in an ended job a stage still marked running stopped there.
 * - Without progress.json the stages are unknown, so a failed job shows them not started, never all failed.
 */
export function deriveStages(progressStages: PipelineStage[] | undefined, defaults: PipelineStage[], macroStatus: string): PipelineStage[] {
  const ended = TERMINAL.includes(macroStatus);
  if (!progressStages?.length) {
    return defaults.map((s, i) => {
      if (macroStatus === 'FINISHED') return { ...s, status: 'COMPLETED' };
      if (macroStatus === 'RUNNING' && i === 0) return { ...s, status: 'IN_PROGRESS', details: 'Running on the cluster' };
      return s;
    });
  }
  const phase2Started = progressStages.some((s) => s.phase === 'Phase 2' && s.status !== 'READY' && s.status !== 'SKIPPED');
  return progressStages.map((s) => {
    if (s.status === 'READY' && (macroStatus === 'FINISHED' || (phase2Started && s.phase === 'Phase 1'))) {
      return { ...s, status: 'COMPLETED' };
    }
    if (ended && s.status === 'IN_PROGRESS') return { ...s, status: macroStatus === 'FINISHED' ? 'COMPLETED' : 'FAILED' };
    return s;
  });
}

/** Share of non-skipped stages that are done, 0-100. */
export function stagePercent(stages: PipelineStage[]): number {
  const counted = stages.filter((s) => s.status !== 'SKIPPED');
  return counted.length ? Math.round((100 * counted.filter((s) => s.status === 'COMPLETED').length) / counted.length) : 0;
}
