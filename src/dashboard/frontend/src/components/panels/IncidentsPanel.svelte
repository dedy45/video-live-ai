<script lang="ts">
  import { onMount } from 'svelte';
  import { getIncidents, ackIncident } from '../../lib/api';
  import type { Incident } from '../../lib/types';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let incidents = $state<Incident[]>([]);
  let loading = $state(true);
  let error = $state('');
  let receipt = $state<ReceiptType | null>(null);

  async function loadIncidents() {
    try {
      incidents = await getIncidents() as Incident[];
      error = '';
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function acknowledge(id: string) {
    try {
      const result = await ackIncident(id);
      receipt = {
        action: 'incident.ack',
        status: result.status === 'error' ? 'error' : 'success',
        message: result.message,
        timestamp: Date.now(),
      };
      await loadIncidents();
    } catch (e: any) {
      receipt = {
        action: 'incident.ack',
        status: 'error',
        message: e.message,
        timestamp: Date.now(),
      };
    }
  }

  onMount(loadIncidents);
</script>

<div class="panel" data-testid="incidents-panel">
  <div class="panel-header">
    <h2 class="panel-title">Incidents</h2>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading incidents...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if incidents.length === 0}
    <p class="muted">No open incidents.</p>
  {:else}
    <div class="list">
      {#each incidents as incident}
        <div class="row">
          <div class="meta">
            <div class="sev">{incident.severity}</div>
            <div class="code">{incident.code}</div>
            <div class="subsystem">{incident.subsystem}</div>
          </div>
          <button class="btn btn-ghost" onclick={() => acknowledge(incident.id)}>Acknowledge</button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .list { display: flex; flex-direction: column; gap: 10px; }
  .row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); }
  .meta { display: grid; gap: 4px; }
  .sev { font-size: 11px; text-transform: uppercase; font-weight: 800; color: var(--accent); }
  .code { font-weight: 700; color: var(--text); }
  .subsystem { font-size: 12px; color: var(--muted); }
  .btn { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--rsm); background: var(--card); color: var(--text); cursor: pointer; }
  .btn-ghost { background: var(--card); }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
