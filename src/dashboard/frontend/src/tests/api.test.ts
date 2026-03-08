import { describe, it, expect } from 'vitest';
import type { EngineStatus, EngineConfig, ReadinessResult, SystemStatus, RuntimeTruth } from '../lib/types';

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
