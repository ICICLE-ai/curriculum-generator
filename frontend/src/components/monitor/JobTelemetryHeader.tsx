import React from 'react';
import type { TapisJob } from '../../utils/tapisJobs';

interface JobTelemetryHeaderProps {
  macroStatus: string;
  selectedJobId: string;
  activeJobDetails: TapisJob | null;
  progressPercent: number;
  elapsedTime: string;
  lastHeartbeat?: string;
}

export const JobTelemetryHeader: React.FC<JobTelemetryHeaderProps> = ({
  macroStatus,
  selectedJobId,
  activeJobDetails,
  progressPercent,
  elapsedTime,
  lastHeartbeat,
}) => {
  const getStatusBadgeStyle = () => {
    switch (macroStatus) {
      case 'FINISHED':
        return {
          background: 'var(--accent-emerald-subtle)',
          color: 'var(--accent-emerald)',
        };
      case 'RUNNING':
        return {
          background: 'var(--accent-primary-subtle)',
          color: 'var(--accent-primary)',
        };
      case 'FAILED':
        return {
          background: 'var(--accent-rose-subtle)',
          color: 'var(--accent-rose)',
        };
      default:
        return {
          background: 'var(--bg-card-subtle)',
          color: 'var(--text-secondary)',
        };
    }
  };

  const badgeStyle = getStatusBadgeStyle();

  return (
    <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
      {/* Card 1: Status & IDs */}
      <div className="card" style={{ marginBottom: 0 }}>
        <div className="meta-item">
          <span className="meta-key">Tapis Status</span>
          <span className="status-badge" style={badgeStyle}>
            <span className="status-dot" />
            {macroStatus}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-key">Job UUID</span>
          <span className="meta-val" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
            {selectedJobId || 'None'}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-key">App ID</span>
          <span className="meta-val">{activeJobDetails?.appId || 'digital-age-edu-test'}</span>
        </div>
      </div>

      {/* Card 2: Cluster Specs */}
      <div className="card" style={{ marginBottom: 0 }}>
        <div className="meta-item">
          <span className="meta-key">Execution System</span>
          <span className="meta-val">{activeJobDetails?.execSystemId || 'OSC / TACC Cluster'}</span>
        </div>
        <div className="meta-item">
          <span className="meta-key">Nodes / Cores</span>
          <span className="meta-val">
            {activeJobDetails?.nodeCount ?? 1} Node / {activeJobDetails?.coresPerNode ?? 12} Cores
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-key">Memory Allocated</span>
          <span className="meta-val">
            {activeJobDetails?.memoryMB ? `${Math.round(activeJobDetails.memoryMB / 1024)} GB` : '64 GB'}
          </span>
        </div>
      </div>

      {/* Card 3: Metrics & Time */}
      <div className="card" style={{ marginBottom: 0 }}>
        <div className="meta-item">
          <span className="meta-key">Overall Progress</span>
          <span className="meta-val" style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
            {progressPercent}%
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-key">Elapsed Time</span>
          <span className="meta-val">{elapsedTime}</span>
        </div>
        <div className="meta-item">
          <span className="meta-key">Last Heartbeat</span>
          <span className="meta-val" style={{ fontSize: '0.78rem' }}>
            {lastHeartbeat
              ? new Date(lastHeartbeat).toLocaleTimeString()
              : macroStatus === 'RUNNING'
              ? 'Active (Polling)'
              : 'Awaiting start'}
          </span>
        </div>
      </div>
    </div>
  );
};
