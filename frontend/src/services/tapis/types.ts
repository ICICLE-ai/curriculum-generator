export interface TapisJob {
  uuid: string;
  name: string;
  appId: string;
  appVersion?: string;
  status: string;
  created?: string;
  ended?: string;
  lastMessage?: string;
  execSystemId?: string;
  execSystemExecDir?: string;
  execSystemOutputDir?: string;
  archiveSystemId?: string;
  archiveSystemDir?: string;
  parameterSet?: any;
  nodeCount?: number;
  coresPerNode?: number;
  memoryMB?: number;
  maxMinutes?: number;
}

export interface PipelineStage {
  id: string;
  name: string;
  phase?: string;
  status: 'READY' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  details?: string;
  progress?: string;
  start_time?: number;
  end_time?: number;
  duration_sec?: number;
  metrics?: Record<string, unknown>;
  error?: string;
}

export interface PipelineProgressData {
  status: string;
  current_stage?: string;
  current_message?: string;
  progress_percent: number;
  elapsed_seconds?: number;
  updated_at?: string;
  stages: PipelineStage[];
  final_metrics?: Record<string, unknown>;
}

export interface TapisJobSubmitPayload {
  name: string;
  appId: string;
  appVersion: string;
  description?: string;
  execSystemId: string;
  execSystemLogicalQueue: string;
  nodeCount: number;
  coresPerNode: number;
  memoryMB: number;
  maxMinutes: number;
  execSystemExecDir?: string;
  execSystemInputDir?: string;
  execSystemOutputDir?: string;
  parameterSet: {
    appArgs?: Array<{ name: string; arg: string }>;
    schedulerOptions?: Array<{ name: string; arg: string }>;
    containerArgs?: Array<{ name: string; arg: string }>;
    envVariables?: Array<{ key: string; value: string }>;
  };
}

export interface TapisJobSubmitResponse {
  uuid: string;
  name: string;
  status: string;
  appId: string;
  created?: string;
}

export interface TapisFileItem {
  name: string;
  path: string;
  clusterPath?: string;
  size?: number;
  lastModified?: string;
  type?: string;
}

export interface TapisDatasetItem {
  name: string;
  path: string;
  clusterPath: string;
  type?: string;
  source: 'shared' | 'user';
}

export interface TapisTransferResponse {
  uuid: string;
  status: string;
  tag?: string;
  estimatedTotalBytes?: number;
  totalBytesTransferred?: number;
  errorMessage?: string;
}

