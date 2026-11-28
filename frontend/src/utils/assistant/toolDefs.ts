// Pure JSON-schema tool definitions (no imports, so a node eval script can load them).
const fn = (name: string, description: string, properties: Record<string, unknown> = {}, required: string[] = []) => ({
  type: 'function' as const,
  function: { name, description, parameters: { type: 'object', properties, required } },
});

const str = (description: string) => ({ type: 'string', description });
const uuid = { uuid: str('Job uuid') };

const moduleProps = {
  title: str('Short module title'),
  context: str('What the students do and learn this week, in 1-3 sentences'),
  difficulty: { type: 'string', enum: ['Beginner', 'Intermediate', 'Advanced'] },
  estimated_days: { type: 'integer', minimum: 1, maximum: 14 },
  learning_outcomes: { type: 'array', items: { type: 'string' }, minItems: 2, maxItems: 5 },
};
const week = { type: 'integer', minimum: 1, maximum: 24 };

const draftFields = {
  domain: str('Subject area of the images, e.g. "plant disease detection"'),
  contextStatement: str('One or two sentences on what the course is about and who it is for'),
  subject: str('Course subject, e.g. "Biology"'),
  targetLevel: str('Student level, e.g. "10th grade"'),
  codingExperience: { type: 'string', enum: ['none', 'some', 'comfortable'], description: "The students' coding experience; 'none' if the teacher is unsure" },
  classificationActive: { type: 'boolean' },
  classificationTask: str('What the image classifier should tell apart'),
  segmentationActive: { type: 'boolean' },
  segmentationPrompt: str('What to outline in each image'),
  xaiActive: { type: 'boolean', description: 'Show which parts of the image the model looked at' },
  outputPath: str('Output folder name'),
  topicName: str('Topic name'),
  topicDescription: str('Topic description'),
  jobName: str('Short run name: letters, numbers and dashes'),
};

export const TOOL_DEFINITIONS = [
  fn('list_datasets', 'List image datasets the educator already has on the cluster.'),
  fn('inspect_dataset', 'Count class folders and sample images in a dataset.', { path: str('Dataset path from list_datasets') }, ['path']),
  fn('list_jobs', "List the educator's most recent runs."),
  fn('get_job_status', 'Get the status of a run.', uuid, ['uuid']),
  fn('get_job_failures', "Read a run's log and explain which weeks failed and why.", uuid, ['uuid']),
  fn('get_rerun_status', 'Check whether a run can be rerun and which weeks would be kept.', uuid, ['uuid']),
  fn(
    'update_draft',
    'Change fields of the draft. Cannot set the dataset; use the upload or picker cards.',
    // config.py's check_weeks_range only accepts 4..24 weeks
    { patch: { type: 'object', properties: { ...draftFields, weeks: { ...week, minimum: 4, description: 'Course length, 4 to 24 weeks' } } } },
    ['patch']
  ),
  fn(
    'set_week_plan',
    'Replace the whole weekly plan: one module per week, in week order, as many modules as the course has weeks.',
    {
      modules: {
        type: 'array',
        minItems: 4,
        maxItems: 24,
        // No week field: the order is the week number (setWeekPlan assigns it)
        items: { type: 'object', properties: moduleProps, required: ['title', 'context', 'difficulty', 'learning_outcomes'] },
      },
    },
    ['modules']
  ),
  fn('edit_week', 'Edit one week of the plan.', { week, patch: { type: 'object', properties: moduleProps } }, ['week', 'patch']),
  fn('show_upload_card', 'Show a card where the educator uploads their image dataset.'),
  fn('show_dataset_picker', 'Show a card where the educator picks a dataset they already have.'),
  fn('search_datasets', 'Search Hugging Face for public image-classification datasets. Returns id, downloads, license and gated.', { query: str('Search words, e.g. "plant leaf disease"') }, ['query']),
  fn(
    'inspect_hf_datasets',
    'Look up 1-3 Hugging Face datasets (no download) and show the educator a card with sample images. Returns the label columns and class names you need to plan.',
    { ids: { type: 'array', items: { type: 'string' }, minItems: 1, maxItems: 3, description: 'Dataset ids from search_datasets' } },
    ['ids']
  ),
  fn(
    'propose_dataset_plan',
    'Propose how to clean the chosen Hugging Face dataset. repo, revision, layout, config and data_files are filled in for you. Shows a plan card; nothing downloads until the educator clicks its button.',
    {
      plan: {
        type: 'object',
        properties: {
          repo: str('Dataset id'),
          splits: { type: 'array', items: { type: 'string' } },
          image_column: str('Image column; "" for imagefolder'),
          label_column: str('Label column; "" for imagefolder'),
          class_map: { type: 'object', description: 'EVERY original class name -> target folder name (lowercase letters, digits, underscore) or null to drop it', additionalProperties: { type: ['string', 'null'] } },
          max_per_class: { type: 'integer', minimum: 20, maximum: 5000 },
          name: str('Dataset folder name: lowercase letters, digits, underscore'),
        },
        required: ['repo', 'splits', 'image_column', 'label_column', 'class_map', 'max_per_class', 'name'],
      },
    },
    ['plan']
  ),
  fn('propose_submit', 'Show the review card with the Submit button. Does not submit by itself.'),
  fn('propose_rerun', 'Show a rerun card for a finished run. Does not rerun by itself.', { ...uuid, weeks: { type: 'string', enum: ['failed', 'all'] } }, ['uuid', 'weeks']),
];
