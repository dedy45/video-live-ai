export interface SystemStatus {
  state: string;
  mock_mode: boolean;
  uptime_sec: number;
  viewer_count: number;
  current_product: { id: number; name: string; price: string } | null;
  stream_status: string;
  stream_running: boolean;
  emergency_stopped: boolean;
  llm_budget_remaining: number;
  safety_incidents: number;
}

export interface ReadinessCheck {
  name: string;
  passed: boolean;
  status: 'ok' | 'warning' | 'fail';
  message: string;
  blocking: boolean;
}

export interface ReadinessResult {
  overall_status: 'ready' | 'not_ready' | 'degraded';
  checks: ReadinessCheck[];
  blocking_issues: string[];
  recommended_next_action: string;
}

export interface EngineStatus {
  state: string;
  pid: number | null;
  port: number;
  model: string;
  avatar_id: string;
  requested_model: string;
  resolved_model: string;
  requested_avatar_id: string;
  resolved_avatar_id: string;
  transport: string;
  uptime_sec: number;
  last_error: string;
  app_py_exists: boolean;
  model_path_exists: boolean;
  avatar_path_exists: boolean;
}

export interface EngineConfig {
  port: number;
  transport: string;
  model: string;
  avatar_id: string;
  requested_model: string;
  resolved_model: string;
  requested_avatar_id: string;
  resolved_avatar_id: string;
  livetalking_dir: string;
  operator_dashboard?: string;
  debug_urls: {
    webrtcapi: string;
    rtcpushapi: string;
    dashboard_vendor: string;
    echoapi: string;
  };
}

export interface DebugTargetProbe {
  url: string;
  reachable: boolean;
  http_status: number | null;
  error: string | null;
}

export interface LiveTalkingDebugTargets {
  checked_at: string;
  targets: {
    webrtcapi: DebugTargetProbe;
    dashboard_vendor: DebugTargetProbe;
    rtcpushapi: DebugTargetProbe;
  };
}

export interface BrainProviderConfig {
  model: string;
  timeout_ms: number;
  backend: string;
  api_base?: string;
  cost?: string;
}

export interface PromptRuntimeSummary {
  active_revision: string;
  slug: string;
  version: number;
  status: string;
  updated_at?: string;
}

export interface BrainConfig {
  daily_budget_usd: number;
  fallback_order: string[];
  routing_table: Record<string, string[]>;
  prompt: PromptRuntimeSummary;
  providers: Record<string, BrainProviderConfig>;
  task_types?: string[];
  error?: string;
}

export interface DirectorTransition {
  from: string;
  to: string;
  timestamp: number | string;
}

export interface DirectorSnapshot {
  state: string;
  stream_running: boolean;
  emergency_stopped: boolean;
  manual_override: boolean;
  current_phase: string;
  phase_sequence: string[];
  active_provider: string;
  active_model: string;
  active_prompt_revision: string;
  uptime_sec?: number;
  history: DirectorTransition[];
  valid_transitions: string[];
}

export interface DirectorRuntimeContract {
  director: DirectorSnapshot;
  brain: {
    active_provider: string;
    active_model: string;
    routing_table: Record<string, string[]>;
    adapter_count: number;
    daily_budget_usd: number;
  };
  prompt: PromptRuntimeSummary;
  persona: {
    name?: string;
    tone?: string;
    language?: string;
    forbidden_topics?: string[];
    catchphrases?: string[];
  };
  script: {
    current_phase: string;
    phase_sequence: string[];
  };
  error?: string;
}

export type OperatorActionStatus = 'success' | 'blocked' | 'error' | 'pending' | 'warning';

export interface OperatorActionResult {
  status: OperatorActionStatus | 'fail' | 'pass';
  message: string;
  action?: string;
  provenance?: string;
  state?: string;
  blockers?: string[];
  reason_code?: string;
  details?: string[];
  next_step?: string;
  checks?: Array<{ check: string; passed: boolean; message: string }>;
}

export interface VoiceTestSpeakResult extends OperatorActionResult {
  text?: string;
  latency_ms?: number;
  duration_ms?: number;
  audio_length_bytes?: number;
}

