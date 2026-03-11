<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { ackIncident, brainTest, getBrainHealth, getBrainStats, getHealthSummary, getIncidents, getRecentChats, getResources } from '../../lib/api';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  const source = 'polling';
  const alertThresholds = {
    cpu: 85,
    ram: 85,
    disk: 80,
    vram: 70,
  };

  let chats = $state<any[]>([]);
  let health = $state<Record<string, any>>({});
  let resources = $state<Record<string, any> | null>(null);
  let incidents = $state<any[]>([]);
  let brainHealth = $state<Record<string, any>>({});
  let brainStats = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');
  let loadedAt = $state<string | null>(null);
  let receipt = $state<ReceiptType | null>(null);
  let pollHandle: number | null = null;

  async function refresh() {
    try {
      const [nextChats, nextHealth, nextResources, nextIncidents, nextBrainHealth, nextBrainStats] = await Promise.all([
        getRecentChats(),
        getHealthSummary(),
        getResources(),
        getIncidents(),
        getBrainHealth(),
        getBrainStats(),
      ]);
      chats = nextChats.slice(0, 5);
      health = nextHealth;
      resources = nextResources;
      incidents = nextIncidents.slice(0, 6);
      brainHealth = nextBrainHealth;
      brainStats = nextBrainStats;
      loadedAt = new Date().toISOString();
      error = '';
    } catch (nextError: any) {
      error = nextError.message || 'Failed to load monitor';
    } finally {
      loading = false;
    }
  }

  async function handleAcknowledge(id: string) {
    receipt = null;
    try {
      const result = await ackIncident(id);
      receipt = { action: 'incident.ack', status: result.status === 'error' ? 'error' : 'success', message: result.message, timestamp: Date.now() };
      await refresh();
    } catch (nextError: any) {
      receipt = { action: 'incident.ack', status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  async function handleBrainTest() {
    receipt = null;
    try {
      const result = await brainTest({ user_prompt: 'Ringkas produk aktif untuk host live.' });
      receipt = {
        action: 'brain.test',
        status: result.success ? 'success' : 'error',
        message: result.success ? `${result.provider}/${result.model} — ${result.latency_ms}ms` : result.error || 'Brain test failed',
        timestamp: Date.now(),
      };
    } catch (nextError: any) {
      receipt = { action: 'brain.test', status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  function pressureTone(value: number | null | undefined, threshold: number): 'ready' | 'warning' {
    if (value == null) return 'ready';
    return value >= threshold ? 'warning' : 'ready';
  }

  onMount(async () => {
    await refresh();
    pollHandle = window.setInterval(() => {
      void refresh();
    }, 10000);
  });

  onDestroy(() => {
    if (pollHandle !== null) {
      window.clearInterval(pollHandle);
    }
  });
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Operations Monitor</h2>
      <p class="panel-subtitle">Pantau resource pressure, health komponen, LLM brain, dan insiden operator dalam satu permukaan realtime.</p>
    </div>
    <div class="panel-meta">
      <ProvenanceBadge provenance="derived" />
      <FreshnessBadge timestamp={loadedAt} />
      <span class="source-tag" data-testid="realtime-source">{source}</span>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading operations monitor...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="grid">
      <section class="card">
        <div class="section-title">Resource pressure</div>
        <div class="meter-list">
          <div class="meter-row">
            <div class="meter-top"><span>CPU</span><strong>{resources?.cpu_pct ?? 0}%</strong></div>
            <div class="meter-bar"><div class="meter-fill" style={`width:${resources?.cpu_pct ?? 0}%`}></div></div>
          </div>
          <div class="meter-row">
            <div class="meter-top"><span>RAM</span><strong>{resources?.ram_pct ?? 0}%</strong></div>
            <div class="meter-bar"><div class="meter-fill" style={`width:${resources?.ram_pct ?? 0}%`}></div></div>
          </div>
          <div class="meter-row">
            <div class="meter-top"><span>Disk</span><strong>{resources?.disk_pct ?? 0}%</strong></div>
            <div class="meter-bar"><div class="meter-fill" style={`width:${resources?.disk_pct ?? 0}%`}></div></div>
          </div>
          <div class="meter-row">
            <div class="meter-top"><span>VRAM</span><strong>{resources?.vram_pct ?? 'n/a'}%</strong></div>
            <div class="meter-bar"><div class="meter-fill" style={`width:${resources?.vram_pct ?? 0}%`}></div></div>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Component health</div>
        <div class="chip-list">
          {#each Object.entries(health.components || {}) as [name, status]}
            <div class="chip">
              <span class="dot" class:green={status === 'healthy' || status === 'mock'} class:yellow={status === 'degraded' || status === 'idle'} class:red={status === 'failed'}></span>
              <span class="name">{name}</span>
              <span class="status">{String(status)}</span>
            </div>
          {:else}
            <p class="muted">No component health data</p>
          {/each}
        </div>
      </section>

      <section class="card">
        <div class="section-title">LLM Brain</div>
        <div class="brain-summary">
          <div class="brain-row"><span>Active</span><strong>{brainStats.active_provider || 'unknown'} {brainStats.active_model ? `(${brainStats.active_model})` : ''}</strong></div>
          <div class="brain-row"><span>Healthy</span><strong>{brainHealth.healthy_count || 0}/{brainHealth.total_count || 0}</strong></div>
        </div>
        <div class="chip-list compact">
          {#each Object.entries(brainStats.adapters || {}) as [name, info]}
            <div class="chip">
              <span class="dot" class:green={Boolean((info as any).available)} class:red={!Boolean((info as any).available)}></span>
              <span class="name">{name}</span>
              <span class="status">{(info as any).model || 'unknown'}</span>
            </div>
          {/each}
        </div>
        <button class="btn btn-ghost" onclick={handleBrainTest}>Test Brain</button>
      </section>

      <section class="card">
        <div class="section-title">Incidents</div>
        <div class="feed">
          {#each incidents as incident}
            <div class="feed-item">
              <div class="feed-copy">
                <strong>{incident.code}</strong>
                <span>[{incident.subsystem}] {incident.severity}</span>
              </div>
              {#if incident.id}
                <button class="btn btn-ghost btn-sm" onclick={() => handleAcknowledge(incident.id)}>Ack</button>
              {/if}
            </div>
          {:else}
            <p class="muted">No recent incidents</p>
          {/each}
        </div>
      </section>

      <section class="card">
        <div class="section-title">Alert posture</div>
        <div class="alert-list">
          <div class="alert-row">
            <span>CPU threshold</span>
            <strong>{alertThresholds.cpu}% · {pressureTone(resources?.cpu_pct, alertThresholds.cpu) === 'warning' ? 'warning' : 'clear'}</strong>
          </div>
          <div class="alert-row">
            <span>RAM threshold</span>
            <strong>{alertThresholds.ram}% · {pressureTone(resources?.ram_pct, alertThresholds.ram) === 'warning' ? 'warning' : 'clear'}</strong>
          </div>
          <div class="alert-row">
            <span>Disk threshold</span>
            <strong>{alertThresholds.disk}% · {pressureTone(resources?.disk_pct, alertThresholds.disk) === 'warning' ? 'warning' : 'clear'}</strong>
          </div>
          <div class="alert-row">
            <span>VRAM threshold</span>
            <strong>{alertThresholds.vram}% · {pressureTone(resources?.vram_pct, alertThresholds.vram) === 'warning' ? 'warning' : 'clear'}</strong>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Recent chat</div>
        <div class="feed">
          {#each chats as chat}
            <div class="feed-item">
              <div class="feed-copy">
                <strong>{chat.username}</strong>
                <span>[{chat.platform}] {chat.message}</span>
              </div>
            </div>
          {:else}
            <p class="muted">No recent chat activity</p>
          {/each}
        </div>
      </section>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  .panel-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
  .panel-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .source-tag { font-size: 9px; padding: 1px 5px; border-radius: 3px; background: rgba(136, 136, 136, 0.15); color: var(--muted); text-transform: uppercase; font-weight: 600; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .section-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; margin-bottom: 12px; }
  .meter-list, .chip-list, .feed, .alert-list { display: flex; flex-direction: column; gap: 10px; }
  .meter-row, .chip, .feed-item, .alert-row, .brain-row { display: flex; gap: 8px; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: var(--rsm); background: rgba(255, 255, 255, 0.03); }
  .meter-top, .feed-copy { display: flex; justify-content: space-between; gap: 10px; width: 100%; align-items: center; }
  .meter-bar { width: 100%; height: 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.06); overflow: hidden; }
  .meter-fill { height: 100%; background: linear-gradient(90deg, rgba(34, 211, 238, 0.85), rgba(59, 130, 246, 0.85)); border-radius: 999px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .dot.green { background: var(--green); }
  .dot.yellow { background: var(--yellow); }
  .dot.red { background: var(--accent); }
  .name { min-width: 80px; font-weight: 700; text-transform: lowercase; }
  .status { color: var(--muted); font-size: 12px; text-align: right; }
  .brain-summary { display: grid; gap: 8px; margin-bottom: 12px; }
  .btn { padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--rsm); cursor: pointer; font-weight: 700; font-family: inherit; }
  .btn-ghost { background: rgba(255, 255, 255, 0.05); color: var(--text); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .compact .chip { padding: 8px 10px; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
