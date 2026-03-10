<script lang="ts">
  import { onMount } from 'svelte';
  import { getOpsSummary } from '../../lib/api';
  import type { OpsSummary } from '../../lib/types';

  let summary = $state<OpsSummary | null>(null);
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    try {
      summary = await getOpsSummary() as OpsSummary;
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  const restartCount = $derived(
    summary ? summary.restart_counters.voice + summary.restart_counters.face + summary.restart_counters.stream : 0
  );
</script>

<div class="panel" data-testid="ops-summary-panel">
  <div class="panel-header">
    <h2 class="panel-title">Ringkasan Operasional</h2>
  </div>

  {#if loading}
    <p class="muted">Memuat ringkasan operasional...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if !summary}
    <p class="muted">Ringkasan operasional tidak tersedia.</p>
  {:else}
    <div class="grid">
      <div class="card"><div class="label">Status Keseluruhan</div><div class="value">{summary.overall_status}</div></div>
      <div class="card"><div class="label">Mode Deployment</div><div class="value">{summary.deployment_mode}</div></div>
      <div class="card"><div class="label">Jumlah Restart</div><div class="value">{restartCount}</div></div>
      <div class="card"><div class="label">Tingkat Insiden</div><div class="value">{summary.incident_summary.highest_severity}</div></div>
      <div class="card"><div class="label">Suara / Wajah / Stream</div><div class="value">{summary.voice_status} / {summary.face_status} / {summary.stream_status}</div></div>
      <div class="card"><div class="label">Tekanan Resource</div><div class="value">CPU {summary.resource_metrics.cpu_pct}% · RAM {summary.resource_metrics.ram_pct}% · Disk {summary.resource_metrics.disk_pct}%</div></div>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 16px; border: 1px solid var(--border); }
  .label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .value { font-size: 14px; font-weight: 600; color: var(--text); word-break: break-word; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
