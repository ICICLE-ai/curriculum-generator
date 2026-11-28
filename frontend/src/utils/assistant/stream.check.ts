// Self-check for readChatStream: node --experimental-strip-types src/utils/assistant/stream.check.ts
import assert from 'node:assert/strict';
import { readChatStream } from './stream.ts';

const chunk = (delta: object) => `data: ${JSON.stringify({ choices: [{ delta }] })}\n\n`;
const sse =
  chunk({ content: 'Hel' }) +
  chunk({ content: 'lo' }) +
  chunk({ tool_calls: [{ index: 0, id: 'a', function: { name: 'set_week_plan' } }] }) +
  chunk({ tool_calls: [{ index: 0, function: { arguments: '{"modules":' } }] }) +
  chunk({ tool_calls: [{ index: 0, function: { arguments: '[]}' } }] }) +
  chunk({ tool_calls: [{ index: 1, id: 'b', function: { name: 'show_upload_card', arguments: '{}' } }] }) +
  'data: [DONE]\n\n';
// Split mid-line to prove buffering across reads
const bytes = new TextEncoder().encode(sse);
const body = new ReadableStream<Uint8Array>({
  start(c) {
    c.enqueue(bytes.slice(0, 37));
    c.enqueue(bytes.slice(37));
    c.close();
  },
});

const names: string[] = [];
const { choices } = await readChatStream(body, (n) => names.push(n));
const msg = choices[0].message;
assert.equal(msg.content, 'Hello');
assert.deepEqual(names, ['set_week_plan', 'show_upload_card']);
assert.deepEqual(msg.tool_calls?.map((c) => [c.id, c.function.name, c.function.arguments]), [
  ['a', 'set_week_plan', '{"modules":[]}'],
  ['b', 'show_upload_card', '{}'],
]);
console.log('stream.check OK');
