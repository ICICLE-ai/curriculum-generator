import React from 'react';
import type { CurriculumResource } from '../../presets';

interface CurriculumSyllabusSectionProps {
  subject: string;
  onChangeSubject: (value: string) => void;
  targetLevel: string;
  onChangeTargetLevel: (value: string) => void;
  topicName: string;
  onChangeTopicName: (value: string) => void;
  topicDescription: string;
  onChangeTopicDescription: (value: string) => void;
  resources: CurriculumResource[];
  onAddResource: () => void;
  onRemoveResource: (index: number) => void;
  onUpdateResource: (index: number, field: keyof CurriculumResource, value: string) => void;
  renderHelpBtn: (fieldKey: string) => React.ReactNode;
}

export const CurriculumSyllabusSection: React.FC<CurriculumSyllabusSectionProps> = ({
  subject,
  onChangeSubject,
  targetLevel,
  onChangeTargetLevel,
  topicName,
  onChangeTopicName,
  topicDescription,
  onChangeTopicDescription,
  resources,
  onAddResource,
  onRemoveResource,
  onUpdateResource,
  renderHelpBtn,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">
            <span>Course / Unit Title</span>
            {renderHelpBtn('curriculum.subject')}
          </label>
          <input
            type="text"
            value={subject}
            onChange={(e) => onChangeSubject(e.target.value)}
            placeholder="e.g. Intro to Agricultural AI"
          />
        </div>
        <div className="form-group">
          <label className="form-label">
            <span>Student Grade Level</span>
            {renderHelpBtn('curriculum.target_level')}
          </label>
          <input
            type="text"
            value={targetLevel}
            onChange={(e) => onChangeTargetLevel(e.target.value)}
            placeholder="e.g. High School STEM or Undergraduate CS"
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          <span>Core Topic Focus</span>
          {renderHelpBtn('curriculum.topics')}
        </label>
        <input
          type="text"
          value={topicName}
          onChange={(e) => onChangeTopicName(e.target.value)}
          placeholder="e.g. Foliar Crop Pathology, Skin Lesion Diagnostics"
        />
      </div>

      <div className="form-group">
        <label className="form-label">
          <span>Topic Description</span>
          {renderHelpBtn('curriculum.topics')}
        </label>
        <textarea
          rows={3}
          value={topicDescription}
          onChange={(e) => onChangeTopicDescription(e.target.value)}
          placeholder="What core concept does this course or curriculum demonstrate?..."
        />
      </div>

      {/* Dynamic Multiple Resources Section */}
      <div style={{ marginTop: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
          <label className="form-label" style={{ marginBottom: 0 }}>
            <span>Recommended Student Resource Links ({resources.length})</span>
            {renderHelpBtn('curriculum.resources')}
          </label>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={onAddResource}
          >
            + Add Resource
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {resources.map((r, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                background: 'var(--bg-card-subtle)',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <input
                type="text"
                value={r.name}
                onChange={(e) => onUpdateResource(idx, 'name', e.target.value)}
                placeholder="Resource Title (e.g. Kaggle Dataset, PyTorch Docs)..."
                style={{ width: '200px', fontWeight: 600 }}
              />
              <input
                type="text"
                value={r.url}
                onChange={(e) => onUpdateResource(idx, 'url', e.target.value)}
                placeholder="https://..."
                style={{ flex: 1, fontFamily: 'var(--font-mono)' }}
              />
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => onRemoveResource(idx)}
                style={{ color: 'var(--accent-rose)' }}
                title="Remove resource"
              >
                Remove
              </button>
            </div>
          ))}
          {resources.length === 0 && (
            <div style={{ textAlign: 'center', padding: '1.25rem', color: 'var(--text-muted)', fontSize: '0.825rem' }}>
              No resources attached. Click "+ Add Resource" to embed links for students.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
