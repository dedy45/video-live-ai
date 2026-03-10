import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import DiagnosticsPanel from '../components/panels/DiagnosticsPanel.svelte';

vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn((cb: (snap: any) => void) => {
    setTimeout(() => {
      cb({
        stream_running: false,
        emergency_stopped: false,
        mock_mode: true,
        pipeline_state: 'IDLE',
        received_at: new Date().toISOString(),
        source: 'polling',
        truth: {
          provenance: {
            system_status: 'mock',
          },
        },
        components: {
          voice: 'healthy',
          face: 'healthy',
          stream: 'idle',
        },
      });
    }, 0);
  }),
  stopRealtime: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  getHealthSummary: vi.fn().mockResolvedValue({
    status: 'healthy',
    mock_mode: true,
    components: {
      voice: 'healthy',
      face: 'healthy',
      stream: 'idle',
    },
  }),
  getBrainStats: vi.fn().mockResolvedValue({
    adapters: {
      gemini: { available: true, model: 'gemini-1.5-flash' },
      openai: { available: false, model: 'gpt-4' },
    },
  }),
  getBrainHealth: vi.fn().mockResolvedValue({
    healthy_count: 1,
    total_count: 2,
    providers: {
      gemini: true,
      openai: false,
    },
  }),
  brainTest: vi.fn().mockResolvedValue({
    success: true,
    provider: 'gemini',
    model: 'gemini-1.5-flash',
    latency_ms: 450,
  }),
  validateMockStack: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'config', passed: true, message: 'ok' }],
  }),
}));

describe('DiagnosticsPanel', () => {
  it('renders diagnostics payload instead of hanging on loading state', async () => {
    render(DiagnosticsPanel);

    expect(await screen.findByText(/system health/i)).toBeInTheDocument();
    expect(await screen.findByText(/llm brain health/i)).toBeInTheDocument();
    expect(await screen.findByText(/llm adapters/i)).toBeInTheDocument();
  });
});
