import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import EnginePanel from '../components/panels/EnginePanel.svelte';

// Mock the API module before importing the component
vi.mock('../lib/api', () => ({
  getLiveTalkingStatus: vi.fn().mockResolvedValue({
    state: 'stopped',
    pid: null,
    port: 8010,
    model: 'wav2lip',
    avatar_id: 'wav2lip256_avatar1',
    requested_model: 'musetalk',
    resolved_model: 'wav2lip',
    requested_avatar_id: 'musetalk_avatar1',
    resolved_avatar_id: 'wav2lip256_avatar1',
    transport: 'webrtc',
    uptime_sec: 0,
    last_error: '',
    app_py_exists: true,
    model_path_exists: false,
    avatar_path_exists: false,
  }),
  getLiveTalkingConfig: vi.fn().mockResolvedValue({
    port: 8010,
    transport: 'webrtc',
    model: 'wav2lip',
    avatar_id: 'wav2lip256_avatar1',
    requested_model: 'musetalk',
    resolved_model: 'wav2lip',
    requested_avatar_id: 'musetalk_avatar1',
    resolved_avatar_id: 'wav2lip256_avatar1',
    debug_urls: {
      webrtcapi: 'http://localhost:8010/webrtcapi.html',
      rtcpushapi: 'http://localhost:8010/rtcpushapi.html',
      dashboard_vendor: 'http://localhost:8010/dashboard.html',
      echoapi: 'http://localhost:8010/echoapi.html',
    },
  }),
  getLiveTalkingLogs: vi.fn().mockResolvedValue({ lines: [], count: 0 }),
  startLiveTalking: vi.fn(),
  stopLiveTalking: vi.fn(),
  validateLiveTalkingEngine: vi.fn(),
  getRuntimeTruth: vi.fn().mockResolvedValue({
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
    timestamp: '2026-03-08T10:00:00Z',
  }),
}));

describe('EnginePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the panel title', async () => {
    render(EnginePanel);

    // Wait for async data load
    const title = await screen.findByText('LiveTalking Engine');
    expect(title).toBeInTheDocument();
  });

  it('shows requested and resolved model after load', async () => {
    render(EnginePanel);

    const requestedModelLabel = await screen.findByText('Requested Model');
    expect(requestedModelLabel).toBeInTheDocument();

    const resolvedModelLabel = await screen.findByText('Resolved Model');
    expect(resolvedModelLabel).toBeInTheDocument();
  });

  it('shows requested and resolved avatar after load', async () => {
    render(EnginePanel);

    const requestedAvatarLabel = await screen.findByText('Requested Avatar');
    expect(requestedAvatarLabel).toBeInTheDocument();

    const resolvedAvatarLabel = await screen.findByText('Resolved Avatar');
    expect(resolvedAvatarLabel).toBeInTheDocument();
  });

  it('shows fallback warning when requested differs from resolved', async () => {
    render(EnginePanel);

    // The fallback indicator should show because musetalk != wav2lip
    const fallbackLabel = await screen.findAllByText('Fallback');
    expect(fallbackLabel.length).toBeGreaterThanOrEqual(1);
  });

  it('shows a provenance badge sourced from runtime truth API', async () => {
    render(EnginePanel);

    const badge = await screen.findByTestId('provenance-badge');
    expect(badge).toBeInTheDocument();
    // Provenance should come from truth.provenance.engine_status ('mock'), not derived from status.state
    expect(badge.textContent).toBe('mock');
  });

  it('shows a freshness badge', async () => {
    render(EnginePanel);

    const badge = await screen.findByTestId('freshness-badge');
    expect(badge).toBeInTheDocument();
  });
});
