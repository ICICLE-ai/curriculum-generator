import React from 'react';
import { type FieldGuideEntry } from '../data/configFieldGuide';
import { Dialog } from './ui';

interface FieldHelpModalProps {
  entry: FieldGuideEntry | null;
  onClose: () => void;
}

export const FieldHelpModal: React.FC<FieldHelpModalProps> = ({ entry, onClose }) => {
  if (!entry) return null;

  return (
    <Dialog
      title={
        <div className="stack-sm">
          <div className="row-wrap">
            <span className="pill-tag">{entry.category}</span>
            <code className="muted">{entry.yamlPath}</code>
          </div>
          <span>{entry.title}</span>
        </div>
      }
      onClose={onClose}
      width={560}
      footer={
        <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
          Close
        </button>
      }
    >
      <div className="stack">
        <div className="callout-info">
          <strong>{entry.summary}</strong>
        </div>

        <div className="stack-sm">
          <div className="section-heading-xs mb-0">
            Explanation &amp; Purpose
          </div>
          <p className="muted text-pre">
            {entry.detailedDescription}
          </p>
        </div>

        {entry.recommendation && (
          <div className="alert alert-success alert-col">
            <strong>Best Practice</strong>
            <span>{entry.recommendation}</span>
          </div>
        )}

        {entry.example && (
          <div className="stack-sm">
            <div className="section-heading-xs mb-0">
              YAML Configuration Example
            </div>
            <pre className="code-box">{entry.example}</pre>
          </div>
        )}
      </div>
    </Dialog>
  );
};
