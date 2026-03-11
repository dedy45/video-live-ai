<script lang="ts">
  import { onMount } from 'svelte';
  import {
    emergencyReset,
    emergencyStop,
    getPipelineState,
    getRuntimeTruth,
    getStatus,
    pipelineTransition,
    startStream,
    stopStream,
    validateRtmpTarget,
    validateStreamDryRun,
  } from '../../lib/api';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let status = $state<Record<string, any>>({});
  let truth = $state<Record<string, any> | null>(null);
  let pipeline = $state<Record<string, any> | null>(null);
  let rtmpResult = $state<Record<string, any> | null>(null);
  let loading = $state(true);
  let loadedAt = $state<string | null>(null);
  let receipt = $state<ReceiptType | null>(null);

  let selectedPlatform = $state('TikTok');
  let rtmpUrl = $state('');
  let streamKey = $state('');

  const pipelineTargets = ['IDLE', 'WARMING', 'LIVE', 'COOLDOWN'];

  async function refresh() {
    loading = true;
    try {
      const [nextStatus, nextTruth, nextPipeline] = await Promise.all([
        getStatus(),
        getRuntimeTruth(),
        getPipelineState(),
      ]);
      status = nextStatus;
      truth = nextTruth;
      pipeline = nextPipeline;
      loadedAt = new Date().toISOString();
    } catch (nextError: any) {
      receipt = { action: 'stream.refresh', status: 'error', message: nextError.message, timestamp: Date.now() };
    } finally {
      loading = false;
    }
  }

  async function handleAction(action: string, work: () => Promise<any>, successMessage: string) {
    receipt = null;
    try {
      const result = await work();
      const message = result?.message || successMessage;
      receipt = { action, status: 'success', message, timestamp: Date.now() };
      await refresh();
    } catch (nextError: any) {
      receipt = { action, status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  async function handleValidateRtmp() {
    receipt = null;
    try {
      rtmpResult = await validateRtmpTarget();
      receipt = {
        action: 'rtmp.validate',
        status: rtmpResult.status === 'pass' ? 'success' : 'error',
        message: `RTMP validation: ${rtmpResult.status}`,
        timestamp: Date.now(),
      };
    } catch (nextError: any) {
      receipt = { action: 'rtmp.validate', status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  async function handleDryRun() {
    await handleAction('stream.dry_run', () => validateStreamDryRun(), 'Dry run selesai');
  }

  async function handlePipelineTransition(target: string) {
    await handleAction(
      'pipeline.transition',
      () => pipelineTransition(target),
      `Pipeline berpindah ke ${target}`,
    );
  }

  onMount(() => {
    void refresh();
  });
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Stream Control Center</h2>
      <p class="panel-subtitle">Kelola target RTMP, verifikasi dry-run, dan kontrol transisi pipeline live dengan data production yang selalu fresh.</p>
    </div>
    <div class="panel-meta">
      <ProvenanceBadge provenance={truth?.provenance?.stream_status || 'unknown'} />
      <FreshnessBadge timestamp={loadedAt} />
      <button class="btn btn-ghost btn-sm" onclick={refresh}>Refresh</button>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading stream control center...</p>
  {:else}
    <div class="hero-grid">
      <section class="hero-card">
        <div class="eyebrow">Stream posture</div>
        <div class="hero-value">{status.stream_status || 'idle'}</div>
        <div class="hero-copy">Runtime {truth?.stream_runtime_mode || 'unknown'} · Pipeline {pipeline?.current_state || 'unknown'}</div>
      </section>
      <section class="hero-card" class:alert={status.emergency_stopped}>
        <div class="eyebrow">Emergency state</div>
        <div class="hero-value">{status.emergency_stopped ? 'LOCKED' : 'CLEAR'}</div>
        <div class="hero-copy">Emergency stop harus dipakai hanya untuk recovery keras, bukan workflow rutin.</div>
      </section>
    </div>

    <section class="card">
      <div class="section-title">RTMP Configuration</div>
      <div class="form-grid">
        <div class="form-group">
          <label for="platform-target">Platform</label>
          <select id="platform-target" class="form-input" bind:value={selectedPlatform}>
            <option>TikTok</option>
            <option>Shopee</option>
          </select>
        </div>
        <div class="form-group">
          <label for="rtmp-url">RTMP URL</label>
          <input id="rtmp-url" class="form-input" bind:value={rtmpUrl} placeholder="rtmp://push.tiktokcdn.com/live/" />
          <span class="form-hint">Field ini bersifat draft operator. Source of truth runtime tetap env host sampai backend config write surface dibuka.</span>
        </div>
        <div class="form-group">
          <label for="stream-key">Stream Key</label>
          <input id="stream-key" type="password" class="form-input" bind:value={streamKey} placeholder="Paste stream key dari platform" />
          <span class="form-hint">Reload halaman tidak akan menyimpan draft ini ke browser storage.</span>
        </div>
      </div>
      <div class="rtmp-actions">
        <button class="btn btn-ghost" onclick={handleValidateRtmp}>Validate RTMP Target</button>
        <button class="btn btn-ghost" onclick={handleDryRun}>Dry Run</button>
      </div>
      {#if rtmpResult}
        <div class="result-box" class:pass={rtmpResult.status === 'pass'} class:fail={rtmpResult.status !== 'pass'}>
          <strong>{rtmpResult.status?.toUpperCase()}</strong>
          {#each rtmpResult.checks || [] as check}
            <div class="check-row">
              <span>{check.passed ? '●' : '○'}</span>
              <span>{check.check}</span>
              <span class="muted">{check.message}</span>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    <div class="section-grid">
      <section class="card">
        <div class="section-title">Live controls</div>
        <div class="button-stack">
          <button class="btn btn-start" onclick={() => handleAction('stream.start', startStream, 'Stream started')} disabled={status.stream_running || status.emergency_stopped}>Start Stream</button>
          <button class="btn btn-stop" onclick={() => handleAction('stream.stop', stopStream, 'Stream stopped')} disabled={!status.stream_running}>Stop Stream</button>
          {#if status.emergency_stopped}
            <button class="btn btn-reset" onclick={() => handleAction('emergency.reset', emergencyReset, 'Emergency reset')}>Reset Emergency</button>
          {:else}
            <button class="btn btn-emergency" onclick={() => handleAction('emergency.stop', emergencyStop, 'Emergency stop activated')}>Emergency Stop</button>
          {/if}
        </div>
      </section>

      <section class="card span-2">
        <div class="section-title">Pipeline state machine</div>
        <div class="stepper">
          {#each pipelineTargets as target, index}
            <button
              class="step"
              class:active={pipeline?.current_state === target}
              disabled={pipeline?.current_state === target}
              onclick={() => handlePipelineTransition(target)}
            >
              <span class="step-index">{index + 1}</span>
              <span class="step-label">{target}</span>
            </button>
          {/each}
        </div>
      </section>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  .panel-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
  .panel-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .hero-grid, .section-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }
  .hero-grid { margin-bottom: 14px; }
  .hero-card, .card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 18px; }
  .hero-card.alert { box-shadow: inset 0 0 0 1px rgba(233, 69, 96, 0.28); }
  .eyebrow, .section-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .hero-value { font-size: 32px; font-weight: 900; margin: 8px 0; }
  .hero-copy { color: var(--muted); font-size: 13px; }
  .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-top: 12px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group label { font-size: 12px; font-weight: 700; color: var(--text); }
  .form-input { padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--rsm); background: rgba(255, 255, 255, 0.03); color: var(--text); font-family: inherit; font-size: 14px; }
  .form-input:focus { outline: none; border-color: rgba(34, 211, 238, 0.6); }
  .form-hint { font-size: 11px; color: var(--muted); line-height: 1.4; }
  .rtmp-actions, .button-stack { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }
  .btn { padding: 10px 14px; border-radius: var(--rsm); border: 1px solid var(--border); cursor: pointer; font-weight: 700; font-family: inherit; }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-ghost { background: rgba(255, 255, 255, 0.05); color: var(--text); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .btn-start { background: rgba(0, 230, 118, 0.88); color: #06150d; }
  .btn-stop { background: rgba(255, 214, 0, 0.88); color: #161102; }
  .btn-emergency { background: rgba(233, 69, 96, 0.9); color: #fff; }
  .btn-reset { background: rgba(34, 211, 238, 0.85); color: #04111f; }
  .span-2 { grid-column: span 2; }
  .stepper { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 12px; }
  .step {
    display: grid;
    gap: 8px;
    padding: 14px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.04);
    color: var(--text);
    font-family: inherit;
    cursor: pointer;
    text-align: left;
  }
  .step.active {
    border-color: rgba(34, 211, 238, 0.5);
    background: rgba(34, 211, 238, 0.08);
  }
  .step:disabled {
    opacity: 1;
    cursor: default;
  }
  .step-index {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.08);
    font-size: 12px;
    font-weight: 800;
  }
  .step-label {
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.4px;
  }
  .result-box { margin-top: 12px; padding: 12px; border-radius: var(--rsm); }
  .result-box.pass { background: rgba(0, 230, 118, 0.05); }
  .result-box.fail { background: rgba(233, 69, 96, 0.05); }
  .check-row { display: flex; gap: 8px; font-size: 12px; padding-top: 8px; }
  .muted { color: var(--muted); }
  @media (max-width: 1024px) {
    .span-2 { grid-column: span 1; }
  }
</style>
