import React, { useEffect, useState } from 'react';
import { Folder } from 'lucide-react';
import { fetchAvailableDatasets, type TapisDatasetItem } from '../../services/tapis';
import { setDataset } from '../../utils/assistant/draft';
import type { CurriculumAgent } from '../../utils/assistant/types';
import { useSession } from './session';

export const DatasetPickerCard: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const { token, username } = useSession();
  const [items, setItems] = useState<TapisDatasetItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    fetchAvailableDatasets(token, username).then(setItems, (e) => setError(String(e?.message || e)));
  }, [token, username]);

  const chosen = agent.state.draft.datasetPath;
  return (
    <div className="stack-sm">
      <strong>Pick a photo set you already have</strong>
      {error && <div role="alert" className="alert alert-error">{error}</div>}
      {!items && !error && <p className="muted mb-0">Looking for your photo sets...</p>}
      {items?.length === 0 && <p className="muted mb-0">No photo sets found yet. Upload one instead.</p>}
      <div className="pill-list">
        {items?.map((it) => (
          <button
            key={it.clusterPath}
            type="button"
            className={`pill ${chosen === it.clusterPath ? 'is-selected' : ''}`}
            onClick={() => agent.editDraft((d) => setDataset(d, it.clusterPath), `Picked dataset "${it.name}"`)}
          >
            <Folder size={14} aria-hidden="true" />
            <span>{it.name}</span>
            <span className="pill-tag">{it.source === 'user' ? 'Yours' : 'Shared'}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
