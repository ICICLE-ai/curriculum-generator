import { useCallback, useEffect, useRef, useState } from 'react';
import { getLlmCompletionsUrl } from '../services/llm';
import {
  ensureRefreshToken,
  exportConfigToTapis,
  fetchJobDetails,
  fetchJobLogs,
  fetchJobStatus,
  fetchSystemRootDir,
  fetchUserJobs,
  parseJobJson,
  submitPhase2Rerun,
  submitTapisJob,
  TAPIS_DATASETS_DIR,
  type TapisJobSubmitResponse,
} from '../services/tapis';
import { runAgentTurn } from '../utils/assistant/agent';
import { validateDatasetPlan } from '../utils/assistant/datasetPlan';
import { DEFAULT_DRAFT, draftContext, setDataset, validateDraft } from '../utils/assistant/draft';
import { executeTool, jobFailures, TOOL_DEFINITIONS, type ToolContext } from '../utils/assistant/tools';
import { readChatStream } from '../utils/assistant/stream';
import type { AssistantState, Card, ChatMessage, CurriculumAgent, DatasetPlan, Draft, HfDatasetInfo, TrackedRun } from '../utils/assistant/types';
import { DEFAULT_JOB_FIELDS, buildJobPayload } from '../utils/jobPayload';
import { cleanTapisUsername } from '../utils/format';
import { parseJwt } from '../utils/jwt';
import { getStoredToken } from '../utils/storage';
import { statusLabel } from '../utils/status';
import { generateCurriculumYaml } from '../utils/yamlGenerator';

const STORAGE_KEY = 'scd_assistant_v1';
const POLL_MS = 30_000;
const DUPLICATE_WINDOW_MS = 10 * 60_000;
const TERMINAL = ['FINISHED', 'FAILED', 'CANCELLED'];

const isTerminal = (s?: string) => !!s && TERMINAL.includes(s);
const errMsg = (e: unknown) => (e instanceof Error ? e.message : String(e));
const isAuthError = (e: unknown) => /\b401\b|expired|sign in/i.test(errMsg(e));
let seq = 0;
const newMsg = (m: Omit<ChatMessage, 'id' | 'at'>): ChatMessage => ({ ...m, id: `${Date.now()}-${seq++}`, at: Date.now() });

const THINKING = 'Thinking...';
const TOOL_STATUS: Record<string, string> = {
  update_draft: 'Updating your course...',
  set_week_plan: 'Drafting your weekly plan...',
  edit_week: 'Editing a week...',
  list_datasets: 'Looking at your datasets...',
  show_dataset_picker: 'Looking at your datasets...',
  show_upload_card: 'Getting the upload ready...',
  inspect_dataset: 'Checking your images...',
  list_jobs: 'Checking your runs...',
  get_job_status: 'Checking your run...',
  get_job_failures: 'Reading the run log...',
  get_rerun_status: 'Checking what can be rerun...',
  propose_submit: 'Preparing your review...',
  propose_rerun: 'Preparing the rerun...',
  search_datasets: 'Searching public datasets...',
  inspect_hf_datasets: 'Looking at the datasets...',
  propose_dataset_plan: 'Planning how to clean the dataset...',
};

const GREETING = "Hi! I'm your Curriculum Assistant. Tell me what you teach, who your students are and how many weeks the course runs, and I'll build it with you.";
const initialState = (): AssistantState => ({
  messages: [{ id: 'greeting', role: 'assistant', text: GREETING, at: Date.now() }],
  draft: DEFAULT_DRAFT,
  runs: [],
  datasetPlan: null,
});

function loadState(): AssistantState {
  try {
    const s = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (s && Array.isArray(s.messages) && Array.isArray(s.runs) && s.draft && typeof s.draft === 'object') return { ...s, datasetPlan: s.datasetPlan ?? null };
  } catch {
    // bad or blocked storage: start fresh
  }
  return initialState();
}

function auth() {
  const token = getStoredToken();
  const decoded = token ? parseJwt(token) : null;
  if (!token || !decoded || decoded.isExpired) throw new Error('Session expired. Please sign in again.');
  const username = decoded.payload['tapis/username'] || (decoded.payload.sub as string) || '';
  return { token, username, cleanUsername: cleanTapisUsername(username) };
}

