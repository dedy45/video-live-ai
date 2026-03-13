import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/svelte';
import ActionReceiptComponent from '../components/common/ActionReceipt.svelte';
import StreamPanel from '../components/panels/StreamPanel.svelte';
import CommercePanel from '../components/panels/CommercePanel.svelte';
import DiagnosticsPanel from '../components/panels/DiagnosticsPanel.svelte';

// Mock the realtime module to prevent WebSocket creation in jsdom
vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn(),
  stopRealtime: vi.fn(),
}));

// --- Mocks ---

const mockTruth = {
  mock_mode: true,
  face_runtime_mode: 'mock',
  voice_runtime_mode: 'mock',
  stream_runtime_mode: 'mock',
  validation_state: 'unvalidated',
  last_validated_at: null,
  provenance: { system_status: 'mock', engine_status: 'mock', stream_status: 'mock' },
  timestamp: '2026-03-08T10:00:00Z',
};

const mockStatus = {
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
};

const mockedApi = vi.hoisted(() => ({
  emergencyReset: vi.fn(),
  switchProduct: vi.fn(),
  brainTest: vi.fn(),
  pipelineTransition: vi.fn(),
  emergencyStop: vi.fn(),
  getStatus: vi.fn(),
  getRuntimeTruth: vi.fn(),
  getPipelineState: vi.fn(),
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
  validateStreamDryRun: vi.fn(),
}));

const mockEmergencyReset = mockedApi.emergencyReset;
const mockSwitchProduct = mockedApi.switchProduct;
const mockBrainTest = mockedApi.brainTest;
const mockPipelineTransition = mockedApi.pipelineTransition;
const mockEmergencyStop = mockedApi.emergencyStop;
const mockGetStatus = mockedApi.getStatus;
const mockGetRuntimeTruth = mockedApi.getRuntimeTruth;
const mockGetPipelineState = mockedApi.getPipelineState;
const mockGetStreamTargets = mockedApi.getStreamTargets;
const mockGetLiveSession = mockedApi.getLiveSession;
const mockCreateStreamTarget = mockedApi.createStreamTarget;
const mockUpdateStreamTarget = mockedApi.updateStreamTarget;
const mockValidateStreamTarget = mockedApi.validateStreamTarget;
const mockActivateStreamTarget = mockedApi.activateStreamTarget;
const mockStartLiveSession = mockedApi.startLiveSession;
const mockStopLiveSession = mockedApi.stopLiveSession;
const mockPauseLiveSession = mockedApi.pauseLiveSession;
const mockResumeLiveSession = mockedApi.resumeLiveSession;
const mockValidateStreamDryRun = mockedApi.validateStreamDryRun;

