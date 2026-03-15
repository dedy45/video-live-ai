import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import App from '../App.svelte';

// Mock the realtime module — feed TruthBar with snapshot data via callback
vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn((cb: (snap: any) => void) => {
    // Simulate a realtime snapshot arriving immediately
    setTimeout(() => {
      cb({
        stream_running: false,
        emergency_stopped: false,
        mock_mode: true,
        pipeline_state: 'IDLE',
        current_product: null,
        received_at: new Date().toISOString(),
        source: 'polling',
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
          timestamp: '2026-03-08T10:00:00Z',
        },
      });
    }, 0);
  }),
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
  getDirectorRuntime: vi.fn().mockResolvedValue({
    director: {
      state: 'IDLE',
      current_phase: 'hook',
      stream_running: false,
      emergency_stopped: false,
      manual_override: false,
      active_provider: 'auto',
      active_model: 'unknown',
      active_prompt_revision: 'default-live-commerce:v1',
      history: [],
      valid_transitions: ['SELLING', 'PAUSED'],
      phase_sequence: ['hook', 'problem', 'solution', 'features', 'social_proof', 'urgency', 'cta'],
    },
    brain: { active_provider: 'auto', active_model: 'unknown', routing_table: {}, adapter_count: 0, daily_budget_usd: 5 },
    prompt: { active_revision: 'default-live-commerce:v1', slug: 'default-live-commerce', version: 1, status: 'active' },
    persona: { name: 'Sari', tone: 'warm', language: 'Indonesian casual', forbidden_topics: [], catchphrases: [] },
    script: { current_phase: 'hook', phase_sequence: ['hook', 'problem', 'solution', 'features', 'social_proof', 'urgency', 'cta'] },
  }),
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
  validateVoiceLocalClone: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateAudioChunkingSmoke: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateStreamDryRun: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateResourceBudget: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateSoakSanity: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  getValidationHistory: vi.fn().mockResolvedValue([]),
  getOpsSummary: vi.fn().mockResolvedValue({
    overall_status: 'ready',
    deployment_mode: 'ready',
    voice_status: 'healthy',
    face_status: 'healthy',
    stream_status: 'idle',
    incident_summary: { open_count: 0, highest_severity: 'none' },
    resource_metrics: { cpu_pct: 0, ram_pct: 0, disk_pct: 0, vram_pct: null },
    restart_counters: { voice: 0, face: 0, stream: 0 },
  }),
  getResources: vi.fn().mockResolvedValue({ cpu_pct: 0, ram_pct: 0, disk_pct: 0, vram_pct: null }),
  getIncidents: vi.fn().mockResolvedValue([]),
  ackIncident: vi.fn().mockResolvedValue({ status: 'success', message: 'acknowledged' }),
  voiceWarmup: vi.fn().mockResolvedValue({ status: 'success', message: 'warmed' }),
  voiceQueueClear: vi.fn().mockResolvedValue({ status: 'success', message: 'cleared' }),
  voiceRestart: vi.fn().mockResolvedValue({ status: 'success', message: 'restarted' }),
}));

describe('App shell', () => {
  it('uses a wide content frame for the performer route', () => {
    window.location.hash = '#/performer';

    render(App);

    const frame = document.querySelector('.page-frame');
    expect(frame).toBeInTheDocument();
    expect(frame).toHaveClass('page-frame-wide');
  });

  it('renders the workflow-based operator navigation links', () => {
    render(App);

    expect(screen.getByRole('link', { name: /Konsol Live/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Setup & Validasi/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Produk & Penawaran/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Avatar & Suara/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Streaming & Platform/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Monitor & Insiden/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Diagnostik$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Validasi$/i })).not.toBeInTheDocument();
  });

  it('renders the header', () => {
    render(App);

    const header = document.querySelector('.app');
    expect(header).toBeInTheDocument();
  });

  it('keeps a fixed sidebar shell and centered main content wrapper', () => {
    render(App);

    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
    expect(screen.getByTestId('app-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('app-main')).toBeInTheDocument();
    expect(screen.getByTestId('app-content')).toBeInTheDocument();
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
