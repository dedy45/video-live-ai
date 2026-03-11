import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import SetupPage from '../pages/SetupPage.svelte';

vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn(),
  stopRealtime: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: false,
    host: { name: 'gpu-01', role: 'server_production' },
    deployment_mode: 'ready',
    face_runtime_mode: 'livetalking_local',
    voice_runtime_mode: 'fish_speech_local',
    stream_runtime_mode: 'idle',
    validation_state: 'passed',
    last_validated_at: '2026-03-11T01:00:00Z',
    provenance: {
      system_status: 'real_live',
      engine_status: 'real_local',
      stream_status: 'real_local',
    },
    timestamp: '2026-03-11T01:00:00Z',
  }),
  getOpsSummary: vi.fn().mockResolvedValue({
    overall_status: 'ready',
    deployment_mode: 'ready',
    voice_status: 'healthy',
    face_status: 'healthy',
    stream_status: 'idle',
    incident_summary: { open_count: 0, highest_severity: 'none' },
    resource_metrics: { cpu_pct: 21, ram_pct: 33, disk_pct: 12, vram_pct: 45 },
    restart_counters: { voice: 0, face: 0, stream: 0 },
  }),
  getReadiness: vi.fn().mockResolvedValue({
    overall_status: 'ready',
    checks: [],
    blocking_issues: [],
    recommended_next_action: 'Proceed to performer checks',
  }),
  getValidationHistory: vi.fn().mockResolvedValue([]),
  validateMockStack: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateLiveTalkingEngine: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateRtmpTarget: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateRuntimeTruth: vi.fn().mockResolvedValue({ status: 'pass', checks: [], evidence_id: 1 }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({ status: 'pass', checks: [], blockers: [] }),
  validateVoiceLocalClone: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateAudioChunkingSmoke: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateStreamDryRun: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateResourceBudget: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateSoakSanity: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  getHealthSummary: vi.fn().mockResolvedValue({ status: 'healthy', components: {} }),
  getBrainStats: vi.fn().mockResolvedValue({ adapters: {} }),
  getBrainHealth: vi.fn().mockResolvedValue({ healthy_count: 1, total_count: 1, providers: { groq: true } }),
  getBrainConfig: vi.fn().mockResolvedValue({
    daily_budget_usd: 5,
    fallback_order: ['groq', 'gemini_local_flash', 'local'],
    routing_table: { chat_reply: ['groq', 'local'] },
    prompt: {
      active_revision: 'default-live-commerce:v1',
      slug: 'default-live-commerce',
      version: 1,
      status: 'active',
    },
    providers: {
      groq: { model: 'groq/llama-3.3-70b-versatile', timeout_ms: 8000, backend: 'litellm' },
      local: { model: 'openai/qwen-local', timeout_ms: 15000, backend: 'litellm' },
    },
  }),
  getDirectorRuntime: vi.fn().mockResolvedValue({
    director: {
      state: 'SELLING',
      current_phase: 'hook',
      stream_running: true,
      emergency_stopped: false,
      manual_override: false,
      active_provider: 'groq',
      active_model: 'llama-3.3-70b-versatile',
      active_prompt_revision: 'default-live-commerce:v1',
      history: [{ from: 'IDLE', to: 'SELLING', timestamp: 1 }],
      valid_transitions: ['REACTING', 'ENGAGING', 'PAUSED', 'IDLE'],
      phase_sequence: ['hook', 'problem', 'solution', 'features', 'social_proof', 'urgency', 'cta'],
    },
    brain: {
      active_provider: 'groq',
      active_model: 'llama-3.3-70b-versatile',
      routing_table: { chat_reply: ['groq', 'local'] },
      adapter_count: 2,
      daily_budget_usd: 5,
    },
    prompt: {
      active_revision: 'default-live-commerce:v1',
      slug: 'default-live-commerce',
      version: 1,
      status: 'active',
      updated_at: '2026-03-12T00:00:00Z',
    },
    persona: {
      name: 'Sari',
      tone: 'warm',
      language: 'Indonesian casual',
      forbidden_topics: ['politik'],
      catchphrases: ['Siapa yang mau?'],
    },
    script: {
      current_phase: 'hook',
      phase_sequence: ['hook', 'problem', 'solution', 'features', 'social_proof', 'urgency', 'cta'],
    },
  }),
  brainTest: vi.fn().mockResolvedValue({
    success: true,
    provider: 'groq',
    model: 'llama-3.3-70b',
    latency_ms: 220,
    text: 'ok',
  }),
}));

describe('SetupPage', () => {
  it('shows environment summary alongside readiness and validation surfaces', async () => {
    render(SetupPage);

    expect(await screen.findByText(/Setup & Validasi Sistem/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/Environment/i)).length).toBeGreaterThan(0);
    expect(await screen.findByText(/gpu-01/i)).toBeInTheDocument();
    expect(await screen.findByText(/server_production/i)).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /Brain & Prompt/i })).toBeInTheDocument();
    expect(await screen.findByText(/default-live-commerce:v1/i)).toBeInTheDocument();
  });
});
