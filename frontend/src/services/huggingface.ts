// Hugging Face search and metadata through same-origin proxies (/hf-api, /hf-viewer); nothing is downloaded here.
import type { HfDatasetInfo } from '../utils/assistant/types';

export interface HfSearchHit {
  id: string;
  downloads: number;
  license?: string;
  gated: boolean;
}

const MAX_SAMPLES = 6;
const IMAGE_FILE = /\.(jpe?g|png|webp|bmp|tiff?)$/i;

async function getJson(token: string, url: string): Promise<any | null> {
  const resp = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (resp.status === 401) throw new Error('401 Session expired');
  return resp.ok ? resp.json() : null; // the viewer answers 404/501 for datasets it cannot read
}

const licenseOf = (d: any): string | undefined =>
  d.cardData?.license ?? d.tags?.find((t: string) => t.startsWith('license:'))?.slice(8);

export async function searchDatasets(token: string, query: string): Promise<HfSearchHit[]> {
  const url = `/hf-api/datasets?search=${encodeURIComponent(query)}&filter=task_categories:image-classification&sort=downloads&limit=10&full=true`;
  const list = await getJson(token, url);
  if (!list) throw new Error('Hugging Face search failed.');
  return list.map((d: any) => ({ id: d.id, downloads: d.downloads ?? 0, license: licenseOf(d), gated: !!d.gated }));
}

function detectLayout(tags: string[], files: string[]): HfDatasetInfo['layout'] {
  if (tags.includes('format:imagefolder')) return 'imagefolder';
  if (tags.includes('format:parquet') || files.some((f) => f.endsWith('.parquet'))) return 'parquet';
  // shortcut: image zips and other layouts are unsupported; add them when educators ask for such datasets
  return files.some((f) => IMAGE_FILE.test(f) && f.includes('/')) ? 'imagefolder' : 'unsupported';
}

// Repo file globs per split for one config: from the card's data_files, else derived from the file list
function dataFilesFor(meta: any, config: string, configs: string[], splits: string[], layout: HfDatasetInfo['layout']): Record<string, string[]> {
  const card = (meta.cardData?.configs ?? []).find((c: any) => c.config_name === config);
  const files: string[] = (meta.siblings ?? []).map((s: any) => s.rfilename).filter((f: string) => (layout === 'parquet' ? f.endsWith('.parquet') : IMAGE_FILE.test(f)));
  const others = configs.filter((c) => c !== config).map((c) => `${c}/`);
  const own = files.filter((f) => (card?.data_dir ? f.startsWith(`${card.data_dir}/`) : config === 'default' ? !others.some((o) => f.startsWith(o)) : f.startsWith(`${config}/`)));
  const out: Record<string, string[]> = {};
  for (const split of splits) {
    const declared = (card?.data_files ?? []).filter((d: any) => d.split === split).flatMap((d: any) => [d.path].flat());
    // imagefolder images are collapsed to "<dir up to the split>/**" so the plan stays small
    const derived = own.filter((f) => f.split('/').some((seg) => seg.startsWith(split))).map((f) => {
      const parts = f.split('/');
      const i = parts.findIndex((seg) => seg === split);
      return layout === 'imagefolder' && i >= 0 ? `${parts.slice(0, i + 1).join('/')}/**` : f;
    });
    const list = declared.length ? declared : [...new Set(derived)];
    if (list.length) out[split] = list;
  }
  return out;
}

