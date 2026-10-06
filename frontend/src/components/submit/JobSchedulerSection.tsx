import React from 'react';

interface JobSchedulerSectionProps {
  resourceAllocation: string;
  onChangeResourceAllocation: (val: string) => void;
  gpuRequest: string;
  onChangeGpuRequest: (val: string) => void;
  execSystemId: string;
  onChangeExecSystemId: (val: string) => void;
  logicalQueue: string;
  onChangeLogicalQueue: (val: string) => void;
}

export const JobSchedulerSection: React.FC<JobSchedulerSectionProps> = ({
  resourceAllocation,
  onChangeResourceAllocation,
  gpuRequest,
  onChangeGpuRequest,
  execSystemId,
  onChangeExecSystemId,
  logicalQueue,
  onChangeLogicalQueue,
}) => {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
        3. Slurm Scheduler & Billing Allocation
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">
            <span>Project Allocation ID (resource-allocation)</span>
          </label>
          <input
            type="text"
            value={resourceAllocation}
            onChange={(e) => onChangeResourceAllocation(e.target.value)}
            placeholder="-A uot260"
          />
          <div className="form-helper">SDSC Expanse scheduler project account charge flag</div>
        </div>

        <div className="form-group">
          <label className="form-label">
            <span>GPU Request (gpu-request)</span>
          </label>
          <input
            type="text"
            value={gpuRequest}
            onChange={(e) => onChangeGpuRequest(e.target.value)}
            placeholder="--gpus=1"
          />
          <div className="form-helper">Requested GPUs per compute allocation</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">
            <span>Execution System</span>
          </label>
          <input
            type="text"
            value={execSystemId}
            onChange={(e) => onChangeExecSystemId(e.target.value)}
            placeholder="expanse-tapis-static"
          />
        </div>

        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">
            <span>Logical Queue</span>
          </label>
          <input
            type="text"
            value={logicalQueue}
            onChange={(e) => onChangeLogicalQueue(e.target.value)}
            placeholder="tapisGPUshared"
          />
        </div>
      </div>
    </div>
  );
};
