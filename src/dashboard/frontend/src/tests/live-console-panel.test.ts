import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import LiveConsolePanel from '../components/panels/LiveConsolePanel.svelte';

// Mock the API module
vi.mock('../lib/api', () => ({
  getStatus: vi.fn().mockResolvedValue({
    state: 'IDLE',
    mock_mode: false,
    current_product: { id: 1, name: 'Kaos Premium' },
    stream_running: false,
    viewer_count: 0,
    uptime_sec: 0,
  }),
  getOpsSummary: vi.fn().mockResolvedValue({
    overall_status: 'ready',
    deployment_mode: 'ready',
    voice_status: 'healthy',
    face_status: 'healthy',
    stream_status: 'idle',
    incident_summary: { open_count: 0, highest_severity: 'none' },
    resource_metrics: { cpu_pct: 22, ram_pct: 44, disk_pct: 12, vram_pct: 71 },
    restart_counters: { voice: 0, face: 0, stream: 0 },
  }),
  getRuntimeTruth: vi.fn().mockResolvedValue({
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
    timestamp: '2026-03-11T01:00:00Z',
    face_engine: {
      requested_model: 'musetalk',
      resolved_model: 'musetalk',
      requested_avatar_id: 'musetalk_avatar1',
      resolved_avatar_id: 'musetalk_avatar1',
      engine_state: 'running',
      fallback_active: false,
      uptime_sec: 120,
    },
    voice_engine: {
      requested_engine: 'fish_speech',
      resolved_engine: 'fish_speech',
      fallback_active: false,
      server_reachable: true,
      reference_ready: true,
      queue_depth: 0,
      chunk_chars: 180,
      time_to_first_audio_ms: 310,
      latency_p50_ms: 420,
      latency_p95_ms: 610,
      last_latency_ms: 430,
      last_error: null,
    },
  }),
  getProducts: vi.fn().mockResolvedValue([
    {
      id: 1,
      name: 'Kaos Premium',
      price_formatted: 'Rp 89.000',
      commission_rate: 12,
      selling_points: ['Cotton premium', 'Adem dipakai'],
      affiliate_links: { tiktok: 'https://example.com/tiktok' },
    },
    {
      id: 2,
      name: 'Earbuds Wireless',
      price_formatted: 'Rp 249.000',
      commission_rate: 10,
      selling_points: ['Bluetooth 5.3'],
      affiliate_links: { shopee: 'https://example.com/shopee' },
    },
  ]),
  getLiveTalkingConfig: vi.fn().mockResolvedValue({
    debug_urls: {
      webrtcapi: 'http://127.0.0.1:8010/webrtcapi.html',
    },
  }),
  switchProduct: vi.fn().mockResolvedValue({ product: 'Earbuds Wireless' }),
  voiceTestSpeak: vi.fn().mockResolvedValue({ status: 'success', message: 'Voice test OK' }),
  startLiveTalking: vi.fn().mockResolvedValue({ status: 'success', message: 'Avatar started' }),
  stopLiveTalking: vi.fn().mockResolvedValue({ status: 'success', message: 'Avatar stopped' }),
  emergencyStop: vi.fn().mockResolvedValue({ status: 'success', message: 'Emergency stop activated' }),
}));

describe('LiveConsolePanel', () => {
  it('renders live console sections for current product, script rail, and quick actions', async () => {
    render(LiveConsolePanel);

    expect(await screen.findByText(/konsol live/i)).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /produk aktif/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /skrip panduan/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /aksi cepat/i })).toBeInTheDocument();
    expect((await screen.findAllByText(/Kaos Premium/i)).length).toBeGreaterThan(0);
    expect(await screen.findByRole('button', { name: /Tes Suara/i })).toBeInTheDocument();
  });
});
