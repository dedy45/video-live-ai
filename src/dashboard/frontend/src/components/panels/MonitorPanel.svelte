<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { getRecentChats, getHealthSummary, getResources, getIncidents } from '../../lib/api';
  import { useDashboardRealtime } from '../../lib/stores/dashboard.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';

  const rt = useDashboardRealtime();

  let chats = $state<any[]>([]);
  let health = $state<Record<string, any>>({});
  let resources = $state<Record<string, any> | null>(null);
  let incidents = $state<any[]>([]);
  let loading = $state(true);
  let error = $state('');

  $effect(() => {
    if (rt.snapshot?.components) {
      const previous = untrack(() => health);
      health = { ...previous, components: rt.snapshot.components };
    }
  });

  onMount(async () => {
    try {
      const [c, h, r, i] = await Promise.all([getRecentChats(), getHealthSummary(), getResources(), getIncidents()]);
      chats = c;
      health = h;
      resources = r;
      incidents = i.slice(0, 5);
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
    <div>
      <h2 class="panel-title">Operations Monitor</h2>
      <p class="panel-subtitle">Track health, pressure, incidents, and recent operator-visible activity.</p>
    </div>
    <div class="panel-meta">
      <ProvenanceBadge provenance={rt.snapshot?.truth?.provenance?.system_status || 'unknown'} />
      <FreshnessBadge timestamp={rt.snapshot?.received_at} />
      {#if rt.source}
        <span class="source-tag" data-testid="realtime-source">{rt.source}</span>
      {/if}
    </div>
  </div>

  {#if loading}
    <p class="muted">Loading operations monitor...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="grid">
      <section class="card">
        <div class="section-title">Component health</div>
        <div class="list">
          {#each Object.entries(health.components || {}) as [name, status]}
            <div class="row">
              <span class="dot" class:green={status === 'healthy' || status === 'mock'} class:red={status === 'failed'} class:yellow={status === 'degraded' || status === 'idle'}></span>
              <span class="name">{name}</span>
              <span class="status">{status}</span>
            </div>
          {/each}
          {#if Object.keys(health.components || {}).length === 0}
            <p class="muted">No component health data</p>
          {/if}
        </div>
      </section>

      <section class="card">
        <div class="section-title">Resource pressure</div>
        {#if resources}
          <div class="list">
            <div class="row"><span class="name">CPU</span><span class="status">{resources.cpu_pct}%</span></div>
            <div class="row"><span class="name">RAM</span><span class="status">{resources.ram_pct}%</span></div>
            <div class="row"><span class="name">Disk</span><span class="status">{resources.disk_pct}%</span></div>
            <div class="row"><span class="name">VRAM</span><span class="status">{resources.vram_pct ?? 'n/a'}</span></div>
          </div>
        {:else}
          <p class="muted">No resource data</p>
        {/if}
      </section>

      <section class="card">
        <div class="section-title">Recent incidents</div>
        <div class="feed">
          {#each incidents as incident}
            <div class="feed-item">
              <strong>{incident.severity}</strong>
              <span>[{incident.subsystem}]</span>
              <span>{incident.code}</span>
            </div>
          {/each}
          {#if incidents.length === 0}
            <p class="muted">No recent incidents</p>
          {/if}
        </div>
      </section>

      <section class="card">
        <div class="section-title">Recent chat</div>
        <div class="feed">
          {#each chats as chat}
            <div class="feed-item">
              <strong>{chat.username}</strong>
              <span>[{chat.platform}]</span>
              <span>{chat.message}</span>
            </div>
          {/each}
          {#if chats.length === 0}
            <p class="muted">No recent chat activity</p>
          {/if}
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
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .section-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; margin-bottom: 12px; }
  .list, .feed { display: flex; flex-direction: column; gap: 8px; }
  .row, .feed-item { display: flex; gap: 8px; align-items: center; padding: 10px 12px; border-radius: var(--rsm); background: rgba(255,255,255,.03); }
  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot.green { background: var(--green); }
  .dot.red { background: var(--accent); }
  .dot.yellow { background: var(--yellow); }
  .name { min-width: 110px; font-weight: 700; }
  .status { color: var(--muted); }
  .source-tag { font-size: 9px; padding: 1px 5px; border-radius: 3px; background: rgba(136,136,136,.15); color: var(--muted); text-transform: uppercase; font-weight: 600; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
