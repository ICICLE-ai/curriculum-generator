import React from 'react';
import type { Card, CurriculumAgent } from '../../utils/assistant/types';
import { UploadCard } from './UploadCard';
import { DatasetPickerCard } from './DatasetPickerCard';
import { ChangesCard } from './ChangesCard';
import { WeekPlanCard } from './WeekPlanCard';
import { ReviewCard } from './ReviewCard';
import { JobCard } from './JobCard';
import { FailureCard } from './FailureCard';
import { RerunCard } from './RerunCard';
import { ArtifactsCard } from './ArtifactsCard';
import { SignInCard } from './SignInCard';
import { HfDatasetsCard } from './HfDatasetsCard';
import { DatasetPlanCard } from './DatasetPlanCard';

export const AssistantCard: React.FC<{ card: Card; agent: CurriculumAgent }> = ({ card, agent }) => {
  switch (card.kind) {
    case 'upload': return <UploadCard agent={agent} />;
    case 'dataset_picker': return <DatasetPickerCard agent={agent} />;
    case 'changes': return <ChangesCard changes={card.changes} />;
    case 'week_plan': return <WeekPlanCard agent={agent} />;
    case 'review': return <ReviewCard agent={agent} />;
    case 'job': return <JobCard agent={agent} jobUuid={card.jobUuid} />;
    case 'failure': return <FailureCard agent={agent} jobUuid={card.jobUuid} failures={card.failures} />;
    case 'rerun': return <RerunCard agent={agent} jobUuid={card.jobUuid} weeks={card.weeks} />;
    case 'artifacts': return <ArtifactsCard jobUuid={card.jobUuid} />;
    case 'sign_in': return <SignInCard />;
    case 'hf_datasets': return <HfDatasetsCard agent={agent} candidates={card.candidates} />;
    case 'dataset_plan': return <DatasetPlanCard agent={agent} />;
  }
};
