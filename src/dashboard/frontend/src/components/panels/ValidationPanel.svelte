<script lang="ts">
  import { onMount } from 'svelte';
  import {
    validateMockStack,
    validateLiveTalkingEngine,
    validateRtmpTarget,
    validateRuntimeTruth,
    validateRealModeReadiness,
    getValidationHistory,
  } from '../../lib/api';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';

  let history = $state<any[]>([]);
  let loading = $state(false);
  let receipt = $state<ReceiptType | null>(null);
  let activeResult = $state<Record<string, any> | null>(null);
  let loadedAt = $state<string | null>(null);

  async function loadHistory() {
    try {
      const data = await getValidationHistory();
      history = data.slice(0, 20);
      loadedAt = new Date().toISOString();
    } catch {
      // history load failure is non-critical
    }
  }

  async function runCheck(name: string, checkFn: () => Promise<any>, actionKey: string) {
    receipt = null;
    loading = true;
    try {
      const result = await checkFn();
      activeResult = { ...result, name };
      receipt = {
        action: `validate.${actionKey}`,
        status: result.status === 'error' ? 'error' : 'success',
        message: `${name}: ${result.status.toUpperCase()}`,
        timestamp: Date.now(),
      };
      await loadHistory();
    } catch (e: any) {
      receipt = {
        action: `validate.${actionKey}`,
        status: 'error',
        message: e.message,
        timestamp: Date.now(),
      };
    } finally {
      loading = false;
    }
  }

  onMount(loadHistory);
</script>

<div class="panel" data-testid="validation-panel">
  <div class="panel-header">
    <h2 class="panel-title">Validation Console</h2>
    <div class="panel-meta">
      <FreshnessBadge timestamp={loadedAt} />
    </div>
  </div>

  <ActionReceipt {receipt} />

  <div class="grid">
    <div class="card">
      <div class="card-title">Mock Stack</div>
      <p class="desc">Check local mock services</p>
      <button class="btn btn-ghost btn-sm"
        data-testid="run-mock-stack"
        onclick={() => runCheck('Mock Stack', validateMockStack, 'mock-stack')}
        disabled={loading}>Run Check</button>
    </div>

    <div class="card">
      <div class="card-title">LiveTalking Engine</div>
      <p class="desc">Test local engine readiness</p>
      <button class="btn btn-ghost btn-sm"
        data-testid="run-live-talking"
        onclick={() => runCheck('LiveTalking Engine', validateLiveTalkingEngine, 'livetalking')}
        disabled={loading}>Run Check</button>
    </div>

    <div class="card">
      <div class="card-title">RTMP Target</div>
      <p class="desc">Verify stream destination</p>
      <button class="btn btn-ghost btn-sm"
        data-testid="run-rtmp-target"
        onclick={() => runCheck('RTMP Target', validateRtmpTarget, 'rtmp')}
        disabled={loading}>Run Check</button>
    </div>

    <div class="card">
      <div class="card-title">Runtime Truth</div>
      <p class="desc">Check env consistency</p>
      <button class="btn btn-ghost btn-sm"
        data-testid="run-runtime-truth"
        onclick={() => runCheck('Runtime Truth', validateRuntimeTruth, 'runtime-truth')}
        disabled={loading}>Run Check</button>
    </div>

    <div class="card">
      <div class="card-title">Real-Mode Readiness</div>
      <p class="desc">Final go/no-go checks</p>
      <button class="btn btn-ghost btn-sm"
        data-testid="run-real-mode"
        onclick={() => runCheck('Real-Mode Readiness', validateRealModeReadiness, 'real-mode')}
        disabled={loading}>Run Check</button>
    </div>
  </div>

  {#if activeResult}
    <div class="detail-card card" data-testid="validation-detail">
      <div class="detail-header">
        <div class="card-title">{activeResult.name} Result</div>
        <span class="status-badge" class:status-pass={activeResult.status === 'pass'}
          class:status-fail={activeResult.status === 'fail' || activeResult.status === 'error'}
          class:status-blocked={activeResult.status === 'blocked'}>{activeResult.status}</span>
      </div>

      {#if activeResult.evidence_id}
        <p class="evidence">Evidence ID: <code>{activeResult.evidence_id}</code></p>
      {/if}

      <div class="checks-list">
        {#each activeResult.checks || [] as check}
          <div class="check-item">
            <span class="indicator" class:passed={check.passed}>{check.passed ? '●' : '○'}</span>
            <span class="check-name">{check.check}</span>
            <span class="check-msg">{check.message}</span>
          </div>
        {/each}
      </div>

      {#if activeResult.blockers && activeResult.blockers.length > 0}
        <div class="blockers">
          <div class="blockers-title">Blockers</div>
          <ul>
            {#each activeResult.blockers as blocker}
              <li>{blocker}</li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>
  {/if}

  <section class="history-section" data-testid="validation-history">
    <div class="section-title">Recent Validation History</div>
    <div class="history-list">
      {#each history as entry}
        <div class="history-row">
          <span class="hist-name">{entry.check_name}</span>
          <span class="hist-status" class:status-pass={entry.status === 'pass'}
            class:status-fail={entry.status === 'fail' || entry.status === 'error'}
            class:status-blocked={entry.status === 'blocked'}>{entry.status}</span>
          <ProvenanceBadge provenance={entry.provenance} />
          <span class="hist-time">{new Date(entry.timestamp).toLocaleTimeString()}</span>
        </div>
      {:else}
        <p class="muted">No validation history found.</p>
      {/each}
    </div>
  </section>
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .panel-meta { display: flex; align-items: center; gap: 8px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 16px; border: 1px solid var(--border); }
  .card:hover { background: var(--card-hover); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px; font-weight: 700; }
  .desc { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  .btn { padding: 8px 16px; border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; transition: all .2s; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); width: 100%; }
  .btn-sm { padding: 6px 12px; font-size: 11px; }
  .detail-card { margin-bottom: 24px; border-left: 4px solid var(--border); }
  .detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .status-badge { text-transform: uppercase; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; }
  .status-pass { background: rgba(0,230,118,.15); color: var(--green); }
  .status-fail { background: rgba(233,69,96,.15); color: var(--accent); }
  .status-blocked { background: rgba(255,214,0,.15); color: var(--yellow); }
  .evidence { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  .evidence code { background: rgba(0,0,0,.2); padding: 2px 4px; border-radius: 2px; }
  .checks-list { display: flex; flex-direction: column; gap: 6px; }
  .check-item { display: flex; align-items: center; gap: 10px; font-size: 12px; padding: 3px 0; }
  .indicator { font-weight: 800; color: var(--accent); }
  .indicator.passed { color: var(--green); }
  .check-name { font-weight: 600; min-width: 140px; }
  .check-msg { color: var(--muted); flex: 1; }
  .blockers { margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--border); }
  .blockers-title { font-size: 12px; color: var(--accent); font-weight: 700; margin-bottom: 6px; }
  .blockers ul { margin: 0; padding-left: 18px; color: var(--accent); font-size: 11px; }
  .section-title { font-size: 14px; font-weight: 700; margin-bottom: 12px; }
  .history-list { display: flex; flex-direction: column; gap: 4px; }
  .history-row { display: flex; align-items: center; gap: 14px; padding: 10px 14px; background: var(--card); border-radius: var(--rsm); border: 1px solid var(--border); font-size: 12px; }
  .hist-name { font-weight: 600; flex: 1; }
  .hist-status { width: 60px; font-weight: 700; text-transform: uppercase; font-size: 10px; }
  .hist-time { font-family: monospace; color: var(--muted); font-size: 10px; }
  .muted { color: var(--muted); }
</style>
