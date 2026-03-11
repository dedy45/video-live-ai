import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import PerformerPanel from '../components/panels/PerformerPanel.svelte';

const api = vi.hoisted(() => ({
  getStatus: vi.fn().mockResolvedValue({
    state: 'IDLE',
    mock_mode: false,
    uptime_sec: 0,
    viewer_count: 0,
    current_product: null,
    stream_status: 'idle',
    stream_running: false,
    emergency_stopped: false,
    llm_budget_remaining: 5.0,
    safety_incidents: 0,
  }),
  getHealthSummary: vi.fn().mockResolvedValue({
    status: 'healthy',
    components: {
      face_pipeline: 'healthy',
      voice: 'warning',
    },
  }),
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: false,
    host: { name: 'gpu-01', role: 'server_production' },
    deployment_mode: 'production_ready',
    face_runtime_mode: 'livetalking_stopped',
    voice_runtime_mode: 'unknown',
    stream_runtime_mode: 'idle',
    validation_state: 'unvalidated',
    last_validated_at: '2026-03-11T03:05:00Z',
    incident_summary: { open_count: 0, highest_severity: 'none' },
    guardrails: { restart_storm: false, disk_pressure: false },
    provenance: {
      system_status: 'real_live',
      engine_status: 'real_live',
      stream_status: 'real_live',
    },
    voice_engine: {
      requested_engine: 'fish_speech',
      resolved_engine: 'unknown',
      fallback_active: false,
      server_reachable: false,
      reference_ready: true,
      queue_depth: 2,
      chunk_chars: 180,
      time_to_first_audio_ms: null,
      latency_p50_ms: null,
      latency_p95_ms: null,
      last_latency_ms: null,
      last_error: 'sidecar down',
    },
    face_engine: {
      requested_model: 'musetalk',
      resolved_model: 'musetalk',
      requested_avatar_id: 'musetalk_avatar1',
      resolved_avatar_id: 'musetalk_avatar1',
      engine_state: 'stopped',
      fallback_active: false,
    },
    timestamp: '2026-03-11T03:06:00Z',
  }),
  getReadiness: vi.fn().mockResolvedValue({
    overall_status: 'not_ready',
    checks: [],
    blocking_issues: ['voice_sidecar'],
    recommended_next_action: 'Start Fish-Speech sidecar',
  }),
  getLiveTalkingConfig: vi.fn().mockResolvedValue({
    port: 8010,
    operator_dashboard: '/dashboard',
    livetalking_dir: 'external/livetalking',
    transport: 'webrtc',
    debug_urls: {
      webrtcapi: 'http://localhost:8010/webrtcapi.html',
      rtcpushapi: 'http://localhost:8010/rtcpushapi.html',
      dashboard_vendor: 'http://localhost:8010/dashboard.html',
      echoapi: 'http://localhost:8010/echoapi.html',
    },
  }),
  getLiveTalkingDebugTargets: vi.fn().mockResolvedValue({
    checked_at: '2026-03-11T03:06:00Z',
    targets: {
      webrtcapi: {
        url: 'http://localhost:8010/webrtcapi.html',
        reachable: false,
        http_status: null,
        error: 'Connection refused',
      },
      dashboard_vendor: {
        url: 'http://localhost:8010/dashboard.html',
        reachable: false,
        http_status: null,
        error: 'Connection refused',
      },
      rtcpushapi: {
        url: 'http://localhost:8010/rtcpushapi.html',
        reachable: false,
        http_status: null,
        error: 'Connection refused',
      },
    },
  }),
  getLiveTalkingStatus: vi.fn().mockResolvedValue({
    state: 'stopped',
    pid: null,
    uptime_sec: 0,
    port: 8010,
    model: 'musetalk',
    avatar_id: 'musetalk_avatar1',
    requested_model: 'musetalk',
    resolved_model: 'musetalk',
    requested_avatar_id: 'musetalk_avatar1',
    resolved_avatar_id: 'musetalk_avatar1',
    transport: 'webrtc',
    last_error: '',
    app_py_exists: true,
    model_path_exists: true,
    avatar_path_exists: true,
  }),
  getLiveTalkingLogs: vi.fn().mockResolvedValue({
    lines: ['INFO: engine boot', 'WARN: preview waiting'],
    count: 2,
  }),
  voiceWarmup: vi.fn().mockResolvedValue({
    status: 'blocked',
    action: 'voice.warmup',
    message: 'Voice sidecar is not reachable yet',
    next_step: 'Jalankan sidecar suara terlebih dahulu.',
  }),
  voiceQueueClear: vi.fn().mockResolvedValue({ status: 'success', message: 'Voice queue cleared' }),
  voiceRestart: vi.fn().mockResolvedValue({ status: 'success', message: 'Voice worker restart requested' }),
  voiceTestSpeak: vi.fn().mockResolvedValue({
    status: 'success',
    message: 'Tes suara selesai.',
    latency_ms: 920,
    duration_ms: 1430,
    audio_length_bytes: 16384,
    text: 'Halo operator',
  }),
  startLiveTalking: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'engine.start',
    message: 'Avatar menerima perintah jalan.',
    state: 'running',
  }),
  stopLiveTalking: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'engine.stop',
    message: 'Avatar menerima perintah berhenti.',
    state: 'stopped',
  }),
  validateLiveTalkingEngine: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateRuntimeTruth: vi.fn().mockResolvedValue({ status: 'pass', checks: [], evidence_id: 10 }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: ['voice_sidecar'] }),
  validateVoiceLocalClone: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: ['voice_sidecar'] }),
  validateAudioChunkingSmoke: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
}));

