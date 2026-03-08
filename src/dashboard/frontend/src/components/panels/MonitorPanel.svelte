<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { getRecentChats, getHealthSummary } from '../../lib/api';
  import { useDashboardRealtime } from '../../lib/stores/dashboard.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';

  const rt = useDashboardRealtime();

  let chats = $state<any[]>([]);
  let health = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');

  $effect(() => {
    if (rt.snapshot) {
      // Update health from snapshot if available
      if (rt.snapshot.components) {
        const previous = untrack(() => health);
        health = {
          ...previous,
          components: rt.snapshot.components
        };
      }
    }
  });

  onMount(async () => {
    try {
      const [c, h] = await Promise.all([getRecentChats(), getHealthSummary()]);
      chats = c;
      health = h;
    } catch (e: any) {
      error = e.message;
    }
    loading = false;
    rt.start();
  });

  onDestroy(() => {
    rt.stop();
  });
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">Monitor</h2>
    <div class="panel-meta">
      <ProvenanceBadge provenance={rt.snapshot?.truth?.provenance?.system_status || 'unknown'} />
      <FreshnessBadge timestamp={rt.snapshot?.received_at} />
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
        <div class="card-title">Component Health</div>
        <div class="health-grid">
          {#each Object.entries(health.components || {}) as [name, status]}
            <div class="health-item">
              <span class="health-dot" class:dot-green={status === 'healthy' || status === 'mock'}
                    class:dot-red={status === 'failed'} class:dot-yellow={status === 'degraded' || status === 'idle'}></span>
              <span class="health-name">{name}</span>
              <span class="health-status">{status}</span>
            </div>
          {/each}
        </div>
      </div>
      <div class="card">
        <div class="card-title">Recent Chat ({chats.length})</div>
        <div class="chat-list">
          {#each chats as chat}
            <div class="chat-item">
              <span class="chat-username">{chat.username}</span>
              <span class="chat-platform">[{chat.platform}]</span>
              <span>{chat.message}</span>
            </div>
          {/each}
          {#if chats.length === 0}
            <p class="muted">No recent chat activity</p>
          {/if}
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
  .health-grid { display: flex; flex-direction: column; gap: 6px; }
  .health-item { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 4px 0; }
  .health-dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot-green { background: var(--green); }
  .dot-red { background: var(--accent); }
  .dot-yellow { background: var(--yellow); }
  .health-name { font-weight: 600; min-width: 120px; }
  .health-status { color: var(--muted); font-size: 11px; }
  .chat-list { max-height: 350px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
  .chat-item { padding: 6px 10px; font-size: 12px; background: rgba(255,255,255,.02); border-radius: var(--rsm); }
  .chat-username { color: var(--accent); font-weight: 600; }
  .chat-platform { font-size: 10px; color: var(--muted); margin: 0 4px; }
  .source-tag { font-size: 9px; padding: 1px 5px; border-radius: 3px; background: rgba(136,136,136,.15); color: var(--muted); text-transform: uppercase; font-weight: 600; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