mockGetStatus.mockResolvedValue(mockStatus);
mockGetRuntimeTruth.mockResolvedValue(mockTruth);
mockGetPipelineState.mockResolvedValue({
  current_state: 'IDLE',
  valid_transitions: ['SELLING', 'PAUSED'],
});
mockGetStreamTargets.mockResolvedValue([
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
mockGetLiveSession.mockResolvedValue({
  session: null,
  state: { current_mode: 'IDLE', rotation_paused: false, pause_reason: '' },
  stream_target: null,
  products: [],
});
mockCreateStreamTarget.mockResolvedValue({ id: 1 });
mockUpdateStreamTarget.mockResolvedValue({ id: 1 });
mockValidateStreamTarget.mockResolvedValue({ status: 'pass', checks: [] });
mockActivateStreamTarget.mockResolvedValue({ status: 'activated' });
mockStartLiveSession.mockResolvedValue({ status: 'started' });
mockStopLiveSession.mockResolvedValue({ status: 'stopped' });
mockPauseLiveSession.mockResolvedValue({ status: 'paused' });
mockResumeLiveSession.mockResolvedValue({ status: 'resumed' });
mockValidateStreamDryRun.mockResolvedValue({ status: 'pass', checks: [] });

vi.mock('../lib/api', () => ({
  getStatus: mockedApi.getStatus,
  getRuntimeTruth: mockedApi.getRuntimeTruth,
  getPipelineState: mockedApi.getPipelineState,
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
  validateRtmpTarget: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateStreamDryRun: mockedApi.validateStreamDryRun,
  startStream: vi.fn().mockResolvedValue({}),
  stopStream: vi.fn().mockResolvedValue({}),
  emergencyStop: vi.fn().mockImplementation(() => mockedApi.emergencyStop()),
  emergencyReset: vi.fn().mockImplementation(() => mockedApi.emergencyReset()),
  pipelineTransition: vi.fn().mockImplementation((t: string) => mockedApi.pipelineTransition(t)),
  switchProduct: vi.fn().mockImplementation((id: number) => mockedApi.switchProduct(id)),
  getProducts: vi.fn().mockResolvedValue([
    { id: 1, name: 'Test Product', price_formatted: 'Rp 100.000' },
  ]),
  getRevenue: vi.fn().mockResolvedValue({ total: 0 }),
  getHealthSummary: vi.fn().mockResolvedValue({ status: 'healthy', components: {}, mock_mode: true }),
  getBrainStats: vi.fn().mockResolvedValue({ adapters: {} }),
  getBrainHealth: vi.fn().mockResolvedValue({ healthy_count: 0, total_count: 0, providers: {} }),
  brainTest: vi.fn().mockImplementation((payload: any) => mockedApi.brainTest(payload)),
  validateMockStack: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateRuntimeTruth: vi.fn().mockResolvedValue({ status: 'pass', checks: [], evidence_id: 1 }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: [] }),
  getValidationHistory: vi.fn().mockResolvedValue([]),
}));

function getPipelineButton(section: HTMLElement, label: string) {
  return within(section).getByText(new RegExp(`^${label}$`, 'i')).closest('button') as HTMLButtonElement;
}

describe('ActionReceipt component', () => {
  it('renders success receipt with correct styling and content', () => {
    const receipt = {
      action: 'engine.start',
      status: 'success' as const,
      message: 'Engine started (state: running)',
      timestamp: Date.now(),
    };

    render(ActionReceiptComponent, { props: { receipt } });

    const el = screen.getByTestId('action-receipt');
    expect(el).toBeInTheDocument();
    expect(el.textContent).toContain('Avatar menerima perintah jalan');
    expect(el.textContent).toContain('Engine started');
    expect(el.classList.contains('receipt-success')).toBe(true);
  });

  it('renders error receipt with correct styling and content', () => {
    const receipt = {
      action: 'stream.start',
      status: 'error' as const,
      message: 'API 500: Internal server error',
      timestamp: Date.now(),
    };

    render(ActionReceiptComponent, { props: { receipt } });

    const el = screen.getByTestId('action-receipt');
    expect(el).toBeInTheDocument();
    expect(el.textContent).toContain('Permintaan mulai streaming dikirim');
    expect(el.textContent).toContain('API 500');
    expect(el.classList.contains('receipt-error')).toBe(true);
  });

  it('renders blocked receipt with operator-visible styling', () => {
    const receipt = {
      action: 'voice.warmup',
      status: 'blocked' as const,
      message: 'Voice sidecar is not reachable yet',
      timestamp: Date.now(),
    };

    render(ActionReceiptComponent, { props: { receipt } });

    const el = screen.getByTestId('action-receipt');
    expect(el).toBeInTheDocument();
    expect(el.textContent).toContain('Permintaan pemanasan suara dikirim');
    expect(el.textContent).toContain('not reachable');
    expect(el.classList.contains('receipt-blocked')).toBe(true);
  });

  it('does not render when receipt is null', () => {
    render(ActionReceiptComponent, { props: { receipt: null } });

    expect(screen.queryByTestId('action-receipt')).not.toBeInTheDocument();
  });
});

describe('StreamPanel — pipeline transition', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelineTransition.mockResolvedValue({ current_state: 'SELLING' });
    mockEmergencyReset.mockResolvedValue({ message: 'System reset' });
    mockEmergencyStop.mockResolvedValue({ message: 'Emergency stop activated' });
  });

  it('shows pipeline state card with current state', async () => {
    render(StreamPanel);

    const pipelineLabel = await screen.findByText(/Pipeline state machine/i);
    expect(pipelineLabel).toBeInTheDocument();

    // IDLE appears as both the metric value and the button — use getAllByText
    const idleElements = await screen.findAllByText('IDLE');
    expect(idleElements.length).toBeGreaterThanOrEqual(1);
  });

  it('shows pipeline transition buttons for all targets', async () => {
    render(StreamPanel);

    const pipelineSection = (await screen.findByText(/Pipeline state machine/i)).closest('section') as HTMLElement;

    for (const target of ['SELLING', 'PAUSED']) {
      const btn = getPipelineButton(pipelineSection, target);
      expect(btn).toBeInTheDocument();
    }
    const idleBtn = getPipelineButton(pipelineSection, 'IDLE');
    expect(idleBtn).toBeInTheDocument();
  });

  it('disables the button for the current pipeline state', async () => {
    render(StreamPanel);

    const pipelineSection = (await screen.findByText(/Pipeline state machine/i)).closest('section') as HTMLElement;

    const idleBtn = getPipelineButton(pipelineSection, 'IDLE');
    expect(idleBtn).toBeDisabled();

    const sellingBtn = getPipelineButton(pipelineSection, 'SELLING');
    expect(sellingBtn).not.toBeDisabled();
  });

  it('calls pipelineTransition API and shows receipt on click', async () => {
    render(StreamPanel);

    const pipelineSection = (await screen.findByText(/Pipeline state machine/i)).closest('section') as HTMLElement;

    const sellingBtn = getPipelineButton(pipelineSection, 'SELLING');
    await fireEvent.click(sellingBtn);

    expect(mockPipelineTransition).toHaveBeenCalledWith('SELLING');

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('Perubahan status pipeline diproses');
  });

  it('shows error receipt when pipeline transition fails', async () => {
    mockPipelineTransition.mockRejectedValue(new Error('API 400: Invalid transition'));

    render(StreamPanel);
    const pipelineSection = (await screen.findByText(/Pipeline state machine/i)).closest('section') as HTMLElement;

    const pausedBtn = getPipelineButton(pipelineSection, 'PAUSED');
    await fireEvent.click(pausedBtn);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('Perubahan status pipeline diproses');
    expect(receipt.textContent).toContain('API 400');
    expect(receipt.classList.contains('receipt-error')).toBe(true);
  });
});

