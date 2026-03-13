import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import VoicePanel from '../components/panels/VoicePanel.svelte';

const truth = {
  mock_mode: false,
  host: { name: 'gpu-01', role: 'server_production' },
  deployment_mode: 'ready',
  face_runtime_mode: 'livetalking_running',
  voice_runtime_mode: 'fish_speech_local',
  stream_runtime_mode: 'idle',
  validation_state: 'passed',
  last_validated_at: null,
  provenance: {
    system_status: 'real_local',
    engine_status: 'real_local',
    stream_status: 'real_local',
  },
  timestamp: '2026-03-14T08:00:00Z',
  voice_engine: {
    requested_engine: 'fish_speech',
    resolved_engine: 'fish_speech',
    fallback_active: false,
    server_reachable: true,
    reference_ready: true,
    queue_depth: 2,
    chunk_chars: 180,
    time_to_first_audio_ms: 320,
    latency_p50_ms: 330,
    latency_p95_ms: 410,
    last_latency_ms: 340,
    last_error: null,
  },
};

const voiceProfiles = [
  {
    id: 1,
    name: 'Sari Quick Clone',
    engine: 'fish_speech',
    profile_type: 'quick_clone',
    supported_languages: ['id', 'en'],
    quality_tier: 'quick',
    reference_wav_path: 'assets/voice/sari.wav',
    reference_text: 'Halo semuanya, aku Sari.',
    language: 'id',
    notes: 'utama',
    is_active: true,
    guidance: {
      min_seconds: 30,
      ideal_seconds: 60,
    },
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
    guidance: {
      training_target_minutes: { id: [30, 60], en: [30, 60] },
    },
  },
];

const voiceLabState = {
  mode: 'standalone',
  active_profile_id: 1,
  preview_session_id: '884422',
  selected_avatar_id: 'wav2lip256_avatar1',
  selected_language: 'id',
  selected_profile_type: 'quick_clone',
  selected_revision_id: null,
  selected_style_preset: 'natural',
  selected_stability: 0.75,
  selected_similarity: 0.8,
  draft_text: 'Halo operator',
  last_generation_id: 10,
};

const voiceGenerations = [
  {
    id: 10,
    mode: 'standalone',
    profile_id: 1,
    profile_name: 'Sari Quick Clone',
    source_type: 'manual_text',
    input_text: 'Halo operator',
    language: 'en',
    emotion: 'friendly',
    style_preset: 'conversational',
    stability: 0.64,
    similarity: 0.88,
    speed: 1.0,
    status: 'success',
    audio_path: 'data/runtime/voice/voice-10.wav',
    audio_filename: 'voice-10.wav',
    download_name: 'sari-quick-clone-en.wav',
    audio_url: '/api/voice/audio/10',
    download_url: '/api/voice/audio/10/download',
    audio_size_bytes: 16384,
    latency_ms: 920,
    duration_ms: 1430,
    attached_to_avatar: false,
    avatar_session_id: '',
  },
];

const voiceTrainingJobs = [
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
];

