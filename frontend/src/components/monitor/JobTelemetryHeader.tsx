import React from 'react';
import type { TapisJob } from '../../services/tapis';
import { KeyValue, StatusBadge } from '../ui';

interface JobTelemetryHeaderProps {
  macroStatus: string;
  selectedJobId: string;
  activeJobDetails: TapisJob | null;
  progressPercent: number;
  elapsedTime: string;
  lastHeartbeat?: string;
  isActive: boolean;
}

/** The selected job: name and status, then its facts. Progress and last update only while it is active. */
export const JobTelemetryHeader: React.FC<JobTelemetryHeaderProps> = ({
  macroStatus,
  selectedJobId,
  activeJobDetails: job,
  progressPercent,
  elapsedTime,
  lastHeartbeat,
  isActive,
}) => {
  const resources =
    job?.nodeCount && job?.coresPerNode
      ? `${job.nodeCount} node · ${job.coresPerNode} cores${job.memoryMB ? ` · ${Math.round(job.memoryMB / 1024)} GB` : ''}`
      : undefined;
  return (
    <section className="card">
      <div className="card-header card-header-start">
        <div>
          <h2 className="section-title">{job?.name || 'Loading job…'}</h2>
          <p className="muted mono">{selectedJobId}</p>
        </div>
        <StatusBadge status={macroStatus} />
      </div>
      <KeyValue
        items={[
          { label: 'App', value: job ? `${job.appId}${job.appVersion ? ` ${job.appVersion}` : ''}` : undefined, mono: true },
          { label: 'System', value: job?.execSystemId, mono: true },
          { label: 'Resources', value: resources },
          { label: 'Submitted', value: job?.created ? new Date(job.created).toLocaleString() : undefined },
          { label: job?.ended ? 'Total time' : 'Elapsed', value: elapsedTime },
          ...(isActive
            ? [
                { label: 'Progress', value: `${progressPercent}%` },
                { label: 'Last update', value: lastHeartbeat ? new Date(lastHeartbeat).toLocaleTimeString() : 'Waiting for the first update' },
              ]
            : []),
        ]}
      />
    </section>
  );
};
