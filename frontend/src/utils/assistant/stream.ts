// Assembles an OpenAI-style SSE chat stream into the same shape as a non-streamed reply.
// Streaming exists so the UI can say which tool the model is writing (a week plan takes ~10s) before it finishes.
type ToolCall = { id: string; type: 'function'; function: { name: string; arguments: string } };

export async function readChatStream(
  body: ReadableStream<Uint8Array>,
  onToolName: (name: string) => void
): Promise<{ choices: Array<{ message: { role: 'assistant'; content: string; tool_calls?: ToolCall[] } }> }> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let content = '';
  const calls: ToolCall[] = [];
  let buf = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split('\n');
    buf = lines.pop() ?? '';
    for (const line of lines) {
      const data = line.startsWith('data:') ? line.slice(5).trim() : '';
      if (!data || data === '[DONE]') continue;
      const delta = JSON.parse(data).choices?.[0]?.delta;
      if (!delta) continue;
      if (delta.content) content += delta.content;
      for (const tc of delta.tool_calls ?? []) {
        const call = (calls[tc.index ?? 0] ??= { id: '', type: 'function', function: { name: '', arguments: '' } });
        if (tc.id) call.id = tc.id;
        if (tc.function?.name) {
          call.function.name += tc.function.name;
          onToolName(call.function.name);
        }
        if (tc.function?.arguments) call.function.arguments += tc.function.arguments;
      }
    }
  }
  const tool_calls = calls.filter(Boolean);
  return { choices: [{ message: { role: 'assistant', content, ...(tool_calls.length ? { tool_calls } : {}) } }] };
}
