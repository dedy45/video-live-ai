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
    <h2 class="panel-title">Stream Control</h2>
    <div class="panel-meta">
      <ProvenanceBadge provenance={truth?.provenance?.stream_status || 'unknown'} />
      <FreshnessBadge timestamp={loadedAt} />
      <button class="btn btn-ghost btn-sm" onclick={refresh}>Refresh</button>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading...</p>
  {:else}
    <div class="grid">
      <div class="card">
        <div class="card-title">Stream Status</div>
        <div class="metric-value">{status.stream_status || 'idle'}</div>
        {#if truth}
          <div class="runtime-mode">Runtime: <span class="mode-value">{truth.stream_runtime_mode}</span></div>
        {/if}
        <div class="btn-row">
          <button class="btn btn-start btn-sm" onclick={handleStartStream}
            disabled={status.stream_running || status.emergency_stopped}>Start Stream</button>
          <button class="btn btn-stop btn-sm" onclick={handleStopStream}
            disabled={!status.stream_running}>Stop Stream</button>
        </div>
        <div class="btn-row" style="margin-top: 8px;">
          {#if status.emergency_stopped}
            <button class="btn btn-reset btn-sm" onclick={handleEmergencyReset}>Reset Emergency</button>
          {:else}
            <button class="btn btn-emergency btn-sm" onclick={handleEmergencyStop}>Emergency Stop</button>
          {/if}
        </div>
      </div>

      <div class="card">
        <div class="card-title">RTMP Validation</div>
        <button class="btn btn-ghost btn-sm" onclick={handleValidateRtmp}>Validate RTMP Target</button>
        {#if rtmpResult}
          <div class="validation-result" class:pass={rtmpResult.status === 'pass'} class:fail={rtmpResult.status !== 'pass'}>
            <p><strong>{rtmpResult.status?.toUpperCase()}</strong></p>
            {#each rtmpResult.checks || [] as check}
              <div class="check-row">
                <span class:green={check.passed} class:red={!check.passed}>{check.passed ? '●' : '○'}</span>
                <span>{check.check}</span>
                <span class="muted">{check.message}</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="card">
        <div class="card-title">Pipeline State</div>
        <div class="metric-value">{pipeline?.current_state || 'UNKNOWN'}</div>
        <div class="btn-row">
          {#each pipelineTargets as target}
            <button class="btn btn-ghost btn-sm"
              class:btn-active={pipeline?.current_state === target}
              disabled={pipeline?.current_state === target}
              onclick={() => handlePipelineTransition(target)}>{target}</button>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .panel-meta { display: flex; align-items: center; gap: 8px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px; }
  .metric-value { font-size: 22px; font-weight: 800; margin-bottom: 10px; }
  .runtime-mode { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
  .mode-value { font-weight: 700; color: var(--text); }
  .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
  .btn { padding: 8px 16px; border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; transition: all .2s; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); }
  .btn-active { background: rgba(255,255,255,.15); border-color: var(--cyan, #22d3ee); color: var(--cyan, #22d3ee); }
  .btn-sm { padding: 5px 10px; font-size: 11px; }
  .btn-start { background: var(--green); color: #000; }
  .btn-stop { background: var(--yellow); color: #000; }
  .btn-emergency { background: var(--accent); color: #fff; }
  .btn-reset { background: var(--blue, #3b82f6); color: #fff; }
  .validation-result { margin-top: 10px; padding: 10px; border-radius: var(--rsm); }
  .validation-result.pass { background: rgba(0,230,118,.05); }
  .validation-result.fail { background: rgba(233,69,96,.05); }
  .check-row { display: flex; gap: 8px; font-size: 12px; padding: 3px 0; }
  .green { color: var(--green); }
  .red { color: var(--accent); }
  .muted { color: var(--muted); }
</style>
