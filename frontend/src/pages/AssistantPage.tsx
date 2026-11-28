import React, { useEffect, useRef, useState } from 'react';
import { RotateCcw, Send } from 'lucide-react';
import { PageHeader } from '../components/ui';
import { AssistantCard } from '../components/assistant/AssistantCard';
import { BackgroundTasksPanel } from '../components/assistant/BackgroundTasksPanel';
import type { CurriculumAgent } from '../utils/assistant/types';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

// Editors that need the whole chat width instead of shrinking to their content
const WIDE_CARDS = new Set(['week_plan', 'review', 'upload', 'hf_datasets', 'dataset_plan']);

// remark-math only knows $...$ / $$...$$ (display only when $$ sits on its own lines); models often write \(...\) and \[...\]
const toDollarMath = (s: string) => s.replace(/\\\[([\s\S]+?)\\\]/g, '\n$$$$\n$1\n$$$$\n').replace(/\\\(([\s\S]+?)\\\)/g, '$$$1$$');

const MessageText: React.FC<{ text: string }> = ({ text }) => (
  <div className="assistant-text">
    <Markdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{ a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" /> }}
    >
      {toDollarMath(text)}
    </Markdown>
  </div>
);

// The agent is owned by App so a turn or a running job survives switching tabs
export const AssistantPage: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const { messages } = agent.state;
  const [text, setText] = useState('');
  const [confirmReset, setConfirmReset] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' });
  }, [messages.length, agent.busy]);

  const send = () => {
    const t = text.trim();
    if (!t) return; // sending during a turn is fine: it is answered in the next turn
    setText('');
    agent.send(t);
  };

  return (
    <div className="page-container assistant-page">
      <PageHeader
        title="Curriculum Assistant"
        description="Tell me about your course and I will set everything up with you."
        actions={
          confirmReset ? (
            <div className="row-wrap" role="alert">
              <span>Erase this conversation?</span>
              <button type="button" className="btn btn-sm btn-primary" onClick={() => { agent.reset(); setConfirmReset(false); }}>Yes, start over</button>
              <button type="button" className="btn btn-sm btn-secondary" onClick={() => setConfirmReset(false)}>Keep it</button>
            </div>
          ) : (
            <button type="button" className="btn btn-secondary" onClick={() => setConfirmReset(true)}>
              <RotateCcw size={14} aria-hidden="true" /><span>Start over</span>
            </button>
          )
        }
      />

      <div className="assistant-body">
      <BackgroundTasksPanel agent={agent} />
      <div className="assistant-chat">
      <div className="assistant-log" role="log" aria-live="polite" aria-label="Conversation">
        {messages.length === 0 && <p className="muted">Say hello, or describe the course you want to build, for example "a 6-week plant disease unit for 10th graders".</p>}
        {messages.map((m) =>
          m.role === 'event' ? (
            <div key={m.id} className="assistant-event">{m.text}</div>
          ) : (
            <div key={m.id} className={`assistant-msg assistant-msg-${m.role}${m.card && WIDE_CARDS.has(m.card.kind) ? ' assistant-msg-wide' : ''}`}>
              {m.text && <MessageText text={m.text} />}
              {m.card && <div className="assistant-card"><AssistantCard card={m.card} agent={agent} /></div>}
            </div>
          )
        )}
        {agent.busy && <div className="assistant-msg assistant-msg-assistant muted" role="status">{agent.status ?? 'Thinking...'}</div>}
        {agent.error && <div role="alert" className="alert alert-error">{agent.error}</div>}
        <div ref={endRef} />
      </div>

      <form className="assistant-composer" onSubmit={(e) => { e.preventDefault(); send(); }}>
        <label htmlFor="assistant-input" className="sr-only">Your message</label>
        <textarea
          id="assistant-input"
          rows={2}
          value={text}
          placeholder="Type your message. Enter to send, Shift+Enter for a new line."
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); }
          }}
        />
        <button type="submit" className="btn btn-primary" disabled={!text.trim()}>
          <Send size={14} aria-hidden="true" /><span>Send</span>
        </button>
      </form>
      </div>
      </div>
    </div>
  );
};
