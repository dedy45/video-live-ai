import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import TruthBar from '../components/common/TruthBar.svelte';

// Track the realtime callback so we can push snapshots into the store
let realtimeCallback: ((snap: any) => void) | null = null;

vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn((cb: (snap: any) => void) => {
    realtimeCallback = cb;
  }),
  stopRealtime: vi.fn(() => {
    realtimeCallback = null;
  }),
}));

function pushSnapshot(overrides: Record<string, any> = {}) {
  const base = {
    stream_running: false,
    emergency_stopped: false,
    mock_mode: true,
    pipeline_state: 'IDLE',
    current_product: null,
    received_at: new Date().toISOString(),
    source: 'websocket',
    truth: {
      mock_mode: true,
      face_runtime_mode: 'mock',
      voice_runtime_mode: 'mock',
      stream_runtime_mode: 'mock',
      validation_state: 'unvalidated',
      last_validated_at: null,
      provenance: {
        system_status: 'mock',
        engine_status: 'mock',
        stream_status: 'mock',
      },
      timestamp: '2026-03-09T01:00:00Z',
    },
    ...overrides,
  };
  realtimeCallback?.(base);
}

describe('TruthBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    realtimeCallback = null;
  });

  it('shows loading state before any snapshot arrives', () => {
    render(TruthBar);
    expect(screen.getByText('Loading truth...')).toBeInTheDocument();
  });

  it('shows MOCK badge when mock_mode is true', async () => {
    render(TruthBar);
    pushSnapshot();

    await waitFor(() => {
      expect(screen.getByText('MOCK')).toBeInTheDocument();
    });
  });

  it('shows LIVE badge when mock_mode is false', async () => {
    render(TruthBar);
    pushSnapshot({
      truth: {
        mock_mode: false,
        face_runtime_mode: 'livetalking_stopped',
        voice_runtime_mode: 'tts_local',
        stream_runtime_mode: 'idle',
        validation_state: 'unvalidated',
        last_validated_at: null,
        provenance: {
          system_status: 'real_local',
          engine_status: 'real_local',
          stream_status: 'real_local',
        },
        timestamp: '2026-03-09T01:00:00Z',
      },
    });

    await waitFor(() => {
      expect(screen.getByText('LIVE')).toBeInTheDocument();
    });
  });

  it('updates face_runtime_mode reactively when snapshot changes (engine.start scenario)', async () => {
    render(TruthBar);

    // Initial: engine stopped
    pushSnapshot({
      mock_mode: false,
      truth: {
        mock_mode: false,
        face_runtime_mode: 'livetalking_stopped',
        voice_runtime_mode: 'tts_local',
        stream_runtime_mode: 'idle',
        validation_state: 'unvalidated',
        last_validated_at: null,
        provenance: {
          system_status: 'real_local',
          engine_status: 'real_local',
          stream_status: 'real_local',
        },
        timestamp: '2026-03-09T01:00:00Z',
      },
    });

    const faceMode = await screen.findByTestId('truth-face-mode');
    expect(faceMode.textContent).toBe('livetalking_stopped');

    // Simulate engine.start -> next snapshot has livetalking_local
    pushSnapshot({
      mock_mode: false,
      truth: {
        mock_mode: false,
        face_runtime_mode: 'livetalking_local',
        voice_runtime_mode: 'tts_local',
        stream_runtime_mode: 'idle',
        validation_state: 'unvalidated',
        last_validated_at: null,
        provenance: {
          system_status: 'real_local',
          engine_status: 'real_local',
          stream_status: 'real_local',
        },
        timestamp: '2026-03-09T01:01:00Z',
      },
    });

    // TruthBar must reactively update WITHOUT reload
    await waitFor(() => {
      expect(faceMode.textContent).toBe('livetalking_local');
    });
  });

  it('shows realtime source indicator', async () => {
    render(TruthBar);
    pushSnapshot({ source: 'websocket' });

    const sourceEl = await screen.findByTestId('truth-source');
    expect(sourceEl.textContent).toBe('websocket');
  });

  it('shows origin from provenance', async () => {
    render(TruthBar);
    pushSnapshot();

    const originEl = await screen.findByTestId('truth-origin');
    expect(originEl.textContent).toBe('mock');
  });

  it('shows host role and deployment mode in the truth bar', async () => {
    render(TruthBar);
    pushSnapshot({
      truth: {
        mock_mode: false,
        host: { name: 'gpu-01', role: 'server_production' },
        deployment_mode: 'ready',
        incident_summary: { open_count: 1, highest_severity: 'warn' },
        guardrails: { restart_storm: false, disk_pressure: false },
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
        timestamp: '2026-03-09T01:00:00Z',
      },
    });

    expect(await screen.findByText(/gpu-01/i)).toBeInTheDocument();
    expect(await screen.findByText(/ready/i)).toBeInTheDocument();
  });
});