export function useCurriculumAgent(): CurriculumAgent {
  const [state, setState] = useState<AssistantState>(loadState);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef(state); // latest state for async code
  const busyRef = useRef(false);
  const pollingRef = useRef(false);
  const hfInfosRef = useRef(new Map<string, HfDatasetInfo>());

  const update = useCallback((fn: (s: AssistantState) => AssistantState) => {
    ref.current = fn(ref.current);
    setState(ref.current);
  }, []);
  const post = useCallback((m: Omit<ChatMessage, 'id' | 'at'>) => update((s) => ({ ...s, messages: [...s.messages, newMsg(m)] })), [update]);
  const track = useCallback((run: TrackedRun) => update((s) => ({ ...s, runs: [...s.runs, run] })), [update]);
  const setBusyBoth = (b: boolean) => {
    busyRef.current = b;
    setBusy(b);
  };
  // Posts the sign-in card unless it is already the last message
  const signIn = useCallback(() => {
    if (ref.current.messages.at(-1)?.card?.kind !== 'sign_in') post({ role: 'assistant', text: 'Your session has expired. Please sign in again.', card: { kind: 'sign_in' } });
  }, [post]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // storage full or blocked: keep working in memory
    }
  }, [state]);

  const runTurn = useCallback(async () => {
    setBusyBoth(true);
    setStatus(THINKING);
    setError(null);
    const cards: Card[] = [];
    try {
      const { token, username } = auth();
      const ctx: ToolContext = {
        token,
        username,
        getDraft: () => ref.current.draft,
        setDraft: (draft) => update((s) => ({ ...s, draft })),
        postCard: (c) => cards.push(c),
        hfInfos: hfInfosRef.current,
        setDatasetPlan: (datasetPlan) => update((s) => ({ ...s, datasetPlan })),
      };
      const { text } = await runAgentTurn(ref.current.messages, {
        llm: async (body) => {
          const resp = await fetch(getLlmCompletionsUrl(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ ...body, stream: true }),
          });
          if (resp.status === 401) throw new Error('401 Session expired');
          if (!resp.ok || !resp.body) throw new Error(`The AI service failed (${resp.status}). Please try again.`);
          setStatus(THINKING);
          return readChatStream(resp.body, (name) => setStatus(TOOL_STATUS[name] ?? THINKING));
        },
        tools: { definitions: TOOL_DEFINITIONS, run: (name, args) => executeTool(name, args, ctx) },
        context: () => draftContext(ref.current.draft),
      });
      if (text) post({ role: 'assistant', text });
      cards.forEach((card) => post({ role: 'assistant', card }));
    } catch (e) {
      if (isAuthError(e)) signIn();
      else setError(errMsg(e));
    } finally {
      setBusyBoth(false);
      setStatus(null);
    }
  }, [post, signIn, update]);

  const send = useCallback(
    async (text: string) => {
      if (busyRef.current || !text.trim()) return;
      post({ role: 'user', text: text.trim() });
      await runTurn();
    },
    [post, runTurn]
  );

  const editDraft = useCallback(
    (fn: (d: Draft) => Draft, note?: string) => {
      update((s) => ({ ...s, draft: fn(s.draft) }));
      if (!note) return;
      post({ role: 'event', text: note });
      if (!busyRef.current) void runTurn();
    },
    [post, runTurn, update]
  );

  const editDatasetPlan = useCallback(
    (fn: (p: DatasetPlan) => DatasetPlan, note?: string) => {
      const cur = ref.current.datasetPlan;
      if (!cur) return;
      const r = validateDatasetPlan(fn(cur.plan), cur.info);
      if (!r.ok) return setError(`That change does not work: ${r.errors.join('; ')}`);
      setError(null);
      update((s) => ({ ...s, datasetPlan: { info: cur.info, plan: r.plan! } }));
      if (!note) return;
      post({ role: 'event', text: note });
      if (!busyRef.current) void runTurn();
    },
    [post, runTurn, update]
  );

  const submit = useCallback(async (): Promise<TapisJobSubmitResponse> => {
    if (busyRef.current) throw new Error('Please wait, the assistant is busy.');
    setBusyBoth(true);
    try {
      const { token, cleanUsername } = auth();
      const draft = ref.current.draft;
      const errors = validateDraft(draft);
      if (errors.length) throw new Error(errors.join('; '));
      const { jobName } = draft;
      if (ref.current.runs.some((r) => r.name === jobName && !isTerminal(r.lastStatus))) throw new Error(`A run named ${jobName} is already in progress.`);
      const recent = (await fetchUserJobs(token, 20)).find((j) => j.name === jobName && Date.now() - Date.parse(j.created || '') < DUPLICATE_WINDOW_MS);
      if (recent) throw new Error(`A run named ${jobName} was just submitted. Change the run name to submit again.`);

      const { clusterPath } = await exportConfigToTapis(token, cleanUsername, `${jobName}.yaml`, generateCurriculumYaml(draft));
      const refresh = await ensureRefreshToken(token);
      const job = await submitTapisJob(
        token,
        buildJobPayload({ ...DEFAULT_JOB_FIELDS, jobName, configFilePath: clusterPath, cleanUsername, selectedArchivePath: '', runMode: 'full' }, refresh)
      );
      track({ jobUuid: job.uuid, name: job.name, kind: 'phase1', lastStatus: job.status });
      post({ role: 'assistant', text: 'Your course run has been submitted.', card: { kind: 'job', jobUuid: job.uuid } });
      return job;
    } catch (e) {
      if (isAuthError(e)) signIn();
      throw e;
    } finally {
      setBusyBoth(false);
    }
  }, [post, signIn, track]);

  const rerun = useCallback(
    async (jobUuid: string, weeks: 'failed' | 'all'): Promise<TapisJobSubmitResponse> => {
      if (busyRef.current) throw new Error('Please wait, the assistant is busy.');
      setBusyBoth(true);
      try {
        const { token } = auth();
        const job = await submitPhase2Rerun(token, await fetchJobDetails(token, jobUuid), weeks, 'cpu');
        track({ jobUuid: job.uuid, name: job.name, kind: 'rerun', parentUuid: jobUuid, lastStatus: job.status });
        post({ role: 'assistant', text: `The rerun of ${weeks === 'failed' ? 'the failed weeks' : 'all weeks'} has been submitted.`, card: { kind: 'job', jobUuid: job.uuid } });
        return job;
      } catch (e) {
        if (isAuthError(e)) signIn();
        throw e;
      } finally {
        setBusyBoth(false);
      }
    },
    [post, signIn, track]
  );

  const prepareDataset = useCallback(async (): Promise<TapisJobSubmitResponse> => {
    if (busyRef.current) throw new Error('Please wait, the assistant is busy.');
    const plan = ref.current.datasetPlan?.plan;
    if (!plan) throw new Error('There is no dataset plan to prepare.');
    setBusyBoth(true);
    try {
      const { token, cleanUsername } = auth();
      const rootDir = (await fetchSystemRootDir(token)).replace(/\/+$/, '');
      if (!rootDir) throw new Error('Could not read the cluster storage location. Please try again.');
      const datasetPath = `${rootDir}/users/${cleanUsername}/${TAPIS_DATASETS_DIR}/${plan.name}`;
      if (ref.current.runs.some((r) => r.kind === 'dataset' && r.datasetPath === datasetPath && !isTerminal(r.lastStatus))) {
        throw new Error(`The dataset ${plan.name} is already being prepared.`);
      }
      // JSON is valid YAML, so the config uploader (which forces .yaml) can store the plan
      const { clusterPath } = await exportConfigToTapis(token, cleanUsername, `${plan.name}_dataset_plan.yaml`, JSON.stringify(plan, null, 2));
      const jobName = `dataset-${plan.name}`;
      const base = buildJobPayload({ ...DEFAULT_JOB_FIELDS, jobName, configFilePath: clusterPath, cleanUsername, selectedArchivePath: '', runMode: 'full' }, await ensureRefreshToken(token));
      // CPU job like the cpu rerun; no archive fields, or it would land among the Phase 1 archives
      const { archiveMode: _m, archiveSystemId: _i, archiveSystemDir: _d, ...payload } = base;
      const ps = payload.parameterSet;
      const job = await submitTapisJob(token, {
        ...payload,
        execSystemLogicalQueue: 'tapisShared',
        parameterSet: {
          ...ps,
          schedulerOptions: ps.schedulerOptions?.map((o) => (o.name === 'gpu-request' ? { ...o, include: false } : o)),
          containerArgs: ps.containerArgs?.map((o) => (o.name === 'bind-gpu' ? { ...o, include: false } : o)),
          envVariables: [...(ps.envVariables ?? []), { key: 'DATASET_PLAN', value: clusterPath }, { key: 'DATASET_OUT', value: `${rootDir}/users/${cleanUsername}/${TAPIS_DATASETS_DIR}` }],
        },
        notes: { task: 'dataset', repo: plan.repo, name: plan.name },
      });
      track({ jobUuid: job.uuid, name: job.name, kind: 'dataset', datasetPath, lastStatus: job.status });
      post({ role: 'assistant', text: `Preparing the dataset "${plan.name}" now. This can take a while.`, card: { kind: 'job', jobUuid: job.uuid } });
      return job;
    } catch (e) {
      if (isAuthError(e)) signIn();
      throw e;
    } finally {
      setBusyBoth(false);
    }
  }, [post, signIn, track]);

  const reset = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    update(() => initialState());
    setError(null);
  }, [update]);

  // Runs to follow: not finished yet, or a finished Phase 1 whose Phase 2 child we haven't found.
  // shortcut: a Phase 1 with no Phase 2 child is polled every 30s while the page is open; add a give-up time if that matters.
  const following = state.runs.some(
    (r) => !isTerminal(r.lastStatus) || (r.kind === 'phase1' && r.lastStatus === 'FINISHED' && !state.runs.some((c) => c.parentUuid === r.jobUuid))
  );

  // Reads the prepare job's log; the dataset path is only trusted when the script printed exactly the path we expected
  const finishDataset = useCallback(
    async (token: string, run: TrackedRun, finished: boolean) => {
      const log = await fetchJobLogs(token, run.jobUuid, await fetchJobDetails(token, run.jobUuid));
      const ready = log.match(/\[DATASET READY\] (.+)/)?.[1].trim();
      const name = run.name.replace(/^dataset-/, '');
      if (finished && ready && ready === run.datasetPath) {
        update((s) => ({ ...s, datasetPlan: s.datasetPlan?.plan.name === name ? null : s.datasetPlan }));
        editDraft((d) => setDataset(d, ready), `Dataset "${name}" is ready and is now the course dataset.`);
      } else {
        const reason = log.match(/\[DATASET FAILED\] (.+)/)?.[1].trim() ?? 'the job ended without finishing the dataset';
        post({ role: 'assistant', text: `The dataset "${name}" could not be prepared: ${reason}. You can change the plan and try again.` });
      }
    },
    [editDraft, post, update]
  );

  useEffect(() => {
    if (!following) return;
    const poll = async () => {
      if (pollingRef.current) return;
      pollingRef.current = true;
      try {
        const { token } = auth();
        for (const run of [...ref.current.runs]) {
          if (!isTerminal(run.lastStatus)) {
            const { status } = await fetchJobStatus(token, run.jobUuid);
            if (status === run.lastStatus) continue;
            const hadStatus = !!run.lastStatus;
            update((s) => ({ ...s, runs: s.runs.map((r) => (r.jobUuid === run.jobUuid ? { ...r, lastStatus: status } : r)) }));
            if (hadStatus) post({ role: 'assistant', text: `${run.name} is now: ${statusLabel(status)}.` });
            if (run.kind === 'dataset') {
              if (status === 'FINISHED' || status === 'FAILED') await finishDataset(token, run, status === 'FINISHED');
            } else if (run.kind !== 'phase1' && status === 'FAILED') {
              const failures = await jobFailures(token, run.jobUuid);
              post({ role: 'assistant', text: `${run.name} had problems.`, card: { kind: 'failure', jobUuid: run.jobUuid, failures } });
            } else if (run.kind !== 'phase1' && status === 'FINISHED') {
              post({ role: 'assistant', text: `${run.name} is done. Your files are ready.`, card: { kind: 'artifacts', jobUuid: run.jobUuid } });
            }
          }
          const latest = ref.current.runs.find((r) => r.jobUuid === run.jobUuid);
          if (run.kind === 'phase1' && latest?.lastStatus === 'FINISHED' && !ref.current.runs.some((c) => c.parentUuid === run.jobUuid)) {
            const child = (await fetchUserJobs(token, 50)).find((j) => parseJobJson(j.notes).parent_job === run.jobUuid);
            if (child) {
              track({ jobUuid: child.uuid, name: child.name, kind: 'phase2', parentUuid: run.jobUuid, lastStatus: child.status });
              post({ role: 'assistant', text: 'The lessons are being written now (Phase 2).', card: { kind: 'job', jobUuid: child.uuid } });
            }
          }
        }
      } catch (e) {
        if (isAuthError(e)) signIn();
      } finally {
        pollingRef.current = false;
      }
    };
    void poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [finishDataset, following, post, signIn, track, update]);

  return { state, busy, status, error, send, editDraft, submit, rerun, editDatasetPlan, prepareDataset, reset };
}