describe('VoicePanel', () => {
  it('renders a multi-workspace voice lab with generate, clone, studio, training, and library sections', async () => {
    render(VoicePanel, {
      props: {
        truth,
        busyAction: '',
        voiceTestResult: null,
        voiceProfiles,
        voiceLabState,
        voiceGenerations,
        voiceTrainingJobs,
        onWarmup: vi.fn(),
        onRestart: vi.fn(),
        onClearQueue: vi.fn(),
        onTestSpeak: vi.fn(),
        onCreateProfile: vi.fn(),
        onActivateProfile: vi.fn(),
        onChangeMode: vi.fn(),
        onGenerateVoice: vi.fn(),
        onCreateTrainingJob: vi.fn(),
      },
    });

    expect(screen.getByRole('heading', { name: /^suara$/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /generate/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /quick clone/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /studio voice/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /training jobs/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /library/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/bahasa output/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/voice profile/i)).toBeInTheDocument();
    expect(screen.getByText(/indonesia dan english/i)).toBeInTheDocument();
  });

  it('submits standalone generation with language and style controls, and exposes play/download links in library', async () => {
    const onGenerateVoice = vi.fn();

    render(VoicePanel, {
      props: {
        truth,
        busyAction: '',
        voiceTestResult: null,
        voiceProfiles,
        voiceLabState,
        voiceGenerations,
        voiceTrainingJobs,
        onWarmup: vi.fn(),
        onRestart: vi.fn(),
        onClearQueue: vi.fn(),
        onTestSpeak: vi.fn(),
        onCreateProfile: vi.fn(),
        onActivateProfile: vi.fn(),
        onChangeMode: vi.fn(),
        onGenerateVoice,
        onCreateTrainingJob: vi.fn(),
      },
    });

    await fireEvent.change(screen.getByLabelText(/bahasa output/i), { target: { value: 'en' } });
    await fireEvent.change(screen.getByLabelText(/gaya suara/i), { target: { value: 'conversational' } });
    await fireEvent.input(screen.getByLabelText(/stability/i), { target: { value: '0.64' } });
    await fireEvent.input(screen.getByLabelText(/similarity/i), { target: { value: '0.88' } });
    await fireEvent.input(screen.getByLabelText(/prompt suara/i), { target: { value: 'Hello operator' } });
    await fireEvent.click(screen.getByRole('button', { name: /generate audio/i }));

    expect(onGenerateVoice).toHaveBeenCalledWith({
      mode: 'standalone',
      profile_id: 1,
      text: 'Hello operator',
      language: 'en',
      emotion: 'neutral',
      style_preset: 'conversational',
      stability: 0.64,
      similarity: 0.88,
      speed: 1,
      attach_to_avatar: false,
    });

    await fireEvent.click(screen.getByRole('tab', { name: /library/i }));
    expect(screen.getAllByText(/sari quick clone/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/conversational/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /unduh sari-quick-clone-en\.wav/i })).toHaveAttribute(
      'href',
      '/api/voice/audio/10/download',
    );
    expect(screen.getByRole('link', { name: /putar sari-quick-clone-en\.wav/i })).toHaveAttribute(
      'href',
      '/api/voice/audio/10',
    );
  });

  it('shows informative quick clone requirements and allows queueing a studio training job', async () => {
    const onCreateProfile = vi.fn();
    const onCreateTrainingJob = vi.fn();

    render(VoicePanel, {
      props: {
        truth,
        busyAction: '',
        voiceTestResult: null,
        voiceProfiles,
        voiceLabState,
        voiceGenerations,
        voiceTrainingJobs,
        onWarmup: vi.fn(),
        onRestart: vi.fn(),
        onClearQueue: vi.fn(),
        onTestSpeak: vi.fn(),
        onCreateProfile,
        onActivateProfile: vi.fn(),
        onChangeMode: vi.fn(),
        onGenerateVoice: vi.fn(),
        onCreateTrainingJob,
      },
    });

    await fireEvent.click(screen.getByRole('tab', { name: /quick clone/i }));
    expect(screen.getByText(/durasi ideal 30-90 detik/i)).toBeInTheDocument();
    expect(screen.getByText(/hindari noise, musik, dan clipping/i)).toBeInTheDocument();
    await fireEvent.input(screen.getByLabelText(/nama clone/i), { target: { value: 'Clone Indo EN' } });
    await fireEvent.input(screen.getByLabelText(/path wav referensi/i), { target: { value: 'assets/voice/clone.wav' } });
    await fireEvent.input(screen.getByLabelText(/transkrip referensi/i), {
      target: { value: 'Halo semuanya, welcome back to the live.' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /simpan quick clone/i }));

    expect(onCreateProfile).toHaveBeenCalledWith({
      name: 'Clone Indo EN',
      reference_wav_path: 'assets/voice/clone.wav',
      reference_text: 'Halo semuanya, welcome back to the live.',
      language: 'id',
      supported_languages: ['id', 'en'],
      profile_type: 'quick_clone',
      quality_tier: 'quick',
      guidance: {
        min_seconds: 30,
        ideal_seconds: 90,
        tips: ['clean_voice', 'exact_transcript', 'bilingual_ready'],
      },
      notes: '',
      engine: 'fish_speech',
    });

    await fireEvent.click(screen.getByRole('tab', { name: /training jobs/i }));
    expect(screen.getAllByText(/training diblok saat live aktif/i).length).toBeGreaterThanOrEqual(1);
    await fireEvent.change(screen.getByLabelText(/studio voice target/i), { target: { value: '2' } });
    await fireEvent.input(screen.getByLabelText(/lokasi dataset/i), {
      target: { value: 'data/runtime/voice/datasets/studio-sari' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /queue training job/i }));

    expect(onCreateTrainingJob).toHaveBeenCalledWith({
      profile_id: 2,
      job_type: 'studio_voice_training',
      dataset_path: 'data/runtime/voice/datasets/studio-sari',
    });
    expect(screen.getAllByText(/queued/i).length).toBeGreaterThanOrEqual(1);
  });
});
