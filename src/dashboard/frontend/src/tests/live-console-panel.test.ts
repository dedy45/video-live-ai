import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import LiveConsolePanel from '../components/panels/LiveConsolePanel.svelte';
import { ingestChatEvent } from '../lib/api';

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
  getLiveSession: vi.fn().mockResolvedValue({
    session: {
      id: 11,
      status: 'active',
      platform: 'tiktok',
      rotation_mode: 'operator_assisted',
      qna_mode: 'enabled',
    },
    stream_target: {
      id: 1,
      label: 'Primary TikTok',
      is_active: true,
    },
    state: {
      current_mode: 'SOFT_PAUSED_FOR_QNA',
      current_phase: 'answering',
      rotation_paused: true,
      pause_reason: 'viewer_question',
      current_focus_product_id: 1,
      pending_question: {
        text: 'Apakah ada COD?',
        reason: 'viewer_question',
        answer_draft: 'Halo kak, untuk COD cek opsi pembayaran di checkout ya.',
      },
    },
    products: [
      {
        id: 100,
        product_id: 1,
        product: {
          id: 1,
          name: 'Kaos Premium',
          price_formatted: 'Rp 89.000',
          commission_rate: 12,
          affiliate_links: { tiktok: 'https://example.com/tiktok' },
          selling_points: ['Cotton premium', 'Adem dipakai'],
        },
      },
      {
        id: 101,
        product_id: 2,
        product: {
          id: 2,
          name: 'Earbuds Wireless',
          price_formatted: 'Rp 249.000',
          commission_rate: 10,
          affiliate_links: { shopee: 'https://example.com/shopee' },
          selling_points: ['Bluetooth 5.3'],
        },
      },
    ],
  }),
  getLiveTalkingConfig: vi.fn().mockResolvedValue({
    debug_urls: {
      webrtcapi: 'http://127.0.0.1:8010/webrtcapi.html',
    },
  }),
  getDirectorRuntime: vi.fn().mockResolvedValue({
    director: {
      state: 'SELLING',
      current_phase: 'hook',
      stream_running: true,
      emergency_stopped: false,
      manual_override: false,
      active_provider: 'groq',
      active_model: 'llama-3.3-70b-versatile',
      active_prompt_revision: 'default-live-commerce:v1',
      history: [{ from: 'IDLE', to: 'SELLING', timestamp: 1 }],
      valid_transitions: ['REACTING', 'ENGAGING', 'PAUSED', 'IDLE'],
      phase_sequence: ['hook', 'problem', 'solution', 'features', 'social_proof', 'urgency', 'cta'],
    },
    brain: {
      active_provider: 'groq',
      active_model: 'llama-3.3-70b-versatile',
      routing_table: { chat_reply: ['groq', 'local'] },
      adapter_count: 2,
      daily_budget_usd: 5,
    },
    prompt: {
      active_revision: 'default-live-commerce:v1',
      slug: 'default-live-commerce',
      version: 1,
      status: 'active',
      updated_at: '2026-03-12T00:00:00Z',
    },
    persona: {
      name: 'Sari',
      tone: 'warm',
      language: 'Indonesian casual',
      forbidden_topics: ['politik'],
      catchphrases: ['Siapa yang mau?'],
    },
    script: {
      current_phase: 'hook',
      phase_sequence: ['hook', 'problem', 'solution', 'features', 'social_proof', 'urgency', 'cta'],
    },
  }),
  switchProduct: vi.fn().mockResolvedValue({ product: 'Earbuds Wireless' }),
  voiceTestSpeak: vi.fn().mockResolvedValue({ status: 'success', message: 'Voice test OK' }),
  startLiveTalking: vi.fn().mockResolvedValue({ status: 'success', message: 'Avatar started' }),
  stopLiveTalking: vi.fn().mockResolvedValue({ status: 'success', message: 'Avatar stopped' }),
  emergencyStop: vi.fn().mockResolvedValue({ status: 'success', message: 'Emergency stop activated' }),
  ingestChatEvent: vi.fn().mockResolvedValue({ status: 'recorded', auto_paused: true }),
}));

describe('LiveConsolePanel', () => {
  it('renders live console sections for current product, script rail, and quick actions', async () => {
    render(LiveConsolePanel);

    expect(await screen.findByText(/konsol live/i)).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /produk aktif/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /kontrol sesi/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /skrip panduan/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /aksi cepat/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /director runtime/i })).toBeInTheDocument();
    expect((await screen.findAllByText(/default-live-commerce:v1/i)).length).toBeGreaterThan(0);
    expect(await screen.findByText(/SOFT_PAUSED_FOR_QNA/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/Kaos Premium/i)).length).toBeGreaterThan(0);
    expect(await screen.findByRole('button', { name: /Tes Suara/i })).toBeInTheDocument();
  });

  it('shows pending question answer draft when qna pause is active', async () => {
    render(LiveConsolePanel);

    expect(await screen.findByText(/Pertanyaan tertunda: Apakah ada COD\?/i)).toBeInTheDocument();
    expect(await screen.findByText(/Draft jawaban: Halo kak, untuk COD cek opsi pembayaran di checkout ya\./i)).toBeInTheDocument();
  });

  it('lets operator inject a simulated viewer question into dashboard chat flow', async () => {
    render(LiveConsolePanel);

    await fireEvent.input(await screen.findByLabelText(/nama viewer/i), {
      target: { value: 'Ayu' },
    });
    await fireEvent.input(screen.getByLabelText(/pesan viewer/i), {
      target: { value: 'Kak ini ori ga?' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /kirim chat simulasi/i }));

    await waitFor(() => {
      expect(ingestChatEvent).toHaveBeenCalledWith({
        platform: 'tiktok',
        username: 'Ayu',
        message: 'Kak ini ori ga?',
      });
    });
  });
});