export async function inspectDataset(token: string, id: string): Promise<HfDatasetInfo> {
  const meta = await getJson(token, `/hf-api/datasets/${id}`);
  if (!meta) throw new Error(`Dataset ${id} was not found on Hugging Face.`);
  const info: HfDatasetInfo = {
    id,
    revision: meta.sha,
    license: licenseOf(meta),
    gated: !!meta.gated,
    downloads: meta.downloads ?? 0,
    layout: detectLayout(meta.tags ?? [], (meta.siblings ?? []).map((s: any) => s.rfilename)),
    config: '',
    configs: [],
    splits: [],
    dataFiles: {},
    imageColumns: [],
    labelColumns: {},
    samples: [],
  };
  if (info.gated || info.layout === 'unsupported') return info;

  const q = `dataset=${encodeURIComponent(id)}`;
  const [splitsRes, size] = await Promise.all([getJson(token, `/hf-viewer/splits?${q}`), getJson(token, `/hf-viewer/size?${q}`)]);
  const all: Array<{ config: string; split: string }> = splitsRes?.splits ?? [];
  if (!all.length) return { ...info, layout: 'unsupported' };
  const configs = [...new Set(all.map((s) => s.config))];
  const config = configs.includes('default') ? 'default' : configs[0]; // shortcut: label names can differ per config, so only one is described
  info.config = config;
  info.configs = configs;
  info.dataFiles = dataFilesFor(meta, config, configs, all.filter((s) => s.config === config).map((s) => s.split), info.layout);
  info.splits = Object.keys(info.dataFiles);
  if (!info.splits.length) return { ...info, layout: 'unsupported' };
  const cfg = (size?.size?.configs ?? []).find((c: any) => c.config === config);
  info.rows = cfg?.num_rows;
  info.bytes = cfg?.num_bytes_original_files ?? cfg?.num_bytes_parquet_files ?? undefined;

  const view = (s: string) => `${q}&config=${encodeURIComponent(config)}&split=${encodeURIComponent(s)}`;
  const first = await getJson(token, `/hf-viewer/first-rows?${view(info.splits[0])}`);
  const features: any[] = first?.features ?? [];
  const isLabel = (f: any) => f.type?._type === 'ClassLabel';
  info.imageColumns = features.filter((f) => f.type?._type === 'Image').map((f) => f.name);
  // imagefolder: labels are folder names, so the single label column is keyed ""
  const labelFeatures = features.filter(isLabel);
  for (const f of info.layout === 'imagefolder' ? labelFeatures.slice(0, 1) : labelFeatures) {
    info.labelColumns[info.layout === 'imagefolder' ? '' : f.name] = f.type.names;
  }
  if (!info.imageColumns.length || !Object.keys(info.labelColumns).length) return { ...info, layout: 'unsupported' };

  // sample images: one per label first, so the educator sees different classes
  const col = labelFeatures[0];
  const seen = new Set<number>();
  let rows: any[] = first.rows ?? [];
  // Class-sorted datasets put one class in the first rows: then take single rows spread across the split
  const splitRows: number | undefined = (size?.size?.splits ?? []).find((s: any) => s.config === config && s.split === info.splits[0])?.num_rows;
  if (new Set(rows.map((r) => r.row[col.name])).size < 3 && splitRows && splitRows > MAX_SAMPLES) {
    const spread = await Promise.all(
      Array.from({ length: MAX_SAMPLES }, (_, k) =>
        getJson(token, `/hf-viewer/rows?${view(info.splits[0])}&offset=${Math.floor((k * splitRows) / MAX_SAMPLES)}&length=1`)
      )
    );
    const more = spread.flatMap((r) => r?.rows ?? []);
    if (more.length) rows = [...more, ...rows];
  }
  const pick = [...rows.filter((r) => !seen.has(r.row[col.name]) && seen.add(r.row[col.name])), ...rows].slice(0, MAX_SAMPLES);
  info.samples = pick.flatMap((r) => {
    const src = r.row[info.imageColumns[0]]?.src;
    return src ? [{ src, label: col.type.names[r.row[col.name]] ?? '' }] : [];
  });

  // class frequencies, summed over splits; absent for datasets the viewer has not profiled
  const stats = await Promise.all(info.splits.map((s) => getJson(token, `/hf-viewer/statistics?${view(s)}`)));
  const counts: Record<string, Record<string, number>> = {};
  for (const st of stats) {
    for (const c of st?.statistics ?? []) {
      const freq = c.column_statistics?.frequencies;
      if (c.column_type !== 'class_label' || !freq) continue;
      const key = info.layout === 'imagefolder' ? '' : c.column_name;
      if (!(key in info.labelColumns)) continue;
      const into = (counts[key] ??= {});
      for (const [name, n] of Object.entries(freq)) into[name] = (into[name] ?? 0) + (n as number);
    }
  }
  if (Object.keys(counts).length) info.classCounts = counts;
  return info;
}
