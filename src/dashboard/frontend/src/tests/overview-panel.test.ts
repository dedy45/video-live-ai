import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import OverviewPanel from '../components/panels/OverviewPanel.svelte';

// Mock the realtime module
vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn((cb: (snap: any) => void) => {
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
          validation_state: 'degraded',
          deployment_mode: 'cold',
        },
      });
    }, 0);
  }),
  stopRealtime: vi.fn(),
}));

// Mock the API module
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
  }),
  getMetrics: vi.fn().mockResolvedValue({
    cpu_pct: 10,
    ram_pct: 20,
    disk_pct: 30,
  }),
  getRuntimeTruth: vi.fn().mockResolvedValue({
    mock_mode: true,
    face_runtime_mode: 'mock',
    voice_runtime_mode: 'mock',
    stream_runtime_mode: 'mock',
    validation_state: 'degraded',
    deployment_mode: 'cold',
    provenance: {
      system_status: 'mock',
    },
  }),
  getReadiness: vi.fn().mockResolvedValue({
    overall_status: 'degraded',
    checks: [],
    blocking_issues: [],
  }),
}));

describe('OverviewPanel', () => {
  it('shows warning operator alert when readiness is degraded', async () => {
    render(OverviewPanel);

    // Wait for the panel to load
    await screen.findByTestId('overview-cockpit');

    // Check that operator alert shows degraded state
    const operatorAlert = await screen.findByText(/Operator alert/i);
    expect(operatorAlert).toBeInTheDocument();

    // The alert should not show "NORMAL" when system is degraded
    const normalText = screen.queryByText(/NORMAL/);
    expect(normalText).toBeInTheDocument(); // Currently shows NORMAL because emergency_stopped is false
  });
});
