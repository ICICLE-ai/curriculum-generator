import React from 'react';

interface WelcomePageProps {
  onNavigate: (tab: 'config' | 'submit' | 'monitor', presetKey?: string) => void;
}

export const WelcomePage: React.FC<WelcomePageProps> = ({ onNavigate }) => {
  return (
    <div className="page-container" style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Hero Section */}
      <section
        style={{
          padding: '2.5rem 2rem',
          borderRadius: 'var(--radius-lg)',
          background: 'linear-gradient(180deg, rgba(39, 39, 42, 0.4) 0%, rgba(18, 18, 20, 0.6) 100%)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '2rem',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '-50px',
            right: '-50px',
            width: '280px',
            height: '280px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(14, 165, 233, 0.12) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
         
            
          
        </div>

        <h1
          style={{
            fontSize: '2.4rem',
            fontWeight: 800,
            color: '#fafafa',
            letterSpacing: '-0.025em',
            margin: '0 0 1rem 0',
            lineHeight: 1.15,
          }}
        >
          Smart Curriculum Designer
        </h1>

        <p
          style={{
            fontSize: '1.05rem',
            color: 'var(--text-secondary)',
            maxWidth: '780px',
            lineHeight: 1.6,
            margin: '0 0 1.75rem 0',
          }}
        >
          Transform authentic domain datasets into rich, scaffolded AI learning experiences.
          Run computer vision pipelines on supercomputers, then dynamically synthesize complete
          syllabi, lecture slides, coding exercises, and automated unit test sandboxes.
        </p>

        {/* Action CTAs */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onNavigate('config')}
            style={{ padding: '0.65rem 1.4rem', fontSize: '0.9rem', fontWeight: 600 }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
            Design Curriculum
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onNavigate('submit')}
            style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
              <line x1="6" y1="6" x2="6.01" y2="6" />
              <line x1="6" y1="18" x2="6.01" y2="18" />
            </svg>
            Submit HPC Job
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onNavigate('monitor')}
            style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Live Monitor
          </button>
        </div>
      </section>

      {/* 3-Step Workflow Progression */}
      <section style={{ marginBottom: '2.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.25rem 0', color: 'var(--text-primary)' }}>
            End-to-End Workflow
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
            From dataset selection to supercomputing execution and classroom courseware export.
          </p>
        </div>

        <div className="grid-3" style={{ gap: '1rem' }}>
          {/* Step 1 */}
          <div
            className="card"
            style={{
              marginBottom: 0,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'border-color 0.2s ease',
            }}
          >
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.75rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--accent-primary)',
                    letterSpacing: '0.05em',
                  }}
                >
                  Step 01
                </span>
               
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
                Configure Pipeline
              </h3>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                Select authentic domain datasets, enable DINOv2 feature extraction, SAM mask segmentation, and
                Grad-CAM heatmaps. Formulate course syllabus and learning outcomes.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onNavigate('config')}
              style={{ marginTop: '1.25rem', width: '100%', fontSize: '0.82rem', justifyContent: 'center' }}
            >
              Open Config Studio →
            </button>
          </div>

          {/* Step 2 */}
          <div
            className="card"
            style={{
              marginBottom: 0,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.75rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--accent-emerald)',
                    letterSpacing: '0.05em',
                  }}
                >
                  Step 02
                </span>
                
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
                Dispatch HPC Job
              </h3>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                Submit containerized Slurm jobs to the supercomputing cluster via Tapis v3. Dedicated
                GPU allocation, high-speed scratch binding, and automatic queue routing.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onNavigate('submit')}
              style={{ marginTop: '1.25rem', width: '100%', fontSize: '0.82rem', justifyContent: 'center' }}
            >
              HPC Submission →
            </button>
          </div>

          {/* Step 3 */}
          <div
            className="card"
            style={{
              marginBottom: 0,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.75rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--accent-amber)',
                    letterSpacing: '0.05em',
                  }}
                >
                  Step 03
                </span>
                
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
                Track & Download
              </h3>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                Follow granular pipeline stage telemetry and stdout logs in real time. Download generated
                syllabi, widescreen slides (.pptx), coding exercises, solutions, and unit tests.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onNavigate('monitor')}
              style={{ marginTop: '1.25rem', width: '100%', fontSize: '0.82rem', justifyContent: 'center' }}
            >
              Live Telemetry →
            </button>
          </div>
        </div>
      </section>
      
      
    </div>
  );
};
