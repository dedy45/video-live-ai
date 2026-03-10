import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ValidationPanel from '../components/panels/ValidationPanel.svelte';
import * as api from '../lib/api';

vi.mock('../lib/api', () => ({
  // System
  getStatus: vi.fn().mockResolvedValue({ state: 'IDLE', mock_mode: true }),
  getMetrics: vi.fn().mockResolvedValue({}),
  getRuntimeTruth: vi.fn().mockResolvedValue({ mock_mode: true, provenance: {} }),

  // Validation endpoints (what ValidationPanel uses)
  validateMockStack: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'config', passed: true, message: 'ok' }],
  }),
  validateLiveTalkingEngine: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'app_py_exists', passed: true, message: 'found' }],
  }),
  validateRtmpTarget: vi.fn().mockResolvedValue({
    status: 'fail',
    checks: [{ check: 'ffmpeg_available', passed: true, message: 'ok' }, { check: 'rtmp_configured', passed: false, message: 'not set' }],
  }),
  validateRuntimeTruth: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'mock_mode_explicit', passed: true, message: 'MOCK_MODE=true' }],
    evidence_id: 12345,
  }),
  validateRealModeReadiness: vi.fn().mockResolvedValue({
    status: 'blocked',
    checks: [
      { check: 'mock_mode_off', passed: false, message: 'MOCK_MODE=true' },
      { check: 'rtmp_configured', passed: false, message: 'not set' },
    ],
    blockers: ['mock_mode_off', 'rtmp_configured'],
  }),
  validateVoiceLocalClone: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'voice_reference_wav', passed: true, message: 'ok' }],
  }),
  validateAudioChunkingSmoke: vi.fn().mockResolvedValue({
    status: 'blocked',
    checks: [{ check: 'chunk_chars_configured', passed: false, message: 'chunk size not configured' }],
  }),
  validateStreamDryRun: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'ffmpeg_available', passed: true, message: 'ok' }],
  }),
  validateResourceBudget: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'cpu_metric_present', passed: true, message: '0.0' }],
  }),
  validateSoakSanity: vi.fn().mockResolvedValue({
    status: 'pass',
    checks: [{ check: 'incident_summary_present', passed: true, message: 'ok' }],
  }),
  getValidationHistory: vi.fn().mockResolvedValue([
    { id: 1, check_name: 'runtime-truth', status: 'pass', provenance: 'mock', timestamp: '2026-03-08T10:00:00Z' },
    { id: 2, check_name: 'real-mode-readiness', status: 'blocked', provenance: 'real_local', timestamp: '2026-03-08T10:01:00Z' },
  ]),

  // Other API functions (needed by other components that might get imported)
  getReadiness: vi.fn().mockResolvedValue({ overall_status: 'ready', checks: [] }),
  getHealthSummary: vi.fn().mockResolvedValue({ status: 'healthy', components: {} }),
  getLiveTalkingStatus: vi.fn().mockResolvedValue({ state: 'stopped' }),
  getLiveTalkingConfig: vi.fn().mockResolvedValue({ port: 8010 }),
  getLiveTalkingLogs: vi.fn().mockResolvedValue({ lines: [], count: 0 }),
  startLiveTalking: vi.fn(),
  stopLiveTalking: vi.fn(),
  getProducts: vi.fn().mockResolvedValue([]),
  getRevenue: vi.fn().mockResolvedValue({}),
  getRecentChats: vi.fn().mockResolvedValue([]),
  getBrainStats: vi.fn().mockResolvedValue({}),
  getBrainHealth: vi.fn().mockResolvedValue({}),
  getBrainConfig: vi.fn().mockResolvedValue({}),
  startStream: vi.fn(),
  stopStream: vi.fn(),
  emergencyStop: vi.fn(),
  emergencyReset: vi.fn(),
  getPipelineState: vi.fn().mockResolvedValue({ current_state: 'IDLE' }),
  pipelineTransition: vi.fn(),
  switchProduct: vi.fn(),
  brainTest: vi.fn(),
}));

describe('ValidationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders validation panel with run buttons', async () => {
    render(ValidationPanel);
    expect(await screen.findByTestId('run-runtime-truth')).toBeTruthy();
    expect(await screen.findByTestId('run-real-mode')).toBeTruthy();
    expect(await screen.findByTestId('run-mock-stack')).toBeTruthy();
    expect(await screen.findByTestId('run-live-talking')).toBeTruthy();
    expect(await screen.findByTestId('run-rtmp-target')).toBeTruthy();
  });

  it('loads validation history on mount', async () => {
    render(ValidationPanel);
    expect(api.getValidationHistory).toHaveBeenCalled();
    expect(await screen.findByTestId('validation-history')).toBeTruthy();
  });

  it('shows history entries', async () => {
    render(ValidationPanel);
    expect(await screen.findByText(/runtime-truth/i)).toBeTruthy();
    expect(await screen.findByText(/real-mode-readiness/i)).toBeTruthy();
  });

  it('run runtime truth check shows detail', async () => {
    render(ValidationPanel);
    const btn = await screen.findByTestId('run-runtime-truth');
    await fireEvent.click(btn);

    expect(api.validateRuntimeTruth).toHaveBeenCalled();
    expect(await screen.findByTestId('validation-detail')).toBeTruthy();
    expect(await screen.findByText(/MOCK_MODE=true/i)).toBeTruthy();
  });

  it('run real-mode readiness shows blockers', async () => {
    render(ValidationPanel);
    const btn = await screen.findByTestId('run-real-mode');
    await fireEvent.click(btn);

    expect(api.validateRealModeReadiness).toHaveBeenCalled();
    const blockedElements = await screen.findAllByText(/blocked/i);
    expect(blockedElements.length).toBeGreaterThanOrEqual(1);
    // mock_mode_off appears in both checks list and blockers list — use findAll
    const mockModeElements = await screen.findAllByText(/mock_mode_off/i);
    expect(mockModeElements.length).toBeGreaterThanOrEqual(1);
    // rtmp_configured appears in both checks and blockers — use findAll
    const rtmpElements = await screen.findAllByText(/rtmp_configured/i);
    expect(rtmpElements.length).toBeGreaterThanOrEqual(1);
  });

  it('shows error receipt when check fails', async () => {
    const mockError = new Error('API 500');
    vi.mocked(api.validateRuntimeTruth).mockRejectedValueOnce(mockError);

    render(ValidationPanel);
    const btn = await screen.findByTestId('run-runtime-truth');
    await fireEvent.click(btn);

    expect(await screen.findByText(/API 500/i)).toBeTruthy();
  });

  it('renders voice local clone and stream dry-run validation actions', async () => {
    render(ValidationPanel);
    expect(await screen.findByText(/voice local clone/i)).toBeTruthy();
    expect(await screen.findByText(/stream dry run/i)).toBeTruthy();
  });
});