describe('StreamPanel — emergency reset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockEmergencyReset.mockResolvedValue({ message: 'System reset' });
    mockPipelineTransition.mockResolvedValue({ current_state: 'IDLE' });
  });

  it('shows Reset Emergency button when emergency_stopped is true and calls API', async () => {
    // Override getStatus to return emergency_stopped: true
    const api = await import('../lib/api');
    (api.getStatus as any).mockResolvedValue({ ...mockStatus, emergency_stopped: true });

    render(StreamPanel);

    const resetBtn = await screen.findByRole('button', { name: 'Reset Emergency' });
    expect(resetBtn).toBeInTheDocument();

    await fireEvent.click(resetBtn);

    expect(mockEmergencyReset).toHaveBeenCalled();
  });
});

describe('CommercePanel — product switch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSwitchProduct.mockResolvedValue({ product: 'Test Product' });
  });

  it('shows Switch button for each product', async () => {
    render(CommercePanel);

    const switchBtn = await screen.findByRole('button', { name: 'Switch' });
    expect(switchBtn).toBeInTheDocument();
  });

  it('calls switchProduct API and shows receipt on click', async () => {
    render(CommercePanel);

    const switchBtn = await screen.findByRole('button', { name: 'Switch' });
    await fireEvent.click(switchBtn);

    expect(mockSwitchProduct).toHaveBeenCalledWith(1);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('Produk aktif berhasil diganti');
    expect(receipt.textContent).toContain('Test Product');
  });

  it('shows error receipt when product switch fails', async () => {
    mockSwitchProduct.mockRejectedValue(new Error('API 404: Product not found'));

    render(CommercePanel);

    const switchBtn = await screen.findByRole('button', { name: 'Switch' });
    await fireEvent.click(switchBtn);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('Produk aktif berhasil diganti');
    expect(receipt.textContent).toContain('API 404');
    expect(receipt.classList.contains('receipt-error')).toBe(true);
  });
});

describe('DiagnosticsPanel — brain test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBrainTest.mockResolvedValue({
      success: true,
      provider: 'openai',
      model: 'gpt-4',
      latency_ms: 250,
      text: 'Hello! This is a test response.',
    });
  });

  it('shows Test Brain button', async () => {
    render(DiagnosticsPanel);

    const btn = await screen.findByRole('button', { name: 'Test Brain' });
    expect(btn).toBeInTheDocument();
  });

  it('calls brainTest API and shows success receipt', async () => {
    render(DiagnosticsPanel);

    const btn = await screen.findByRole('button', { name: 'Test Brain' });
    await fireEvent.click(btn);

    expect(mockBrainTest).toHaveBeenCalledWith({ user_prompt: 'Halo, perkenalkan produk ini!' });

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('Pemeriksaan diagnostik selesai');
    expect(receipt.textContent).toContain('openai');
    expect(receipt.classList.contains('receipt-success')).toBe(true);
  });

  it('shows error receipt when brain test fails', async () => {
    mockBrainTest.mockRejectedValue(new Error('API 503: Service unavailable'));

    render(DiagnosticsPanel);

    const btn = await screen.findByRole('button', { name: 'Test Brain' });
    await fireEvent.click(btn);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('Pemeriksaan diagnostik selesai');
    expect(receipt.textContent).toContain('API 503');
    expect(receipt.classList.contains('receipt-error')).toBe(true);
  });
});
