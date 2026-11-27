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
    <div className="stack">
      <div>
        <h2 className="card-title">AI Vision Tools — Course Artifact Generation</h2>
        <p className="card-subtitle">Models run on your dataset before lessons are generated.</p>
      </div>

      <div className="callout-info">
        <strong>Why are AI Vision Tools needed?</strong> Before writing your course, the pipeline runs these models on
        your images to produce real <strong>artifacts</strong> — accuracy scores, confusion matrices, prediction tables,
        object masks, and attention heatmaps — embedded directly into student slides and Python labs.
      </div>

      {/* Classification Stage */}
      <div className="tool-card">
        <div className="row-between card-header-start">
          <div className="checkbox-row">
            <input
              type="checkbox"
              id="stage_cls"
              checked={classificationActive}
              onChange={(e) => onChangeClassificationActive(e.target.checked)}
            />
            <div>
              <label htmlFor="stage_cls" className="checkbox-label">
                Image Classification (DINOv2)
              </label>
              <p className="form-helper">
                Attaches a linear classifier head to the pre-trained DINOv2 backbone to categorize images and generate accuracy metrics and confusion matrices.
              </p>
            </div>
          </div>
          {renderHelpBtn('pipeline.classification')}
        </div>

        {classificationActive && (
          <div className="tool-card-body">
            <label htmlFor="classification-task-input" className="form-label">
              Task Identifier
            </label>
            <input
              id="classification-task-input"
              type="text"
              className="mono"
              value={classificationTask}
              onChange={(e) => onChangeClassificationTask(e.target.value)}
              placeholder="e.g. crop_disease_classification"
            />
            <div className="form-helper">
              Short snake_case label used to identify this task in the config and tag its generated metrics.
            </div>
          </div>
        )}
      </div>

      {/* Segmentation Stage */}
      <div className="tool-card">
        <div className="row-between card-header-start">
          <div className="checkbox-row">
            <input
              type="checkbox"
              id="stage_seg"
              checked={segmentationActive}
              onChange={(e) => onChangeSegmentationActive(e.target.checked)}
            />
            <div>
              <label htmlFor="stage_seg" className="checkbox-label">
                Object Outlining (Segment Anything / SAM)
              </label>
              <p className="form-helper">
                Isolates and outlines specific objects in your photos so students can measure region boundaries and area ratios.
              </p>
            </div>
          </div>
          {renderHelpBtn('pipeline.segmentation')}
        </div>

        {segmentationActive && (
          <div className="tool-card-body">
            <label htmlFor="segmentation-prompt-input" className="form-label">
              Target Object Prompt
            </label>
            <input
              id="segmentation-prompt-input"
              type="text"
              value={segmentationPrompt}
              onChange={(e) => onChangeSegmentationPrompt(e.target.value)}
              placeholder="e.g. the infected leaf spot, the dark mole on skin"
            />
            <div className="form-helper">
              Plain-English description of what SAM should outline in each photo.
            </div>
          </div>
        )}
      </div>

      {/* Visual XAI Stage */}
      <div className="tool-card">
        <div className="row-between card-header-start">
          <div className="checkbox-row">
            <input
              type="checkbox"
              id="stage_xai"
              checked={xaiActive}
              onChange={(e) => onChangeXaiActive(e.target.checked)}
            />
            <div>
              <label htmlFor="stage_xai" className="checkbox-label">
                Visual Attention Heatmaps (Grad-CAM)
              </label>
              <p className="form-helper">
                Generates heatmaps showing which parts of an image influenced predictions, for lessons on AI transparency and debugging.
              </p>
            </div>
          </div>
          {renderHelpBtn('pipeline.visual_xai')}
        </div>
      </div>
    </div>
  );
};
