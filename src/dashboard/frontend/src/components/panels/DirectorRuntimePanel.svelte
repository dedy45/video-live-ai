<script lang="ts">
  import Card from '../common/Card.svelte';
  import type { DirectorRuntimeContract } from '../../lib/types';

  interface Props {
    runtime: DirectorRuntimeContract | null;
    loading?: boolean;
    error?: string;
  }

  let { runtime, loading = false, error = '' }: Props = $props();

  function labelPhase(phase: string): string {
    return phase.replaceAll('_', ' ');
  }

  function labelFlag(active: boolean, onLabel: string, offLabel: string): string {
    return active ? onLabel : offLabel;
  }
</script>

<Card title="Director Runtime" size="lg">
  <p class="panel-copy">Status show director yang menentukan fase live, provider aktif, prompt aktif, dan jalur transisi sesi.</p>

  {#if loading}
    <div class="panel-state">Memuat runtime director...</div>
  {:else if error}
    <div class="panel-state panel-state-error" role="status">{error}</div>
  {:else if !runtime}
    <div class="panel-state">Runtime director belum tersedia.</div>
  {:else}
    <div class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">State</span>
        <strong>{runtime.director.state}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Fase aktif</span>
        <strong>{labelPhase(runtime.script.current_phase)}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Provider aktif</span>
        <strong>{runtime.brain.active_provider}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Prompt aktif</span>
        <strong>{runtime.prompt.active_revision}</strong>
      </div>
    </div>

    <div class="flag-strip">
      <span class="flag-chip">{labelFlag(runtime.director.stream_running, 'Stream berjalan', 'Stream belum jalan')}</span>
      <span class="flag-chip">{labelFlag(runtime.director.emergency_stopped, 'Stop darurat aktif', 'Stop darurat aman')}</span>
      <span class="flag-chip">{labelFlag(runtime.director.manual_override, 'Override manual aktif', 'Mode otomatis')}</span>
    </div>

    <div class="phase-track">
      {#each runtime.script.phase_sequence as phase}
        <div class:phase-active={phase === runtime.script.current_phase} class="phase-pill">{labelPhase(phase)}</div>
      {/each}
    </div>

    <div class="history-block">
      <div class="summary-label">Transisi terakhir</div>
      {#if runtime.director.history.length > 0}
        {#each runtime.director.history.slice(-3).reverse() as item}
          <div class="history-row">
            <span>{item.from}</span>
            <strong>{item.to}</strong>
          </div>
        {/each}
      {:else}
        <div class="panel-copy">Belum ada riwayat transisi pada sesi ini.</div>
      {/if}
    </div>
  {/if}
</Card>

<style>
  .panel-copy,
  .panel-state {
    color: var(--muted);
    line-height: 1.6;
  }

  .panel-state {
    margin-top: 16px;
    padding: 16px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.03);
  }

  .panel-state-error {
    border-color: rgba(233, 69, 96, 0.28);
    color: var(--text);
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(190px, 100%), 1fr));
    gap: 12px;
    margin-top: 16px;
  }

  .summary-card,
  .history-row {
    padding: 14px;
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
  }

  .summary-label {
    display: block;
    margin-bottom: 8px;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .flag-strip,
  .phase-track {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 16px;
  }

  .flag-chip,
  .phase-pill {
    padding: 9px 12px;
    border-radius: 999px;
    border: 1px solid rgba(34, 211, 238, 0.2);
    background: rgba(34, 211, 238, 0.08);
    font-size: 12px;
    font-weight: 700;
  }

  .phase-pill {
    border-color: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.04);
    color: var(--muted);
    text-transform: capitalize;
  }

  .phase-active {
    background: rgba(233, 69, 96, 0.18);
    border-color: rgba(233, 69, 96, 0.26);
    color: var(--text);
  }

  .history-block {
    display: grid;
    gap: 10px;
    margin-top: 18px;
  }

  .history-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
  }

  .history-row span {
    color: var(--muted);
  }
</style>
