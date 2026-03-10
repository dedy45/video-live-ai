<script lang="ts">
  import { onMount } from 'svelte';
  import { getRuntimeTruth } from '../../lib/api';
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

  onMount(loadTruth);

  const voiceReady = $derived(truth?.voice_engine?.server_reachable && truth?.voice_engine?.reference_ready);
  const faceReady = $derived(truth?.face_engine?.model_ready && truth?.face_engine?.gpu_loaded);
</script>

<div class="panel" data-testid="performer-panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Voice & Face</h2>
      <p class="panel-subtitle">Unified performer control for voice synthesis and face animation.</p>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading performer panel...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if !truth}
    <p class="muted">No performer truth available.</p>
  {:else}
    <div class="performer-grid">
      <!-- Voice Section -->
      <section class="performer-card voice">
        <div class="card-header">
          <h3 class="card-title">Voice Runtime</h3>
          <span class="status-badge status-{voiceReady ? 'ready' : 'not-ready'}">
            {voiceReady ? 'READY' : 'NOT READY'}
          </span>
        </div>
        <div class="stats-list">
          <div class="stat-row">
            <span class="label">Engine</span>
            <span class="value">{truth.voice_engine?.resolved_engine || 'unknown'}</span>
          </div>
          <div class="stat-row">
            <span class="label">Sidecar</span>
            <span class="value">{truth.voice_engine?.server_reachable ? 'reachable' : 'down'}</span>
          </div>
          <div class="stat-row">
            <span class="label">Reference</span>
            <span class="value">{truth.voice_engine?.reference_ready ? 'loaded' : 'missing'}</span>
          </div>
          <div class="stat-row">
            <span class="label">Queue</span>
            <span class="value">{truth.voice_engine?.queue_depth || 0}</span>
          </div>
        </div>
      </section>

      <!-- Face Section -->
      <section class="performer-card face">
        <div class="card-header">
          <h3 class="card-title">Face Engine</h3>
          <span class="status-badge status-{faceReady ? 'ready' : 'not-ready'}">
            {faceReady ? 'READY' : 'NOT READY'}
          </span>
        </div>
        <div class="stats-list">
          <div class="stat-row">
            <span class="label">Model</span>
            <span class="value">{truth.face_engine?.engine_type || 'unknown'}</span>
          </div>
          <div class="stat-row">
            <span class="label">GPU</span>
            <span class="value">{truth.face_engine?.gpu_loaded ? 'loaded' : 'unloaded'}</span>
          </div>
          <div class="stat-row">
            <span class="label">FPS Target</span>
            <span class="value">{truth.face_engine?.fps_target || 25}</span>
          </div>
          <div class="stat-row">
            <span class="label">Latency</span>
            <span class="value">{truth.face_engine?.latency_ms || 'n/a'} ms</span>
          </div>
        </div>
      </section>

      <!-- Preview Section -->
      <section class="performer-card preview span-full">
        <div class="card-header">
          <h3 class="card-title">Preview</h3>
          <span class="status-badge status-unknown">COMING SOON</span>
        </div>
        <div class="preview-placeholder">
          <p>Preview panel for performer output</p>
          <p class="note">Video preview and playback controls coming in next phase</p>
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
  .performer-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
  .performer-card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 18px; }
  .performer-card.voice { border-left: 3px solid var(--accent); }
  .performer-card.face { border-left: 3px solid var(--secondary); }
  .span-full { grid-column: span 2; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
  .card-title { font-size: 16px; font-weight: 700; margin: 0; color: var(--text); }
  .status-badge { padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
  .status-badge.status-ready { background: var(--success-bg); color: var(--success-color); }
  .status-badge.status-not-ready { background: var(--error-bg); color: var(--error-color); }
  .status-badge.status-unknown { background: var(--neutral-bg); color: var(--text-secondary); }
  .stats-list { display: flex; flex-direction: column; gap: 8px; }
  .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
  .stat-row:last-child { border-bottom: none; }
  .label { font-size: 12px; color: var(--muted); }
  .value { font-size: 14px; font-weight: 600; color: var(--text); }
  .preview-placeholder { padding: 40px 20px; text-align: center; background: rgba(255,255,255,.02); border-radius: 8px; }
  .preview-placeholder p { margin: 8px 0; color: var(--text-secondary); }
  .note { font-size: 12px; color: var(--muted); font-style: italic; }
  @media (max-width: 768px) { .performer-grid { grid-template-columns: 1fr; } .span-full { grid-column: span 1; } }
</style>
