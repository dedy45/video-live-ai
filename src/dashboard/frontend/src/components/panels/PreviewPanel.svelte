<script lang="ts">
  import { onMount } from 'svelte';
  import { getLiveTalkingConfig } from '../../lib/api';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';

  let config = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    try {
      config = await getLiveTalkingConfig();
    } catch (e: any) {
      error = e.message;
    }
    loading = false;
  });
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">Preview & Debug</h2>
    <ProvenanceBadge provenance="real_local" />
  </div>

  {#if loading}
    <p class="muted">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <p class="desc">These links open the vendor LiveTalking UI pages running on port {config.port || 8010}. Use them for direct debugging and preview.</p>

    <div class="links-grid">
      {#if config.debug_urls}
        <a href={config.debug_urls.dashboard_vendor} target="_blank" rel="noopener" class="link-card">
          <div class="link-title">Vendor Dashboard</div>
          <div class="link-url">{config.debug_urls.dashboard_vendor}</div>
        </a>
        <a href={config.debug_urls.webrtcapi} target="_blank" rel="noopener" class="link-card">
          <div class="link-title">WebRTC Preview</div>
          <div class="link-url">{config.debug_urls.webrtcapi}</div>
        </a>
        <a href={config.debug_urls.rtcpushapi} target="_blank" rel="noopener" class="link-card">
          <div class="link-title">RTC Push API</div>
          <div class="link-url">{config.debug_urls.rtcpushapi}</div>
        </a>
        <a href={config.debug_urls.echoapi} target="_blank" rel="noopener" class="link-card">
          <div class="link-title">Echo API</div>
          <div class="link-url">{config.debug_urls.echoapi}</div>
        </a>
      {:else}
        <p class="muted">No debug URLs available. Start the engine first.</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .desc { font-size: 13px; color: var(--muted); margin-bottom: 16px; }
  .links-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
  .link-card { display: block; padding: 16px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); text-decoration: none; transition: all .2s; }
  .link-card:hover { background: var(--card-hover); border-color: var(--cyan); }
  .link-title { font-size: 14px; font-weight: 700; color: var(--cyan); margin-bottom: 4px; }
  .link-url { font-size: 11px; color: var(--muted); word-break: break-all; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
