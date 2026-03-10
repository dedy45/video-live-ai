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

<div class="panel" data-testid="overview-cockpit">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Operations Cockpit</h2>
      <p class="panel-subtitle">Global command view for state, pressure, live posture, and operator focus.</p>
    </div>
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
    <p class="muted">Loading operations cockpit...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="hero-grid">
      <section class="hero-card primary">
        <div class="eyebrow">System posture</div>
        <div class="hero-value">{status.state || 'UNKNOWN'}</div>
        <div class="hero-copy">Deployment {truth?.deployment_mode || 'unknown'} · Stream {status.stream_status || 'idle'} · Mock {status.mock_mode ? 'on' : 'off'}</div>
      </section>

      <section class="hero-card danger" class:danger-active={status.emergency_stopped}>
        <div class="eyebrow">Operator alert</div>
        <div class="hero-value">{status.emergency_stopped ? 'STOPPED' : 'NORMAL'}</div>
        <div class="hero-copy">Emergency latch {status.emergency_stopped ? 'active' : 'clear'} · Voice {truth?.voice_runtime_mode || 'unknown'} · Face {truth?.face_runtime_mode || 'unknown'}</div>
      </section>
    </div>

    <div class="section-grid">
      <section class="card span-2">
        <div class="section-title">Live snapshot</div>
        <div class="stats-grid">
          <div class="stat"><span class="label">Viewers</span><span class="value">{status.viewer_count ?? 0}</span></div>
          <div class="stat"><span class="label">Uptime</span><span class="value">{Math.floor((status.uptime_sec || 0) / 60)}m</span></div>
          <div class="stat"><span class="label">Budget</span><span class="value">${(status.llm_budget_remaining ?? 0).toFixed(2)}</span></div>
          <div class="stat"><span class="label">Current Product</span><span class="value small">{status.current_product?.name || 'none'}</span></div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Voice / Face / Stream</div>
        <div class="stack-list">
          <div class="stack-row"><span>Voice</span><strong>{truth?.voice_runtime_mode || 'unknown'}</strong></div>
          <div class="stack-row"><span>Face</span><strong>{truth?.face_runtime_mode || 'unknown'}</strong></div>
          <div class="stack-row"><span>Stream</span><strong>{truth?.stream_runtime_mode || 'unknown'}</strong></div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Resource pressure</div>
        <div class="stack-list">
          <div class="stack-row"><span>CPU</span><strong>{metrics.cpu_pct ?? 0}%</strong></div>
          <div class="stack-row"><span>RAM</span><strong>{metrics.memory_pct ?? metrics.ram_pct ?? 0}%</strong></div>
          <div class="stack-row"><span>Disk</span><strong>{metrics.disk_pct ?? 0}%</strong></div>
        </div>
      </section>

      <section class="card span-2">
        <div class="section-title">Operator focus</div>
        <div class="focus-grid">
          <div class="focus-item">
            <div class="focus-label">Next check</div>
            <div class="focus-value">Validation before live handoff</div>
          </div>
          <div class="focus-item">
            <div class="focus-label">Watch item</div>
            <div class="focus-value">Queue depth, fallback state, incidents</div>
          </div>
          <div class="focus-item">
            <div class="focus-label">Recommended path</div>
            <div class="focus-value">Overview → Voice → Face Engine → Stream → Validation</div>
          </div>
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
  .hero-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 14px; }
  .hero-card { border-radius: var(--radius); padding: 20px; border: 1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02)); }
  .hero-card.primary { box-shadow: inset 0 0 0 1px rgba(34,211,238,.12); }
  .hero-card.danger { box-shadow: inset 0 0 0 1px rgba(255,255,255,.04); }
  .hero-card.danger-active { box-shadow: inset 0 0 0 1px rgba(233,69,96,.28); }
  .eyebrow, .section-title, .label, .focus-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .hero-value { font-size: 34px; font-weight: 900; margin: 8px 0; color: var(--text); }
  .hero-copy { font-size: 13px; color: var(--muted); line-height: 1.5; }
  .section-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .span-2 { grid-column: span 2; }
  .stats-grid, .focus-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 12px; }
  .stat, .focus-item { padding: 12px; border-radius: var(--rsm); background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.04); }
  .value, .focus-value { display: block; margin-top: 6px; font-size: 22px; font-weight: 800; color: var(--text); }
  .value.small, .focus-value { font-size: 14px; font-weight: 700; line-height: 1.5; }
  .stack-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
  .stack-row { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
  .source-tag { font-size: 9px; padding: 1px 5px; border-radius: 3px; background: rgba(136,136,136,.15); color: var(--muted); text-transform: uppercase; font-weight: 600; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
  @media (max-width: 1024px) {
    .section-grid { grid-template-columns: 1fr; }
    .span-2 { grid-column: span 1; }
  }
</style>
