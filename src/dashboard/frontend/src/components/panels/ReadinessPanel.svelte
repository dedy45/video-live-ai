<script lang="ts">
  import { onMount } from 'svelte';
  import { getReadiness } from '../../lib/api';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let result = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');
  let lastRefreshedAt = $state<string | null>(null);
  let receipt = $state<ReceiptType | null>(null);

  async function refresh() {
    loading = true;
    error = '';
    receipt = null;
    try {
      result = await getReadiness();
      lastRefreshedAt = new Date().toISOString();
      receipt = { action: 'readiness.refresh', status: 'success', message: `${result.overall_status} — ${(result.checks || []).length} checks`, timestamp: Date.now() };
    } catch (e: any) {
      error = e.message;
      receipt = { action: 'readiness.refresh', status: 'error', message: e.message, timestamp: Date.now() };
    } finally {
      loading = false;
    }
  }

  onMount(refresh);
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">Readiness</h2>
    <div class="panel-meta">
      <ProvenanceBadge provenance="derived" />
      <FreshnessBadge timestamp={lastRefreshedAt} />
      <button class="btn btn-ghost btn-sm" onclick={refresh} disabled={loading}>Refresh</button>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Checking readiness...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="overall-status" class:ready={result.overall_status === 'ready'}
         class:degraded={result.overall_status === 'degraded'}
         class:not-ready={result.overall_status === 'not_ready'}>
      {result.overall_status?.toUpperCase() || 'UNKNOWN'}
    </div>

    {#if result.recommended_next_action}
      <p class="next-action">{result.recommended_next_action}</p>
    {/if}

    {#if result.blocking_issues?.length > 0}
      <div class="blocking">
        <h3>Blocking Issues</h3>
        {#each result.blocking_issues as issue}
          <p class="blocking-item">{issue}</p>
        {/each}
      </div>
    {/if}

    <div class="checks-list">
      {#each result.checks || [] as check}
        <div class="check-row" class:passed={check.passed} class:failed={!check.passed}>
          <span class="check-indicator">{check.passed ? '●' : '○'}</span>
          <span class="check-name">{check.name}</span>
          <span class="check-status badge-{check.status}">{check.status}</span>
          <span class="check-msg">{check.message}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .panel-meta { display: flex; align-items: center; gap: 8px; }
  .overall-status { font-size: 22px; font-weight: 800; padding: 12px 20px; border-radius: var(--rsm); margin-bottom: 12px; text-align: center; }
  .overall-status.ready { background: rgba(0,230,118,.1); color: var(--green); }
  .overall-status.degraded { background: rgba(255,214,0,.1); color: var(--yellow); }
  .overall-status.not-ready { background: rgba(233,69,96,.1); color: var(--accent); }
  .next-action { font-size: 13px; color: var(--muted); margin-bottom: 16px; padding: 8px 12px; background: rgba(255,255,255,.03); border-radius: var(--rsm); }
  .blocking { margin-bottom: 16px; }
  .blocking h3 { font-size: 13px; color: var(--accent); margin-bottom: 6px; }
  .blocking-item { font-size: 12px; color: var(--accent); padding: 4px 0; }
  .checks-list { display: flex; flex-direction: column; gap: 6px; }
  .check-row { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: var(--card); border-radius: var(--rsm); border: 1px solid var(--border); font-size: 13px; }
  .check-indicator { font-size: 10px; }
  .check-row.passed .check-indicator { color: var(--green); }
  .check-row.failed .check-indicator { color: var(--accent); }
  .check-name { font-weight: 600; min-width: 180px; }
  .check-status { font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; }
  .badge-ok { background: rgba(0,230,118,.15); color: var(--green); }
  .badge-warning { background: rgba(255,214,0,.15); color: var(--yellow); }
  .badge-fail { background: rgba(233,69,96,.15); color: var(--accent); }
  .check-msg { color: var(--muted); font-size: 11px; flex: 1; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .btn { padding: 8px 16px; border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; transition: all .2s; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); }
  .btn-ghost:hover { background: rgba(255,255,255,.1); }
  .btn-sm { padding: 5px 10px; font-size: 11px; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
