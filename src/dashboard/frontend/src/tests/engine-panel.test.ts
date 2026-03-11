import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import EnginePanel from '../components/panels/EnginePanel.svelte';

const stoppedTruth = {
  mock_mode: false,
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
  face_engine: {
    requested_model: 'musetalk',
    resolved_model: 'musetalk',
    requested_avatar_id: 'musetalk_avatar1',
    resolved_avatar_id: 'musetalk_avatar1',
    engine_state: 'stopped',
    fallback_active: false,
  },
};

const runningTruth = {
  ...stoppedTruth,
  face_runtime_mode: 'livetalking_running',
  face_engine: {
    ...stoppedTruth.face_engine,
    engine_state: 'running',
  },
};

const engineStatus = {
  state: 'stopped',
  pid: null,
  port: 8010,
  model: 'musetalk',
  avatar_id: 'musetalk_avatar1',
  requested_model: 'musetalk',
  resolved_model: 'musetalk',
  requested_avatar_id: 'musetalk_avatar1',
  resolved_avatar_id: 'musetalk_avatar1',
  transport: 'webrtc',
  uptime_sec: 0,
  last_error: '',
  app_py_exists: true,
  model_path_exists: true,
  avatar_path_exists: true,
};

describe('EnginePanel', () => {
  it('renders avatar controls from props when engine is stopped', () => {
    render(EnginePanel, {
      props: {
        truth: stoppedTruth,
        engineStatus,
        busyAction: '',
        onStart: vi.fn(),
        onStop: vi.fn(),
        onValidate: vi.fn(),
      },
    });

    expect(screen.getByRole('heading', { name: /^avatar$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /jalankan avatar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cek engine avatar/i })).toBeInTheDocument();
    expect(screen.getByText(/path dan runtime/i)).toBeInTheDocument();
    expect(screen.getAllByText(/musetalk_avatar1/i).length).toBeGreaterThanOrEqual(1);
  });

  it('calls stop handler when avatar is already running', async () => {
    const onStop = vi.fn();

    render(EnginePanel, {
      props: {
        truth: runningTruth,
        engineStatus: { ...engineStatus, state: 'running' },
        busyAction: '',
        onStart: vi.fn(),
        onStop,
        onValidate: vi.fn(),
      },
    });

    const button = screen.getByRole('button', { name: /hentikan avatar/i });
    expect(button).toBeInTheDocument();
    await fireEvent.click(button);
    expect(onStop).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/berjalan/i)).toBeInTheDocument();
  });
});
