import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
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
  getVoiceProfiles: vi.fn().mockResolvedValue([
    {
      id: 1,
      name: 'Sari Fish',
      engine: 'fish_speech',
      profile_type: 'quick_clone',
      supported_languages: ['id', 'en'],
      quality_tier: 'quick',
      reference_wav_path: 'assets/voice/sari.wav',
      reference_text: 'Halo semuanya, aku Sari.',
      language: 'id',
      notes: 'utama',
      is_active: true,
      guidance: { min_seconds: 30, ideal_seconds: 60 },
    },
    {
      id: 2,
      name: 'Sari Studio Voice',
      engine: 'fish_speech',
      profile_type: 'studio_voice',
      supported_languages: ['id', 'en'],
      quality_tier: 'studio',
      reference_wav_path: 'data/runtime/voice/studio-sari/reference.wav',
      reference_text: 'Halo semuanya, aku Sari studio voice.',
      language: 'id',
      notes: 'production stable',
      is_active: false,
      guidance: { training_target_minutes: { id: [30, 60], en: [30, 60] } },
    },
  ]),
  createVoiceProfile: vi.fn().mockResolvedValue({
    id: 2,
    name: 'Clone Baru',
    engine: 'fish_speech',
    profile_type: 'quick_clone',
    supported_languages: ['id', 'en'],
    quality_tier: 'quick',
    reference_wav_path: 'assets/voice/baru.wav',
    reference_text: 'Halo, ini clone baru.',
    language: 'id',
    notes: '',
    is_active: false,
    guidance: { min_seconds: 30, ideal_seconds: 60 },
  }),
  activateVoiceProfile: vi.fn().mockResolvedValue({
    id: 1,
    name: 'Sari Fish',
    engine: 'fish_speech',
    profile_type: 'quick_clone',
    supported_languages: ['id', 'en'],
    quality_tier: 'quick',
    reference_wav_path: 'assets/voice/sari.wav',
    reference_text: 'Halo semuanya, aku Sari.',
    language: 'id',
    notes: 'utama',
    is_active: true,
    guidance: { min_seconds: 30, ideal_seconds: 60 },
  }),
  getVoiceLabState: vi.fn().mockResolvedValue({
    mode: 'standalone',
    active_profile_id: 1,
    preview_session_id: '',
    selected_avatar_id: 'musetalk_avatar1',
    selected_language: 'id',
    selected_profile_type: 'quick_clone',
    selected_revision_id: null,
    selected_style_preset: 'natural',
    selected_stability: 0.75,
    selected_similarity: 0.8,
    draft_text: 'Halo operator',
    last_generation_id: null,
  }),
  updateVoiceLabState: vi.fn().mockImplementation(async (payload) => ({
    mode: payload.mode ?? 'standalone',
    active_profile_id: payload.active_profile_id ?? 1,
    preview_session_id: payload.preview_session_id ?? '',
    selected_avatar_id: payload.selected_avatar_id ?? 'musetalk_avatar1',
    selected_language: payload.selected_language ?? 'id',
    selected_profile_type: payload.selected_profile_type ?? 'quick_clone',
    selected_revision_id: payload.selected_revision_id ?? null,
    selected_style_preset: payload.selected_style_preset ?? 'natural',
    selected_stability: payload.selected_stability ?? 0.75,
    selected_similarity: payload.selected_similarity ?? 0.8,
    draft_text: payload.draft_text ?? 'Halo operator',
    last_generation_id: payload.last_generation_id ?? null,
  })),
  updateVoiceLabPreviewSession: vi.fn().mockImplementation(async (payload) => ({
    mode: 'attach_avatar',
    active_profile_id: 1,
    preview_session_id: payload.preview_session_id,
    selected_avatar_id: payload.selected_avatar_id ?? 'musetalk_avatar1',
    selected_language: 'id',
    selected_profile_type: 'quick_clone',
    selected_revision_id: null,
    selected_style_preset: 'natural',
    selected_stability: 0.75,
    selected_similarity: 0.8,
    draft_text: 'Halo operator',
    last_generation_id: null,
  })),
  generateVoice: vi.fn().mockResolvedValue({
    status: 'success',
    message: 'Audio berhasil dibuat.',
    generation_id: 44,
    audio_url: '/api/voice/audio/44',
    download_url: '/api/voice/audio/44/download',
    latency_ms: 510,
    duration_ms: 1020,
    audio_length_bytes: 8192,
    attached_to_avatar: false,
    avatar_session_id: '',
    language: 'en',
    style_preset: 'conversational',
    stability: 0.62,
    similarity: 0.88,
    profile: {
      id: 1,
      name: 'Sari Fish',
      engine: 'fish_speech',
      profile_type: 'quick_clone',
      supported_languages: ['id', 'en'],
      quality_tier: 'quick',
      reference_wav_path: 'assets/voice/sari.wav',
      reference_text: 'Halo semuanya, aku Sari.',
      language: 'id',
      notes: 'utama',
      is_active: true,
      guidance: { min_seconds: 30, ideal_seconds: 60 },
    },
    lab_state: {
      mode: 'standalone',
      active_profile_id: 1,
      preview_session_id: '',
      selected_avatar_id: 'musetalk_avatar1',
      selected_language: 'en',
      selected_profile_type: 'quick_clone',
      selected_revision_id: null,
      selected_style_preset: 'conversational',
      selected_stability: 0.62,
      selected_similarity: 0.88,
      draft_text: 'Hello operator',
      last_generation_id: 44,
    },
  }),
  getVoiceGenerations: vi.fn().mockResolvedValue([
    {
      id: 44,
      mode: 'standalone',
      profile_id: 1,
      profile_name: 'Sari Fish',
      source_type: 'manual_text',
      input_text: 'Halo operator',
      language: 'en',
      emotion: 'neutral',
      style_preset: 'conversational',
      stability: 0.62,
      similarity: 0.88,
      speed: 1,
      status: 'success',
      audio_path: 'data/runtime/voice/voice-44.wav',
      audio_filename: 'voice-44.wav',
      download_name: 'sari-fish-en.wav',
      audio_url: '/api/voice/audio/44',
      download_url: '/api/voice/audio/44/download',
      audio_size_bytes: 8192,
      latency_ms: 510,
      duration_ms: 1020,
      attached_to_avatar: false,
      avatar_session_id: '',
    },
  ]),
  getVoiceTrainingJobs: vi.fn().mockResolvedValue([
    {
      id: 7,
      profile_id: 2,
      profile_name: 'Sari Studio Voice',
      job_type: 'studio_voice_training',
      status: 'queued',
      current_stage: 'queued',
      progress_pct: 0,
      dataset_path: 'data/runtime/voice/datasets/studio-sari',
      log_path: 'data/runtime/voice/training/studio-sari.log',
    },
  ]),
  createVoiceTrainingJob: vi.fn().mockResolvedValue({
    status: 'success',
    message: 'Voice training job queued',
    job: {
      id: 8,
      profile_id: 2,
      profile_name: 'Sari Studio Voice',
      job_type: 'studio_voice_training',
      status: 'queued',
      current_stage: 'queued',
      progress_pct: 0,
      dataset_path: 'data/runtime/voice/datasets/studio-sari',
      log_path: 'data/runtime/voice/training/studio-sari.log',
    },
  }),
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
  getVoiceProfiles: api.getVoiceProfiles,
  createVoiceProfile: api.createVoiceProfile,
  activateVoiceProfile: api.activateVoiceProfile,
  getVoiceLabState: api.getVoiceLabState,
  updateVoiceLabState: api.updateVoiceLabState,
  updateVoiceLabPreviewSession: api.updateVoiceLabPreviewSession,
  generateVoice: api.generateVoice,
  getVoiceGenerations: api.getVoiceGenerations,
  getVoiceTrainingJobs: api.getVoiceTrainingJobs,
  createVoiceTrainingJob: api.createVoiceTrainingJob,
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

  it('defers heavy preview and technical requests until the related tab is opened', async () => {
    render(PerformerPanel);

    await screen.findByRole('button', { name: /ringkasan/i });

    expect(api.getLiveTalkingStatus).not.toHaveBeenCalled();
    expect(api.getLiveTalkingLogs).not.toHaveBeenCalled();
    expect(api.getLiveTalkingDebugTargets).not.toHaveBeenCalled();

    await fireEvent.click(await screen.findByRole('button', { name: /^avatar$/i }));
    expect(api.getLiveTalkingStatus).toHaveBeenCalledTimes(1);

    await fireEvent.click(await screen.findByRole('button', { name: /preview/i }));
    expect(api.getLiveTalkingDebugTargets).toHaveBeenCalledTimes(1);

    await fireEvent.click(await screen.findByRole('button', { name: /teknis/i }));
    expect(api.getLiveTalkingLogs).toHaveBeenCalledTimes(1);
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

  it('loads voice lab data lazily and submits standalone generation from the suara tab', async () => {
    render(PerformerPanel);

    await screen.findByRole('button', { name: /ringkasan/i });
    expect(api.getVoiceProfiles).not.toHaveBeenCalled();
    expect(api.getVoiceLabState).not.toHaveBeenCalled();
    expect(api.getVoiceGenerations).not.toHaveBeenCalled();

    await fireEvent.click(await screen.findByRole('button', { name: /^suara$/i }));

    await waitFor(() => {
      expect(api.getVoiceProfiles).toHaveBeenCalledTimes(1);
      expect(api.getVoiceLabState).toHaveBeenCalledTimes(1);
      expect(api.getVoiceGenerations).toHaveBeenCalledTimes(1);
    });

    expect(await screen.findByRole('tab', { name: /generate/i })).toBeInTheDocument();
    expect((await screen.findAllByText(/assets\/voice\/sari\.wav/i)).length).toBeGreaterThanOrEqual(1);

    const promptInput = screen.getByLabelText(/prompt suara/i);
    await fireEvent.change(screen.getByLabelText(/bahasa output/i), { target: { value: 'en' } });
    await fireEvent.change(screen.getByLabelText(/gaya suara/i), { target: { value: 'conversational' } });
    await fireEvent.input(screen.getByLabelText(/stability/i), { target: { value: '0.62' } });
    await fireEvent.input(screen.getByLabelText(/similarity/i), { target: { value: '0.88' } });
    await fireEvent.input(promptInput, { target: { value: 'Hello operator' } });
    await fireEvent.click(screen.getByRole('button', { name: /generate audio/i }));

    await waitFor(() => {
      expect(api.generateVoice).toHaveBeenCalledWith({
        mode: 'standalone',
        profile_id: 1,
        text: 'Hello operator',
        language: 'en',
        emotion: 'neutral',
        style_preset: 'conversational',
        stability: 0.62,
        similarity: 0.88,
        speed: 1,
        attach_to_avatar: false,
      });
    });

    expect(await screen.findByTestId('action-receipt')).toHaveTextContent(/audio berhasil dibuat/i);
  });

  it('queues a studio voice training job from the training workspace', async () => {
    render(PerformerPanel);

    await fireEvent.click(await screen.findByRole('button', { name: /^suara$/i }));
    await screen.findByRole('tab', { name: /training jobs/i });
    await fireEvent.click(screen.getByRole('tab', { name: /training jobs/i }));
    await fireEvent.change(screen.getByLabelText(/studio voice target/i), { target: { value: '2' } });
    await fireEvent.input(screen.getByLabelText(/lokasi dataset/i), {
      target: { value: 'data/runtime/voice/datasets/studio-sari' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /queue training job/i }));

    await waitFor(() => {
      expect(api.createVoiceTrainingJob).toHaveBeenCalledWith({
        profile_id: 2,
        job_type: 'studio_voice_training',
        dataset_path: 'data/runtime/voice/datasets/studio-sari',
      });
    });
  });

  it('captures preview session messages so attach mode can sync avatar session id', async () => {
    render(PerformerPanel);

    await fireEvent.click(await screen.findByRole('button', { name: /^suara$/i }));
    await screen.findByRole('tab', { name: /generate/i });

    window.dispatchEvent(
      new MessageEvent('message', {
        data: {
          type: 'livetalking.preview.session',
          session_id: '77',
          avatar_id: 'musetalk_avatar1',
        },
      }),
    );

    await waitFor(() => {
      expect(api.updateVoiceLabPreviewSession).toHaveBeenCalledWith({
        preview_session_id: '77',
        selected_avatar_id: 'musetalk_avatar1',
      });
    });
  });
});
