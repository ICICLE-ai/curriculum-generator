import React from 'react';
import { Plus, Trash2 } from 'lucide-react';
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
    <div className="stack">
      <div>
        <h2 className="card-title">Course Syllabus &amp; Resources</h2>
        <p className="card-subtitle">Set the course title, grade level, core focus, and student reference links.</p>
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label htmlFor="syllabus-subject" className="form-label">
            <span>Course / Unit Title</span>
            {renderHelpBtn('curriculum.subject')}
          </label>
          <input
            id="syllabus-subject"
            type="text"
            value={subject}
            onChange={(e) => onChangeSubject(e.target.value)}
            placeholder="e.g. Intro to Agricultural AI"
          />
        </div>
        <div className="form-group">
          <label htmlFor="syllabus-level" className="form-label">
            <span>Student Grade Level</span>
            {renderHelpBtn('curriculum.target_level')}
          </label>
          <input
            id="syllabus-level"
            type="text"
            value={targetLevel}
            onChange={(e) => onChangeTargetLevel(e.target.value)}
            placeholder="e.g. High School STEM (Grades 9-12)"
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="syllabus-topic" className="form-label">
          <span>Core Topic Focus</span>
          {renderHelpBtn('curriculum.topics')}
        </label>
        <input
          id="syllabus-topic"
          type="text"
          value={topicName}
          onChange={(e) => onChangeTopicName(e.target.value)}
          placeholder="e.g. Foliar Crop Pathology, Skin Lesion Diagnostics"
        />
      </div>

      <div className="form-group">
        <label htmlFor="syllabus-desc" className="form-label">
          <span>Topic Description</span>
          {renderHelpBtn('curriculum.topics')}
        </label>
        <textarea
          id="syllabus-desc"
          rows={3}
          value={topicDescription}
          onChange={(e) => onChangeTopicDescription(e.target.value)}
          placeholder="What core concept does this course demonstrate?"
        />
      </div>

      <div className="divider-top stack-sm">
        <div className="row-between">
          <div className="inline-label-pair">
            <span className="form-label mb-0">
              Student Resource Links ({resources.length})
            </span>
            {renderHelpBtn('curriculum.resources')}
          </div>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={onAddResource}
          >
            <Plus size={14} aria-hidden="true" />
            <span>Add Resource</span>
          </button>
        </div>

        {resources.length === 0 ? (
          <div className="empty-state">
            No resources attached. Click <strong>Add Resource</strong> to embed links for students.
          </div>
        ) : (
          <div className="stack-sm">
            {resources.map((r, idx) => (
              <div key={idx} className="inset-panel row-wrap">
                <input
                  type="text"
                  aria-label="Resource name"
                  value={r.name}
                  onChange={(e) => onUpdateResource(idx, 'name', e.target.value)}
                  placeholder="Resource Title (e.g. Kaggle Dataset)"
                  style={{ flex: '1 1 180px', fontWeight: 600 }}
                />
                <input
                  type="text"
                  aria-label="Resource URL"
                  className="mono"
                  value={r.url}
                  onChange={(e) => onUpdateResource(idx, 'url', e.target.value)}
                  placeholder="https://..."
                  style={{ flex: '2 1 260px' }}
                />
                <button
                  type="button"
                  className="btn btn-sm btn-danger"
                  onClick={() => onRemoveResource(idx)}
                  aria-label={`Remove resource ${r.name}`}
                >
                  <Trash2 size={14} aria-hidden="true" />
                  <span>Remove</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
