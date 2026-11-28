import React from 'react';
import { PipelineProgressCard } from '../monitor';
import { StatusBadge } from '../ui';
import { deriveStages, stagePercent } from '../../utils/stages';
import type { PipelineStage } from '../../services/tapis';
import type { CurriculumAgent } from '../../utils/assistant/types';
import { TERMINAL, useJob } from './session';

const STAGE = (id: string, name: string, phase: string): PipelineStage => ({ id, name, phase, status: 'READY', details: '' });
const DEFAULT_STAGES: PipelineStage[] = [
  STAGE('dataset_ingestion', 'Dataset Ingestion', 'Phase 1'),
  STAGE('classification', 'Classification', 'Phase 1'),
  STAGE('segmentation', 'Segmentation', 'Phase 1'),
  STAGE('curriculum_synthesis', 'Curriculum Synthesis', 'Phase 2'),
  STAGE('exercise_generation', 'Exercise Scaffolding & Validation', 'Phase 2'),
  STAGE('packaging', 'Artifact Packaging', 'Phase 2'),
];

export const JobCard: React.FC<{ agent: CurriculumAgent; jobUuid: string }> = ({ agent, jobUuid }) => {
  const run = agent.state.runs.find((r) => r.jobUuid === jobUuid);
  const { job, status, progress } = useJob(jobUuid, 30000, run?.lastStatus);
  const stages = deriveStages(progress?.stages, DEFAULT_STAGES, status);
  const active = !TERMINAL.includes(status);
  return (
    <div className="stack-sm">
      <div className="row-between">
        <strong>{job?.name || run?.name || 'Your run'}</strong>
        <StatusBadge status={status} />
      </div>
      <PipelineProgressCard
        displayedStages={stages}
        onSelectStage={() => {}}
        progressPercent={stagePercent(stages)}
        statusDescription={progress?.current_message || (active ? 'Working...' : status === 'FINISHED' ? 'All stages finished.' : `Run ${status.toLowerCase()}.`)}
        isActive={active}
      />
    </div>
  );
};
