import React from 'react';

export type SectionTab = 'project' | 'curriculum' | 'modules' | 'execution';

interface ConfigSummary {
  domain: string;
  datasetName: string;
  weeksCount: number;
  modulesCount: number;
}

interface CapsuleNavProps {
  activeSection: SectionTab;
  onSelectSection: (section: SectionTab) => void;
  modulesCount: number;
  summary?: ConfigSummary;
}

interface TabDef {
  id: SectionTab;
  step: number;
  label: string;
  badge?: number;
}

export const CapsuleNav: React.FC<CapsuleNavProps> = ({
  activeSection,
  onSelectSection,
  modulesCount,
  summary,
}) => {
  const tabs: TabDef[] = [
    { id: 'project', step: 1, label: 'Course & Data' },
    { id: 'curriculum', step: 2, label: 'Syllabus' },
    { id: 'modules', step: 3, label: 'Weekly Labs', badge: modulesCount },
    { id: 'execution', step: 4, label: 'Lab Settings' },
  ];

  return (
    <aside className="config-rail">
      <nav className="config-rail-nav" role="tablist" aria-label="Curriculum Studio Navigation" aria-orientation="vertical">
        {tabs.map((tab) => {
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={`config-rail-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectSection(tab.id)}
            >
              <span className="capsule-step">{tab.step}</span>
              <span className="capsule-label">{tab.label}</span>
              {tab.badge !== undefined && (
                <span className="capsule-count">{tab.badge}</span>
              )}
            </button>
          );
        })}
      </nav>

      {summary && (
        <div className="config-rail-summary">
          <div className="section-heading-xs mb-0">
            Course Summary
          </div>
          <dl className="kv kv-single">
            <div>
              <dt>Subject Area</dt>
              <dd>{summary.domain || 'Not set'}</dd>
            </div>
            <div>
              <dt>Dataset</dt>
              <dd className="mono">{summary.datasetName || 'Not selected'}</dd>
            </div>
            <div>
              <dt>Schedule</dt>
              <dd>
                {summary.weeksCount} {summary.weeksCount === 1 ? 'week' : 'weeks'} · {summary.modulesCount} {summary.modulesCount === 1 ? 'module' : 'modules'}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </aside>
  );
};
