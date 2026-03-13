import { API_BASE } from './constants';
import type {
  BrainConfig,
  DirectorRuntimeContract,
  EngineConfig,
  EngineStatus,
  LiveSessionSummary,
  LiveTalkingDebugTargets,
  OperatorActionResult,
  Product,
  ReadinessResult,
  RuntimeTruth,
  StreamTarget,
  SystemStatus,
  ValidationResult,
  VoiceGeneration,
  VoiceGenerationResult,
  VoiceLabState,
  VoiceProfile,
  VoiceTrainingJob,
  VoiceTestSpeakResult,
} from './types';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      Pragma: 'no-cache',
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

// System
export const getStatus = () => request<SystemStatus>('/status');
export const getMetrics = (window = 60) => request<Record<string, any>>(`/metrics?window=${window}`);

// Readiness
export const getReadiness = () => request<ReadinessResult>('/readiness');

// Health
export const getHealthSummary = () => request<Record<string, any>>('/health/summary');

// LiveTalking Engine
export const getLiveTalkingStatus = () => request<EngineStatus>('/engine/livetalking/status');
export const getLiveTalkingConfig = () => request<EngineConfig>('/engine/livetalking/config');
export const getLiveTalkingLogs = (tail = 100) => request<Record<string, any>>(`/engine/livetalking/logs?tail=${tail}`);
export const startLiveTalking = () => request<OperatorActionResult & Partial<EngineStatus>>('/engine/livetalking/start', { method: 'POST' });
export const stopLiveTalking = () => request<OperatorActionResult & Partial<EngineStatus>>('/engine/livetalking/stop', { method: 'POST' });
export const getLiveTalkingDebugTargets = () => request<LiveTalkingDebugTargets>('/engine/livetalking/debug-targets');

// Validation
export const validateLiveTalkingEngine = () => request<ValidationResult>('/validate/livetalking-engine', { method: 'POST' });
export const validateRtmpTarget = () => request<Record<string, any>>('/validate/rtmp-target', { method: 'POST' });
export const validateRuntimeTruth = () => request<ValidationResult>('/validate/runtime-truth', { method: 'POST' });
export const validateRealModeReadiness = () => request<ValidationResult>('/validate/real-mode-readiness', { method: 'POST' });
export const validateVoiceLocalClone = () => request<ValidationResult>('/validate/voice-local-clone', { method: 'POST' });
export const validateAudioChunkingSmoke = () => request<ValidationResult>('/validate/audio-chunking-smoke', { method: 'POST' });
export const validateStreamDryRun = () => request<Record<string, any>>('/validate/stream-dry-run', { method: 'POST' });
export const validateResourceBudget = () => request<Record<string, any>>('/validate/resource-budget', { method: 'POST' });
export const validateSoakSanity = () => request<Record<string, any>>('/validate/soak-sanity', { method: 'POST' });
export const getValidationHistory = () => request<any[]>('/validation/history');

