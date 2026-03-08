import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
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

const mockEmergencyReset = vi.fn();
const mockSwitchProduct = vi.fn();
const mockBrainTest = vi.fn();
const mockPipelineTransition = vi.fn();
const mockEmergencyStop = vi.fn();

vi.mock('../lib/api', () => ({
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
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: true,
    face_runtime_mode: 'mock',
    voice_runtime_mode: 'mock',
    stream_runtime_mode: 'mock',
    validation_state: 'unvalidated',
    last_validated_at: null,
    provenance: { system_status: 'mock', engine_status: 'mock', stream_status: 'mock' },
    timestamp: '2026-03-08T10:00:00Z',
  }),
  getPipelineState: vi.fn().mockResolvedValue({ current_state: 'IDLE' }),
  validateRtmpTarget: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  startStream: vi.fn().mockResolvedValue({}),
  stopStream: vi.fn().mockResolvedValue({}),
  emergencyStop: vi.fn().mockImplementation(() => mockEmergencyStop()),
  emergencyReset: vi.fn().mockImplementation(() => mockEmergencyReset()),
  pipelineTransition: vi.fn().mockImplementation((t: string) => mockPipelineTransition(t)),
  switchProduct: vi.fn().mockImplementation((id: number) => mockSwitchProduct(id)),
  getProducts: vi.fn().mockResolvedValue([
    { id: 1, name: 'Test Product', price_formatted: 'Rp 100.000' },
  ]),
  getRevenue: vi.fn().mockResolvedValue({ total: 0 }),
  getHealthSummary: vi.fn().mockResolvedValue({ status: 'healthy', components: {}, mock_mode: true }),
  getBrainStats: vi.fn().mockResolvedValue({ adapters: {} }),
  getBrainHealth: vi.fn().mockResolvedValue({ healthy_count: 0, total_count: 0, providers: {} }),
  brainTest: vi.fn().mockImplementation((payload: any) => mockBrainTest(payload)),
  validateMockStack: vi.fn().mockResolvedValue({ status: 'pass', checks: [] }),
  validateRuntimeTruth: vi.fn().mockResolvedValue({ status: 'pass', checks: [], evidence_id: 1 }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({ status: 'blocked', checks: [], blockers: [] }),
  getValidationHistory: vi.fn().mockResolvedValue([]),
}));

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
    expect(el.textContent).toContain('engine.start');
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
    expect(el.textContent).toContain('stream.start');
    expect(el.textContent).toContain('API 500');
    expect(el.classList.contains('receipt-error')).toBe(true);
  });

  it('does not render when receipt is null', () => {
    render(ActionReceiptComponent, { props: { receipt: null } });

    expect(screen.queryByTestId('action-receipt')).not.toBeInTheDocument();
  });
});

describe('StreamPanel — pipeline transition', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelineTransition.mockResolvedValue({ current_state: 'WARMING' });
    mockEmergencyReset.mockResolvedValue({ message: 'System reset' });
    mockEmergencyStop.mockResolvedValue({ message: 'Emergency stop activated' });
  });

  it('shows pipeline state card with current state', async () => {
    render(StreamPanel);

    const pipelineLabel = await screen.findByText('Pipeline State');
    expect(pipelineLabel).toBeInTheDocument();

    // IDLE appears as both the metric value and the button — use getAllByText
    const idleElements = await screen.findAllByText('IDLE');
    expect(idleElements.length).toBeGreaterThanOrEqual(1);
  });

  it('shows pipeline transition buttons for all targets', async () => {
    render(StreamPanel);

    // Wait for load
    await screen.findByText('Pipeline State');

    for (const target of ['WARMING', 'LIVE', 'COOLDOWN']) {
      const btn = screen.getByRole('button', { name: target });
      expect(btn).toBeInTheDocument();
    }
    // IDLE button also exists (disabled since it's current state)
    const idleBtn = screen.getByRole('button', { name: 'IDLE' });
    expect(idleBtn).toBeInTheDocument();
  });

  it('disables the button for the current pipeline state', async () => {
    render(StreamPanel);

    await screen.findByText('Pipeline State');

    // IDLE is current state, so its button should be disabled
    const idleBtn = screen.getByRole('button', { name: 'IDLE' });
    expect(idleBtn).toBeDisabled();

    // WARMING should be enabled
    const warmingBtn = screen.getByRole('button', { name: 'WARMING' });
    expect(warmingBtn).not.toBeDisabled();
  });

  it('calls pipelineTransition API and shows receipt on click', async () => {
    render(StreamPanel);

    await screen.findByText('Pipeline State');

    const warmingBtn = screen.getByRole('button', { name: 'WARMING' });
    await fireEvent.click(warmingBtn);

    expect(mockPipelineTransition).toHaveBeenCalledWith('WARMING');

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('pipeline.transition');
  });

  it('shows error receipt when pipeline transition fails', async () => {
    mockPipelineTransition.mockRejectedValue(new Error('API 400: Invalid transition'));

    render(StreamPanel);
    await screen.findByText('Pipeline State');

    const liveBtn = screen.getByRole('button', { name: 'LIVE' });
    await fireEvent.click(liveBtn);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('pipeline.transition');
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
    expect(receipt.textContent).toContain('product.switch');
    expect(receipt.textContent).toContain('Test Product');
  });

  it('shows error receipt when product switch fails', async () => {
    mockSwitchProduct.mockRejectedValue(new Error('API 404: Product not found'));

    render(CommercePanel);

    const switchBtn = await screen.findByRole('button', { name: 'Switch' });
    await fireEvent.click(switchBtn);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('product.switch');
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
    expect(receipt.textContent).toContain('brain.test');
    expect(receipt.textContent).toContain('openai');
    expect(receipt.classList.contains('receipt-success')).toBe(true);
  });

  it('shows error receipt when brain test fails', async () => {
    mockBrainTest.mockRejectedValue(new Error('API 503: Service unavailable'));

    render(DiagnosticsPanel);

    const btn = await screen.findByRole('button', { name: 'Test Brain' });
    await fireEvent.click(btn);

    const receipt = await screen.findByTestId('action-receipt');
    expect(receipt.textContent).toContain('brain.test');
    expect(receipt.textContent).toContain('API 503');
    expect(receipt.classList.contains('receipt-error')).toBe(true);
  });
});