export interface VoiceProfile {
  id: number;
  name: string;
  engine: string;
  profile_type?: string;
  supported_languages?: string[];
  quality_tier?: string;
  reference_wav_path: string;
  reference_text: string;
  language: string;
  notes: string;
  guidance?: Record<string, any>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface VoiceLabState {
  mode: 'standalone' | 'attach_avatar' | string;
  active_profile_id: number | null;
  preview_session_id: string;
  selected_avatar_id: string;
  selected_language: 'id' | 'en' | string;
  selected_profile_type: 'quick_clone' | 'studio_voice' | string;
  selected_revision_id?: number | null;
  selected_style_preset?: string;
  selected_stability?: number;
  selected_similarity?: number;
  draft_text: string;
  last_generation_id?: number | null;
  updated_at?: string;
}

export interface VoiceGenerationResult extends OperatorActionResult {
  generation_id: number;
  audio_url: string;
  download_url?: string;
  latency_ms?: number;
  duration_ms?: number;
  audio_length_bytes?: number;
  attached_to_avatar: boolean;
  avatar_session_id?: string;
  language?: string;
  style_preset?: string;
  stability?: number;
  similarity?: number;
  profile?: VoiceProfile;
  lab_state?: VoiceLabState;
}

export interface VoiceGeneration {
  id: number;
  mode: string;
  profile_id: number | null;
  profile_name?: string | null;
  source_type: string;
  input_text: string;
  language?: string;
  emotion: string;
  style_preset?: string;
  stability?: number;
  similarity?: number;
  speed: number;
  status: string;
  audio_path: string;
  audio_filename?: string;
  download_name?: string;
  audio_url?: string;
  download_url?: string;
  audio_size_bytes: number;
  latency_ms: number;
  duration_ms: number;
  attached_to_avatar: boolean;
  avatar_session_id: string;
  created_at?: string;
}

export interface VoiceTrainingJob {
  id: number;
  profile_id: number;
  profile_name?: string | null;
  job_type: string;
  status: string;
  current_stage: string;
  progress_pct: number;
  dataset_path: string;
  log_path: string;
  meta?: Record<string, any>;
  error_text?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ValidationResult {
  status: 'pass' | 'fail' | 'error' | 'blocked';
  checks: Array<{ check: string; passed: boolean; message: string }>;
  blockers?: string[];
  evidence_id?: number;
  error?: string;
}

export type PerformerValidationCheckId =
  | 'runtime_truth'
  | 'engine'
  | 'voice_clone'
  | 'audio_chunking'
  | 'real_mode'
  | 'preview_targets';

export interface PerformerValidationEntry {
  label: string;
  status: 'pass' | 'fail' | 'blocked' | 'error' | 'pending';
  summary: string;
  timestamp: string;
  details?: string[];
}

export interface FaceEngineTruth {
  requested_model: string;
  resolved_model: string;
  requested_avatar_id: string;
  resolved_avatar_id: string;
  engine_state: string;
  fallback_active: boolean;
}

export interface VoiceEngineTruth {
  requested_engine: string;
  resolved_engine: string;
  fallback_active: boolean;
  server_reachable: boolean;
  reference_ready: boolean;
  queue_depth: number;
  chunk_chars: number | null;
  time_to_first_audio_ms: number | null;
  latency_p50_ms: number | null;
  latency_p95_ms: number | null;
  last_latency_ms: number | null;
  last_error: string | null;
}

export interface ResourceMetrics {
  cpu_pct: number;
  ram_pct: number;
  disk_pct: number;
  vram_pct: number | null;
}

export interface RestartCounters {
  voice: number;
  face: number;
  stream: number;
}

export interface IncidentSummary {
  open_count: number;
  highest_severity: string;
}

export interface OpsSummary {
  overall_status: string;
  deployment_mode: string;
  voice_status: string;
  face_status: string;
  stream_status: string;
  incident_summary: IncidentSummary;
  resource_metrics: ResourceMetrics;
  restart_counters: RestartCounters;
}

export interface Incident {
  id: string;
  code: string;
  severity: string;
  subsystem: string;
  message?: string;
  acknowledged?: boolean;
  resolved?: boolean;
  created_at?: string;
}

export interface RuntimeTruth {
  mock_mode: boolean;
  host?: { name: string; role: string };
  deployment_mode?: string;
  incident_summary?: { open_count: number; highest_severity: string };
  guardrails?: { restart_storm: boolean; disk_pressure: boolean };
  director?: DirectorSnapshot;
  face_runtime_mode: string;
  face_engine?: FaceEngineTruth;
  voice_engine?: VoiceEngineTruth;
  voice_runtime_mode: string;
  stream_runtime_mode: string;
  validation_state: string;
  last_validated_at: string | null;
  provenance: Record<string, string>;
  timestamp: string;
}

export interface Product {
  id: number;
  name: string;
  price: number;
  price_formatted: string;
  category: string;
  is_active: boolean;
  stock?: number;
  margin_percent?: number;
  description?: string;
  image_path?: string;
  affiliate_links?: Record<string, string>;
  selling_points?: string[];
  commission_rate?: number;
  objection_handling?: Record<string, string>;
  compliance_notes?: string;
}

export interface ChatEvent {
  platform: string;
  username: string;
  message: string;
  intent: string;
  priority: number;
  timestamp: number;
}

// UI Constants
export const STATUS_COLORS = {
  ready: '#10b981', // Emerald green
  warning: '#f59e0b', // Amber
  error: '#ef4444', // Red
  idle: '#6b7280', // Gray
  info: '#3b82f6', // Blue
} as const;

export type StatusType = 'ready' | 'warning' | 'error' | 'idle' | 'info';

export interface StatusBadgeProps {
  status: StatusType;
  label: string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export interface StreamTarget {
  id: number;
  platform: string;
  label: string;
  rtmp_url: string;
  stream_key_masked: string;
  is_active: boolean;
  enabled?: boolean;
  validation_status: string;
  validation_checks?: Array<{ check: string; passed: boolean; message: string }>;
  last_validated_at?: string | null;
}

export interface LiveSessionState {
  current_mode: string;
  current_phase?: string;
  rotation_paused: boolean;
  pause_reason: string;
  current_focus_product_id: number | null;
  current_focus_session_product_id?: number | null;
  pending_question?: {
    text?: string;
    reason?: string;
    answer_draft?: string;
    task_type?: string;
    answer_provider?: string;
    answer_model?: string;
    safety?: { safe?: boolean; reason_code?: string; rewrite?: string };
  } | null;
  awaiting_operator?: boolean;
  stream_status?: string;
}

export interface SessionProduct {
  id: number;
  session_id?: number;
  product_id: number;
  queue_order?: number;
  enabled_for_rotation?: boolean;
  operator_priority?: number;
  ai_score?: number;
  state?: string;
  product: Product;
}

export interface LiveSessionSummary {
  session: {
    id: number;
    platform: string;
    status: string;
    stream_target_id?: number;
    rotation_mode?: string;
    qna_mode?: string;
    pause_reason?: string;
    started_at?: string;
    ended_at?: string | null;
  } | null;
  stream_target: StreamTarget | null;
  state: LiveSessionState | null;
  products: SessionProduct[];
}
