import React, { useEffect } from 'react';
import { type FieldGuideEntry } from '../data/configFieldGuide';

interface FieldHelpModalProps {
  entry: FieldGuideEntry | null;
  onClose: () => void;
}

export const FieldHelpModal: React.FC<FieldHelpModalProps> = ({ entry, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!entry) return null;

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          maxWidth: '560px',
          width: '100%',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'modalFadeIn 0.15s ease-out',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            padding: '1.15rem 1.25rem 0.75rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '0.15rem 0.45rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--accent-primary-subtle)',
                  color: 'var(--accent-primary)',
                }}
              >
                {entry.category}
              </span>
              <span
                style={{
                  fontSize: '0.725rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-card-subtle)',
                  padding: '0.15rem 0.45rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                {entry.yamlPath}
              </span>
            </div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              {entry.title}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              fontSize: '1.25rem',
              cursor: 'pointer',
              padding: '0.2rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
              lineHeight: 1,
            }}
            title="Close modal (Esc)"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div
          style={{
            padding: '1.25rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            fontSize: '0.85rem',
            lineHeight: 1.5,
          }}
        >
          {/* Summary Box */}
          <div
            style={{
              padding: '0.75rem 1rem',
              background: 'var(--bg-card-subtle)',
              borderLeft: '3px solid var(--accent-primary)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              fontWeight: 500,
            }}
          >
            {entry.summary}
          </div>

          {/* Detailed Explanation */}
          <div>
            <h3 style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Explanation & Purpose
            </h3>
            <p style={{ color: 'var(--text-secondary)', whiteSpace: 'pre-line' }}>
              {entry.detailedDescription}
            </p>
          </div>

          {/* Recommendation */}
          {entry.recommendation && (
            <div
              style={{
                padding: '0.65rem 0.85rem',
                background: 'var(--accent-emerald-subtle)',
                border: '1px solid var(--accent-emerald-border)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                color: 'var(--accent-emerald)',
              }}
            >
              <strong>Best Practice:</strong> {entry.recommendation}
            </div>
          )}

          {/* Example Code */}
          {entry.example && (
            <div>
              <h3 style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                YAML Configuration Example
              </h3>
              <pre
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.775rem',
                  background: 'var(--bg-card-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.65rem 0.85rem',
                  overflowX: 'auto',
                  lineHeight: 1.4,
                  color: 'var(--text-primary)',
                }}
              >
                {entry.example}
              </pre>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            padding: '0.75rem 1.25rem',
            borderTop: '1px solid var(--border-subtle)',
            background: 'var(--bg-card-subtle)',
          }}
        >
          <button type="button" className="btn btn-secondary btn-sm" onClick={onClose} style={{ padding: '0.35rem 0.85rem' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