vi.mock('../lib/api', () => ({
  getStatus: api.getStatus,
  getHealthSummary: api.getHealthSummary,
  getRuntimeTruth: api.getRuntimeTruth,
  getReadiness: api.getReadiness,
  getLiveTalkingConfig: api.getLiveTalkingConfig,
  getLiveTalkingDebugTargets: api.getLiveTalkingDebugTargets,
  getLiveTalkingStatus: api.getLiveTalkingStatus,
  getLiveTalkingLogs: api.getLiveTalkingLogs,
  voiceWarmup: api.voiceWarmup,
  voiceQueueClear: api.voiceQueueClear,
  voiceRestart: api.voiceRestart,
  voiceTestSpeak: api.voiceTestSpeak,
  startLiveTalking: api.startLiveTalking,
  stopLiveTalking: api.stopLiveTalking,
  validateLiveTalkingEngine: api.validateLiveTalkingEngine,
  validateRuntimeTruth: api.validateRuntimeTruth,
  validateRealModeReadiness: api.validateRealModeReadiness,
  validateVoiceLocalClone: api.validateVoiceLocalClone,
  validateAudioChunkingSmoke: api.validateAudioChunkingSmoke,
}));

describe('PerformerPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the tabbed performer workspace wrapper', async () => {
    render(PerformerPanel);

    expect(await screen.findByRole('button', { name: /ringkasan/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /^suara$/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /^avatar$/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /preview/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /validasi/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /teknis/i })).toBeInTheDocument();
  });

  it('routes voice action feedback through the shared operator receipt', async () => {
    render(PerformerPanel);

    await fireEvent.click(await screen.findByRole('button', { name: /^suara$/i }));
    await fireEvent.click(await screen.findByRole('button', { name: /panaskan mesin suara/i }));

    expect(api.voiceWarmup).toHaveBeenCalledTimes(1);
    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt).toHaveTextContent(/not reachable/i);
    expect(receipt.classList.contains('receipt-blocked')).toBe(true);
  });

  it('shows logs and vendor health on the technical tab', async () => {
    render(PerformerPanel);

    await fireEvent.click(await screen.findByRole('button', { name: /teknis/i }));

    expect(await screen.findByText(/INFO: engine boot/i)).toBeInTheDocument();
    expect(await screen.findByText(/dashboard_vendor/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/connection refused/i)).length).toBeGreaterThanOrEqual(1);
    expect(api.getLiveTalkingLogs).toHaveBeenCalled();
  });
});
