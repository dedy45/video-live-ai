<script lang="ts">
  import { onMount } from 'svelte';
  import { getRuntimeTruth, voiceWarmup, voiceQueueClear, voiceRestart } from '../../lib/api';
  import type { RuntimeTruth } from '../../lib/types';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let truth = $state<RuntimeTruth | null>(null);
  let loading = $state(true);
  let error = $state('');
  let receipt = $state<ReceiptType | null>(null);

  async function loadTruth() {
    loading = true;
    try {
      truth = await getRuntimeTruth() as RuntimeTruth;
      error = '';
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function runAction(action: 'warmup' | 'clear' | 'restart') {
    try {
      const fn = action === 'warmup' ? voiceWarmup : action === 'clear' ? voiceQueueClear : voiceRestart;
      const result = await fn();
      receipt = {
        action: `voice.${action}`,
        status: result.status === 'error' ? 'error' : 'success',
        message: result.message,
        timestamp: Date.now(),
      };
      await loadTruth();
    } catch (e: any) {
      receipt = {
        action: `voice.${action}`,
        status: 'error',
        message: e.message,
        timestamp: Date.now(),
      };
    }
  }

  onMount(loadTruth);
</script>

<div class="panel" data-testid="voice-panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Voice Control Center</h2>
      <p class="panel-subtitle">Operator cockpit for Fish-Speech state, clone readiness, queue health, and recovery actions.</p>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading voice control center...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if !truth?.voice_engine}
    <p class="muted">No voice engine truth available.</p>
  {:else}
    <div class="hero-grid">
      <section class="hero-card">
        <div class="eyebrow">Voice runtime</div>
        <div class="hero-value">{truth.voice_runtime_mode}</div>
        <div class="hero-copy">Requested {truth.voice_engine.requested_engine} · Resolved {truth.voice_engine.resolved_engine}</div>
      </section>
      <section class="hero-card" class:warning={truth.voice_engine.fallback_active}>
        <div class="eyebrow">Fallback state</div>
        <div class="hero-value">{truth.voice_engine.fallback_active ? 'ACTIVE' : 'OFF'}</div>
        <div class="hero-copy">Reference ready {truth.voice_engine.reference_ready ? 'yes' : 'no'} · Sidecar {truth.voice_engine.server_reachable ? 'reachable' : 'down'}</div>
      </section>
    </div>

    <div class="section-grid">
      <section class="card span-2">
        <div class="section-title">Voice status</div>
        <div class="stats-grid">
          <div class="stat"><span class="label">Queue Depth</span><span class="value">{truth.voice_engine.queue_depth}</span></div>
          <div class="stat"><span class="label">Chunk Size</span><span class="value">{truth.voice_engine.chunk_chars ?? 'n/a'}</span></div>
          <div class="stat"><span class="label">Last Latency</span><span class="value">{truth.voice_engine.last_latency_ms ?? 'n/a'} ms</span></div>
          <div class="stat"><span class="label">P50 / P95</span><span class="value small">{truth.voice_engine.latency_p50_ms ?? 'n/a'} / {truth.voice_engine.latency_p95_ms ?? 'n/a'} ms</span></div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Operator controls</div>
        <div class="button-stack">
          <button class="btn btn-ghost" onclick={() => runAction('warmup')}>Warmup Voice</button>
          <button class="btn btn-ghost" onclick={() => runAction('clear')}>Clear Queue</button>
          <button class="btn btn-ghost" onclick={() => runAction('restart')}>Restart Voice</button>
          <button class="btn btn-ghost" onclick={loadTruth}>Refresh Truth</button>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Voice testing</div>
        <div class="stack-list">
          <div class="stack-row"><span>Load Reference</span><strong>{truth.voice_engine.reference_ready ? 'ready' : 'not ready'}</strong></div>
          <div class="stack-row"><span>Run Clone Smoke</span><strong>manual via Validation</strong></div>
          <div class="stack-row"><span>Chunking Check</span><strong>manual via Validation</strong></div>
        </div>
      </section>

      <section class="card span-2">
        <div class="section-title">Diagnostics</div>
        <div class="stats-grid">
          <div class="stat"><span class="label">Deployment</span><span class="value small">{truth.deployment_mode ?? 'unknown'}</span></div>
          <div class="stat"><span class="label">Time to First Audio</span><span class="value">{truth.voice_engine.time_to_first_audio_ms ?? 'n/a'} ms</span></div>
          <div class="stat"><span class="label">Last Error</span><span class="value small">{truth.voice_engine.last_error ?? 'none'}</span></div>
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
  .hero-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 14px; }
  .hero-card, .card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 18px; }
  .hero-card.warning { box-shadow: inset 0 0 0 1px rgba(255,214,0,.22); }
  .eyebrow, .section-title, .label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .hero-value { font-size: 32px; font-weight: 900; margin: 8px 0; }
  .hero-copy { color: var(--muted); font-size: 13px; }
  .section-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
  .span-2 { grid-column: span 2; }
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 12px; }
  .stat { padding: 12px; border-radius: var(--rsm); background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.04); }
  .value { display: block; margin-top: 6px; font-size: 22px; font-weight: 800; color: var(--text); }
  .value.small { font-size: 14px; font-weight: 700; line-height: 1.5; }
  .button-stack { display: grid; gap: 10px; margin-top: 12px; }
  .btn { padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--rsm); background: rgba(255,255,255,.05); color: var(--text); cursor: pointer; font-weight: 700; font-family: inherit; }
  .stack-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
  .stack-row { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
  @media (max-width: 1024px) { .section-grid { grid-template-columns: 1fr; } .span-2 { grid-column: span 1; } }
</style>
