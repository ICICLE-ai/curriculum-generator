// Trust boundary for dataset plans from the model or the plan card: nothing reaches state or the prepare job unchecked.
import type { DatasetPlan, HfDatasetInfo } from './types.ts';

const SAFE_NAME = /^[a-z0-9_]+$/;
export const MAX_PER_CLASS_MIN = 20;
export const MAX_PER_CLASS_MAX = 5000;

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

export function validateDatasetPlan(plan: unknown, info: HfDatasetInfo): { ok: boolean; plan?: DatasetPlan; errors: string[] } {
  if (!isObj(plan)) return { ok: false, errors: ['plan must be an object'] };
  const errors: string[] = [];
  const p = plan;

  if (p.repo !== info.id) errors.push(`repo must be "${info.id}"`);
  if (p.revision !== info.revision) errors.push(`revision must be "${info.revision}"`);
  if (info.layout === 'unsupported') errors.push('this dataset layout is not supported');
  else if (p.layout !== info.layout) errors.push(`layout must be "${info.layout}"`);

  if (p.config !== info.config) errors.push(`config must be "${info.config}"`);
  const splits = p.splits;
  if (!Array.isArray(splits) || !splits.length || !splits.every((s) => typeof s === 'string' && info.splits.includes(s))) {
    errors.push(`splits must be a non-empty subset of ${JSON.stringify(info.splits)}`);
  }

  if (Array.isArray(splits) && Array.isArray(p.data_files)) {
    const want = [...new Set(splits.flatMap((x) => info.dataFiles[x] ?? []))].sort();
    const got = [...p.data_files].sort();
    if (!want.length || want.length !== got.length || want.some((f, i) => f !== got[i]) || got.some((f) => String(f).includes('..'))) errors.push('data_files must be exactly the inspected data_files of the chosen splits');
  } else errors.push('data_files must be an array');

  if (info.layout === 'parquet') {
    if (typeof p.image_column !== 'string' || !info.imageColumns.includes(p.image_column)) errors.push(`image_column must be one of ${JSON.stringify(info.imageColumns)}`);
  } else if (p.image_column !== '') errors.push('image_column must be "" for imagefolder datasets');

  const labels = typeof p.label_column === 'string' ? info.labelColumns[p.label_column] : undefined;
  if (!labels) errors.push(`label_column must be one of ${JSON.stringify(Object.keys(info.labelColumns))}`);

  const map = p.class_map;
  if (!isObj(map)) errors.push('class_map must be an object');
  else {
    if (labels) {
      const missing = labels.filter((l) => !(l in map));
      const extra = Object.keys(map).filter((k) => !labels.includes(k));
      if (missing.length) errors.push(`class_map is missing labels: ${JSON.stringify(missing)}`);
      if (extra.length) errors.push(`class_map has unknown labels: ${JSON.stringify(extra)}`);
    }
    const bad = Object.entries(map).filter(([, t]) => t !== null && !(typeof t === 'string' && SAFE_NAME.test(t)));
    if (bad.length) errors.push(`class_map targets must be null or match [a-z0-9_]+: ${JSON.stringify(bad.map(([k]) => k))}`);
    else if (new Set(Object.values(map).filter((t) => t !== null)).size < 2) errors.push('at least 2 different target folders must remain');
  }

  if (typeof p.name !== 'string' || !SAFE_NAME.test(p.name) || p.name.length > 60) errors.push('name must match [a-z0-9_]+ and be at most 60 characters');
  const n = p.max_per_class;
  if (!Number.isInteger(n) || (n as number) < MAX_PER_CLASS_MIN || (n as number) > MAX_PER_CLASS_MAX) errors.push(`max_per_class must be an integer from ${MAX_PER_CLASS_MIN} to ${MAX_PER_CLASS_MAX}`);

  if (errors.length) return { ok: false, errors };
  // Rebuilt from known keys so stray fields never reach the plan file
  return {
    ok: true,
    errors,
    plan: {
      repo: p.repo as string,
      revision: p.revision as string,
      config: p.config as string,
      layout: p.layout as DatasetPlan['layout'],
      data_files: p.data_files as string[],
      splits: splits as string[],
      image_column: p.image_column as string,
      label_column: p.label_column as string,
      class_map: { ...(map as Record<string, string | null>) },
      max_per_class: n as number,
      name: p.name as string,
    },
  };
}

/** Plain-English summary lines for the plan card and the model. */
export function describePlan(plan: DatasetPlan, info: HfDatasetInfo): string[] {
  const folders = new Map<string, string[]>();
  const dropped: string[] = [];
  for (const [label, target] of Object.entries(plan.class_map)) {
    if (target === null) dropped.push(label);
    else folders.set(target, [...(folders.get(target) ?? []), label]);
  }
  const labelCount = Object.keys(plan.class_map).length;
  const lines = [`${labelCount} labels become ${folders.size} folders.`];
  for (const [target, from] of folders) if (from.length > 1) lines.push(`${from.join(' and ')} are merged into ${target}.`);
  if (dropped.length) lines.push(`${dropped.join(', ')} ${dropped.length > 1 ? 'are' : 'is'} dropped.`);
  const counts = info.classCounts?.[plan.label_column];
  if (counts) {
    const est = [...folders].map(([target, from]) => [target, Math.min(plan.max_per_class, from.reduce((s, l) => s + (counts[l] ?? 0), 0))] as const);
    lines.push(`About ${est.map(([t, c]) => `${c} images in ${t}`).join(', ')}.`);
    const sizes = est.map(([, c]) => c);
    if (Math.min(...sizes) > 0 && Math.max(...sizes) >= 10 * Math.min(...sizes)) lines.push('Some folders have far more images than others, which can skew the results.');
  }
  return lines;
}