// Products
export const getProducts = () => request<Product[]>('/products');
export const createProduct = (payload: Partial<Product> & { name: string; price: number }) =>
  request<Product>('/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const updateProduct = (productId: number, payload: Partial<Product> & { name: string; price: number }) =>
  request<Product>(`/products/${productId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
export const deleteProduct = (productId: number) =>
  request<Record<string, any>>(`/products/${productId}`, { method: 'DELETE' });

// Revenue
export const getRevenue = (hours = 1) => request<Record<string, any>>(`/analytics/revenue?hours=${hours}`);

// Chat
export const getRecentChats = (limit = 20) => request<any[]>(`/chat/recent?limit=${limit}`);
export const ingestChatEvent = (payload: { platform: string; username: string; message: string; trace_id?: string; raw_data?: Record<string, any> }) =>
  request<Record<string, any>>('/chat/ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// Runtime Truth
export const getRuntimeTruth = () => request<RuntimeTruth>('/runtime/truth');
export const getOpsSummary = () => request<Record<string, any>>('/ops/summary');
export const getResources = () => request<Record<string, any>>('/resources');
export const getIncidents = () => request<any[]>('/incidents');
export const ackIncident = (incidentId: string) => request<Record<string, any>>(`/incidents/${incidentId}/ack`, { method: 'POST' });
export const voiceWarmup = () => request<OperatorActionResult>('/voice/warmup', { method: 'POST' });
export const voiceQueueClear = () => request<OperatorActionResult>('/voice/queue/clear', { method: 'POST' });
export const voiceRestart = () => request<OperatorActionResult>('/voice/restart', { method: 'POST' });
export const voiceTestSpeak = (text: string) =>
  request<VoiceTestSpeakResult>(`/voice/test/speak?text=${encodeURIComponent(text)}`, {
    method: 'POST',
  });
export const getVoiceProfiles = () => request<VoiceProfile[]>('/voice/profiles');
export const createVoiceProfile = (payload: {
  name: string;
  reference_wav_path: string;
  reference_text: string;
  language?: string;
  supported_languages?: string[];
  profile_type?: string;
  quality_tier?: string;
  guidance?: Record<string, any>;
  notes?: string;
  engine?: string;
}) =>
  request<VoiceProfile>('/voice/profiles', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const activateVoiceProfile = (profileId: number) =>
  request<VoiceProfile>(`/voice/profiles/${profileId}/activate`, { method: 'POST' });
export const getVoiceLabState = () => request<VoiceLabState>('/voice/lab');
export const updateVoiceLabState = (payload: {
  mode: string;
  active_profile_id?: number | null;
  preview_session_id?: string;
  selected_avatar_id?: string;
  selected_language?: string;
  selected_profile_type?: string;
  selected_revision_id?: number | null;
  selected_style_preset?: string;
  selected_stability?: number;
  selected_similarity?: number;
  draft_text?: string;
  last_generation_id?: number | null;
}) =>
  request<VoiceLabState>('/voice/lab', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
export const updateVoiceLabPreviewSession = (payload: {
  preview_session_id: string;
  selected_avatar_id?: string;
}) =>
  request<VoiceLabState>('/voice/lab/preview-session', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const generateVoice = (payload: {
  mode: string;
  profile_id?: number | null;
  text: string;
  language?: string;
  emotion?: string;
  style_preset?: string;
  stability?: number;
  similarity?: number;
  speed?: number;
  attach_to_avatar?: boolean;
  avatar_id?: string;
  preview_session_id?: string;
  source_type?: string;
}) =>
  request<VoiceGenerationResult>('/voice/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const getVoiceGenerations = (limit = 20) => request<VoiceGeneration[]>(`/voice/generations?limit=${limit}`);
export const getVoiceTrainingJobs = (limit = 20) => request<VoiceTrainingJob[]>(`/voice/training-jobs?limit=${limit}`);
export const createVoiceTrainingJob = (payload: { profile_id: number; job_type?: string; dataset_path?: string }) =>
  request<Record<string, any>>('/voice/training-jobs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// Stream Control
export const startStream = () => request<Record<string, any>>('/stream/start', { method: 'POST' });
export const stopStream = () => request<Record<string, any>>('/stream/stop', { method: 'POST' });
export const emergencyStop = () => request<Record<string, any>>('/emergency-stop', { method: 'POST' });
export const emergencyReset = () => request<Record<string, any>>('/emergency-reset', { method: 'POST' });
export const getStreamTargets = () => request<StreamTarget[]>('/stream-targets');
export const createStreamTarget = (payload: { platform: string; label: string; rtmp_url: string; stream_key: string; enabled?: boolean }) =>
  request<StreamTarget>('/stream-targets', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const updateStreamTarget = (targetId: number, payload: { platform: string; label: string; rtmp_url: string; stream_key: string; enabled?: boolean }) =>
  request<StreamTarget>(`/stream-targets/${targetId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
export const validateStreamTarget = (targetId: number) =>
  request<Record<string, any>>(`/stream-targets/${targetId}/validate`, { method: 'POST' });
export const activateStreamTarget = (targetId: number) =>
  request<Record<string, any>>(`/stream-targets/${targetId}/activate`, { method: 'POST' });
export const getLiveSession = () => request<LiveSessionSummary>('/live-session');
export const startLiveSession = (payload: { platform: string }) =>
  request<Record<string, any>>('/live-session/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const stopLiveSession = () => request<Record<string, any>>('/live-session/stop', { method: 'POST' });
export const addLiveSessionProducts = (payload: { product_ids: number[] }) =>
  request<Record<string, any>>('/live-session/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const setLiveSessionFocus = (payload: { session_product_id: number }) =>
  request<Record<string, any>>('/live-session/focus', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const pauseLiveSession = (payload: { reason: string; question?: string }) =>
  request<Record<string, any>>('/live-session/pause', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const resumeLiveSession = () => request<Record<string, any>>('/live-session/resume', { method: 'POST' });

// Pipeline
export const getPipelineState = () => request<Record<string, any>>('/pipeline/state');
export const pipelineTransition = (targetState: string) =>
  request<Record<string, any>>('/pipeline/transition', {
    method: 'POST',
    body: JSON.stringify({ target_state: targetState }),
  });

// Product Switch
export const switchProduct = (productId: number) =>
  request<Record<string, any>>(`/products/${productId}/switch`, { method: 'POST' });

// Brain
export const getBrainStats = () => request<Record<string, any>>('/brain/stats');
export const getBrainHealth = () => request<Record<string, any>>('/brain/health');
export const getBrainConfig = () => request<BrainConfig>('/brain/config');
export const getDirectorRuntime = () => request<DirectorRuntimeContract>('/director/runtime');
export const brainTest = (payload: { system_prompt?: string; user_prompt?: string; task_type?: string; provider?: string | null }) =>
  request<Record<string, any>>('/brain/test', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// Validation (mock stack)
export const validateMockStack = () => request<Record<string, any>>('/validate/mock-stack', { method: 'POST' });
