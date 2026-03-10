<script lang="ts">
  import { onMount } from 'svelte';
  import { getStatus, validateRtmpTarget, startStream, stopStream, emergencyStop, emergencyReset, getRuntimeTruth, getPipelineState, pipelineTransition } from '../../lib/api';
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

  const pipelineTargets = ['IDLE', 'WARMING', 'LIVE', 'COOLDOWN'];

  async function refresh() {
    loading = true;
    receipt = null;
    try {
      const [s, t, p] = await Promise.all([getStatus(), getRuntimeTruth(), getPipelineState()]);
      status = s;
      truth = t;
      pipeline = p;
      loadedAt = new Date().toISOString();
    } catch (e: any) {
      receipt = { action: 'stream.refresh', status: 'error', message: e.message, timestamp: Date.now() };
    }
    loading = false;
  }

  async function handleValidateRtmp() {
    receipt = null;
    try {
      rtmpResult = await validateRtmpTarget();
      receipt = { action: 'rtmp.validate', status: rtmpResult.status === 'pass' ? 'success' : 'error', message: `RTMP validation: ${rtmpResult.status}`, timestamp: Date.now() };
    } catch (e: any) {
      receipt = { action: 'rtmp.validate', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  async function handleStartStream() {
    receipt = null;
    try {
      await startStream();
      receipt = { action: 'stream.start', status: 'success', message: 'Stream started', timestamp: Date.now() };
      await refresh();
    } catch (e: any) {
      receipt = { action: 'stream.start', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  async function handleStopStream() {
    receipt = null;
    try {
      await stopStream();
      receipt = { action: 'stream.stop', status: 'success', message: 'Stream stopped', timestamp: Date.now() };
      await refresh();
    } catch (e: any) {
      receipt = { action: 'stream.stop', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  async function handleEmergencyStop() {
    if (confirm('Are you sure? This will halt ALL operations.')) {
      receipt = null;
      try {
        const result = await emergencyStop();
        receipt = { action: 'emergency.stop', status: 'success', message: result.message || 'Emergency stop activated', timestamp: Date.now() };
        await refresh();
      } catch (e: any) {
        receipt = { action: 'emergency.stop', status: 'error', message: e.message, timestamp: Date.now() };
      }
    }
  }

  async function handleEmergencyReset() {
    receipt = null;
    try {
      const result = await emergencyReset();
      receipt = { action: 'emergency.reset', status: 'success', message: result.message || 'System reset', timestamp: Date.now() };
      await refresh();
    } catch (e: any) {
      receipt = { action: 'emergency.reset', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  async function handlePipelineTransition(target: string) {
    receipt = null;
    try {
      const result = await pipelineTransition(target);
      pipeline = result;
      receipt = { action: 'pipeline.transition', status: 'success', message: `Pipeline → ${result.current_state || target}`, timestamp: Date.now() };
    } catch (e: any) {
      receipt = { action: 'pipeline.transition', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  onMount(refresh);
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Stream Control Center</h2>
      <p class="panel-subtitle">Run dry-runs, validate RTMP, move pipeline state, and control live output.</p>
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
      <section class="hero-card emergency" class:alert={status.emergency_stopped}>
        <div class="eyebrow">Emergency state</div>
        <div class="hero-value">{status.emergency_stopped ? 'LOCKED' : 'CLEAR'}</div>
        <div class="hero-copy">Use emergency stop only for hard recovery situations.</div>
      </section>
    </div>

    <div class="section-grid">
      <section class="card">
        <div class="section-title">Live controls</div>
        <div class="button-stack">
          <button class="btn btn-start" onclick={handleStartStream} disabled={status.stream_running || status.emergency_stopped}>Start Stream</button>
          <button class="btn btn-stop" onclick={handleStopStream} disabled={!status.stream_running}>Stop Stream</button>
          {#if status.emergency_stopped}
            <button class="btn btn-reset" onclick={handleEmergencyReset}>Reset Emergency</button>
          {:else}
            <button class="btn btn-emergency" onclick={handleEmergencyStop}>Emergency Stop</button>
          {/if}
        </div>
      </section>

      <section class="card">
        <div class="section-title">RTMP validation</div>
        <button class="btn btn-ghost" onclick={handleValidateRtmp}>Validate RTMP Target</button>
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

      <section class="card span-2">
        <div class="section-title">Pipeline state machine</div>
        <div class="pipeline-grid">
          {#each pipelineTargets as target}
            <button class="btn btn-ghost" class:active={pipeline?.current_state === target} disabled={pipeline?.current_state === target} onclick={() => handlePipelineTransition(target)}>{target}</button>
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
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; }
  .panel-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .hero-grid, .section-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }
  .hero-grid { margin-bottom: 14px; }
  .hero-card, .card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 18px; }
  .hero-card.emergency.alert { box-shadow: inset 0 0 0 1px rgba(233,69,96,.28); }
  .eyebrow, .section-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .hero-value { font-size: 32px; font-weight: 900; margin: 8px 0; }
  .hero-copy { color: var(--muted); font-size: 13px; }
  .button-stack, .pipeline-grid { display: grid; gap: 10px; margin-top: 12px; }
  .pipeline-grid { grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
  .span-2 { grid-column: span 2; }
  .btn { padding: 10px 14px; border-radius: var(--rsm); border: 1px solid var(--border); cursor: pointer; font-weight: 700; font-family: inherit; }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn-ghost { background: rgba(255,255,255,.05); color: var(--text); }
  .btn-ghost.active { border-color: var(--cyan); color: var(--cyan); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .btn-start { background: var(--green); color: #000; }
  .btn-stop { background: var(--yellow); color: #000; }
  .btn-emergency { background: var(--accent); color: #fff; }
  .btn-reset { background: var(--blue, #3b82f6); color: #fff; }
  .result-box { margin-top: 12px; padding: 12px; border-radius: var(--rsm); }
  .result-box.pass { background: rgba(0,230,118,.05); }
  .result-box.fail { background: rgba(233,69,96,.05); }
  .check-row { display: flex; gap: 8px; font-size: 12px; padding-top: 8px; }
  .muted { color: var(--muted); }
  @media (max-width: 1024px) { .span-2 { grid-column: span 1; } }
</style>
