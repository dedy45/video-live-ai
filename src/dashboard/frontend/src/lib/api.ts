import { API_BASE } from './constants';
import type {
  BrainConfig,
  DirectorRuntimeContract,
  EngineConfig,
  EngineStatus,
  LiveTalkingDebugTargets,
  OperatorActionResult,
  ReadinessResult,
  RuntimeTruth,
  SystemStatus,
  ValidationResult,
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
export const getProducts = () => request<any[]>('/products');

// Revenue
export const getRevenue = (hours = 1) => request<Record<string, any>>(`/analytics/revenue?hours=${hours}`);

// Chat
export const getRecentChats = (limit = 20) => request<any[]>(`/chat/recent?limit=${limit}`);

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

// Stream Control
export const startStream = () => request<Record<string, any>>('/stream/start', { method: 'POST' });
export const stopStream = () => request<Record<string, any>>('/stream/stop', { method: 'POST' });
export const emergencyStop = () => request<Record<string, any>>('/emergency-stop', { method: 'POST' });
export const emergencyReset = () => request<Record<string, any>>('/emergency-reset', { method: 'POST' });

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
