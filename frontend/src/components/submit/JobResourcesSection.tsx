import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface JobResourcesSectionProps {
  gpuCount: number;
  onChangeGpuCount: (val: number) => void;
  nodeCount: number;
  onChangeNodeCount: (val: number) => void;
  coresPerNode: number;
  onChangeCoresPerNode: (val: number) => void;
  memoryMB: number;
  onChangeMemoryMB: (val: number) => void;
  maxMinutes: number;
  onChangeMaxMinutes: (val: number) => void;
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
  scratchCacheDir: string;
  onChangeScratchCacheDir: (val: string) => void;
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
  scratchCacheDir,
  onChangeScratchCacheDir,
  execDir,
  onChangeExecDir,
  inputDir,
  onChangeInputDir,
  outputDir,
  onChangeOutputDir,
}) => {
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  return (
    <div className="stack">
      <div className="section-title">Compute Resources</div>

      <div className="grid-2">
        <div className="form-group">
          <label htmlFor="submit-allocation" className="form-label">
            Project Allocation
          </label>
          <input
            id="submit-allocation"
            type="text"
            className="mono"
            value={resourceAllocation}
            onChange={(e) => onChangeResourceAllocation(e.target.value)}
            placeholder="-A uot260"
          />
          <div className="form-helper">Slurm project account flag (e.g. <code>-A uot260</code>).</div>
        </div>

        <div className="form-group">
          <label htmlFor="submit-gpu-count" className="form-label">
            <span>GPUs</span>
            <span className="muted mono">{gpuCount > 0 ? `--gpus=${gpuCount}` : 'CPU only'}</span>
          </label>
          <div className="row">
            <input
              id="submit-gpu-count"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              className="input-compact"
              value={String(gpuCount)}
              placeholder="1"
              onChange={(e) => {
                const clean = e.target.value.replace(/\D/g, '');
                onChangeGpuCount(clean === '' ? 0 : parseInt(clean, 10));
              }}
            />
            {[0, 1, 2, 4].map((count) => (
              <button
                key={count}
                type="button"
                onClick={() => onChangeGpuCount(count)}
                className={`pill ${gpuCount === count ? 'is-selected' : ''}`}
              >
                {count === 0 ? '0 (CPU)' : `${count} ${count === 1 ? 'GPU' : 'GPUs'}`}
              </button>
            ))}
          </div>
          <div className="form-helper">1 GPU is enough for Phase 1; use 0 (CPU) for Content Bank / Phase 2-only runs.</div>
        </div>
      </div>

      <div>
        <button
          type="button"
          className="disclosure-btn"
          onClick={() => setShowAdvanced(!showAdvanced)}
          aria-expanded={showAdvanced}
        >
          {showAdvanced ? <ChevronDown size={15} aria-hidden="true" /> : <ChevronRight size={15} aria-hidden="true" />}
          <span>Advanced settings (nodes, CPUs, memory, cache, directories)</span>
        </button>

        {showAdvanced && (
          <div className="inset-panel stack" style={{ marginTop: 'var(--space-3)' }}>
            <div>
              <div className="section-heading-xs">Compute Specs</div>
              <div className="grid-2">
                <div className="form-group">
                  <label htmlFor="adv-nodes" className="form-label">Nodes</label>
                  <input
                    id="adv-nodes"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={nodeCount === 0 ? '' : nodeCount}
                    placeholder="1"
                    onChange={(e) => {
                      const clean = e.target.value.replace(/\D/g, '');
                      onChangeNodeCount(clean === '' ? 0 : parseInt(clean, 10));
                    }}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-cores" className="form-label">Cores per Node</label>
                  <input
                    id="adv-cores"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={coresPerNode === 0 ? '' : coresPerNode}
                    placeholder="12"
                    onChange={(e) => {
                      const clean = e.target.value.replace(/\D/g, '');
                      onChangeCoresPerNode(clean === '' ? 0 : parseInt(clean, 10));
                    }}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-mem" className="form-label">Memory (MB)</label>
                  <input
                    id="adv-mem"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={memoryMB === 0 ? '' : memoryMB}
                    placeholder="64000"
                    onChange={(e) => {
                      const clean = e.target.value.replace(/\D/g, '');
                      onChangeMemoryMB(clean === '' ? 0 : parseInt(clean, 10));
                    }}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-minutes" className="form-label">Max Runtime (Minutes)</label>
                  <input
                    id="adv-minutes"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={maxMinutes === 0 ? '' : maxMinutes}
                    placeholder="480"
                    onChange={(e) => {
                      const clean = e.target.value.replace(/\D/g, '');
                      onChangeMaxMinutes(clean === '' ? 0 : parseInt(clean, 10));
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="divider-top">
              <div className="section-heading-xs">Cluster &amp; Cache</div>
              <div className="grid-2">
                <div className="form-group">
                  <label htmlFor="adv-queue" className="form-label">Queue</label>
                  <input
                    id="adv-queue"
                    type="text"
                    value={logicalQueue}
                    onChange={(e) => onChangeLogicalQueue(e.target.value)}
                    placeholder="tapisGPUshared"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-system" className="form-label">Execution System</label>
                  <input
                    id="adv-system"
                    type="text"
                    value={execSystemId}
                    onChange={(e) => onChangeExecSystemId(e.target.value)}
                    placeholder="expanse-tapis-static"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-bind-gpu" className="form-label">GPU Bind Flag</label>
                  <input
                    id="adv-bind-gpu"
                    type="text"
                    className="mono"
                    value={bindGpu}
                    onChange={(e) => onChangeBindGpu(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-bind-scratch" className="form-label">Scratch Mount</label>
                  <input
                    id="adv-bind-scratch"
                    type="text"
                    className="mono"
                    value={bindExpanse}
                    onChange={(e) => onChangeBindExpanse(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginTop: 'var(--space-3)' }}>
                <label htmlFor="adv-cache" className="form-label">Cache Directory</label>
                <input
                  id="adv-cache"
                  type="text"
                  className="mono"
                  value={scratchCacheDir}
                  onChange={(e) => onChangeScratchCacheDir(e.target.value)}
                  placeholder="/expanse/lustre/scratch/harvest/temp_project/.cache"
                />
                <div className="form-helper">
                  Redirects Singularity, Hugging Face, Triton, Matplotlib, and W&amp;B caches to scratch storage instead of <code>$HOME</code>.
                </div>
              </div>
            </div>

            <div className="divider-top">
              <div className="section-heading-xs">Job Directories</div>
              <div className="grid-3">
                <div className="form-group">
                  <label htmlFor="adv-exec-dir" className="form-label">Exec Directory</label>
                  <input
                    id="adv-exec-dir"
                    type="text"
                    className="mono"
                    value={execDir}
                    onChange={(e) => onChangeExecDir(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-in-dir" className="form-label">Input Directory</label>
                  <input
                    id="adv-in-dir"
                    type="text"
                    className="mono"
                    value={inputDir}
                    onChange={(e) => onChangeInputDir(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="adv-out-dir" className="form-label">Output Directory</label>
                  <input
                    id="adv-out-dir"
                    type="text"
                    className="mono"
                    value={outputDir}
                    onChange={(e) => onChangeOutputDir(e.target.value)}
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
