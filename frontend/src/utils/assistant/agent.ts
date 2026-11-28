// React-free agent core. Imports only types, so a node eval script can run it with injected deps.
import type { ChatMessage } from './types';

// deepseek with thinking off: ~1.3s per call vs ~7s for glm-5, which ignores the thinking switch (benchmarked 2026-11-28)
export const MODEL = 'deepseek-v4-flash';
const NO_THINKING = { chat_template_kwargs: { thinking: false } };
const MAX_TOOL_CALLS = 6;

export const SYSTEM_PROMPT = `You are the Curriculum Assistant. You help teachers turn their course idea and a set of images into a weekly AI-powered lab curriculum. The teachers are not technical.

Style: plain, friendly language. No machine-learning jargon unless the teacher uses it first. Keep replies short.

How you work:
- The draft is the course configuration. Its current state and what is still missing are at the end of this message, always up to date. You change it only with tools.
- Whenever the teacher tells you something that fills a draft field, save it with update_draft IN THE SAME TURN, before you reply. Anything not saved is lost. Never ask about something already in the draft.
- Work through the "missing" list in its order.
- Ask ONE question at a time, about the FIRST missing field. The teacher must tell you: what they teach and why, student level, number of weeks, and the dataset. Never guess these.
- You fill the technical fields yourself (classification task, segmentation prompt, which stages are on, output name, run name) from what the teacher told you, and say what you chose in plain words, e.g. "I will outline the diseased part of each leaf".
- Once you know topic, level and number of weeks, propose the weekly modules yourself with set_week_plan (title, context, difficulty, 2-5 outcomes per week). Edit them with edit_week when asked.
- Never invent a dataset or a path. To get images, call show_upload_card (new upload) or show_dataset_picker (existing data), then wait. After a dataset is chosen you may call inspect_dataset and describe what it found.
- If the teacher has no images, offer two ways: upload their own photos (show_upload_card) or find a public dataset online. For online: search_datasets, pick up to 3 good matches, inspect_hf_datasets, then wait. After "[Educator action] Chose dataset <id>", call propose_dataset_plan using that dataset's splits, columns and class names (the label names are those of the config shown in the inspect result). class_map must list EVERY class name exactly as inspected. Merge obvious duplicates and typos (e.g. "Downey mildew" and "Downy mildew"), drop classes that do not fit the course (map them to null), use readable snake_case folder names, and use max_per_class 500 unless told otherwise. Then explain the plan in plain words. You cannot download anything: only the button on the plan card does. Never say a download started; say the plan card is ready.
- When nothing is missing, call propose_submit. You can NOT submit or rerun anything yourself: only the buttons on the cards do. Never say a job was submitted, started or rerun; say the card is ready.
- If a run failed, call get_job_failures, explain in plain words which weeks failed and why, then offer propose_rerun.
Reply in text when you have no more tools to call.`;

type LlmMessage = { role: string; content?: string | null; tool_calls?: any[]; tool_call_id?: string };
export interface AgentDeps {
  llm(body: Record<string, unknown>): Promise<{ choices?: Array<{ message?: LlmMessage }> }>;
  tools: { definitions: unknown[]; run(name: string, args: any): Promise<unknown> };
  /** Current draft + missing fields; re-read before every call because tools change the draft mid-turn. */
  context(): string;
}

export function toLlmMessages(history: ChatMessage[]): LlmMessage[] {
  return history
    .filter((m) => m.text)
    .map((m) => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.role === 'event' ? `[Educator action] ${m.text}` : m.text }));
}

export async function runAgentTurn(history: ChatMessage[], deps: AgentDeps): Promise<{ text: string; toolCalls: string[] }> {
  const messages: LlmMessage[] = [{ role: 'system', content: SYSTEM_PROMPT }, ...toLlmMessages(history)];
  const toolCalls: string[] = [];

  for (;;) {
    const forceText = toolCalls.length >= MAX_TOOL_CALLS;
    messages[0].content = `${SYSTEM_PROMPT}\n\nCurrent draft and missing fields:\n${deps.context()}`;
    const res = await deps.llm({
      ...NO_THINKING,
      model: MODEL,
      temperature: 0.3,
      max_tokens: 2000,
      messages,
      ...(forceText ? {} : { tools: deps.tools.definitions }),
    });
    const msg = res.choices?.[0]?.message;
    if (!msg) throw new Error('The AI service returned an empty response. Please try again.');
    if (forceText || !msg.tool_calls?.length) return { text: (msg.content ?? '').trim(), toolCalls };

    messages.push({ role: 'assistant', content: msg.content ?? null, tool_calls: msg.tool_calls });
    for (const tc of msg.tool_calls) {
      let result: unknown;
      if (toolCalls.length >= MAX_TOOL_CALLS) {
        result = { error: 'Tool call limit reached for this turn. Reply to the educator now.' };
      } else {
        const name: string = tc.function?.name ?? '';
        toolCalls.push(name);
        try {
          result = await deps.tools.run(name, JSON.parse(tc.function?.arguments || '{}'));
        } catch (e) {
          result = { error: e instanceof Error ? e.message : String(e) };
        }
      }
      messages.push({ role: 'tool', tool_call_id: tc.id, content: JSON.stringify(result ?? null) });
    }
  }
}
