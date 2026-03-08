<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { getStatus, getMetrics, getRuntimeTruth } from '../../lib/api';
  import { useDashboardRealtime } from '../../lib/stores/dashboard.svelte';
  import type { RealtimeSnapshot } from '../../lib/realtime';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';

  const rt = useDashboardRealtime();

  let status = $state<Record<string, any>>({});
  let metrics = $state<Record<string, any>>({});
  let truth = $state<Record<string, any> | null>(null);
  let loading = $state(true);
  let error = $state('');
  let loadedAt = $state<string | null>(null);

  function handleSnapshot(snapshot: RealtimeSnapshot) {
    const previous = untrack(() => status);
    status = {
      ...previous,
      state: snapshot.pipeline_state || previous.state,
      stream_running: snapshot.stream_running,
      emergency_stopped: snapshot.emergency_stopped,
      mock_mode: snapshot.mock_mode,
      stream_status: snapshot.emergency_stopped ? 'stopped' : (snapshot.stream_running ? 'live' : 'idle'),
      viewer_count: snapshot.gauges?.viewers ?? previous.viewer_count ?? 0,
      current_product: snapshot.current_product,
    };
    if (snapshot.truth) {
      truth = snapshot.truth;
    }
    loadedAt = snapshot.received_at;
  }

  $effect(() => {
    if (rt.snapshot) {
      handleSnapshot(rt.snapshot);
    }
  });

  onMount(async () => {
    try {
      const [s, m, t] = await Promise.all([getStatus(), getMetrics(), getRuntimeTruth()]);
      status = s;
      metrics = m;
      truth = t;
      loadedAt = new Date().toISOString();
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }

    rt.start();
  });

  onDestroy(() => {
    rt.stop();
  });
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">Overview</h2>
    <div class="panel-meta">
      {#if truth}
        <ProvenanceBadge provenance={truth.provenance?.system_status || 'unknown'} />
      {/if}
      <FreshnessBadge timestamp={loadedAt} />
      {#if rt.source}
        <span class="source-tag" data-testid="realtime-source">{rt.source}</span>
      {/if}
    </div>
  </div>
  {#if loading}
    <p class="muted">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="grid">
      <div class="card">
        <div class="card-title">System State</div>
        <div class="metric-value">{status.state || 'UNKNOWN'}</div>
      </div>
      <div class="card">
        <div class="card-title">Uptime</div>
        <div class="metric-value">{Math.floor((status.uptime_sec || 0) / 60)}m</div>
      </div>
      <div class="card">
        <div class="card-title">Viewers</div>
        <div class="metric-value">{status.viewer_count ?? 0}</div>
      </div>
      <div class="card">
        <div class="card-title">Stream</div>
        <div class="metric-value">{status.stream_status || 'idle'}</div>
      </div>
      <div class="card">
        <div class="card-title">Mock Mode</div>
        <div class="metric-value">{status.mock_mode ? 'ON' : 'OFF'}</div>
      </div>
      <div class="card">
        <div class="card-title">Budget Remaining</div>
        <div class="metric-value">${(status.llm_budget_remaining ?? 0).toFixed(2)}</div>
      </div>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .panel-meta { display: flex; align-items: center; gap: 8px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .card:hover { background: var(--card-hover); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 8px; }
  .metric-value { font-size: 26px; font-weight: 800; }
  .source-tag { font-size: 9px; padding: 1px 5px; border-radius: 3px; background: rgba(136,136,136,.15); color: var(--muted); text-transform: uppercase; font-weight: 600; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
