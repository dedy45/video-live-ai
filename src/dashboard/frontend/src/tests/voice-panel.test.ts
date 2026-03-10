import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import VoicePanel from '../components/panels/VoicePanel.svelte';

vi.mock('../lib/api', () => ({
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: false,
    host: { name: 'gpu-01', role: 'server_production' },
    deployment_mode: 'ready',
    face_runtime_mode: 'livetalking_local',
    voice_runtime_mode: 'fish_speech_local',
    stream_runtime_mode: 'idle',
    validation_state: 'passed',
    last_validated_at: null,
    provenance: {
      system_status: 'real_local',
      engine_status: 'real_local',
      stream_status: 'real_local',
    },
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
    timestamp: '2026-03-09T01:00:00Z',
  }),
  voiceWarmup: vi.fn(),
  voiceQueueClear: vi.fn(),
  voiceRestart: vi.fn(),
}));

describe('VoicePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders voice control center sections and actions', async () => {
    render(VoicePanel);
    expect(await screen.findByText(/voice control center/i)).toBeInTheDocument();
    expect(await screen.findByText(/warmup voice/i)).toBeInTheDocument();
    expect(await screen.findByText(/voice testing/i)).toBeInTheDocument();
    expect(await screen.findByText(/load reference/i)).toBeInTheDocument();
    expect(await screen.findByText(/run clone smoke/i)).toBeInTheDocument();
    expect(await screen.findByText(/last error/i)).toBeInTheDocument();
  });
});
