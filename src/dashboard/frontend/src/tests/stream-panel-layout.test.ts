import { describe, it, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/svelte';
import StreamPanel from '../components/panels/StreamPanel.svelte';

const mockedApi = vi.hoisted(() => ({
  getStatus: vi.fn(),
  getRuntimeTruth: vi.fn(),
  getPipelineState: vi.fn(),
  validateRtmpTarget: vi.fn(),
  getStreamTargets: vi.fn(),
  getLiveSession: vi.fn(),
  createStreamTarget: vi.fn(),
  updateStreamTarget: vi.fn(),
  validateStreamTarget: vi.fn(),
  activateStreamTarget: vi.fn(),
  startLiveSession: vi.fn(),
  stopLiveSession: vi.fn(),
  pauseLiveSession: vi.fn(),
  resumeLiveSession: vi.fn(),
  startStream: vi.fn(),
  stopStream: vi.fn(),
  emergencyStop: vi.fn(),
  emergencyReset: vi.fn(),
  pipelineTransition: vi.fn(),
}));

mockedApi.getStatus.mockResolvedValue({
    state: 'IDLE',
    mock_mode: false,
    uptime_sec: 0,
    viewer_count: 0,
    current_product: null,
    stream_status: 'idle',
    stream_running: false,
    emergency_stopped: false,
  });
mockedApi.getRuntimeTruth.mockResolvedValue({
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
  });
mockedApi.getPipelineState.mockResolvedValue({
  state: 'SELLING',
  valid_transitions: ['REACTING', 'ENGAGING', 'PAUSED', 'IDLE'],
});
mockedApi.validateRtmpTarget.mockResolvedValue({ status: 'pass', checks: [] });
mockedApi.getStreamTargets.mockResolvedValue([
    {
      id: 1,
      platform: 'tiktok',
      label: 'Primary TikTok',
      rtmp_url: 'rtmp://push.tiktok.test/live/',
      stream_key_masked: '***123',
      is_active: true,
      validation_status: 'pass',
      validation_checks: [],
    },
  ]);
mockedApi.getLiveSession.mockResolvedValue({
    session: { id: 11, status: 'active', platform: 'tiktok' },
    state: { current_mode: 'ROTATING', rotation_paused: false, pause_reason: '' },
    stream_target: { id: 1, label: 'Primary TikTok', is_active: true },
    products: [],
  });
mockedApi.createStreamTarget.mockResolvedValue({ id: 1 });
mockedApi.updateStreamTarget.mockResolvedValue({ id: 1 });
mockedApi.validateStreamTarget.mockResolvedValue({ status: 'pass', checks: [] });
mockedApi.activateStreamTarget.mockResolvedValue({ status: 'activated', target: { id: 1, is_active: true } });
mockedApi.startLiveSession.mockResolvedValue({ status: 'started', session: { id: 11, status: 'active' } });
mockedApi.stopLiveSession.mockResolvedValue({ status: 'stopped' });
mockedApi.pauseLiveSession.mockResolvedValue({ status: 'paused', state: { rotation_paused: true } });
mockedApi.resumeLiveSession.mockResolvedValue({ status: 'resumed', state: { rotation_paused: false } });
mockedApi.startStream.mockResolvedValue({});
mockedApi.stopStream.mockResolvedValue({});
mockedApi.emergencyStop.mockResolvedValue({ message: 'Emergency stop activated' });
mockedApi.emergencyReset.mockResolvedValue({ message: 'System reset' });
mockedApi.pipelineTransition.mockResolvedValue({ state: 'SELLING' });

vi.mock('../lib/api', () => ({
  getStatus: mockedApi.getStatus,
  getRuntimeTruth: mockedApi.getRuntimeTruth,
  getPipelineState: mockedApi.getPipelineState,
  validateRtmpTarget: mockedApi.validateRtmpTarget,
  getStreamTargets: mockedApi.getStreamTargets,
  getLiveSession: mockedApi.getLiveSession,
  createStreamTarget: mockedApi.createStreamTarget,
  updateStreamTarget: mockedApi.updateStreamTarget,
  validateStreamTarget: mockedApi.validateStreamTarget,
  activateStreamTarget: mockedApi.activateStreamTarget,
  startLiveSession: mockedApi.startLiveSession,
  stopLiveSession: mockedApi.stopLiveSession,
  pauseLiveSession: mockedApi.pauseLiveSession,
  resumeLiveSession: mockedApi.resumeLiveSession,
  startStream: mockedApi.startStream,
  stopStream: mockedApi.stopStream,
  emergencyStop: mockedApi.emergencyStop,
  emergencyReset: mockedApi.emergencyReset,
  pipelineTransition: mockedApi.pipelineTransition,
}));

describe('StreamPanel layout contract', () => {
  it('keeps persisted RTMP target management visible by default for operators', async () => {
    render(StreamPanel);

    expect(await screen.findByText(/RTMP Configuration/i)).toBeInTheDocument();
    expect(await screen.findByText(/Target RTMP Tersimpan/i)).toBeInTheDocument();
    expect(await screen.findByText(/Kontrol Sesi Live/i)).toBeInTheDocument();
    expect(await screen.findByLabelText(/RTMP URL/i)).toBeInTheDocument();
    expect(await screen.findByLabelText(/Stream Key/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Show/i })).not.toBeInTheDocument();
  });

  it('keeps RTMP target inputs inside a labelled form for accessible submission flows', async () => {
    render(StreamPanel);

    const form = await screen.findByRole('form', { name: /RTMP Target/i });
    expect(within(form).getByLabelText(/RTMP URL/i)).toBeInTheDocument();
    expect(within(form).getByLabelText(/Stream Key/i)).toBeInTheDocument();
    expect(within(form).getByRole('button', { name: /Simpan Target/i })).toBeInTheDocument();
  });

  it('renders backend-driven pipeline states instead of stale hardcoded targets', async () => {
    render(StreamPanel);

    const section = (await screen.findByText(/Pipeline state machine/i)).closest('section') as HTMLElement;
    expect(within(section).getByText(/^SELLING$/i)).toBeInTheDocument();
    expect(within(section).getByText(/^REACTING$/i)).toBeInTheDocument();
    expect(within(section).getByText(/^ENGAGING$/i)).toBeInTheDocument();
    expect(within(section).getByText(/^PAUSED$/i)).toBeInTheDocument();
    expect(within(section).queryByText(/^WARMING$/i)).not.toBeInTheDocument();
    expect(within(section).queryByText(/^COOLDOWN$/i)).not.toBeInTheDocument();
  });
});
