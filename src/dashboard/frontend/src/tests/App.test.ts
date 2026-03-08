import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import App from '../App.svelte';

// Mock the realtime module to prevent WebSocket creation in jsdom
vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn(),
  stopRealtime: vi.fn(),
}));

// Mock the API module — must include all exports used by child components
vi.mock('../lib/api', () => ({
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
  getStatus: vi.fn().mockResolvedValue({
    state: 'IDLE',
    mock_mode: true,
    uptime_sec: 0,
    viewer_count: 0,
    current_product: null,
    stream_status: 'idle',
    stream_running: false,
    emergency_stopped: false,
    llm_budget_remaining: 5.0,
    safety_incidents: 0,
  }),
  getMetrics: vi.fn().mockResolvedValue({}),
  getReadiness: vi.fn().mockResolvedValue({ overall_status: 'ready', checks: [], blocking_issues: [], recommended_next_action: '' }),
  getHealthSummary: vi.fn().mockResolvedValue({ status: 'healthy', components: {} }),
  getLiveTalkingStatus: vi.fn().mockResolvedValue({ state: 'stopped' }),
  getLiveTalkingConfig: vi.fn().mockResolvedValue({ port: 8010 }),
  getLiveTalkingLogs: vi.fn().mockResolvedValue({ lines: [], count: 0 }),
  startLiveTalking: vi.fn(),
  stopLiveTalking: vi.fn(),
  validateLiveTalkingEngine: vi.fn(),
  validateRtmpTarget: vi.fn(),
  getProducts: vi.fn().mockResolvedValue([]),
  getRevenue: vi.fn().mockResolvedValue({}),
  getRecentChats: vi.fn().mockResolvedValue([]),
  getBrainStats: vi.fn().mockResolvedValue({}),
  getBrainHealth: vi.fn().mockResolvedValue({}),
  getBrainConfig: vi.fn().mockResolvedValue({}),
  startStream: vi.fn(),
  stopStream: vi.fn(),
  emergencyStop: vi.fn(),
  emergencyReset: vi.fn(),
  getPipelineState: vi.fn().mockResolvedValue({ current_state: 'IDLE' }),
  pipelineTransition: vi.fn(),
  switchProduct: vi.fn(),
  brainTest: vi.fn(),
  validateMockStack: vi.fn(),
  validateRuntimeTruth: vi.fn().mockResolvedValue({ status: 'pass', checks: [], evidence_id: 1 }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: [] }),
  getValidationHistory: vi.fn().mockResolvedValue([]),
}));

describe('App shell', () => {
  it('renders the tab navigation with Engine tab', () => {
    render(App);

    expect(screen.getByRole('tab', { name: 'Engine' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Readiness' })).toBeInTheDocument();
  });

  it('renders the header', () => {
    render(App);

    const header = document.querySelector('.app');
    expect(header).toBeInTheDocument();
  });

  it('renders the truth bar', async () => {
    render(App);

    const truthBar = await screen.findByTestId('truth-bar');
    expect(truthBar).toBeInTheDocument();
  });

  it('truth bar shows MOCK badge from runtime truth (not hardcoded header)', async () => {
    render(App);

    const mockBadge = await screen.findByText('MOCK');
    expect(mockBadge).toBeInTheDocument();

    // MOCK badge must be inside truth-bar, not in header
    const truthBar = await screen.findByTestId('truth-bar');
    expect(truthBar.contains(mockBadge)).toBe(true);
  });

  it('header does not contain a hardcoded mode badge', () => {
    render(App);

    const header = document.querySelector('header.header');
    expect(header).toBeInTheDocument();
    // Header should have no badge elements anymore
    const badges = header!.querySelectorAll('.badge');
    expect(badges.length).toBe(0);
  });

  it('truth bar shows validation state', async () => {
    render(App);

    const validationState = await screen.findByText(/unvalidated/i);
    expect(validationState).toBeInTheDocument();
  });

  it('truth bar shows data origin derived from provenance', async () => {
    render(App);

    const originEl = await screen.findByTestId('truth-origin');
    expect(originEl).toBeInTheDocument();
    // All provenance values are 'mock', so origin should be 'mock'
    expect(originEl.textContent).toBe('mock');
  });

  it('truth bar shows last_validated_at placeholder when null', async () => {
    render(App);

    const lastValidated = await screen.findByTestId('truth-last-validated');
    expect(lastValidated).toBeInTheDocument();
    expect(lastValidated.textContent).toBe('never');
  });
});
