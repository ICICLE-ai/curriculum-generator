import React, { useState } from 'react';

export const PlaygroundPage: React.FC = () => {
  const [activeModel, setActiveModel] = useState<'sam' | 'dinov2'>('sam');
  const [pointMode, setPointMode] = useState<'positive' | 'negative'>('positive');
  const [points, setPoints] = useState<Array<{ x: number; y: number; type: 'positive' | 'negative' }>>([]);
  const [maskOpacity, setMaskOpacity] = useState<number>(65);

  const sampleImages = [
    { name: 'Wheat and Weed Field (Crop 01)', path: 'sample_crop_01.jpg' },
    { name: 'Corn Leaf Disease (Crop 02)', path: 'sample_corn_02.jpg' },
    { name: 'ISIC Melanoma Lesion (Derm 01)', path: 'sample_skin_01.jpg' },
  ];
  const [selectedImage, setSelectedImage] = useState<string>(sampleImages[0].name);

  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 100);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 100);
    setPoints([...points, { x, y, type: pointMode }]);
  };

  const handleClearPoints = () => {
    setPoints([]);
  };

  return (
    <div className="page-container">
      <h1 className="page-title">Visual AI Interactive Playground</h1>
      <p className="page-description">
        Test foundation vision models interactively on agricultural and medical imaging samples directly from the compute node.
      </p>

      {/* Model Selector Bar */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button
          type="button"
          className={`btn ${activeModel === 'sam' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveModel('sam')}
        >
          SAM Segmentation (Segment Anything)
        </button>
        <button
          type="button"
          className={`btn ${activeModel === 'dinov2' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveModel('dinov2')}
        >
          DINOv2 + Grad-CAM XAI
        </button>
      </div>

      <div className="grid-2">
        {/* Interactive Canvas Area */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Interactive Vision Canvas</h2>
              <p className="card-subtitle">Click on image to add foreground/background prompt points</p>
            </div>
            {activeModel === 'sam' && (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${pointMode === 'positive' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPointMode('positive')}
                  style={{ background: pointMode === 'positive' ? 'var(--accent-emerald)' : undefined }}
                >
                  + Foreground Point
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${pointMode === 'negative' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPointMode('negative')}
                  style={{ background: pointMode === 'negative' ? 'var(--accent-rose)' : undefined }}
                >
                  - Background Point
                </button>
              </div>
            )}
          </div>

          {/* Interactive Image Frame */}
          <div
            onClick={handleCanvasClick}
            style={{
              position: 'relative',
              width: '100%',
              height: '380px',
              background: 'radial-gradient(circle at center, hsl(158, 40%, 15%), hsl(222, 47%, 10%))',
              borderRadius: 'var(--radius-md)',
              border: '2px dashed var(--border-strong)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'crosshair',
              overflow: 'hidden',
            }}
          >
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', userSelect: 'none' }}>
              <p style={{ fontWeight: 600 }}>{selectedImage}</p>
              <p style={{ fontSize: '0.8rem' }}>Click anywhere on this canvas to set SAM prompt points</p>
            </div>

            {/* Render Prompt Points */}
            {points.map((pt, idx) => (
              <div
                key={idx}
                style={{
                  position: 'absolute',
                  left: `${pt.x}%`,
                  top: `${pt.y}%`,
                  transform: 'translate(-50%, -50%)',
                  width: '14px',
                  height: '14px',
                  borderRadius: '50%',
                  background: pt.type === 'positive' ? 'hsl(158, 64%, 52%)' : 'hsl(351, 86%, 58%)',
                  border: '2px solid white',
                  boxShadow: '0 0 8px rgba(0,0,0,0.5)',
                  pointerEvents: 'none',
                }}
              />
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
            <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
              Points placed: <strong>{points.length}</strong> ({points.filter((p) => p.type === 'positive').length} foreground,{' '}
              {points.filter((p) => p.type === 'negative').length} background)
            </span>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={handleClearPoints}
              disabled={points.length === 0}
            >
              Clear Points
            </button>
          </div>
        </div>

        {/* Inference Controls & Live Results */}
        <div>
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: '1rem' }}>Model Controls</h2>

            <div className="form-group">
              <label className="form-label">Sample Image</label>
              <select value={selectedImage} onChange={(e) => setSelectedImage(e.target.value)}>
                {sampleImages.map((img) => (
                  <option key={img.name} value={img.name}>
                    {img.name}
                  </option>
                ))}
              </select>
            </div>

            {activeModel === 'sam' && (
              <div className="form-group">
                <label className="form-label">Mask Transparency Overlay ({maskOpacity}%)</label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={maskOpacity}
                  onChange={(e) => setMaskOpacity(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
            )}

            <button type="button" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
              Run Real-Time Inference
            </button>
          </div>

          <div className="card">
            <h2 className="card-title" style={{ marginBottom: '0.75rem' }}>Predictions & Telemetry</h2>
            <div className="meta-list">
              <div className="meta-item">
                <span className="meta-key">Inference Latency</span>
                <span className="meta-val" style={{ color: 'var(--accent-emerald)' }}>42.1 ms (GPU CUDA)</span>
              </div>
              <div className="meta-item">
                <span className="meta-key">Predicted Class</span>
                <span className="meta-val">Weed (Broadleaf Lambsquarters) - 97.4%</span>
              </div>
              <div className="meta-item">
                <span className="meta-key">Mask IoU Score</span>
                <span className="meta-val">0.941</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
