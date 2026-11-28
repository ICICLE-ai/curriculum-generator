// Tool executors. None of these may submit, rerun, upload or export: only the cards' buttons do.
import {
  fetchAvailableDatasets,
  fetchJobDetails,
  fetchJobLogs,
  fetchJobStatus,
  fetchPhase2RerunStatus,
  fetchSystemRootDir,
  fetchUserJobs,
  listSystemFiles,
} from '../../services/tapis';
import { inspectDataset as inspectHfDataset, searchDatasets } from '../../services/huggingface';
import { applyPatch, editWeek, missingFields, setWeekPlan, validateDraft } from './draft';
import { describePlan, validateDatasetPlan } from './datasetPlan';
import { explainFailure, parseFailures } from './failures';
import type { AssistantState, Card, Draft, HfDatasetInfo, ModuleFailure, PatchResult } from './types';

export { TOOL_DEFINITIONS } from './toolDefs';

export interface ToolContext {
  token: string;
  username: string;
  getDraft(): Draft; // a getter: the draft changes mid-turn
  setDraft(d: Draft): void;
  postCard(card: Card): void;
  hfInfos: Map<string, HfDatasetInfo>; // datasets inspected so far; propose_dataset_plan validates against these
  setDatasetPlan(p: AssistantState['datasetPlan']): void;
}

const SYSTEM_ID = 'expanse-tapis-static';
const MAX_CLASSES_SAMPLED = 3; // bounds the Tapis listing calls
const MAX_DATASET_BYTES = 5e9;
const CLASSES_MIN = 2;
const CLASSES_MAX = 50;

/** Failures of a finished run; also used by the polling in useCurriculumAgent. */
export async function jobFailures(token: string, uuid: string): Promise<ModuleFailure[]> {
  const job = await fetchJobDetails(token, uuid);
  return parseFailures(await fetchJobLogs(token, uuid, job));
}

async function inspectDataset(token: string, path: string) {
  const root = (await fetchSystemRootDir(token)).replace(/\/+$/, '');
  const rel = path.startsWith(root) ? path.slice(root.length) : path;
  const dirs = (await listSystemFiles(token, SYSTEM_ID, rel)).filter((f) => f.type === 'dir');
  const sample: Record<string, number> = {};
  for (const d of dirs.slice(0, MAX_CLASSES_SAMPLED)) {
    sample[d.name] = (await listSystemFiles(token, SYSTEM_ID, d.path)).filter((f) => f.type !== 'dir').length;
  }
  return { classCount: dirs.length, classNames: dirs.slice(0, 20).map((d) => d.name), imagesInSampledClasses: sample };
}

// Why a dataset can't be offered, or null when it can
function unusable(i: HfDatasetInfo): string | null {
  if (i.gated) return 'gated (needs an access request)';
  if (i.layout === 'unsupported') return 'unsupported layout';
  if ((i.bytes ?? 0) > MAX_DATASET_BYTES) return 'larger than 5 GB';
  if (!Object.values(i.labelColumns).some((n) => n.length >= CLASSES_MIN && n.length <= CLASSES_MAX)) return `needs ${CLASSES_MIN} to ${CLASSES_MAX} classes`;
  return null;
}

// Compact for the model: no sample URLs
const summary = ({ samples: _s, ...rest }: HfDatasetInfo) => rest;

async function inspectCandidates(ids: unknown, ctx: ToolContext) {
  if (!Array.isArray(ids) || !ids.length) return { error: 'ids must be a non-empty array' };
  const candidates: HfDatasetInfo[] = [];
  const skipped: Array<{ id: string; reason: string }> = [];
  for (const id of ids.slice(0, 3).map(String)) {
    try {
      const info = await inspectHfDataset(ctx.token, id);
      const reason = unusable(info);
      if (reason) skipped.push({ id, reason });
      else {
        candidates.push(info);
        ctx.hfInfos.set(info.id, info);
      }
    } catch (e) {
      if (/401/.test(String(e))) throw e;
      skipped.push({ id, reason: e instanceof Error ? e.message : String(e) });
    }
  }
  if (candidates.length) ctx.postCard({ kind: 'hf_datasets', candidates });
  return { candidates: candidates.map(summary), skipped, note: candidates.length ? 'Card shown. Wait for the educator to choose.' : 'Nothing usable. Search again.' };
}

