import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import IncidentsPanel from '../components/panels/IncidentsPanel.svelte';

vi.mock('../lib/api', () => ({
  getIncidents: vi.fn().mockResolvedValue([
    {
      id: 'inc-1',
      code: 'voice.timeout',
      severity: 'critical',
      subsystem: 'voice',
      acknowledged: false,
      resolved: false,
      created_at: '2026-03-09T01:00:00Z',
    },
  ]),
  ackIncident: vi.fn().mockResolvedValue({
    status: 'success',
    message: 'Incident inc-1 acknowledged',
    incident_id: 'inc-1',
  }),
}));

describe('IncidentsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders incident rows with severity and ack action', async () => {
    render(IncidentsPanel);
    expect(await screen.findByText(/critical/i)).toBeInTheDocument();
    expect(await screen.findByText(/acknowledge/i)).toBeInTheDocument();
  });
});
