import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import PerformerPanel from '../components/panels/PerformerPanel.svelte';

vi.mock('../lib/api', () => ({
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: false,
    deployment_mode: 'ready',
    face_runtime_mode: 'livetalking_local',
    voice_runtime_mode: 'fish_speech_local',
    stream_runtime_mode: 'idle',
    validation_state: 'passed',
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
      queue_depth: 0,
    },
    face_engine: {
      engine_type: 'musetalk',
      model_ready: true,
      gpu_loaded: true,
      fps_target: 25,
      latency_ms: 120,
    },
    timestamp: '2026-03-09T01:00:00Z',
  }),
}));

describe('PerformerPanel', () => {
  it('renders combined voice and face performer sections', async () => {
    render(PerformerPanel);

    expect(await screen.findByRole('heading', { name: /voice & face/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /voice runtime/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /face engine/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /preview/i })).toBeInTheDocument();
  });
});
