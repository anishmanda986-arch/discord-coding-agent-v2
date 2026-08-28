export interface TelemetryMetrics {
  uptime_seconds: number;
  total_tasks: number;
  success_rate_pct: number;
  failed_tasks: number;
  total_tokens_used: number;
  total_tokens_saved: number;
  estimated_cost_reduction_ratio: string;
  average_task_latency_sec: number;
  total_cost_usd: number;
  cache_hit_rate_pct: number;
  total_tool_calls: number;
}

export interface GatewayHealth {
  status: string;
  gateway: string;
  version: string;
  timestamp: number;
  registered_agents: string[];
  metrics: TelemetryMetrics;
}

export interface DiscoveredModel {
  id: string;
  name: string;
  context_window?: number;
  pricing?: {
    prompt: string;
    completion: string;
  };
}

export interface SkillItem {
  id: string;
  title: string;
  summary: string;
}

export interface TaskExecutionResult {
  success: boolean;
  status: string;
  task_id: string;
  summary: string;
  files_changed: string[];
  test_result: {
    success: boolean;
    passed: boolean;
    details: string;
  };
  deliverable_zip?: string;
  zip_size_bytes?: number;
  metrics: {
    model_calls: number;
    tool_calls: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
  language?: string;
  framework?: string;
  error?: string;
}
