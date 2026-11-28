// @ts-nocheck (node script) Live multi-turn smoke against the LLM proxy, real draft logic, streamed like the browser.
// Run from frontend/: node --experimental-strip-types src/utils/assistant/agent.smoke.ts
import { readFileSync } from 'node:fs';
import { runAgentTurn } from './agent.ts';
import { TOOL_DEFINITIONS } from './toolDefs.ts';
import { readChatStream } from './stream.ts';
import { DEFAULT_DRAFT, applyPatch, draftContext, editWeek, missingFields, setWeekPlan } from './draft.ts';

const env = readFileSync(new URL('../../../../.env', import.meta.url), 'utf8');
const jwt = env.match(/^TAPIS_JWT=(.+)$/m)?.[1].trim().replace(/^["']|["']$/g, '');

// Real draft logic; Tapis-backed tools are faked
let draft = DEFAULT_DRAFT;
const apply = (r) => {
  if (r.ok) draft = r.draft;
  else console.log('  REJECTED:', r.errors.join(' | '));
  return { ok: r.ok, errors: r.errors, missing: missingFields(draft) };
};
const run = async (name, args) => {
  if (name === 'update_draft') return apply(applyPatch(draft, args.patch));
  if (name === 'set_week_plan') return apply(setWeekPlan(draft, args.modules));
  if (name === 'edit_week') return apply(editWeek(draft, args.week, args.patch));
  if (name === 'list_datasets') return [];
  if (name.startsWith('show_') || name.startsWith('propose_')) return { ok: true, note: 'Card shown. Wait for the educator.' };
  return { error: `not available in smoke: ${name}` };
};

const llm = async (body) => {
  const r = await fetch('https://smartcurriculumdesigner.pods.icicleai.tapis.io/llm/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
    body: JSON.stringify({ ...body, stream: true }),
  });
  if (!r.ok) throw new Error(`LLM ${r.status}`);
  return readChatStream(r.body, () => {});
};

const history = [];
const turns = [
  'I teach 10th grade biology and want a 6 week unit on plant diseases',
  'I want students to see how computers can spot sick leaves from photos, so they connect biology to AI',
  'They have never coded before',
];
for (const [i, text] of turns.entries()) {
  history.push({ id: `u${i}`, role: 'user', text, at: 0 });
  const t = Date.now();
  const { text: reply, toolCalls } = await runAgentTurn(history, { llm, tools: { definitions: TOOL_DEFINITIONS, run }, context: () => draftContext(draft) });
  history.push({ id: `a${i}`, role: 'assistant', text: reply, at: 0 });
  console.log(`TURN ${i + 1} (${((Date.now() - t) / 1000).toFixed(1)}s) tools: ${toolCalls.join(', ') || '(none)'}`);
  console.log(`  reply: ${reply.replace(/\n/g, ' ').slice(0, 220)}`);
}
console.log('coding:', draft.codingExperience, '| week 1:', draft.modules[0]?.title, '| week 2:', draft.modules[1]?.title);
console.log('weeks planned:', draft.modules.filter((m) => m.title).length, '| datasetPath:', JSON.stringify(draft.datasetPath), '| missing:', missingFields(draft).map((m) => m.field).join(', '));
