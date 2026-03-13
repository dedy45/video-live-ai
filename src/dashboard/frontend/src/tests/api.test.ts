import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { EngineStatus, EngineConfig, ReadinessResult, SystemStatus, RuntimeTruth } from '../lib/types';
import {
  activateStreamTarget,
  createProduct,
  createStreamTarget,
  getLiveSession,
  getLiveTalkingDebugTargets,
  getRuntimeTruth,
  getStatus,
  pauseLiveSession,
  resumeLiveSession,
  voiceTestSpeak,
} from '../lib/api';

describe('API request policy', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockClear();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends operator requests with no-store cache policy', async () => {
    await getStatus();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, options] = fetchMock.mock.calls[0];
    expect(options.cache).toBe('no-store');
    expect(options.headers['Cache-Control']).toBe('no-cache');
    expect(options.headers.Pragma).toBe('no-cache');
  });

  it('applies the same no-store policy to truth requests', async () => {
    await getRuntimeTruth();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, options] = fetchMock.mock.calls[0];
    expect(options.cache).toBe('no-store');
    expect(options.headers['Cache-Control']).toBe('no-cache');
  });

  it('sends tes suara text as a query parameter so backend receives operator input', async () => {
    await voiceTestSpeak('Halo operator');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain('/voice/test/speak?text=Halo%20operator');
    expect(options.method).toBe('POST');
  });

  it('requests preview target probing from the dedicated debug endpoint', async () => {
    await getLiveTalkingDebugTargets();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain('/engine/livetalking/debug-targets');
    expect(options.method ?? 'GET').toBe('GET');
  });

  it('posts product mutations to the SQLite-backed control-plane endpoint', async () => {
    await createProduct({ name: 'Lip Cream', price: 89000 });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain('/products');
    expect(options.method).toBe('POST');
    expect(options.body).toContain('"name":"Lip Cream"');
  });

  it('posts stream target mutations to the persisted target endpoint', async () => {
    await createStreamTarget({
      platform: 'tiktok',
      label: 'Primary TikTok',
      rtmp_url: 'rtmp://push.tiktok.test/live/',
      stream_key: 'abc123',
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain('/stream-targets');
    expect(options.method).toBe('POST');
    expect(options.body).toContain('"platform":"tiktok"');
  });

  it('uses the session control-plane endpoints for activate, pause, resume, and summary', async () => {
    await activateStreamTarget(3);
    await pauseLiveSession({ reason: 'viewer_question', question: 'Harga berapa?' });
    await resumeLiveSession();
    await getLiveSession();

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(fetchMock.mock.calls[0][0]).toContain('/stream-targets/3/activate');
    expect(fetchMock.mock.calls[0][1].method).toBe('POST');
    expect(fetchMock.mock.calls[1][0]).toContain('/live-session/pause');
    expect(fetchMock.mock.calls[1][1].method).toBe('POST');
    expect(fetchMock.mock.calls[2][0]).toContain('/live-session/resume');
    expect(fetchMock.mock.calls[3][0]).toContain('/live-session');
  });
});

describe('API response types', () => {
  it('EngineStatus includes requested and resolved fields', () => {
    const status: EngineStatus = {
      state: 'stopped',
      pid: null,
      port: 8010,
      model: 'wav2lip',
      avatar_id: 'wav2lip256_avatar1',
      requested_model: 'musetalk',
      resolved_model: 'wav2lip',
      requested_avatar_id: 'musetalk_avatar1',
      resolved_avatar_id: 'wav2lip256_avatar1',
      transport: 'webrtc',
      uptime_sec: 0,
      last_error: '',
      app_py_exists: true,
      model_path_exists: false,
      avatar_path_exists: false,
    };

    expect(status.requested_model).toBe('musetalk');
    expect(status.resolved_model).toBe('wav2lip');
    expect(status.requested_avatar_id).toBe('musetalk_avatar1');
    expect(status.resolved_avatar_id).toBe('wav2lip256_avatar1');
  });

  it('EngineConfig includes requested and resolved fields', () => {
    const config: EngineConfig = {
      port: 8010,
      transport: 'webrtc',
      model: 'wav2lip',
      avatar_id: 'wav2lip256_avatar1',
      requested_model: 'musetalk',
      resolved_model: 'wav2lip',
      requested_avatar_id: 'musetalk_avatar1',
      resolved_avatar_id: 'wav2lip256_avatar1',
      livetalking_dir: 'external/livetalking',
      debug_urls: {
        webrtcapi: 'http://localhost:8010/webrtcapi.html',
        rtcpushapi: 'http://localhost:8010/rtcpushapi.html',
        dashboard_vendor: 'http://localhost:8010/dashboard.html',
        echoapi: 'http://localhost:8010/echoapi.html',
      },
    };

    expect(config.requested_model).toBe('musetalk');
    expect(config.resolved_model).toBe('wav2lip');
  });

  it('ReadinessResult shape is valid', () => {
    const result: ReadinessResult = {
      overall_status: 'degraded',
      checks: [
        { name: 'test', passed: true, status: 'ok', message: 'good', blocking: false },
      ],
      blocking_issues: [],
      recommended_next_action: 'none',
    };

    expect(result.overall_status).toBe('degraded');
    expect(result.checks).toHaveLength(1);
  });

  it('SystemStatus shape is valid', () => {
    const status: SystemStatus = {
      state: 'IDLE',
      mock_mode: true,
      uptime_sec: 123,
      viewer_count: 0,
      current_product: null,
      stream_status: 'idle',
      stream_running: false,
      emergency_stopped: false,
      llm_budget_remaining: 5.0,
      safety_incidents: 0,
    };

    expect(status.state).toBe('IDLE');
    expect(status.mock_mode).toBe(true);
  });

  it('RuntimeTruth shape includes provenance and validation state', () => {
    const truth: RuntimeTruth = {
      mock_mode: true,
      face_runtime_mode: 'mock',
      voice_runtime_mode: 'mock',
      stream_runtime_mode: 'mock',
      validation_state: 'unvalidated',
      last_validated_at: null,
      provenance: {
        system_status: 'mock',
        engine_status: 'mock',
        stream_status: 'mock',
        products: 'derived',
        metrics: 'derived',
      },
      timestamp: '2026-03-08T10:00:00Z',
    };

    expect(truth.mock_mode).toBe(true);
    expect(truth.validation_state).toBe('unvalidated');
    expect(truth.provenance.system_status).toBe('mock');
    expect(truth.last_validated_at).toBeNull();
  });
});
