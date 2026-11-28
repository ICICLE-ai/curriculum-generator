import type { ModuleFailure } from './types';

const CONNECTION = /RemoteProtocolError|peer closed connection|APIConnectionError|incomplete chunked read|timed out/i;

function kindOf(message: string): ModuleFailure['kind'] {
  if (CONNECTION.test(message)) return 'connection';
  if (/Lesson planning failed/i.test(message)) return 'planning';
  return 'other';
}

/** Failed Phase 2 modules from tapisjob.out: the final summary block, else the per-week FAILED lines. */
export function parseFailures(log: string): ModuleFailure[] {
  const found = new Map<string, ModuleFailure>(); // keyed by week+module: the summary appears twice in the log
  const add = (week: string, module: string, message: string) => {
    found.set(`${week}/${module}`, { week: Number(week), module, kind: kindOf(message), message: message.trim() });
  };

  const header = log.search(/module\(s\) failed:/);
  if (header >= 0) {
    for (const m of log.slice(header).matchAll(/^(\w+) \(Week (\d+)\): (.+)$/gm)) add(m[2], m[1], m[3]);
  }
  if (found.size === 0) {
    for (const m of log.matchAll(/^\[Week (\d+)\] FAILED: (.+)$/gm)) {
      const [, msg, logPath] = m[2].match(/^(.*?)(?: \(\d+ min\))?(?: \| log: (.*))?$/)!;
      add(m[1], logPath?.match(/Week_\d+\/(\w+)\//)?.[1] ?? 'unknown', msg);
    }
  }
  return [...found.values()].sort((a, b) => a.week - b.week);
}

/** Plain-English reason and next step for a non-technical educator. */
export function explainFailure(f: ModuleFailure): { reason: string; advice: string } {
  if (f.kind === 'connection') {
    return {
      reason: `Week ${f.week} lost its connection to the AI service part-way through.`,
      advice: 'This is usually temporary. Rerunning the failed weeks normally works.',
    };
  }
  if (f.kind === 'planning') {
    return {
      reason: `The AI could not come up with a lesson plan for week ${f.week}.`,
      advice:
        'Rerun the failed weeks once. If it fails again, reword that week\'s title or outcomes; that needs a new run, because the settings are locked once a job starts.',
    };
  }
  const last = f.message.split('\n').filter(Boolean).pop() ?? f.message;
  return {
    reason: `Week ${f.week} stopped with an error: ${last}`,
    advice: 'Try rerunning the failed weeks. If it fails again, send this message to the team.',
  };
}
