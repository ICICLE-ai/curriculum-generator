export interface LearningObjectiveIdea {
  objective: string;
  plainEnglishOverview: string;
}

interface GenerateObjectivesParams {
  domain: string;
  contextStatement: string;
  subject: string;
  targetLevel: string;
  moduleTitle: string;
  moduleContext: string;
  difficulty: string;
  week: number;
  estimatedDays?: number;
  existingObjectives: string[];
}

export function getLlmCompletionsUrl(): string {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === 'smartcurriculumdesigner.pods.icicleai.tapis.io'
    ) {
      return '/llm/v1/chat/completions';
    }
  }
  return 'https://smartcurriculumdesigner.pods.icicleai.tapis.io/llm/v1/chat/completions';
}

function parseIdeasFromContent(rawContent: string): LearningObjectiveIdea[] {
  const stripped = rawContent
    .trim()
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim();

  const startIdx = stripped.indexOf('[');
  const endIdx = stripped.lastIndexOf(']');
  if (startIdx === -1 || endIdx === -1 || endIdx <= startIdx) {
    throw new Error('Could not parse learning objective suggestions from the AI response.');
  }

  const parsed: unknown = JSON.parse(stripped.slice(startIdx, endIdx + 1));
  if (!Array.isArray(parsed)) {
    throw new Error('Expected a list of learning objective suggestions.');
  }

  const ideas: LearningObjectiveIdea[] = [];
  for (const item of parsed) {
    if (!item || typeof item !== 'object') continue;
    const record = item as Record<string, unknown>;
    const objective = typeof record.objective === 'string' ? record.objective.trim() : '';
    const overview =
      typeof record.plain_english_overview === 'string'
        ? record.plain_english_overview.trim()
        : typeof record.plainEnglishOverview === 'string'
        ? record.plainEnglishOverview.trim()
        : '';

    if (objective && overview) {
      ideas.push({ objective, plainEnglishOverview: overview });
    }
  }

  if (ideas.length === 0) {
    throw new Error('No valid learning objective suggestions were returned. Try again.');
  }

  return ideas;
}

export async function generateLearningObjectiveIdeas(
  token: string,
  params: GenerateObjectivesParams
): Promise<LearningObjectiveIdea[]> {
  if (!token?.trim()) {
    throw new Error('Please sign in to generate learning objective ideas.');
  }

  const systemPrompt = [
    'You are an expert curriculum designer helping instructors plan hands-on AI and computer vision modules.',
    'Return ONLY a valid JSON array of 4 objects, with no extra prose or markdown outside the JSON.',
    'Each object must have exactly two string keys:',
    '- "objective": a concise, actionable student learning objective (1 sentence, starting with a concrete verb like Load, Compute, Build, Evaluate, Inspect, Implement).',
    '- "plain_english_overview": a 1-2 sentence jargon-free explanation in plain English describing what this objective means in practice and why students learn it.',
  ].join(' ');

  const existingList =
    params.existingObjectives.length > 0
      ? params.existingObjectives.map((o) => `- ${o}`).join('\n')
      : '(none yet)';

  const userPrompt = [
    `Course Domain: ${params.domain || 'General AI / Computer Vision'}`,
    `Course Subject: ${params.subject || 'AI Vision Curriculum'}`,
    `Student Level: ${params.targetLevel || 'Undergraduate / High School STEM'}`,
    `Course Goal: ${params.contextStatement || 'Apply computer vision to real image datasets'}`,
    '',
    `Week: ${params.week}`,
    `Module Title: ${params.moduleTitle || 'Untitled Module'}`,
    `Module Context: ${params.moduleContext || 'Hands-on coding lab using the course dataset'}`,
    `Difficulty: ${params.difficulty || 'Intermediate'}`,
    params.estimatedDays ? `Estimated Time: ${params.estimatedDays} day(s)` : '',
    '',
    'Existing learning objectives for this module (do not repeat these):',
    existingList,
    '',
    'Suggest 4 distinct, practical learning objectives tailored to this module and student level.',
  ]
    .filter(Boolean)
    .join('\n');

  const response = await fetch(getLlmCompletionsUrl(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token.trim()}`,
    },
    body: JSON.stringify({
      model: 'qwen3-small',
      chat_template_kwargs: { enable_thinking: false },
      temperature: 0.5,
      max_tokens: 900,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired — please sign in again.');
    }
    if (response.status === 429) {
      throw new Error('Rate limit reached — please wait a moment and try again.');
    }
    const detail = await response.text().catch(() => '');
    throw new Error(`Idea generation failed (${response.status})${detail ? `: ${detail.slice(0, 180)}` : ''}`);
  }

  const data = (await response.json()) as {
    choices?: Array<{ message?: { content?: string | null } }>;
  };
  const content = data?.choices?.[0]?.message?.content;
  if (!content) {
    throw new Error('The AI service returned an empty response. Please try again.');
  }

  return parseIdeasFromContent(content);
}
