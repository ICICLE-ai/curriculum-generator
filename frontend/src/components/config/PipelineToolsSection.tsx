import React from 'react';

interface PipelineToolsSectionProps {
  classificationActive: boolean;
  onChangeClassificationActive: (active: boolean) => void;
  classificationTask: string;
  onChangeClassificationTask: (task: string) => void;
  segmentationActive: boolean;
  onChangeSegmentationActive: (active: boolean) => void;
  segmentationPrompt: string;
  onChangeSegmentationPrompt: (prompt: string) => void;
  xaiActive: boolean;
  onChangeXaiActive: (active: boolean) => void;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
}

export const PipelineToolsSection: React.FC<PipelineToolsSectionProps> = ({
  classificationActive,
  onChangeClassificationActive,
  classificationTask,
  onChangeClassificationTask,
  segmentationActive,
  onChangeSegmentationActive,
  segmentationPrompt,
  onChangeSegmentationPrompt,
  xaiActive,
  onChangeXaiActive,
  renderHelpBtn,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Classification Stage Card */}
      <div
        style={{
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem 1.4rem',
          background: 'var(--bg-card-subtle)',
          transition: 'border-color 0.15s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input
              type="checkbox"
              id="stage_cls"
              checked={classificationActive}
              onChange={(e) => onChangeClassificationActive(e.target.checked)}
              style={{ width: '18px', height: '18px' }}
            />
            <label htmlFor="stage_cls" style={{ fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', color: 'var(--text-primary)' }}>
              Foundation Feature Classification (DINOv2)
            </label>
          </div>
          {renderHelpBtn('pipeline.classification')}
        </div>
        {classificationActive && (
          <div style={{ marginTop: '1rem', paddingLeft: '2rem' }}>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Task Identifier</label>
            <input
              type="text"
              value={classificationTask}
              onChange={(e) => onChangeClassificationTask(e.target.value)}
              placeholder="e.g. crop_disease_classification"
            />
          </div>
        )}
      </div>

      {/* Segmentation Stage Card */}
      <div
        style={{
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem 1.4rem',
          background: 'var(--bg-card-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input
              type="checkbox"
              id="stage_seg"
              checked={segmentationActive}
              onChange={(e) => onChangeSegmentationActive(e.target.checked)}
              style={{ width: '18px', height: '18px' }}
            />
            <label htmlFor="stage_seg" style={{ fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', color: 'var(--text-primary)' }}>
              Promptable Segmentation (Segment Anything / SAM)
            </label>
          </div>
          {renderHelpBtn('pipeline.segmentation')}
        </div>
        {segmentationActive && (
          <div style={{ marginTop: '1rem', paddingLeft: '2rem' }}>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Target Object Prompt</label>
            <input
              type="text"
              value={segmentationPrompt}
              onChange={(e) => onChangeSegmentationPrompt(e.target.value)}
              placeholder="e.g. the infected leaf lesion, the tumor boundary, the food item"
            />
          </div>
        )}
      </div>

      {/* Visual XAI Stage Card */}
      <div
        style={{
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem 1.4rem',
          background: 'var(--bg-card-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <input
            type="checkbox"
            id="stage_xai"
            checked={xaiActive}
            onChange={(e) => onChangeXaiActive(e.target.checked)}
            style={{ width: '18px', height: '18px' }}
          />
          <label htmlFor="stage_xai" style={{ fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', color: 'var(--text-primary)' }}>
            Visual AI Heatmaps & Transparency (Grad-CAM)
          </label>
        </div>
        {renderHelpBtn('pipeline.visual_xai')}
      </div>
    </div>
  );
};
