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
  debug_urls: {
    webrtcapi: string;
    rtcpushapi: string;
    dashboard_vendor: string;
    echoapi: string;
  };
}

export interface ValidationResult {
  status: 'pass' | 'fail' | 'error';
  checks: Array<{ check: string; passed: boolean; message: string }>;
  error?: string;
}

export interface FaceEngineTruth {
  requested_model: string;
  resolved_model: string;
  requested_avatar_id: string;
  resolved_avatar_id: string;
  engine_state: string;
  fallback_active: boolean;
}

export interface RuntimeTruth {
  mock_mode: boolean;
  face_runtime_mode: string;
  face_engine?: FaceEngineTruth;
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
}

export interface ChatEvent {
  platform: string;
  username: string;
  message: string;
  intent: string;
  priority: number;
  timestamp: number;
}
