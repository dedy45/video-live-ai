import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import StreamPanel from '../components/panels/StreamPanel.svelte';

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
  }),
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: false,
    face_runtime_mode: 'livetalking_local',
    voice_runtime_mode: 'fish_speech_local',
    stream_runtime_mode: 'idle',
    validation_state: 'passed',
    last_validated_at: '2026-03-11T01:00:00Z',
    provenance: {
      system_status: 'real_local',
      engine_status: 'real_local',
      stream_status: 'real_local',
    },
    timestamp: '2026-03-11T01:00:00Z',
  }),
  getPipelineState: vi.fn().mockResolvedValue({ current_state: 'IDLE' }),
  validateRtmpTarget: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  startStream: vi.fn().mockResolvedValue({}),
  stopStream: vi.fn().mockResolvedValue({}),
  emergencyStop: vi.fn().mockResolvedValue({ message: 'Emergency stop activated' }),
  emergencyReset: vi.fn().mockResolvedValue({ message: 'System reset' }),
  pipelineTransition: vi.fn().mockResolvedValue({ current_state: 'WARMING' }),
}));

describe('StreamPanel layout contract', () => {
  it('keeps RTMP configuration visible by default for operators', async () => {
    render(StreamPanel);

    expect(await screen.findByText(/RTMP Configuration/i)).toBeInTheDocument();
    expect(await screen.findByLabelText(/RTMP URL/i)).toBeInTheDocument();
    expect(await screen.findByLabelText(/Stream Key/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Show/i })).not.toBeInTheDocument();
  });
});
