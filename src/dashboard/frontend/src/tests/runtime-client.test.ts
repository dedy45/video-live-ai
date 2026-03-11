import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../lib/api', () => ({
  getStatus: vi.fn().mockResolvedValue({
    state: 'LIVE',
    mock_mode: false,
    uptime_sec: 45,
    viewer_count: 12,
    current_product: { id: 1, name: 'Serum A', price: 'Rp 99.000' },
    stream_status: 'live',
    stream_running: true,
    emergency_stopped: false,
    llm_budget_remaining: 4.2,
    safety_incidents: 0,
  }),
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: false,
    face_runtime_mode: 'livetalking_local',
    voice_runtime_mode: 'fish_speech_local',
    stream_runtime_mode: 'live',
    validation_state: 'passed',
    last_validated_at: '2026-03-11T01:00:00Z',
    provenance: {
      system_status: 'real_local',
      engine_status: 'real_local',
      stream_status: 'real_local',
    },
    timestamp: '2026-03-11T01:00:00Z',
  }),
  getHealthSummary: vi.fn().mockResolvedValue({
    status: 'healthy',
    components: {
      voice: 'healthy',
      face: 'healthy',
    },
  }),
}));

describe('runtime client', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it('bootstraps fresh status, truth, and health into one snapshot', async () => {
    const { bootstrapRuntimeSnapshot } = await import('../lib/runtime-client');

    const snapshot = await bootstrapRuntimeSnapshot();

    expect(snapshot.source).toBe('bootstrap');
    expect(snapshot.stream_running).toBe(true);
    expect(snapshot.truth?.voice_runtime_mode).toBe('fish_speech_local');
    expect(snapshot.health?.components?.voice).toBe('healthy');
  });

  it('normalizes polling data into the same snapshot shape as websocket mode', async () => {
    const { normalizePolledSnapshot } = await import('../lib/runtime-client');

    const snapshot = await normalizePolledSnapshot();

    expect(snapshot.source).toBe('polling');
    expect(snapshot.received_at).toBeTruthy();
    expect(snapshot.truth?.validation_state).toBe('passed');
    expect(snapshot.health?.status).toBe('healthy');
  });
});
