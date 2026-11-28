// Shared contract for the Curriculum Assistant (dev/plans/chatbot_page_plan.md). Every assistant module codes against these.
import type { ConfigFormData } from '../yamlGenerator';
import type { CurriculumModule } from '../../presets';
import type { TapisJobSubmitResponse } from '../../services/tapis';

/** The config being built in chat. Rendered to YAML with generateCurriculumYaml(draft). */
export type Draft = ConfigFormData & { jobName: string };

/** Fields the LLM may set through update_draft. datasetPath is deliberately absent: only the upload/picker cards set it. */
export type DraftPatch = Partial<
  Pick<
    Draft,
    | 'domain'
    | 'contextStatement'
    | 'subject'
    | 'targetLevel'
    | 'classificationActive'
    | 'classificationTask'
    | 'segmentationActive'
    | 'segmentationPrompt'
    | 'xaiActive'
    | 'outputPath'
    | 'topicName'
    | 'topicDescription'
    | 'jobName'
  >
> & { weeks?: number };

export interface FieldChange {
  field: string;
  from: unknown;
  to: unknown;
}

/** A required item still missing; `question` is a plain-English hint for what to ask the educator. */
export interface MissingField {
  field: string;
  question: string;
}

export interface PatchResult {
  ok: boolean;
  draft: Draft; // unchanged draft when ok is false
  errors: string[]; // fed back to the model, not shown to the educator
  changes: FieldChange[];
}

/** One failed Phase 2 module, parsed from tapisjob.out. */
export interface ModuleFailure {
  week: number;
  module: string;
  kind: 'connection' | 'planning' | 'other';
  message: string;
}

/** Cleaning plan for a Hugging Face dataset (dev/plans/dataset_fetch_plan.md). scripts/prepare_dataset.py reads this exact JSON. */
export interface DatasetPlan {
  repo: string; // "owner/name"
  revision: string; // commit sha, pinned
  layout: 'parquet' | 'imagefolder';
  /** Hugging Face config (subset), e.g. "default" or "raw"; label names can differ between configs. */
  config: string;
  splits: string[];
  /** Repo file globs for this config's splits, from inspect (e.g. ["augmented/train-*"]); the script downloads and reads only these. */
  data_files: string[];
  image_column: string; // parquet only; "" for imagefolder
  label_column: string; // parquet: the ClassLabel column; imagefolder: "" (labels are folder names)
  class_map: Record<string, string | null>; // every original label -> target folder ([a-z0-9_]+) or null to drop
  max_per_class: number;
  name: string; // dataset folder name ([a-z0-9_]+), under smart_curriculum_designer_datasets
}

/** What inspect_hf_dataset learned, without downloading. */
export interface HfDatasetInfo {
  id: string;
  revision: string;
  license?: string;
  gated: boolean;
  downloads: number;
  rows?: number;
  bytes?: number;
  layout: 'parquet' | 'imagefolder' | 'unsupported';
  /** The config this info describes ("default" when present, else the first), and all configs the repo has. */
  config: string;
  configs: string[];
  splits: string[]; // splits of `config`
  /** split -> repo file globs, from cardData.configs[].data_files; else derived from the repo's file list (files under "<config>/" for a named config). */
  dataFiles: Record<string, string[]>;
  imageColumns: string[];
  labelColumns: Record<string, string[]>; // ClassLabel column (or "" for imagefolder) -> class names
  classCounts?: Record<string, Record<string, number>>; // column -> class name -> images, when the viewer has statistics
  samples: Array<{ src: string; label: string }>;
}

export type Card =
  | { kind: 'upload' }
  | { kind: 'dataset_picker' }
  | { kind: 'changes'; changes: FieldChange[] }
  | { kind: 'week_plan' }
  | { kind: 'review' }
  | { kind: 'job'; jobUuid: string }
  | { kind: 'failure'; jobUuid: string; failures: ModuleFailure[] }
  | { kind: 'rerun'; jobUuid: string; weeks: 'failed' | 'all' }
  | { kind: 'artifacts'; jobUuid: string }
  | { kind: 'sign_in' }
  | { kind: 'hf_datasets'; candidates: HfDatasetInfo[] } // snapshot: candidates don't change
  | { kind: 'dataset_plan' }; // live: reads AssistantState.datasetPlan

export interface ChatMessage {
  id: string;
  /** 'event' = something the educator did in a card (e.g. uploaded a dataset); shown small, and sent to the model as a user turn. */
  role: 'user' | 'assistant' | 'event';
  text?: string;
  card?: Card;
  at: number; // Date.now()
}

export interface TrackedRun {
  jobUuid: string;
  name: string;
  kind: 'phase1' | 'phase2' | 'rerun' | 'dataset';
  /** dataset runs: the cluster path the prepared dataset lands in */
  datasetPath?: string;
  parentUuid?: string;
  lastStatus?: string;
}

export interface AssistantState {
  messages: ChatMessage[];
  draft: Draft;
  runs: TrackedRun[];
  /** The dataset plan being reviewed; one at a time, like the draft. Optional so older saved state still loads. */
  datasetPlan?: { info: HfDatasetInfo; plan: DatasetPlan } | null;
}

/** What useCurriculumAgent() returns; the page and cards use only this. */
export interface CurriculumAgent {
  state: AssistantState;
  busy: boolean;
  /** What the assistant is doing right now in plain words ("Drafting your weekly plan..."); null when idle. */
  status: string | null;
  error: string | null;
  send(text: string): Promise<void>;
  /** Card-side edits (dataset chosen, week plan edited). `note` is posted as an 'event' message and told to the model. */
  editDraft(fn: (d: Draft) => Draft, note?: string): void;
  /** Only the review card's Submit button calls this. */
  submit(): Promise<TapisJobSubmitResponse>;
  /** Only the rerun card's button calls this. */
  rerun(jobUuid: string, weeks: 'failed' | 'all'): Promise<TapisJobSubmitResponse>;
  /** Card-side edits of the dataset plan; the result is checked with validateDatasetPlan before it is kept. */
  editDatasetPlan(fn: (p: DatasetPlan) => DatasetPlan, note?: string): void;
  /** Only the dataset plan card's "Download and prepare" button calls this. */
  prepareDataset(): Promise<TapisJobSubmitResponse>;
  reset(): void;
}

export type { CurriculumModule };
