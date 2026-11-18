import React from 'react';
import { STATUS, statusLabel } from '../../utils/status';

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const tone = STATUS[status]?.[0] ?? 'neutral';
  return <span className={`badge${tone === 'neutral' ? '' : ` badge-${tone}`}`}>{statusLabel(status)}</span>;
};
