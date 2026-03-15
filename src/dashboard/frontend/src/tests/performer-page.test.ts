import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import PerformerPage from '../pages/PerformerPage.svelte';

const api = vi.hoisted(() => {
  const truthSequence = [
    {
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
        queue_depth: 0,
        chunk_chars: null,
        time_to_first_audio_ms: null,
        latency_p50_ms: null,
        latency_p95_ms: null,
        last_latency_ms: null,
        last_error: null,
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
    },
    {
      mock_mode: false,
      host: { name: 'gpu-01', role: 'server_production' },
      deployment_mode: 'production_ready',
      face_runtime_mode: 'livetalking_running',
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
        queue_depth: 0,
        chunk_chars: null,
        time_to_first_audio_ms: null,
        latency_p50_ms: null,
        latency_p95_ms: null,
        last_latency_ms: null,
        last_error: null,
      },
      face_engine: {
        requested_model: 'musetalk',
        resolved_model: 'musetalk',
        requested_avatar_id: 'musetalk_avatar1',
        resolved_avatar_id: 'musetalk_avatar1',
        engine_state: 'running',
        fallback_active: false,
      },
      timestamp: '2026-03-11T03:06:05Z',
    },
  ];

  let truthCallIndex = 0;

  return {
    resetTruth() {
      truthCallIndex = 0;
    },
    getRuntimeTruth: vi.fn(async () => {
      const next = truthSequence[Math.min(truthCallIndex, truthSequence.length - 1)];
      truthCallIndex += 1;
      return next;
    }),
  };
});

vi.mock('../lib/api', () => ({
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
  getRuntimeTruth: api.getRuntimeTruth,
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
    state: 'running',
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
  getLiveTalkingLogs: vi.fn().mockResolvedValue({ lines: [], count: 0 }),
  voiceWarmup: vi.fn().mockResolvedValue({
    status: 'blocked',
    action: 'voice.warmup',
    message: 'Voice sidecar is not reachable yet',
    next_step: 'Jalankan Fish-Speech sidecar terlebih dahulu.',
  }),
  voiceQueueClear: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'voice.queue.clear',
    message: 'Antrian suara berhasil dibersihkan.',
  }),
  voiceRestart: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'voice.restart',
    message: 'Worker suara diminta restart.',
  }),
  voiceTestSpeak: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'voice.test.speak',
    message: 'Tes suara selesai.',
    text: 'Halo operator',
    latency_ms: 15,
    duration_ms: 780,
    audio_length_bytes: 37440,
  }),
  startLiveTalking: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'engine.start',
    message: 'Avatar menerima perintah jalan.',
    reason_code: 'engine_start_requested',
    next_step: 'Tunggu sampai status avatar berubah menjadi berjalan.',
    state: 'running',
  }),
  stopLiveTalking: vi.fn().mockResolvedValue({
    status: 'success',
    action: 'engine.stop',
    message: 'Avatar menerima perintah berhenti.',
    reason_code: 'engine_stop_requested',
    next_step: 'Tunggu sampai status avatar berubah menjadi berhenti.',
    state: 'stopped',
  }),
  validateLiveTalkingEngine: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateRuntimeTruth: vi.fn().mockResolvedValue({ status: 'pass', checks: [], evidence_id: 10 }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: ['voice_sidecar'] }),
  validateVoiceLocalClone: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: ['voice_sidecar'] }),
  validateAudioChunkingSmoke: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
}));

describe('PerformerPage', () => {
  beforeEach(() => {
    api.resetTruth();
    vi.clearAllMocks();
  });

  it('renders the tabbed avatar dan suara workspace instead of one long cockpit', async () => {
    render(PerformerPage);

    expect(await screen.findByRole('heading', { name: /avatar & suara/i })).toBeInTheDocument();
    expect(screen.getByTestId('performer-page')).toHaveClass('page-full-width');
    expect(await screen.findByRole('button', { name: /ringkasan/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /^suara$/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /^avatar$/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /preview/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /validasi/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /teknis/i })).toBeInTheDocument();
  });

  it('reconciles avatar state after start without requiring manual refresh', async () => {
    render(PerformerPage);

    await fireEvent.click(await screen.findByRole('button', { name: /^avatar$/i }));
    await fireEvent.click(await screen.findByRole('button', { name: /jalankan avatar/i }));

    expect(await screen.findByText(/avatar menerima perintah jalan/i)).toBeInTheDocument();
    expect(await screen.findByText(/berjalan/i, {}, { timeout: 2500 })).toBeInTheDocument();
  });

  it('shows preview fallback when vendor targets are unreachable', async () => {
    render(PerformerPage);

    await fireEvent.click(await screen.findByRole('button', { name: /preview/i }));

    expect(await screen.findByText(/preview belum bisa dibuka/i)).toBeInTheDocument();
    expect(await screen.findByText(/connection refused/i)).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /cek lagi/i })).toBeInTheDocument();
  });
});
