import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import LiveConsolePanel from '../components/panels/LiveConsolePanel.svelte';

// Mock the API module
vi.mock('../lib/api', () => ({
  getStatus: vi.fn().mockResolvedValue({
    state: 'IDLE',
    mock_mode: true,
    current_product: null,
    stream_running: false,
  }),
  getOpsSummary: vi.fn().mockResolvedValue({
    overall_status: 'ready',
    deployment_mode: 'ready',
    voice_status: 'healthy',
    face_status: 'healthy',
    stream_status: 'idle',
  }),
}));

describe('LiveConsolePanel', () => {
  it('renders live console sections for current product, script rail, and quick actions', async () => {
    render(LiveConsolePanel);

    expect(await screen.findByText(/live console/i)).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /current product/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /script rail/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /next best action/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /quick actions/i })).toBeInTheDocument();
  });
});
