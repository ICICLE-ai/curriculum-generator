import React from 'react';
import type { FieldChange } from '../../utils/assistant/types';

const LABELS: Record<string, string> = {
  domain: 'Subject area', contextStatement: 'Course description', subject: 'Subject', targetLevel: 'Student level',
  classificationActive: 'Sort photos into categories', classificationTask: 'What to sort',
  segmentationActive: 'Outline objects in photos', segmentationPrompt: 'What to outline',
  xaiActive: 'Show why the AI decided', outputPath: 'Where results are saved', topicName: 'Topic name',
  topicDescription: 'Topic description', jobName: 'Run name', weeks: 'Number of weeks', datasetPath: 'Photo set',
};

const show = (v: unknown) =>
  v === undefined || v === null || v === '' ? '(empty)' : typeof v === 'boolean' ? (v ? 'Yes' : 'No') : typeof v === 'object' ? JSON.stringify(v) : String(v);

export const ChangesCard: React.FC<{ changes: FieldChange[] }> = ({ changes }) => (
  <div className="stack-sm">
    <strong>Updated</strong>
    <ul className="assistant-list">
      {changes.map((c) => (
        <li key={c.field}>
          <strong>{LABELS[c.field] ?? c.field}:</strong> {show(c.from)} → {show(c.to)}
        </li>
      ))}
    </ul>
  </div>
);
