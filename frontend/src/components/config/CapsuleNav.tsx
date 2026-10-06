import React from 'react';

export type SectionTab = 'project' | 'pipeline' | 'curriculum' | 'modules' | 'execution';

interface CapsuleNavProps {
  activeSection: SectionTab;
  onSelectSection: (section: SectionTab) => void;
  modulesCount: number;
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
}) => {
  const tabs: TabDef[] = [
    { id: 'project', step: 1, label: 'Course & Data' },
    { id: 'pipeline', step: 2, label: 'Vision Tools' },
    { id: 'curriculum', step: 3, label: 'Syllabus' },
    { id: 'modules', step: 4, label: 'Weekly Labs', badge: modulesCount },
    { id: 'execution', step: 5, label: 'Lab Settings' },
  ];

  return (
    <div className="capsule-nav" role="tablist" aria-label="Curriculum Studio Navigation">
      {tabs.map((tab) => {
        const isActive = activeSection === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={`capsule-tab ${isActive ? 'active' : ''}`}
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
    </div>
  );
};

