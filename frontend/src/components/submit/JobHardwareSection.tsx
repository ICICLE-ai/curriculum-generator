import React, { useState } from 'react';

interface JobHardwareSectionProps {
  nodeCount: number;
  onChangeNodeCount: (val: number) => void;
  coresPerNode: number;
  onChangeCoresPerNode: (val: number) => void;
  memoryMB: number;
  onChangeMemoryMB: (val: number) => void;
  maxMinutes: number;
  onChangeMaxMinutes: (val: number) => void;
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

export const JobHardwareSection: React.FC<JobHardwareSectionProps> = ({
  nodeCount,
  onChangeNodeCount,
  coresPerNode,
  onChangeCoresPerNode,
  memoryMB,
  onChangeMemoryMB,
  maxMinutes,
  onChangeMaxMinutes,
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
          fontSize: '0.825rem',
          fontWeight: 600,
          cursor: 'pointer',
          padding: '0.2rem 0',
        }}
      >
        <span>{showAdvanced ? '▼ Hide' : '▶ Show'} Advanced Compute Specs & Container Binds</span>
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
            gap: '1rem',
          }}
        >
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
              <label className="form-label">Cores per Node</label>
              <input
                type="number"
                min="1"
                value={coresPerNode}
                onChange={(e) => onChangeCoresPerNode(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="grid-2">
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

          <div className="grid-2">
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">NVIDIA Singularity Driver Bind</label>
              <input
                type="text"
                value={bindGpu}
                onChange={(e) => onChangeBindGpu(e.target.value)}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Lustre Scratch Mount</label>
              <input
                type="text"
                value={bindExpanse}
                onChange={(e) => onChangeBindExpanse(e.target.value)}
              />
            </div>
          </div>

          <div className="grid-3">
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Exec Directory</label>
              <input
                type="text"
                value={execDir}
                onChange={(e) => onChangeExecDir(e.target.value)}
                style={{ fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Input Directory</label>
              <input
                type="text"
                value={inputDir}
                onChange={(e) => onChangeInputDir(e.target.value)}
                style={{ fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Output Directory</label>
              <input
                type="text"
                value={outputDir}
                onChange={(e) => onChangeOutputDir(e.target.value)}
                style={{ fontFamily: 'var(--font-mono)' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
