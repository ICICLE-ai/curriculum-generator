import React, { useState } from 'react';
import { ExternalLink } from 'lucide-react';
import type { CurriculumAgent, HfDatasetInfo } from '../../utils/assistant/types';

const SHOWN_CLASSES = 12;

const formatSize = (bytes: number) => (bytes >= 1e9 ? `${(bytes / 1e9).toFixed(1)} GB` : `${Math.max(1, Math.round(bytes / 1e6))} MB`);

export const HfDatasetsCard: React.FC<{ agent: CurriculumAgent; candidates: HfDatasetInfo[] }> = ({ agent, candidates }) => {
  const [chosen, setChosen] = useState<string | null>(null);

  return (
    <div className="stack-sm">
      <strong>Datasets I found</strong>
      {candidates.map((c) => {
        const column = Object.keys(c.labelColumns)[0];
        const classes = column === undefined ? [] : c.labelColumns[column];
        const counts = column === undefined ? undefined : c.classCounts?.[column];
        const max = counts ? Math.max(1, ...Object.values(counts)) : 1;
        return (
          <section key={c.id} className="hf-candidate stack-sm" aria-label={c.id}>
            <div className="row-wrap">
              <strong>{c.id}</strong>
              <a href={`https://huggingface.co/datasets/${c.id}`} target="_blank" rel="noopener noreferrer" className="hf-link">
                View on Hugging Face <ExternalLink size={14} aria-hidden="true" />
              </a>
            </div>
            <p className="muted mb-0">
              {c.license || 'No license listed'}
              {c.bytes != null && ` · ${formatSize(c.bytes)}`}
              {c.rows != null && ` · ${c.rows.toLocaleString()} images`}
            </p>
            {classes.length > 0 && (
              <ul className="hf-chips" aria-label="Categories">
                {classes.slice(0, SHOWN_CLASSES).map((name) => (
                  <li key={name} className="hf-chip">{name}</li>
                ))}
                {classes.length > SHOWN_CLASSES && <li className="hf-chip hf-chip-more">+{classes.length - SHOWN_CLASSES} more</li>}
              </ul>
            )}
            {counts && (
              <details>
                <summary>Images per category</summary>
                <ul className="hf-bars">
                  {classes.filter((n) => counts[n] != null).map((n) => (
                    <li key={n}>
                      <span className="hf-bar-label">{n}</span>
                      <span className="hf-bar" aria-hidden="true"><span style={{ width: `${(100 * counts[n]) / max}%` }} /></span>
                      <span className="hf-bar-n">{counts[n].toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
            {c.samples.length > 0 && (
              <div className="hf-samples">
                {c.samples.slice(0, 6).map((s, i) => (
                  <img key={i} src={s.src} alt={`Sample: ${s.label}`} title={s.label} loading="lazy" className="hf-sample" />
                ))}
              </div>
            )}
            <div className="col-end">
              <button
                type="button"
                className="btn btn-primary btn-sm"
                disabled={chosen !== null}
                onClick={() => {
                  setChosen(c.id);
                  agent.editDraft((d) => d, `Chose dataset ${c.id}`);
                }}
              >
                {chosen === c.id ? 'Chosen' : 'Use this one'}
              </button>
            </div>
          </section>
        );
      })}
    </div>
  );
};
