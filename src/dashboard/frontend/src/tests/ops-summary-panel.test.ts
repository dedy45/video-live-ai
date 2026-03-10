import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import OpsSummaryPanel from '../components/panels/OpsSummaryPanel.svelte';

vi.mock('../lib/api', () => ({
  getOpsSummary: vi.fn().mockResolvedValue({
    overall_status: 'ready',
    deployment_mode: 'ready',
    voice_status: 'fish_speech_local',
    face_status: 'livetalking_local',
    stream_status: 'idle',
    incident_summary: { open_count: 1, highest_severity: 'warn' },
    resource_metrics: { cpu_pct: 12.5, ram_pct: 33.2, disk_pct: 44.1, vram_pct: null },
    restart_counters: { voice: 2, face: 1, stream: 0 },
  }),
}));

describe('OpsSummaryPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders core ops summary metrics', async () => {
    render(OpsSummaryPanel);
    expect(await screen.findByText(/overall status/i)).toBeInTheDocument();
    expect(await screen.findByText(/restart count/i)).toBeInTheDocument();
  });
});
