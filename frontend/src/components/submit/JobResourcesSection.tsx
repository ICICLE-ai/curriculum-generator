import React, { useState } from 'react';

interface JobResourcesSectionProps {
  // Main visible field
  gpuCount: number;
  onChangeGpuCount: (val: number) => void;

  // Advanced Compute Specs
  nodeCount: number;
  onChangeNodeCount: (val: number) => void;
  coresPerNode: number;
  onChangeCoresPerNode: (val: number) => void;
  memoryMB: number;
  onChangeMemoryMB: (val: number) => void;
  maxMinutes: number;
  onChangeMaxMinutes: (val: number) => void;

  // Advanced Slurm & Cluster Settings
  resourceAllocation: string;
  onChangeResourceAllocation: (val: string) => void;
  execSystemId: string;
  onChangeExecSystemId: (val: string) => void;
  logicalQueue: string;
  onChangeLogicalQueue: (val: string) => void;
  bindGpu: string;
  onChangeBindGpu: (val: string) => void;
  bindExpanse: string;
  onChangeBindExpanse: (val: string) => void;
  execDir: string;
  onChangeExecDir: (val: string) => void;
  inputDir: string;
  onChangeInputDir: (val: string) => void;
  outputDir: string;
  onChangeOutputDir: (val: string) => void;
}

export const JobResourcesSection: React.FC<JobResourcesSectionProps> = ({
  gpuCount,
  onChangeGpuCount,
  nodeCount,
  onChangeNodeCount,
  coresPerNode,
  onChangeCoresPerNode,
  memoryMB,
  onChangeMemoryMB,
  maxMinutes,
  onChangeMaxMinutes,
  resourceAllocation,
  onChangeResourceAllocation,
  execSystemId,
  onChangeExecSystemId,
  logicalQueue,
  onChangeLogicalQueue,
  bindGpu,
  onChangeBindGpu,
  bindExpanse,
  onChangeBindExpanse,
  execDir,
  onChangeExecDir,
  inputDir,
  onChangeInputDir,
  outputDir,
  onChangeOutputDir,
}) => {
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
        3. Compute Resources
      </div>

      {/* Primary Simplified GPU Input */}
      <div className="form-group" style={{ marginBottom: '1rem' }}>
        <label className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 600 }}>GPUs Allocated</span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            --gpus={gpuCount}
          </span>
        </label>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="number"
            min="1"
            max="8"
            step="1"
            value={gpuCount}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              onChangeGpuCount(isNaN(val) || val < 1 ? 1 : val);
            }}
            style={{ width: '110px', fontSize: '0.9rem', fontWeight: 600 }}
          />

          {/* Quick preset buttons */}
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            {[1, 2, 4].map((count) => (
              <button
                key={count}
                type="button"
                onClick={() => onChangeGpuCount(count)}
                style={{
                  background: gpuCount === count ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${gpuCount === count ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                  color: gpuCount === count ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  padding: '0.35rem 0.65rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {count} {count === 1 ? 'GPU' : 'GPUs'}
              </button>
            ))}
          </div>
        </div>

        <div className="form-helper" style={{ marginTop: '0.35rem' }}>
          Number of compute GPUs allocated to the job. The scheduler flag <code>--gpus={gpuCount}</code> is set automatically.
        </div>
      </div>

      {/* Collapsible Advanced Compute & Cluster Settings */}
      <div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            padding: '0.3rem 0',
          }}
        >
          <span>{showAdvanced ? '▼ Hide' : '▶ Show'} Advanced Settings (Nodes, CPUs, Memory & Cluster Defaults)</span>
        </button>

        {showAdvanced && (
          <div
            style={{
              marginTop: '0.85rem',
              padding: '1.25rem',
              background: 'var(--bg-card-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            {/* Subsection A: Compute Hardware Specs */}
            <div>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.65rem', fontWeight: 600 }}>
                Compute Hardware Specs
              </div>
              <div className="grid-2">
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Node Count</label>
                  <input
                    type="number"
                    min="1"
                    value={nodeCount}
                    onChange={(e) => onChangeNodeCount(Number(e.target.value))}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Cores per Node (CPUs)</label>
                  <input
                    type="number"
                    min="1"
                    value={coresPerNode}
                    onChange={(e) => onChangeCoresPerNode(Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="grid-2" style={{ marginTop: '0.75rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Memory (MB)</label>
                  <input
                    type="number"
                    value={memoryMB}
                    onChange={(e) => onChangeMemoryMB(Number(e.target.value))}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Max Runtime (Minutes)</label>
                  <input
                    type="number"
                    value={maxMinutes}
                    onChange={(e) => onChangeMaxMinutes(Number(e.target.value))}
                  />
                </div>
              </div>
            </div>

            {/* Subsection B: Cluster Plumbing & Slurm Queue Defaults */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.65rem', fontWeight: 600 }}>
                Slurm Scheduler & Cluster Plumbing (Auto-configured)
              </div>

              <div className="grid-2">
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Project Allocation ID</label>
                  <input
                    type="text"
                    value={resourceAllocation}
                    onChange={(e) => onChangeResourceAllocation(e.target.value)}
                    placeholder="-A uot260"
                  />
                  <div className="form-helper">Slurm scheduler account flag</div>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Logical Queue</label>
                  <input
                    type="text"
                    value={logicalQueue}
                    onChange={(e) => onChangeLogicalQueue(e.target.value)}
                    placeholder="tapisGPUshared"
                  />
                </div>
              </div>

              <div className="grid-2" style={{ marginTop: '0.75rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Execution System</label>
                  <input
                    type="text"
                    value={execSystemId}
                    onChange={(e) => onChangeExecSystemId(e.target.value)}
                    placeholder="expanse-tapis-static"
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Container Driver Bind</label>
                  <input
                    type="text"
                    value={bindGpu}
                    onChange={(e) => onChangeBindGpu(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginTop: '0.75rem', marginBottom: 0 }}>
                <label className="form-label">Cluster Scratch Storage Mount</label>
                <input
                  type="text"
                  value={bindExpanse}
                  onChange={(e) => onChangeBindExpanse(e.target.value)}
                />
              </div>
            </div>

            {/* Subsection C: Execution Directory Specs */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.65rem', fontWeight: 600 }}>
                Execution Directory Specs
              </div>

              <div className="grid-3">
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Exec Directory</label>
                  <input
                    type="text"
                    value={execDir}
                    onChange={(e) => onChangeExecDir(e.target.value)}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Input Directory</label>
                  <input
                    type="text"
                    value={inputDir}
                    onChange={(e) => onChangeInputDir(e.target.value)}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Output Directory</label>
                  <input
                    type="text"
                    value={outputDir}
                    onChange={(e) => onChangeOutputDir(e.target.value)}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
