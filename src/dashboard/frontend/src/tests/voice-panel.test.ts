import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import VoicePanel from '../components/panels/VoicePanel.svelte';

const truth = {
  mock_mode: false,
  host: { name: 'gpu-01', role: 'server_production' },
  deployment_mode: 'ready',
  face_runtime_mode: 'livetalking_stopped',
  voice_runtime_mode: 'fish_speech_local',
  stream_runtime_mode: 'idle',
  validation_state: 'passed',
  last_validated_at: null,
  provenance: {
    system_status: 'real_local',
    engine_status: 'real_local',
    stream_status: 'real_local',
  },
  timestamp: '2026-03-11T03:06:00Z',
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

describe('VoicePanel', () => {
  it('renders voice operator controls from props without fetching its own data', async () => {
    render(VoicePanel, {
      props: {
        truth,
        busyAction: '',
        voiceTestResult: null,
        onWarmup: vi.fn(),
        onRestart: vi.fn(),
        onClearQueue: vi.fn(),
        onTestSpeak: vi.fn(),
      },
    });

    expect(screen.getByRole('heading', { name: /^suara$/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /kontrol operator/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /panaskan mesin suara/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /mulai ulang mesin suara/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /kosongkan antrian suara/i })).toBeInTheDocument();
    expect(screen.getByText(/latency p50 \/ p95/i)).toBeInTheDocument();
    expect(screen.getByText(/error terakhir/i)).toBeInTheDocument();
  });

  it('submits inline voice test through callback and renders telemetry from props', async () => {
    const onTestSpeak = vi.fn();

    render(VoicePanel, {
      props: {
        truth,
        busyAction: '',
        voiceTestResult: {
          status: 'success',
          message: 'Tes suara selesai.',
          latency_ms: 920,
          duration_ms: 1430,
          audio_length_bytes: 16384,
          timestamp: undefined,
        },
        onWarmup: vi.fn(),
        onRestart: vi.fn(),
        onClearQueue: vi.fn(),
        onTestSpeak,
      },
    });

    const input = screen.getByPlaceholderText(/masukkan teks untuk disintesis/i);
    await fireEvent.input(input, { target: { value: 'Halo operator' } });
    await fireEvent.click(screen.getByRole('button', { name: /^tes suara$/i }));

    expect(onTestSpeak).toHaveBeenCalledWith('Halo operator');
    expect(screen.getByText(/latency 920 ms/i)).toBeInTheDocument();
    expect(screen.getByText(/durasi 1430 ms/i)).toBeInTheDocument();
    expect(screen.getByText(/ukuran audio 16384 bytes/i)).toBeInTheDocument();
  });
});
