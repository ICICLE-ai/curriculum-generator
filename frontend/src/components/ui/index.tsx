import React from 'react';

export { StatusBadge } from './StatusBadge';
export { Dialog } from './Dialog';

/** Page title, one line saying what the page is for, and the page's actions on the right. */
export const PageHeader: React.FC<{ title: string; description?: React.ReactNode; actions?: React.ReactNode; children?: React.ReactNode }> = ({
  title,
  description,
  actions,
  children,
}) => (
  <header className="page-header page-header-row">
    <div>
      <h1 className="page-title">{title}</h1>
      {description && <p className="page-description">{description}</p>}
      {children}
    </div>
    {actions && <div className="page-actions">{actions}</div>}
  </header>
);

/** Label/value pairs in a responsive grid. `mono` for machine values (ids, paths). */
export const KeyValue: React.FC<{ items: Array<{ label: string; value: React.ReactNode; mono?: boolean }> }> = ({ items }) => (
  <dl className="kv">
    {items.map(({ label, value, mono }) => (
      <div key={label}>
        <dt>{label}</dt>
        <dd className={mono ? 'mono' : undefined}>{value ?? '—'}</dd>
      </div>
    ))}
  </dl>
);