export async function executeTool(name: string, args: any, ctx: ToolContext): Promise<unknown> {
  const { token } = ctx;
  const draftResult = (r: PatchResult, card: Card | null) => {
    if (r.ok) {
      ctx.setDraft(r.draft);
      if (card) ctx.postCard(card);
    }
    return { ok: r.ok, errors: r.errors, missing: missingFields(r.draft) };
  };

  switch (name) {
    case 'list_datasets':
      return (await fetchAvailableDatasets(token, ctx.username)).map((d) => ({ name: d.name, path: d.clusterPath, source: d.source }));
    case 'inspect_dataset':
      return inspectDataset(token, String(args.path ?? ''));
    case 'list_jobs':
      return (await fetchUserJobs(token, 10)).map((j) => ({ uuid: j.uuid, name: j.name, status: j.status, created: j.created }));
    case 'get_job_status':
      return fetchJobStatus(token, args.uuid);
    case 'get_job_failures':
      return (await jobFailures(token, args.uuid)).map((f) => ({ ...f, ...explainFailure(f) }));
    case 'get_rerun_status': {
      const job = await fetchJobDetails(token, args.uuid);
      return fetchPhase2RerunStatus(token, job, (await fetchJobStatus(token, args.uuid)).status);
    }
    case 'search_datasets':
      return (await searchDatasets(token, String(args.query ?? ''))).filter((d) => !d.gated);
    case 'inspect_hf_datasets':
      return inspectCandidates(args.ids, ctx);
    case 'propose_dataset_plan': {
      const info = ctx.hfInfos.get(String(args.plan?.repo));
      if (!info) return { ok: false, errors: ['Inspect this dataset with inspect_hf_datasets first.'] };
      // The model only chooses splits, columns, class_map, max_per_class and name; the rest comes from the inspected info
      const splits = Array.isArray(args.plan.splits) ? args.plan.splits : [];
      const filled = { ...args.plan, repo: info.id, revision: info.revision, layout: info.layout, config: info.config, data_files: [...new Set(splits.flatMap((x: string) => info.dataFiles[x] ?? []))] };
      const r = validateDatasetPlan(filled, info);
      if (!r.ok) return { ok: false, errors: r.errors };
      ctx.setDatasetPlan({ info, plan: r.plan! });
      ctx.postCard({ kind: 'dataset_plan' });
      return { ok: true, summary: describePlan(r.plan!, info), note: 'Plan card shown. Nothing downloads until the educator clicks its button.' };
    }
    case 'update_draft': {
      const r = applyPatch(ctx.getDraft(), args.patch);
      return draftResult(r, r.changes.length ? { kind: 'changes', changes: r.changes } : null);
    }
    case 'set_week_plan':
      return draftResult(setWeekPlan(ctx.getDraft(), args.modules), { kind: 'week_plan' });
    case 'edit_week':
      return draftResult(editWeek(ctx.getDraft(), Number(args.week), args.patch), { kind: 'week_plan' });
    case 'show_upload_card':
      ctx.postCard({ kind: 'upload' });
      return { ok: true, note: 'Card shown. Wait for the educator to upload.' };
    case 'show_dataset_picker':
      ctx.postCard({ kind: 'dataset_picker' });
      return { ok: true, note: 'Card shown. Wait for the educator to pick.' };
    case 'propose_submit': {
      const d = ctx.getDraft();
      const missing = missingFields(d);
      const errors = missing.length ? [] : validateDraft(d);
      if (missing.length || errors.length) return { ok: false, missing, errors };
      ctx.postCard({ kind: 'review' });
      return { ok: true, note: 'Review card shown. Nothing is submitted until the educator clicks Submit.' };
    }
    case 'propose_rerun':
      ctx.postCard({ kind: 'rerun', jobUuid: String(args.uuid), weeks: args.weeks === 'all' ? 'all' : 'failed' });
      return { ok: true, note: 'Rerun card shown. Nothing reruns until the educator clicks it.' };
    default:
      return { error: `Unknown tool ${name}` };
  }
}
