import React, { useState } from 'react';

export const MonitorPage: React.FC = () => {
  const [isRunning] = useState<boolean>(false);

  const stages = [
    { name: 'DINOv2 Classification', phase: 'Phase 1', status: 'completed', duration: '12m 30s' },
    { name: 'SAM Image Segmentation', phase: 'Phase 1', status: 'completed', duration: '18m 45s' },
    { name: 'Visual XAI & Attention Maps', phase: 'Phase 1', status: 'completed', duration: '8m 10s' },
    { name: 'Visual Feature & Metric Ingestion', phase: 'Phase 1', status: 'completed', duration: '5m 15s' },
    { name: 'Agent 0: Problem Formulation', phase: 'Phase 2', status: 'active', duration: 'Synthesizing...' },
    { name: 'Agent 1: PyTorch Reference Code', phase: 'Phase 2', status: 'pending', duration: 'Queued' },
    { name: 'Agent 2: Adversarial QA Testing', phase: 'Phase 2', status: 'pending', duration: 'Queued' },
  ];

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="page-title">Live Pipeline & Job Monitor</h1>
          <p className="page-description" style={{ marginBottom: 0 }}>
            Real-time pipeline telemetry, GPU memory metrics, and WebSocket execution logs.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="button" className="btn btn-primary" disabled={isRunning}>
            Run Full Pipeline
          </button>
        </div>
      </div>

      {/* GPU & Resource Gauges */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="meta-item">
            <span className="meta-key">GPU Assigned</span>
            <span className="meta-val">NVIDIA A100 (40GB)</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">VRAM Utilization</span>
            <span className="meta-val" style={{ color: 'var(--accent-emerald)' }}>35.54 GiB / 39.49 GiB (90%)</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">vLLM Inference Engine</span>
            <span className="meta-val">Port 8000 (Active)</span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="meta-item">
            <span className="meta-key">Job ID (Tapis)</span>
            <span className="meta-val">tapis-job-8942a</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Execution Host</span>
            <span className="meta-val">stampede3.tacc.utexas.edu</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Reverse Port</span>
            <span className="meta-val">60098 ➔ 8000</span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="meta-item">
            <span className="meta-key">ICICLE Vector DB</span>
            <span className="meta-val" style={{ color: 'var(--accent-emerald)' }}>Connected (4,409 vectors)</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">RAG Retrieval Mode</span>
            <span className="meta-val">Dense + Cross-Encoder</span>
          </div>
          <div className="meta-item">
            <span className="meta-key">Total Generated Slides</span>
            <span className="meta-val">12 Widescreen Decks</span>
          </div>
        </div>
      </div>

      {/* Pipeline Stage Progression */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: '1rem' }}>Pipeline Stage Progression</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {stages.map((stg) => (
            <div
              key={stg.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-card-subtle)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.2rem 0.5rem',
                    borderRadius: 'var(--radius-sm)',
                    background: stg.phase === 'Phase 1' ? 'var(--accent-primary-subtle)' : 'var(--accent-amber-subtle)',
                    color: stg.phase === 'Phase 1' ? 'var(--accent-primary)' : 'var(--accent-amber)',
                  }}
                >
                  {stg.phase}
                </span>
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{stg.name}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{stg.duration}</span>
                <span
                  className="status-badge"
                  style={{
                    background:
                      stg.status === 'completed'
                        ? 'var(--accent-emerald-subtle)'
                        : stg.status === 'active'
                        ? 'var(--accent-primary-subtle)'
                        : 'var(--bg-card)',
                    color:
                      stg.status === 'completed'
                        ? 'var(--accent-emerald)'
                        : stg.status === 'active'
                        ? 'var(--accent-primary)'
                        : 'var(--text-muted)',
                  }}
                >
                  <span className="status-dot" />
                  {stg.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
