import React from 'react';

interface JobArtifactsCardProps {
  macroStatus: string;
  onDownloadArtifact: (filename: string) => void;
}

export const JobArtifactsCard: React.FC<JobArtifactsCardProps> = ({
  macroStatus,
  onDownloadArtifact,
}) => {
  const isFinished = macroStatus === 'FINISHED';

  return (
    <div className="card">
      <h2 className="card-title" style={{ marginBottom: '0.5rem' }}>
        Curriculum Artifacts & Results
      </h2>
      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
        Download the synthesized syllabus, machine learning metrics report, student exercises, and
        dependency configurations.
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onDownloadArtifact('curriculum.json')}
          disabled={!isFinished}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download curriculum.json
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onDownloadArtifact('curriculum_grade_10.md')}
          disabled={!isFinished}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          Download Syllabus (Markdown)
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onDownloadArtifact('presentation.pptx')}
          disabled={!isFinished}
          title="Download synthesized widescreen lecture slides"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          Download Lecture Slides (.pptx)
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onDownloadArtifact('results.csv')}
          disabled={!isFinished}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Download results.csv
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onDownloadArtifact('eval_confusion_matrix.png')}
          disabled={!isFinished}
          title="Download visual confusion matrix heatmap"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
          Download Confusion Matrix (.png)
        </button>
      </div>
    </div>
  );
};
