import React from 'react';
import { JobArtifactsCard } from '../monitor';
import { downloadJobArtifact } from '../../services/tapis';
import { useJob } from './session';

export const ArtifactsCard: React.FC<{ jobUuid: string }> = ({ jobUuid }) => {
  const { token, job, status } = useJob(jobUuid);
  return (
    <JobArtifactsCard
      macroStatus={status}
      job={job}
      token={token}
      onDownloadArtifact={(name) =>
        downloadJobArtifact(token!, jobUuid, name, job).catch((e) => alert(`Could not download ${name}: ${e instanceof Error ? e.message : 'File not available'}`))
      }
    />
  );
};
