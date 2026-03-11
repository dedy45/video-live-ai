import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import MonitorPanel from '../components/panels/MonitorPanel.svelte';

vi.mock('../lib/realtime', () => ({
  startRealtime: vi.fn((cb: (snap: any) => void) => {
    setTimeout(() => {
      cb({
        stream_running: false,
        emergency_stopped: false,
        mock_mode: false,
        pipeline_state: 'IDLE',
        current_product: null,
        received_at: '2026-03-11T01:00:05Z',
        source: 'polling',
        truth: {
          mock_mode: false,
          face_runtime_mode: 'livetalking_local',
          voice_runtime_mode: 'fish_speech_local',
          stream_runtime_mode: 'idle',
          validation_state: 'passed',
          last_validated_at: '2026-03-11T01:00:00Z',
          provenance: {
            system_status: 'real_local',
            engine_status: 'real_local',
            stream_status: 'real_local',
          },
          timestamp: '2026-03-11T01:00:05Z',
        },
        health: {
          status: 'healthy',
          components: {
            voice: 'healthy',
            face: 'healthy',
          },
        },
      });
    }, 0);
  }),
  stopRealtime: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  getRecentChats: vi.fn().mockResolvedValue([]),
  getHealthSummary: vi.fn().mockResolvedValue({
    status: 'healthy',
    components: {
      voice: 'healthy',
      face: 'healthy',
    },
  }),
  getResources: vi.fn().mockResolvedValue({ cpu_pct: 12, ram_pct: 48, disk_pct: 33, vram_pct: null }),
  getIncidents: vi.fn().mockResolvedValue([]),
  getBrainHealth: vi.fn().mockResolvedValue({
    healthy_count: 1,
    total_count: 2,
    providers: { groq: true, openai: false },
  }),
  getBrainStats: vi.fn().mockResolvedValue({
    active_provider: 'groq',
    active_model: 'llama-3.3-70b',
    adapters: {
      groq: { available: true, model: 'llama-3.3-70b' },
      openai: { available: false, model: 'gpt-4o-mini' },
    },
  }),
}));

describe('MonitorPanel', () => {
  it('renders health, resource pressure, llm brain posture, and realtime source', async () => {
    render(MonitorPanel);

    expect(await screen.findByText(/operations monitor/i)).toBeInTheDocument();
    expect(await screen.findByText('voice')).toBeInTheDocument();
    expect(await screen.findByText('face')).toBeInTheDocument();
    expect((await screen.findAllByText(/LLM Brain/i)).length).toBeGreaterThan(0);
    expect(await screen.findByText(/Alert posture/i)).toBeInTheDocument();
    expect(await screen.findByTestId('realtime-source')).toHaveTextContent('polling');
  });
});
